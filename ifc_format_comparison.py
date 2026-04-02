#!/usr/bin/env python
"""
IFC Format Comparison Tool: Analyzes differences between IFC 2.3 and IFC 4.3 files
Examines schema versions, element types, materials, properties, and quantities
"""

import sys
import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple, Any

try:
    import ifcopenshell
    import ifcopenshell.util
except ImportError:
    print("ERROR: ifcopenshell not installed. Install with: pip install ifcopenshell")
    sys.exit(1)


class IFCAnalyzer:
    """Comprehensive IFC file analyzer for version comparison"""
    
    # Material-related entity types
    MATERIAL_ENTITIES = {
        'IfcMaterial',
        'IfcMaterialList',
        'IfcMaterialLayer',
        'IfcMaterialLayerSet',
        'IfcMaterialLayerSetUsage',
        'IfcMaterialProfile',
        'IfcMaterialProfileSet',
        'IfcMaterialProfileSetUsage',
        'IfcMaterialConstituentSet',
        'IfcMaterialConstituent',
        'IfcMaterialProperties'
    }
    
    # Property and quantity entity types
    PROPERTY_ENTITIES = {
        'IfcPropertySet',
        'IfcElementQuantities',
        'IfcProperty',
        'IfcSimpleProperty',
        'IfcComplexProperty'
    }
    
    def __init__(self, filepath: str):
        """Initialize analyzer with IFC file"""
        self.filepath = Path(filepath)
        self.file = None
        self.schema_version = None
        self.analysis_results = {}
        
    def load(self) -> bool:
        """Load IFC file"""
        try:
            self.file = ifcopenshell.open(str(self.filepath))
            return True
        except Exception as e:
            print(f"ERROR: Failed to load {self.filepath}: {e}")
            return False
    
    def get_schema_version(self) -> str:
        """Extract schema version from file header"""
        if not self.file:
            return "Unknown"
        
        # Parse FILE_SCHEMA from IFC file
        with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'FILE_SCHEMA' in line:
                    # Extract version from FILE_SCHEMA line
                    if 'IFC4' in line:
                        return 'IFC 4.3' if '4.3' in line or 'IFC4X3' in line else 'IFC 4.0'
                    elif 'IFC2X3' in line:
                        return 'IFC 2.3'
                    elif 'IFC2X4' in line:
                        return 'IFC 2.4'
        return "Unknown"
    
    def get_element_types(self) -> Dict[str, int]:
        """Count all element types in file"""
        entity_counts = defaultdict(int)
        
        for entity in self.file.by_type("IfcRoot"):
            entity_type = entity.is_a()
            entity_counts[entity_type] += 1
        
        return dict(sorted(entity_counts.items()))
    
    def get_material_types(self) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze material entities available and used"""
        material_data = {}
        
        for material_type in self.MATERIAL_ENTITIES:
            try:
                entities = self.file.by_type(material_type)
                if entities:
                    material_data[material_type] = {
                        'count': len(entities),
                        'samples': []
                    }
                    # Get sample data
                    for entity in entities[:2]:  # First 2 samples
                        sample = {
                            'id': entity.id(),
                            'name': getattr(entity, 'Name', None),
                            'description': getattr(entity, 'Description', None),
                        }
                        material_data[material_type]['samples'].append(sample)
            except:
                pass
        
        return material_data
    
    def get_property_sets(self) -> Dict[str, Any]:
        """Analyze Property Sets (Pset) and Element Quantities (Qto)"""
        pset_data = {
            'property_sets': defaultdict(int),
            'element_quantities': defaultdict(int),
            'total_properties': 0,
            'total_quantities': 0
        }
        
        # Analyze Property Sets
        try:
            psets = self.file.by_type("IfcPropertySet")
            for pset in psets:
                pset_name = getattr(pset, 'Name', 'Unknown')
                pset_data['property_sets'][pset_name] += 1
                if hasattr(pset, 'HasProperties'):
                    pset_data['total_properties'] += len(pset.HasProperties)
        except:
            pass
        
        # Analyze Element Quantities
        try:
            qsets = self.file.by_type("IfcElementQuantities")
            for qset in qsets:
                qset_name = getattr(qset, 'Name', 'Unknown')
                pset_data['element_quantities'][qset_name] += 1
                if hasattr(qset, 'Quantities'):
                    pset_data['total_quantities'] += len(qset.Quantities)
        except:
            pass
        
        return {
            'property_sets': dict(pset_data['property_sets']),
            'element_quantities': dict(pset_data['element_quantities']),
            'total_properties': pset_data['total_properties'],
            'total_quantities': pset_data['total_quantities']
        }
    
    def get_quantity_types(self) -> Dict[str, int]:
        """Analyze specific quantity types used"""
        quantity_types = defaultdict(int)
        
        try:
            qsets = self.file.by_type("IfcElementQuantities")
            for qset in qsets:
                if hasattr(qset, 'Quantities'):
                    for quantity in qset.Quantities:
                        qty_type = quantity.is_a()
                        quantity_types[qty_type] += 1
        except:
            pass
        
        return dict(sorted(quantity_types.items()))
    
    def get_schema_entities(self) -> Set[str]:
        """Get all unique entity types used in file"""
        entities = set()
        try:
            for entity in self.file:
                entities.add(entity.is_a())
        except:
            pass
        return entities
    
    def analyze(self) -> Dict[str, Any]:
        """Perform complete analysis"""
        if not self.load():
            return None
        
        self.schema_version = self.get_schema_version()
        
        results = {
            'filepath': str(self.filepath),
            'schema_version': self.schema_version,
            'file_size_mb': self.filepath.stat().st_size / (1024 * 1024),
            'element_types': self.get_element_types(),
            'material_types': self.get_material_types(),
            'property_data': self.get_property_sets(),
            'quantity_types': self.get_quantity_types(),
            'all_entities': sorted(self.get_schema_entities())
        }
        
        self.analysis_results = results
        return results
    
    def print_summary(self):
        """Print formatted summary of analysis"""
        if not self.analysis_results:
            print("ERROR: No analysis results. Call analyze() first.")
            return
        
        r = self.analysis_results
        print(f"\n{'='*80}")
        print(f"FILE: {self.filepath.name}")
        print(f"{'='*80}")
        print(f"Schema Version: {r['schema_version']}")
        print(f"File Size: {r['file_size_mb']:.2f} MB")
        print(f"\nTotal Entities: {len(r['all_entities'])}")
        
        # Element type breakdown
        print(f"\nTop 15 Element Types by Count:")
        print(f"{'-'*80}")
        sorted_elements = sorted(r['element_types'].items(), key=lambda x: x[1], reverse=True)
        for entity_type, count in sorted_elements[:15]:
            print(f"  {entity_type:40s}: {count:6d}")
        
        # Material types
        if r['material_types']:
            print(f"\nMaterial Types Available:")
            print(f"{'-'*80}")
            for material_type, data in sorted(r['material_types'].items()):
                print(f"  {material_type:40s}: {data['count']:6d} instances")
        else:
            print(f"\nMaterial Types: NONE FOUND")
        
        # Properties and Quantities
        pdata = r['property_data']
        print(f"\nProperty & Quantity Summary:")
        print(f"{'-'*80}")
        print(f"  Property Sets: {len(pdata['property_sets'])} unique types, {pdata['total_properties']} total properties")
        print(f"  Element Quantities: {len(pdata['element_quantities'])} unique types, {pdata['total_quantities']} total quantities")
        
        if pdata['property_sets']:
            print(f"\n  Property Set Types:")
            for pset_name, count in sorted(pdata['property_sets'].items())[:10]:
                print(f"    {pset_name:40s}: {count:4d}")
        
        if pdata['element_quantities']:
            print(f"\n  Element Quantity Types:")
            for qset_name, count in sorted(pdata['element_quantities'].items())[:10]:
                print(f"    {qset_name:40s}: {count:4d}")
        
        # Quantity types
        if r['quantity_types']:
            print(f"\nQuantity Entity Types:")
            print(f"{'-'*80}")
            for qty_type, count in sorted(r['quantity_types'].items()):
                print(f"  {qty_type:40s}: {count:6d}")
        
        print(f"\n{'='*80}")


def compare_files(file23: str, file43: str):
    """Compare two IFC files and generate detailed report"""
    
    print("\n" + "="*80)
    print("IFC FORMAT COMPARISON: IFC 2.3 vs IFC 4.3")
    print("="*80)
    
    # Analyze both files
    analyzer23 = IFCAnalyzer(file23)
    analyzer43 = IFCAnalyzer(file43)
    
    results23 = analyzer23.analyze()
    results43 = analyzer43.analyze()
    
    if not results23 or not results43:
        print("ERROR: Failed to analyze files")
        return
    
    analyzer23.print_summary()
    analyzer43.print_summary()
    
    # Comparison analysis
    print("\n" + "="*80)
    print("COMPARATIVE ANALYSIS")
    print("="*80)
    
    # Schema differences
    print(f"\nSchema Versions:")
    print(f"  2.3 File: {results23['schema_version']}")
    print(f"  4.3 File: {results43['schema_version']}")
    
    # Entity type differences
    entities23 = set(results23['all_entities'])
    entities43 = set(results43['all_entities'])
    
    entities_only_in_23 = entities23 - entities43
    entities_only_in_43 = entities43 - entities23
    
    if entities_only_in_23:
        print(f"\nEntity Types ONLY in IFC 2.3 ({len(entities_only_in_23)}):")
        for entity in sorted(entities_only_in_23)[:10]:
            print(f"  - {entity}")
        if len(entities_only_in_23) > 10:
            print(f"  ... and {len(entities_only_in_23) - 10} more")
    
    if entities_only_in_43:
        print(f"\nEntity Types ONLY in IFC 4.3 ({len(entities_only_in_43)}):")
        for entity in sorted(entities_only_in_43)[:10]:
            print(f"  - {entity}")
        if len(entities_only_in_43) > 10:
            print(f"  ... and {len(entities_only_in_43) - 10} more")
    
    # Material type comparison
    print(f"\nMaterial Types Comparison:")
    print(f"{'-'*80}")
    
    materials_in_23 = set(results23['material_types'].keys())
    materials_in_43 = set(results43['material_types'].keys())
    
    for material_type in sorted(materials_in_23 | materials_in_43):
        count23 = results23['material_types'].get(material_type, {}).get('count', 0)
        count43 = results43['material_types'].get(material_type, {}).get('count', 0)
        status = ""
        if count23 > 0 and count43 == 0:
            status = " [ONLY in IFC 2.3]"
        elif count43 > 0 and count23 == 0:
            status = " [ONLY in IFC 4.3]"
        print(f"  {material_type:40s}: IFC2.3={count23:4d}  IFC4.3={count43:4d}{status}")
    
    # Property Sets comparison
    print(f"\nProperty Set Comparison:")
    print(f"{'-'*80}")
    psets23 = set(results23['property_data']['property_sets'].keys())
    psets43 = set(results43['property_data']['property_sets'].keys())
    
    print(f"  Total unique Property Set names in IFC2.3: {len(psets23)}")
    print(f"  Total unique Property Set names in IFC4.3: {len(psets43)}")
    
    if len(psets23 | psets43) <= 20:
        for pset in sorted(psets23 | psets43):
            print(f"    {pset:40s}: IFC2.3={results23['property_data']['property_sets'].get(pset, 0):4d}  IFC4.3={results43['property_data']['property_sets'].get(pset, 0):4d}")
    
    # Quantity types comparison
    print(f"\nQuantity Types Comparison:")
    print(f"{'-'*80}")
    qty_types23 = results23['quantity_types']
    qty_types43 = results43['quantity_types']
    
    for qty_type in sorted(set(qty_types23.keys()) | set(qty_types43.keys())):
        count23 = qty_types23.get(qty_type, 0)
        count43 = qty_types43.get(qty_type, 0)
        print(f"  {qty_type:40s}: IFC2.3={count23:4d}  IFC4.3={count43:4d}")
    
    print(f"\n{'='*80}\n")


def generate_handling_script():
    """Generate sample script for handling both IFC versions"""
    
    script = '''"""
