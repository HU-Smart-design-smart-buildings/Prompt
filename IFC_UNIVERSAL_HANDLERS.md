# Universele Handlers voor Materiaal- & Dimensie-Informatie uit IFC

## Analyse van beide IFC-bestanden

### Entity Type Overview

| Entity Type | IFC2X3 | IFC4X3 | Doel |
|-------------|--------|---------|------|
| **IfcWall, IfcSlab, IfcBeam, etc.** | 2,381 | 2,908 | Bouwelementen basis |
| **IfcPropertySet** | 13,307 | 47,741 | Basisgegevens per element |
| **IfcRelDefinesByProperties** | 11,985 | 44,918 | Koppeling element ↔ properties |
| **IfcRelDefinesByType** | 968 | 1,105 | Type-definities (parametrisch) |
| **IfcRelAssociatesClassification** | 47 | 49 | Classificatie/categorie |
| **IfcProductDefinitionShape** | 5,781 | 5,784 | Geometrie & representaties |
| **IfcExtrudedArea, IfcDirection** | 7,506 | 7,476 | Geometrie-primitieven |

## Handler 1: Property Sets (IfcPropertySet) - UNIVERSEEL

### Wat wordt gebruikt in testbestanden:
- `Pset_BuildingElementProxyCommon` - Algemene eigenschappen
- `Pset_QuantityTakeOff` - Materiaal/productinfo
- `Pset_SlabCommon` - Slab-specifieke data
- `Pset_ReinforcementBarPitchOfSlab` - Versterking specifiek
- `Pset_WallCommon` - Muur-specifieke data
- `Pset_DoorCommon` - Deur-specifieke data
- `Pset_WindowCommon` - Raam-specifieke data

### Implementatie Pattern:
```python
def extract_properties_from_element(element):
    """Extract all property sets linked to element"""
    properties = {}
    
    # Query: element.IsDefinedBy (both IFC2X3 and IFC4)
    if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
        for rel in element.IsDefinedBy:
            # Universal in both versions
            if rel.is_a("IfcRelDefinesByProperties"):
                prop_def = rel.RelatingPropertyDefinition
                
                if prop_def.is_a("IfcPropertySet"):
                    pset_name = prop_def.Name  # e.g., "Pset_SlabCommon"
                    properties[pset_name] = {}
                    
                    # Iterate all properties in set
                    for prop in prop_def.HasProperties:
                        prop_name = prop.Name
                        prop_value = None
                        
                        if prop.is_a("IfcPropertySingleValue"):
                            prop_value = prop.NominalValue.wrappedValue if prop.NominalValue else None
                        elif prop.is_a("IfcPropertyEnumeratedValue"):
                            prop_value = [v.wrappedValue for v in prop.EnumerationValues]
                        elif prop.is_a("IfcPropertyBoundedValue"):
                            prop_value = {
                                'min': prop.LowerBoundValue.wrappedValue if prop.LowerBoundValue else None,
                                'max': prop.UpperBoundValue.wrappedValue if prop.UpperBoundValue else None
                            }
                        
                        properties[pset_name][prop_name] = prop_value
    
    return properties
```

## Handler 2: Element Quantities (IfcElementQuantity) - UNIVERSEEL

### Beschikbare Quantity Types in beide versies:
- `IfcQuantityVolume` - Volume (m³)
- `IfcQuantityArea` - Oppervlakte (m²)
- `IfcQuantityLength` - Lengte (m)
- `IfcQuantityCount` - Aantal items
- `IfcQuantityWeight` - Gewicht (kg)

### Implementatie Pattern:
```python
def extract_quantities_from_element(element):
    """Extract all quantities (volumes, areas, lengths) from element"""
    quantities = {}
    
    # Query: element.IsDefinedBy (both versions)
    if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                prop_def = rel.RelatingPropertyDefinition
                
                if prop_def.is_a("IfcElementQuantity"):
                    qty_set_name = prop_def.Name
                    quantities[qty_set_name] = {}
                    
                    # Iterate quantities
                    for qty in prop_def.Quantities:
                        qty_type = qty.is_a()
                        qty_name = qty.Name
                        qty_value = qty.wrappedValue if hasattr(qty, 'wrappedValue') else None
                        
                        quantities[qty_set_name][qty_name] = {
                            'type': qty_type,
                            'value': qty_value,
                            'unit': 'varies by type'  # m3, m2, m, kg, etc.
                        }
    
    return quantities
```

## Handler 3: Element Type Definitions (IfcRelDefinesByType) - UNIVERSEEL

### Found: 968 (IFC2X3), 1,105 (IFC4X3)

### Doel: Parametrische/type-gebaseerde elementen koppelen

### Implementatie Pattern:
```python
def extract_element_type_reference(element):
    """Get element type definition for parametric properties"""
    type_info = None
    
    # Query: element.IsDefinedBy (both versions)
    if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
        for rel in element.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByType"):
                element_type = rel.RelatingType
                
                type_info = {
                    'type_name': element_type.Name if hasattr(element_type, 'Name') else None,
                    'type_id': element_type.GlobalId if hasattr(element_type, 'GlobalId') else None,
                    'type_class': element_type.is_a(),
                    'description': element_type.Description if hasattr(element_type, 'Description') else None,
                }
                
                # Type elements may have their own properties/quantities
                if hasattr(element_type, 'HasPropertySets') and element_type.HasPropertySets:
                    type_info['type_properties'] = extract_properties_from_element(element_type)
    
    return type_info
```

## Handler 4: Classification & Categories (IfcRelAssociatesClassification) - UNIVERSEEL

### Found: 47 (IFC2X3), 49 (IFC4X3)

### Doel: Elementen categoriseren per Uniformat/andere systems

