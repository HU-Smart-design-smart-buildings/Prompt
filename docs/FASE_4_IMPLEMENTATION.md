# Fase 4: Materiaalkoppelingen Ophalen - Implementation Plan

## Overzicht

**Doel**: Voor elk element uit Fase 3 de materiaalkoppeling(en) opvragen.

**Input**: 
- `elements` list uit Fase 3 (met GlobalId, Name, Type, object-referentie, schema)
- `ifc_file` object

**Output**:
- `materials` list met gekoppelde materialen per element
- `material_stats` dict met statistieken

**Scope**: 
- Universele handler werkt voor beide IFC2X3 en IFC4X3
- Geen materiaal-typebepaling nog (Fase 5)
- Alleen relationshipslookahead

---

## Conceptueel Model

```
IfcElement (muur, raam, deur, etc.)
    ↓ HasAssociations
    ├─ IfcRelAssociatesMaterial [Rel-1]
    │   └─ RelatingMaterial → Object (IfcMaterial, IfcMaterialList, etc.)
    │
    ├─ IfcRelAssociatesClassification [Rel-2]
    │   └─ RelatingClassification → Classification info
    │
    └─ ... andere IfcRel types ...

Fase 4 Focus: IfcRelAssociatesMaterial ONLY
```

---

## Architecture

### Module: `src/material_mapper.py` (NEW)

**Klasse**: `MaterialMapper`

**Verantwoordelijkheden**:
1. Per element de HasAssociations-loop
2. Filter op IfcRelAssociatesMaterial
3. Extract RelatingMaterial object
4. Structuur relatiedata
5. Statistieken verzamelen

**Niet in Fase 4**:
- Materiaaltype bepaling (is dat IfcMaterial, List, LayerSet, etc.?)
- Property extraction
- Quantity matching

---

## Design: MaterialMapper Klasse

```python
class MaterialMapper:
    """Koppel elementen aan materialen via IfcRelAssociatesMaterial"""
    
    def __init__(self, ifc_file: object, schema: str):
        """
        Args:
            ifc_file: ifcopenshell file object
            schema: "IFC2X3" of "IFC4X3"
        """
    
    def map(self, elements: List[Dict]) -> List[Dict]:
        """
        Map materials voor alle elementen
        
        Returns: [
            {
                'element_global_id': '3Mfg...',
                'element_name': 'Wall-A',
                'element_type': 'IfcWall',
                'material_global_id': 'mat123' (None als geen),
                'material_object': <ifcopenshell object>,
                'material_raw_type': 'IfcMaterial', 'IfcMaterialList', etc.
                'schema': 'IFC2X3'
            },
            ...
        ]
        """
    
    def _map_single_element(self, element: Dict) -> Optional[Dict]:
        """Map één element"""
        
    def _get_material_relationship(self, element_obj: object) -> Optional[object]:
        """
        Zoek IfcRelAssociatesMaterial in element.HasAssociations
        
        Returns: IfcRelAssociatesMaterial object of None
        """
    
    def _generate_statistics(self) -> Dict:
        """
        Statistics:
        - total_elements_processed
        - elements_with_material: count
        - elements_without_material: count
        - material_type_distribution (IfcMaterial, IfcMaterialList, etc.)
        """
```

---

## Implementatie Stappen

### Stap 1: Element Loop
```python
def map(self, elements: List[Dict]) -> List[Dict]:
    self.logger.info("Mapping materials for {} elements".format(len(elements)))
    
    materials = []
    errors = 0
    
    for elem in elements:
        try:
            result = self._map_single_element(elem)
            if result:
                materials.append(result)
        except Exception as e:
            errors += 1
            if errors <= 5:
                self.logger.warning("Error mapping element: {}".format(str(e)))
    
    self.statistics = self._generate_statistics()
    return materials
```

