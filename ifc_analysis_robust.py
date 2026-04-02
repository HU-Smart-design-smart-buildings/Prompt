#!/usr/bin/env python
"""
Robust IFC Format Comparison - Handles both IFC 2.3 and IFC 4.3 safely
"""

import sys
import os
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Any, Optional

def extract_schema_from_file_header(filepath: str) -> str:
    """Extract schema version directly from IFC file header"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(2000)  # Read first 2000 chars
            if 'IFC4' in content or 'IFC4X3' in content:
                return 'IFC 4.3' if '4.3' in content or 'IFC4X3' in content else 'IFC 4.0'
            elif 'IFC2X3' in content:
                return 'IFC 2.3'
            elif 'IFC2X4' in content:
                return 'IFC 2.4'
    except:
        pass
    return "Unknown"

def analyze_ifc_file_safe(filepath: str) -> Optional[Dict[str, Any]]:
    """Safely analyze IFC file without relying on ifcopenshell"""
    
    result = {
        'filepath': filepath,
        'filename': os.path.basename(filepath),
        'size_mb': os.path.getsize(filepath) / (1024 * 1024),
        'schema_version': extract_schema_from_file_header(filepath),
        'material_types_found': [],
        'property_sets_found': [],
        'quantity_types_found': [],
        'element_summary': {},
    }
    
    # Parse file to extract metadata
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Count material types
            material_types = [
                'IfcMaterial',
                'IfcMaterialList', 
                'IfcMaterialLayer',
                'IfcMaterialLayerSet',
                'IfcMaterialLayerSetUsage',
                'IfcMaterialProfile',
                'IfcMaterialProfileSet',
                'IfcMaterialProfileSetUsage',
                'IfcMaterialConstituentSet',
                'IfcMaterialConstituent'
            ]
            
            for material_type in material_types:
                count = content.count(f'#{material_type}')
                if count > 0:
                    result['material_types_found'].append({
                        'type': material_type,
                        'count': count
                    })
            
            # Count property sets
            pset_count = content.count('IfcPropertySet')
            qset_count = content.count('IfcElementQuantities')
            
            if pset_count > 0:
                result['property_sets_found'].append({
                    'type': 'IfcPropertySet',
                    'count': pset_count
                })
            
            if qset_count > 0:
                result['property_sets_found'].append({
                    'type': 'IfcElementQuantities', 
                    'count': qset_count
                })
            
            # Count quantity types
            quantity_types = [
                'IfcQuantityVolume',
                'IfcQuantityArea',
                'IfcQuantityLength',
                'IfcQuantityCount',
                'IfcQuantityWeight',
                'IfcQuantityTime'
            ]
            
            for qty_type in quantity_types:
                count = content.count(qty_type)
                if count > 0:
                    result['quantity_types_found'].append({
                        'type': qty_type,
                        'count': count
                    })
            
            # Count major element types
            element_types = [
                'IfcWall', 'IfcDoor', 'IfcWindow', 'IfcSlab', 'IfcRoof',
                'IfcColumn', 'IfcBeam', 'IfcStair', 'IfcRamp',
                'IfcSite', 'IfcBuilding', 'IfcBuildingStorey',
                'IfcSpace', 'IfcFurniture'
            ]
            
            for elem_type in element_types:
                count = content.count(f'#{elem_type}')
                if count > 0:
                    result['element_summary'][elem_type] = count
    
    except Exception as e:
        result['error'] = str(e)
    
    return result

def load_with_ifcopenshell_safe(filepath: str) -> Optional[Dict[str, Any]]:
    """Attempt to use ifcopenshell if available, with fallback"""
    try:
        import ifcopenshell
        
        file = ifcopenshell.open(filepath)
        schema = file.schema if hasattr(file, 'schema') else 'Unknown'
        
        result = {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'schema_version': schema,
            'total_entities': 0,
            'entity_types': {},
            'material_entities': {},
        }
        
        # Count entities
        entity_count = 0
        entity_types = defaultdict(int)
        material_types = defaultdict(int)
        
        # Safely iterate through entities
        try:
            for entity in file:
                entity_count += 1
                entity_type = entity.is_a()
                entity_types[entity_type] += 1
                
                # Track material types
                if 'Material' in entity_type:
                    material_types[entity_type] += 1
        except:
            pass
        
        result['total_entities'] = entity_count
        result['entity_types'] = dict(sorted(entity_types.items(), key=lambda x: x[1], reverse=True)[:20])
        result['material_entities'] = dict(material_types)
        
        return result
    
    except Exception as e:
        return None

def compare_analysis(file23_path: str, file43_path: str):
    """Perform safe comparison of IFC files"""
    
    print("\n" + "="*90)
    print("IFC FORMAT COMPARISON: IFC 2.3 vs IFC 4.3")
    print("="*90)
    
    # Try with ifcopenshell first, fall back to text parsing
    print("\nAttempting to load files with ifcopenshell...")
    
    result23 = load_with_ifcopenshell_safe(file23_path)
    result43 = load_with_ifcopenshell_safe(file43_path)
    
    if result23 is None:
        print("ifcopenshell failed, using text-based analysis...")
        result23 = analyze_ifc_file_safe(file23_path)
    
    if result43 is None:
        print("ifcopenshell failed, using text-based analysis...")
        result43 = analyze_ifc_file_safe(file43_path)
    
    if result23 is None or result43 is None:
        print("ERROR: Could not analyze files")
        return
    
    # Print detailed results
    print("\n" + "-"*90)
    print(f"FILE 1: {result23['filename']}")
    print("-"*90)
    print(f"Schema Version: {result23.get('schema_version', 'Unknown')}")
    print(f"File Size: {result23.get('size_mb', 0):.2f} MB")
    
    if 'total_entities' in result23:
        print(f"Total Entities: {result23['total_entities']}")
        if result23.get('entity_types'):
            print(f"\nTop 10 Entity Types:")
            for entity_type, count in list(result23['entity_types'].items())[:10]:
                print(f"  {entity_type:40s}: {count:6d}")
    
    if result23.get('element_summary'):
        print(f"\nBuildingElement Summary:")
        for elem_type, count in sorted(result23['element_summary'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {elem_type:40s}: {count:6d}")
    
    if result23.get('material_types_found'):
        print(f"\nMaterial Types:")
        for mat in result23['material_types_found']:
            print(f"  {mat['type']:40s}: {mat['count']:6d}")
    
    if result23.get('property_sets_found'):
        print(f"\nProperty & Quantity Sets:")
        for pset in result23['property_sets_found']:
            print(f"  {pset['type']:40s}: {pset['count']:6d}")
    
    if result23.get('quantity_types_found'):
        print(f"\nQuantity Types:")
        for qty in result23['quantity_types_found']:
            print(f"  {qty['type']:40s}: {qty['count']:6d}")
    
    # File 2 analysis
    print("\n" + "-"*90)
    print(f"FILE 2: {result43['filename']}")
    print("-"*90)
    print(f"Schema Version: {result43.get('schema_version', 'Unknown')}")
    print(f"File Size: {result43.get('size_mb', 0):.2f} MB")
    
    if 'total_entities' in result43:
        print(f"Total Entities: {result43['total_entities']}")
        if result43.get('entity_types'):
            print(f"\nTop 10 Entity Types:")
            for entity_type, count in list(result43['entity_types'].items())[:10]:
                print(f"  {entity_type:40s}: {count:6d}")
    
    if result43.get('element_summary'):
        print(f"\nBuildingElement Summary:")
        for elem_type, count in sorted(result43['element_summary'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {elem_type:40s}: {count:6d}")
    
    if result43.get('material_types_found'):
        print(f"\nMaterial Types:")
        for mat in result43['material_types_found']:
            print(f"  {mat['type']:40s}: {mat['count']:6d}")
    
    if result43.get('property_sets_found'):
        print(f"\nProperty & Quantity Sets:")
        for pset in result43['property_sets_found']:
            print(f"  {pset['type']:40s}: {pset['count']:6d}")
    
    if result43.get('quantity_types_found'):
        print(f"\nQuantity Types:")
        for qty in result43['quantity_types_found']:
            print(f"  {qty['type']:40s}: {qty['count']:6d}")
    
    # COMPARISON SUMMARY
    print("\n" + "="*90)
    print("SCHEMA-SPECIFIC DIFFERENCES & RECOMMENDATIONS")
    print("="*90)
    
    schema23 = result23.get('schema_version', 'IFC 2.3')
    schema43 = result43.get('schema_version', 'IFC 4.3')
    
    print(f"\n1. SCHEMA VERSIONS:")
    print(f"   File 1: {schema23}")
    print(f"   File 2: {schema43}")
    
    print(f"\n2. MATERIAL HANDLING DIFFERENCES:")
    print(f"\n   IFC 2.3 / 2X3:")
    print(f"   - Primary material containers: IfcMaterial, IfcMaterialList")
    print(f"   - Layer support: IfcMaterialLayerSet, IfcMaterialLayerSetUsage")
    print(f"   - No profile set support")
    print(f"   - No constituent set support")
    
    print(f"\n   IFC 4.0 / 4.3:")
    print(f"   - Expanded material system")
    print(f"   - Added: IfcMaterialProfileSet, IfcMaterialProfileSetUsage")
    print(f"   - Added: IfcMaterialConstituentSet for composite materials")
    print(f"   - Improved layer set usage")
    
    mat_types_23 = {m['type'] for m in result23.get('material_types_found', [])}
    mat_types_43 = {m['type'] for m in result43.get('material_types_found', [])}
    
    only_in_23 = mat_types_23 - mat_types_43
    only_in_43 = mat_types_43 - mat_types_23
    
    if only_in_23:
        print(f"\n   Material Types ONLY in {schema23}:")
        for mat_type in sorted(only_in_23):
            print(f"   - {mat_type}")
    
    if only_in_43:
        print(f"\n   Material Types ONLY in {schema43}:")
        for mat_type in sorted(only_in_43):
            print(f"   - {mat_type}")
    
    print(f"\n3. QUANTITY TYPES ANALYSIS:")
    qty_types_23 = {q['type'] for q in result23.get('quantity_types_found', [])}
    qty_types_43 = {q['type'] for q in result43.get('quantity_types_found', [])}
    
    common_qty = qty_types_23 & qty_types_43
    only_in_23_qty = qty_types_23 - qty_types_43
    only_in_43_qty = qty_types_43 - qty_types_23
    
    print(f"   Common quantity types: {', '.join(sorted(common_qty)) if common_qty else 'None'}")
    if only_in_23_qty:
        print(f"   Only in {schema23}: {', '.join(sorted(only_in_23_qty))}")
    if only_in_43_qty:
        print(f"   Only in {schema43}: {', '.join(sorted(only_in_43_qty))}")
    
    print(f"\n4. RECOMMENDATIONS FOR HANDLING BOTH VERSIONS:")
    print(f"\n   a) Schema Detection:")
    print(f"      - Parse FILE_SCHEMA line in IFC file header")
    print(f"      - Check for 'IFC2X3' (version 2.3) vs 'IFC4' (version 4.x)")
    print(f"      - Store schema version as metadata")
    
    print(f"\n   b) Material Extraction:")
    print(f"      - Use conditional entity type queries based on schema")
    print(f"      - For IFC2.3: Query IfcMaterial, IfcMaterialList, IfcMaterialLayerSet")
    print(f"      - For IFC4.x: Include profile sets and constituent sets")
    print(f"      - Wrap queries in try-except for unknown types")
    
    print(f"\n   c) Property & Quantity Handling:")
    print(f"      - Both versions use IfcPropertySet (compatible)")
    print(f"      - Both versions use IfcElementQuantities (compatible)")
    print(f"      - Validate quantity types before use")
    
    print(f"\n   d) Code Strategy:")
    print(f"      - Create version-aware handler class")
    print(f"      - Define material type lists per schema version")
    print(f"      - Use safe iteration with error handling")
    print(f"      - Normalize output for both versions")
    
    print("\n" + "="*90 + "\n")

if __name__ == '__main__':
    file23 = r'C:\Users\cathy\Downloads\Prompt\23BIM.ifc'
    file43 = r'C:\Users\cathy\Downloads\Prompt\43BIM.ifc'
    
    compare_analysis(file23, file43)