### Implementatie Pattern:
```python
def extract_element_classification(element):
    """Extract classification tags for element"""
    classifications = []
    
    # Query: element.HasAssociations (both versions)
    if hasattr(element, 'HasAssociations') and element.HasAssociations:
        for rel in element.HasAssociations:
            if rel.is_a("IfcRelAssociatesClassification"):
                classifier = rel.RelatingClassification
                
                classifications.append({
                    'classification_system': classifier.ReferencedSource if hasattr(classifier, 'ReferencedSource') else None,
                    'classification_id': classifier.ItemReference if hasattr(classifier, 'ItemReference') else None,
                    'classification_name': classifier.Name if hasattr(classifier, 'Name') else None,
                })
    
    return classifications
```

## Handler 5: Material Density & Mass Properties - UNIVERSEEL

### Patroon in Pset_MaterialCommon (waar beschikbaar):
- `MassDensity` (kg/m³) - Via IfcPropertySingleValue met waarde in kg/m³
- `Flammability` (boolean)
- `SurfaceRoughness` (mm)

### Implementatie Pattern:
```python
def extract_material_properties(material):
    """Extract detailed material properties (density, cost, etc.)"""
    mat_props = {
        'material_name': material.Name if hasattr(material, 'Name') else None,
        'material_id': material.GlobalId if hasattr(material, 'GlobalId') else None,
        'description': material.Description if hasattr(material, 'Description') else None,
        'properties': {}
    }
    
    # Material may have property sets
    if hasattr(material, 'HasProperties') and material.HasProperties:
        for prop in material.HasProperties:
            if prop.is_a("IfcPropertySingleValue"):
                prop_name = prop.Name
                prop_value = prop.NominalValue.wrappedValue if prop.NominalValue else None
                
                # Extract key material properties
                if prop_name in ['MassDensity', 'YoungModulus', 'ThermalConductivity', 'Cost']:
                    mat_props['properties'][prop_name] = prop_value
    
    return mat_props
```

## Handler 6: Geometric Representation (Shape) - UNIVERSEEL

### Entity Types:
- `IfcProductDefinitionShape` - Link naar shape representation
- `IfcRepresentation` - Geometrie in 3D
- `IfcExtrudedAreaSolid` - Extrude-primitieve (afmeting via diepte)
- `IfcAxis2Placement3D` - Positie/orientatie

### Implementatie Pattern:
```python
def extract_geometry_dimensions(element):
    """Extract geometric dimensions (for volume/area estimation)"""
    dimensions = {
        'has_geometry': False,
        'representation_types': [],
        'bounding_box': None,
    }
    
    # Query: element.Representation
    if hasattr(element, 'Representation') and element.Representation:
        shape = element.Representation
        dimensions['has_geometry'] = True
        
        # Iterate representations (Body, Axis, Box, etc.)
        for rep in shape.Representations:
            rep_type = rep.RepresentationType  # e.g., 'Body', 'Box', 'Axis'
            dimensions['representation_types'].append(rep_type)
            
            # For Box representation, bounds are often available
            if rep_type == 'Box':
                for item in rep.Items:
                    if item.is_a("IfcBoundingBox"):
                        dimensions['bounding_box'] = {
                            'corner': (item.Corner.Coordinates[0], 
                                      item.Corner.Coordinates[1],
                                      item.Corner.Coordinates[2]),
                            'x_dimension': item.XDimension,
                            'y_dimension': item.YDimension,
                            'z_dimension': item.ZDimension,
                        }
    
    return dimensions
```

## Geïntegreerde Extraction Flow

```python
def extract_complete_element_data(element, schema):
    """
    Extract all universally available material and dimension data
    Works with both IFC2X3 and IFC4X3
    """
    return {
        'element_id': element.GlobalId,
        'element_name': element.Name,
        'element_type': element.is_a(),
        'ifc_schema': schema,
        
        # Material info (Fase 4-5)
        'materials': extract_material_from_element(element, schema),
        'material_properties': {
            'density': extract_density_from_material(element),
            'classifications': extract_element_classification(element),
        },
        
        # Dimensions & Quantities (Fase 7)
        'quantities': extract_quantities_from_element(element),
        'geometry': extract_geometry_dimensions(element),
        
        # Properties (Fase 8)
        'properties': extract_properties_from_element(element),
        'type_definition': extract_element_type_reference(element),
    }
```

## Recommendations voor Implementatie

1. **Handler Priority (Universeel → Specifiek)**:
   - Level 1: IfcMaterial + IfcMaterialLayerSet (beide versies)
   - Level 2: Properties + Quantities via IfcRelDefinesByProperties (beide)
   - Level 3: Type definitions via IfcRelDefinesByType (beide)
   - Level 4: Classifications via IfcRelAssociatesClassification (beide)
   - Level 5: Geometry via IfcProductDefinitionShape (beide)
   - Level 6+: IFC4-specific (Constituent sets, Profile sets)

2. **Safe Iteration Pattern**:
   ```python
   # Always check existence before accessing
   for rel in getattr(element, 'HasAssociations', []) or []:
       if hasattr(rel, 'is_a') and rel.is_a("IfcRelAssociatesMaterial"):
           # Process material association
   ```

3. **Property Value Extraction**:
   - `IfcPropertySingleValue` → .NominalValue.wrappedValue
   - `IfcPropertyEnumeratedValue` → .EnumerationValues (list)
   - `IfcPropertyBoundedValue` → .LowerBoundValue / .UpperBoundValue
   - Altijd .wrappedValue gebruiken voor numerieke waarden

4. **Schema-Aware Normalization**:
   - Output format identiek voor beide schemas
   - Null voor onbeschikbare velden (geen defaults)
   - Schema-versie als metadata meenemen
