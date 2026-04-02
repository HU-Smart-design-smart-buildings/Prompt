"""
Quick IFC analysis using text parsing to identify schema differences
"""

def analyze_ifc_text(filepath):
    """Analyze IFC file by text parsing"""
    result = {
        'schema': None,
        'material_types': [],
        'quantity_types': [],
        'elements': [],
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            # Find schema in FILE_SCHEMA line
            import re
            schema_match = re.search(r'FILE_SCHEMA\s*\(\s*\(\'([^\']+)\'\)', content)
            if schema_match:
                result['schema'] = schema_match.group(1)
            
            # Find material types
            material_patterns = [
                'IfcMaterial', 'IfcMaterialList', 'IfcMaterialLayer',
                'IfcMaterialLayerSet', 'IfcMaterialLayerSetUsage',
                'IfcMaterialProfile', 'IfcMaterialProfileSet',
                'IfcMaterialConstituentSet', 'IfcMaterialConstituent'
            ]
            
            for mat in material_patterns:
                if f'#{mat}' in content:
                    count = content.count(f'#{mat}')
                    result['material_types'].append((mat, count))
            
            # Find quantity types
            qty_patterns = [
                'IfcQuantityVolume', 'IfcQuantityArea', 'IfcQuantityLength',
                'IfcQuantityCount', 'IfcQuantityWeight'
            ]
            
            for qty in qty_patterns:
                if qty in content:
                    count = content.count(qty)
                    result['quantity_types'].append((qty, count))
            
            # Find element types
            element_patterns = [
                'IfcWall', 'IfcDoor', 'IfcWindow', 'IfcSlab', 'IfcRoof',
                'IfcColumn', 'IfcBeam', 'IfcStair'
            ]
            
            for elem in element_patterns:
                if f'#{elem}' in content:
                    count = content.count(f'#{elem}')
                    result['elements'].append((elem, count))
    
    except Exception as e:
        result['error'] = str(e)
    
    return result

# Analyze both files
file23 = "23BIM.ifc"
file43 = "43BIM.ifc"

print("\n" + "="*80)
print("IFC FILE ANALYSIS - SCHEMA DIFFERENCES")
print("="*80)

result23 = analyze_ifc_text(file23)
result43 = analyze_ifc_text(file43)

print(f"\nFile: {file23}")
print(f"Schema: {result23.get('schema', 'Unknown')}")
print("\nMaterial Types:")
for mat, count in result23.get('material_types', []):
    print(f"  - {mat}: {count}")
print("\nQuantity Types:")
for qty, count in result23.get('quantity_types', []):
    print(f"  - {qty}: {count}")
print("\nElement Types:")
for elem, count in result23.get('elements', []):
    print(f"  - {elem}: {count}")

print(f"\n{'-'*80}")

print(f"\nFile: {file43}")
print(f"Schema: {result43.get('schema', 'Unknown')}")
print("\nMaterial Types:")
for mat, count in result43.get('material_types', []):
    print(f"  - {mat}: {count}")
print("\nQuantity Types:")
for qty, count in result43.get('quantity_types', []):
    print(f"  - {qty}: {count}")
print("\nElement Types:")
for elem, count in result43.get('elements', []):
    print(f"  - {elem}: {count}")

print(f"\n{'-'*80}")
print("\nKEY DIFFERENCES:")

mat23_types = set(m[0] for m in result23.get('material_types', []))
mat43_types = set(m[0] for m in result43.get('material_types', []))

only_23 = mat23_types - mat43_types
only_43 = mat43_types - mat23_types

if only_23:
    print(f"\nMaterial types ONLY in {result23.get('schema', 'IFC 2.3')}:")
    for m in sorted(only_23):
        print(f"  - {m}")

if only_43:
    print(f"\nMaterial types ONLY in {result43.get('schema', 'IFC 4.3')}:")
    for m in sorted(only_43):
        print(f"  - {m}")

common = mat23_types & mat43_types
if common:
    print(f"\nMaterial types in BOTH versions:")
    for m in sorted(common):
        print(f"  - {m}")