### Stap 2: Per-element Mapping
```python
def _map_single_element(self, element: Dict) -> Optional[Dict]:
    elem_obj = element['object']
    
    # Stap 2a: Haal IfcRelAssociatesMaterial op
    rel = self._get_material_relationship(elem_obj)
    
    if not rel:
        # Element heeft geen materiaal-koppeling
        return {
            'element_global_id': element['global_id'],
            'element_name': element['name'],
            'element_type': element['type'],
            'material_global_id': None,
            'material_object': None,
            'material_raw_type': None,
            'schema': element['schema']
        }
    
    # Stap 2b: Extract RelatingMaterial
    material = rel.RelatingMaterial
    
    return {
        'element_global_id': element['global_id'],
        'element_name': element['name'],
        'element_type': element['type'],
        'material_global_id': material.GlobalId if hasattr(material, 'GlobalId') else None,
        'material_object': material,
        'material_raw_type': material.is_a(),  # IfcMaterial, IfcMaterialList, etc.
        'schema': element['schema']
    }
```

### Stap 3: Material Relationship Query
```python
def _get_material_relationship(self, element_obj: object) -> Optional[object]:
    """
    Zoek IfcRelAssociatesMaterial in HasAssociations
    
    HasAssociations kan bevatten:
    - IfcRelAssociatesMaterial (TIP: dit willen we)
    - IfcRelAssociatesClassification
    - IfcRelAssociatesConstraint
    - etc.
    """
    
    if not hasattr(element_obj, 'HasAssociations'):
        return None
    
    associations = element_obj.HasAssociations
    if not associations:
        return None
    
    for assoc in associations:
        if assoc.is_a() == "IfcRelAssociatesMaterial":
            return assoc
    
    return None
```

### Stap 4: Statistics Generation
```python
def _generate_statistics(self) -> Dict:
    """Collect statistics"""
    
    by_type = defaultdict(int)
    with_material = 0
    without_material = 0
    
    for item in self.materials:
        if item['material_raw_type']:
            with_material += 1
            by_type[item['material_raw_type']] += 1
        else:
            without_material += 1
    
    return {
        'total_elements_mapped': len(self.materials),
        'elements_with_material': with_material,
        'elements_without_material': without_material,
        'material_type_distribution': dict(sorted(by_type.items())),
        'schema': self.schema
    }
```

---

## Logging Output (Expected)

```
======================================================================
FASE 4: Mapping Material Relationships
======================================================================
Mapping materials for 2381 elements...
- Processing element 1: 3Mfg_Wall_A
- Processing element 2: 3Mfg_Window_1
...
Successfully mapped 2381 elements
----------------------------------------------------------------------
MAPPING SUMMARY:
  Total elements mapped: 2381
  Elements with material: 2156 (90.5%)
  Elements without material: 225 (9.5%)
  Material type distribution:
    - IfcMaterial: 1987
    - IfcMaterialList: 89
    - IfcMaterialLayerSet: 67
    - IfcMaterialLayerSetUsage: 13
----------------------------------------------------------------------
```

---

## Data Flow Fase 4

### Input (uit Fase 3)
```python
elements = [
    {
        'global_id': '3Mfg_001',
        'name': 'Wall-A',
        'type': 'IfcWall',
        'object': <ifcopenshell object>,
        'schema': 'IFC2X3'
    },
    ...
]
```

### Output (naar Fase 5)
```python
materials = [
    {
        'element_global_id': '3Mfg_001',
        'element_name': 'Wall-A',
        'element_type': 'IfcWall',
        'material_global_id': 'mat_001',
        'material_object': <ifcopenshell IfcMaterial object>,
        'material_raw_type': 'IfcMaterial',
        'schema': 'IFC2X3'
    },
    {
        'element_global_id': '3Mfg_002',
        'element_name': 'Window-1',
        'element_type': 'IfcWindow',
        'material_global_id': None,
        'material_object': None,
        'material_raw_type': None,
        'schema': 'IFC2X3'
    },
    ...
]
```

---

## Integration met main.py

### Toevoegingen in IFCMaterialExtractor.__init__()
```python
self.materials = []      # NEW
self.material_stats = {} # NEW
```

### Toevoegingen in IFCMaterialExtractor._extract_materials()
```python
def _extract_materials(self):
    """Fase 4: Map material relationships"""
    from material_mapper import map_materials
    
    if not self.ifc_file:
        raise IFCReadError("IFC file not loaded")
    
    try:
        self.materials, self.material_stats = map_materials(
            self.elements,
            self.ifc_file,
            self.ifc_schema
        )
        self.logger.info("Mapped {} materials".format(len(self.materials)))
    except Exception as e:
        self.logger.warning("Error mapping materials: {}".format(str(e)))
```

