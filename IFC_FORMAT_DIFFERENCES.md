# IFC Format Analysis: 2X3 vs 4X3

## File Information
- **23BIM.ifc**: Schema = IFC2X3
- **43BIM.ifc**: Schema = IFC4X3_ADD2

## Material Entity Type Comparison

| Entity Type | IFC2X3 | IFC4X3_ADD2 | Status |
|-------------|--------|-----------|--------|
| IfcMaterial | 1789 | 3748 | ✓ Both |
| IfcMaterialLayerSet | 1531 | 177 | ✓ Both |
| IfcMaterialLayerSetUsage | Present | Present | ✓ Both |
| IfcMaterialConstituentSet | ✗ NOT FOUND | 831 | ⚠ IFC4 Only |
| IfcMaterialProfileSet | ✗ NOT FOUND | 36 | ⚠ IFC4 Only |

## Property Sets Comparison

| Entity Type | IFC2X3 | IFC4X3_ADD2 |
|-------------|--------|-----------|
| IfcPropertySet | 13,307 | 47,741 |

## Key Findings

### IFC2X3 Characteristics
- Primary material representation: `IfcMaterial`
- Layer-based composites: `IfcMaterialLayerSet` + `IfcMaterialLayerSetUsage`
- No support for constituent sets
- No support for profile-based materials
- Property sets are present

### IFC4X3_ADD2 Characteristics
- All IFC2X3 material types supported (backwards compatible)
- **NEW**: `IfcMaterialConstituentSet` (831 instances) - for composite materials with fractions
- **NEW**: `IfcMaterialProfileSet` (36 instances) - for profile-based structural materials
- Significantly more property sets (3.6x increase)
- Enhanced material representation capabilities

## Extraction Strategy

### Phase-Specific Handling

**Fase 5 - Materiaaltypen Bepalen (Updated)**

1. **Base material handling (both IFC2X3 & IFC4X3):**
   - `IfcMaterial` → Extract .Name directly
   - `IfcMaterialList` → Iterate .Materials, extract each .Name

2. **Layer-based materials (both versions):**
   - `IfcMaterialLayerSet` → Iterate .MaterialLayers
     - Per layer: Extract .Material.Name + .LayerThickness
   - `IfcMaterialLayerSetUsage` → Via .ForLayerSet.MaterialLayers

3. **IFC4 Extended materials (schema check required):**
   ```python
   if schema == "IFC4X3_ADD2":
       # IfcMaterialConstituentSet (831 instances)
       # - For composite materials
       # - Access: .MaterialConstituents
       # - Per constituent: .Material.Name + .Fraction
       
       # IfcMaterialProfileSet (36 instances)
       # - For profiled materials (e.g., structural steel)
       # - Access: .MaterialProfiles
       # - Per profile: .Material.Name + .Profile reference
   ```

### Code Implementation Pattern

```python
def extract_material_from_element(element, schema):
    materials = []
    
    for rel in element.HasAssociations:
        if not rel.is_a("IfcRelAssociatesMaterial"):
            continue
        
        mat = rel.RelatingMaterial
        mat_type = mat.is_a()
        
        # Universal handlers (both schemas)
        if mat_type == "IfcMaterial":
            materials.append({
                'name': mat.Name,
                'type': 'Simple',
                'schema': schema
            })
        
        elif mat_type == "IfcMaterialLayerSet":
            for layer in mat.MaterialLayers:
                materials.append({
                    'name': layer.Material.Name,
                    'type': 'Layer',
                    'thickness': layer.LayerThickness,
                    'schema': schema
                })
        
        # IFC4 specific
        elif schema == "IFC4X3_ADD2":
            if mat_type == "IfcMaterialConstituentSet":
                for constituent in mat.MaterialConstituents:
                    materials.append({
                        'name': constituent.Material.Name,
                        'type': 'Constituent',
                        'fraction': constituent.Fraction,
                        'schema': schema
                    })
            
            elif mat_type == "IfcMaterialProfileSet":
                for profile in mat.MaterialProfiles:
                    materials.append({
                        'name': profile.Material.Name,
                        'type': 'Profile',
                        'profile_ref': profile.Profile,
                        'schema': schema
                    })
    
    return materials
```

## Recommendations

1. **Schema Detection (Fase 2)**
   - Always read FILE_SCHEMA from IFC header
   - Store as metadata in all output records
   - Use for conditional processing in Fase 5+

2. **Material Extraction (Fase 5)**
   - Implement base handlers first (universal)
   - Add conditional schema checks for IFC4 features
   - Wrap with try-except for forward compatibility

3. **Testing**
   - Test all material paths with both files
   - Verify IfcMaterialConstituentSet extraction (IFC4 only)
   - Verify IfcMaterialProfileSet extraction (IFC4 only)
   - Ensure IFC2X3 handling is robust (no errors on unknown types)

4. **Output**
   - Include 'ifc_schema' column in all exports
   - Document material_type separately
   - Track extraction confidence per entity