Multi-Version IFC Handler: Supports both IFC 2.3 and IFC 4.3
Demonstrates proper schema-aware entity extraction and property handling
"""

import ifcopenshell
from typing import Optional, List, Dict, Any


class MultiVersionIFCHandler:
    """Handler for reading and processing both IFC 2.3 and 4.3 files"""
    
    # IFC 2.3 material types
    IFC23_MATERIALS = {
        'IfcMaterial',
        'IfcMaterialList',
        'IfcMaterialLayerSet',
        'IfcMaterialLayerSetUsage',
    }
    
    # IFC 4.x material types (additional/changed)
    IFC4_MATERIALS = {
        'IfcMaterial',
        'IfcMaterialLayerSet',
        'IfcMaterialLayerSetUsage',
        'IfcMaterialProfileSet',
        'IfcMaterialProfileSetUsage',
        'IfcMaterialConstituentSet',
    }
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.file = ifcopenshell.open(filepath)
        self.schema_version = self._detect_schema()
        self.is_ifc4 = self.schema_version.startswith('IFC4')
    
    def _detect_schema(self) -> str:
        """Detect IFC schema version from file"""
        try:
            schema = self.file.schema
            if '2X' in schema or '2x' in schema:
                return 'IFC2X3'
            elif '4' in schema:
                return 'IFC4'
        except:
            pass
        
        # Fallback: check FILE_SCHEMA
        with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if 'FILE_SCHEMA' in line:
                    if 'IFC4' in line or '4.3' in line:
                        return 'IFC4'
                    elif 'IFC2X' in line:
                        return 'IFC2X3'
        
        return 'Unknown'
    
    def get_materials(self) -> List[Dict[str, Any]]:
        """Extract materials, handling schema differences"""
        materials = []
        
        # Get appropriate material types for schema
        material_types = self.IFC4_MATERIALS if self.is_ifc4 else self.IFC23_MATERIALS
        
        for material_type in material_types:
            try:
                for material in self.file.by_type(material_type):
                    mat_dict = {
                        'type': material_type,
                        'id': material.id(),
                        'name': getattr(material, 'Name', None),
                        'description': getattr(material, 'Description', None),
                    }
                    
                    # Extract schema-specific properties
                    if material_type == 'IfcMaterialLayerSet':
                        if hasattr(material, 'MaterialLayers'):
                            mat_dict['layer_count'] = len(material.MaterialLayers)
                    
                    materials.append(mat_dict)
            except:
                pass
        
        return materials
    
    def get_element_quantities(self, element) -> Dict[str, Any]:
        """Extract quantities from element, handling schema differences"""
        quantities = {}
        
        try:
            # Method differs slightly between versions
            if hasattr(element, 'IsDefinedBy'):
                for rel in element.IsDefinedBy:
                    if rel.is_a('IfcRelDefinesByProperties'):
                        pset = rel.RelatingPropertyDefinition
                        if pset.is_a('IfcElementQuantities'):
                            for qty in pset.Quantities:
                                qty_type = qty.is_a()
                                qty_name = getattr(qty, 'Name', 'Unknown')
                                
                                # Common quantity properties
                                qty_value = None
                                if hasattr(qty, 'Value'):
                                    qty_value = qty.Value
                                
                                quantities[qty_name] = {
                                    'type': qty_type,
                                    'value': qty_value,
                                    'unit': getattr(qty, 'Unit', None),
                                }
        except:
            pass
        
        return quantities
    
    def get_properties(self, element) -> Dict[str, Dict[str, Any]]:
        """Extract properties from element"""
        properties = {}
        
        try:
            if hasattr(element, 'IsDefinedBy'):
                for rel in element.IsDefinedBy:
                    if rel.is_a('IfcRelDefinesByProperties'):
                        pset = rel.RelatingPropertyDefinition
                        if pset.is_a('IfcPropertySet'):
                            pset_name = getattr(pset, 'Name', 'Unknown')
                            properties[pset_name] = {}
                            
                            if hasattr(pset, 'HasProperties'):
                                for prop in pset.HasProperties:
                                    prop_name = getattr(prop, 'Name', 'Unknown')
                                    prop_value = getattr(prop, 'NominalValue', None)
                                    properties[pset_name][prop_name] = prop_value
        except:
            pass
        
        return properties
    
    def get_all_elements(self, element_type: str = 'IfcBuildingElement') -> List[Dict[str, Any]]:
        """Extract all elements of given type with properties and quantities"""
        elements = []
        
        try:
            for element in self.file.by_type(element_type):
                elem_dict = {
                    'id': element.id(),
                    'type': element.is_a(),
                    'name': getattr(element, 'Name', None),
                    'guid': getattr(element, 'GlobalId', None),
                    'properties': self.get_properties(element),
                    'quantities': self.get_element_quantities(element),
                }
                elements.append(elem_dict)
        except:
            pass
        
        return elements


# Usage Example
if __name__ == '__main__':
    # Handle IFC 2.3 file
    handler23 = MultiVersionIFCHandler('23BIM.ifc')
    print(f"IFC 2.3 Schema: {handler23.schema_version}")
    materials23 = handler23.get_materials()
    print(f"Materials found: {len(materials23)}")
    
    # Handle IFC 4.3 file
    handler43 = MultiVersionIFCHandler('43BIM.ifc')
    print(f"IFC 4.3 Schema: {handler43.schema_version}")
    materials43 = handler43.get_materials()
    print(f"Materials found: {len(materials43)}")
    
    # Get elements from both
    walls23 = handler23.get_all_elements('IfcWall')
    walls43 = handler43.get_all_elements('IfcWall')
    print(f"Walls in IFC 2.3: {len(walls23)}, IFC 4.3: {len(walls43)}")
'''
    
    return script


if __name__ == '__main__':
    file23 = r'C:\Users\cathy\Downloads\Prompt\23BIM.ifc'
    file43 = r'C:\Users\cathy\Downloads\Prompt\43BIM.ifc'
    
    # Perform comparison
    compare_files(file23, file43)
    
    # Generate handling script
    print("\n" + "="*80)
    print("SAMPLE MULTI-VERSION HANDLER SCRIPT")
    print("="*80)
    print(generate_handling_script())