---

## Module Function (Convenience)

```python
def map_materials(elements: List[Dict], ifc_file: object, schema: str) \
    -> Tuple[List[Dict], Dict]:
    """
    Convenience function to map materials in one call
    
    Usage:
        from material_mapper import map_materials
        
        materials, stats = map_materials(elements, ifc_file, "IFC2X3")
    """
    mapper = MaterialMapper(ifc_file, schema)
    materials = mapper.map(elements)
    stats = mapper.get_statistics()
    return materials, stats
```

---

## Testing Strategy

### Unit Tests
```python
# Test 1: Element zonder HasAssociations
# Test 2: Element met HasAssociations maar geen IfcRelAssociatesMaterial
# Test 3: Element met IfcRelAssociatesMaterial
# Test 4: Statistics generation met mix van beide
```

### Integration Tests
```python
# Test 1: map_materials() convenience function
# Test 2: main.py._extract_materials() integration
# Test 3: With 23BIM.ifc (IFC2X3)
# Test 4: With 43BIM.ifc (IFC4X3)
# Test 5: Verify material counts match expected ranges
```

---

## Known Issues & Considerations

### HasAssociations Structure
- Kan None zijn (element heeft geen associations)
- Kan lege list zijn (element heeft associations maar geen materialen)
- Kan meerdere IfcRel types bevatten

### GlobalId op Material Object
- IfcMaterial heeft altijd GlobalId
- IfcMaterialList GEEN GlobalId (geaggregeerde entity)
- IfcMaterialLayerSet GEEN GlobalId
- IfcMaterialLayerSetUsage GEEN GlobalId
- Dus: niet alle materials hebben GlobalId

### Performance
- Per element 1x HasAssociations loop (weinig overhead)
- Object-referentie bewaren voor Fase 5 (veel geheugen voor grote modellen)
- Alternatief: Alleen GlobalId bewaren en reload in Fase 5

### Error Handling
- Skip elementen die kaput zijn
- Log eerste 5 errors, rest tellen
- Never crashen op individueel element

---

## Next Phase (Fase 5)

Fase 5 bepaalt materiaaltypen:
```python
# Fase 4 output → Fase 5 input
material_raw_type = 'IfcMaterial' / 'IfcMaterialList' / etc.

# Fase 5 determineert:
# - Als 'IfcMaterial': Extract material.Name
# - Als 'IfcMaterialList': Loop .Materials, extract per sub-material
# - Als 'IfcMaterialLayerSet': Loop .MaterialLayers, extract per layer
# - Etc.
```

---

## File Structure After Implementation

```
src/
├── material_mapper.py      # NEW - Phase 4 implementation
├── element_extractor.py    # Phase 3
├── ifc_reader.py          # Phase 2
├── main.py                # Updated with material_stats
├── config.py
├── logger.py

docs/
├── FASE_4_IMPLEMENTATION.md # This file
├── FASE_3_COMPLETE.md
├── FASE_2_IMPLEMENTATION.md
├── FASE_1_IMPLEMENTATION.md
├── PLAN.md
```

---

## Completion Checklist (For Implementation Phase)

- [ ] Create src/material_mapper.py
- [ ] Implement MaterialMapper class
- [ ] Implement map() orchestration method
- [ ] Implement _map_single_element() per-element logic
- [ ] Implement _get_material_relationship() relationship query
- [ ] Implement _generate_statistics() statistics collection
- [ ] Create map_materials() convenience function
- [ ] Update main.py with material_stats attribute
- [ ] Update main.py._extract_materials() to use map_materials()
- [ ] Verify imports work
- [ ] Integration test with 23BIM.ifc
- [ ] Integration test with 43BIM.ifc
- [ ] Create FASE_4_COMPLETE.md with results
- [ ] Update PLAN.md with completion status

---

## Summary

**Fase 4** is straightforward:
- Loop elements
- Find HasAssociations
- Filter IfcRelAssociatesMaterial
- Extract RelatingMaterial + type
- Record results

No complexity with material type handling (that's Fase 5).
No property extraction (that's Fase 8).

Just the relationship mapping.
