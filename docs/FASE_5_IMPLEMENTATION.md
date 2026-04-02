# Fase 5: Materiaaltypen Bepalen - Implementatie Plan

## Overzicht

**Doel**: Bepaal expliciet welke materiaalstructuren zijn gekoppeld aan elk element en transformeer de ruwe IFC-materiaalrelaties uit Fase 4 naar goed gestructureerde materiaalrecords.

## Input

- `materials` output uit Fase 4:
  - `element_global_id`
  - `element_name`
  - `element_type`
  - `material_global_id`
  - `material_object`
  - `material_raw_type`
  - `schema`

## Output

- `material_types` list met gedetailleerde materiaalrecords per element
- `material_type_stats` dict met statistieken per materiaalgroep
- `phase_5_summary` met duidelijk onderscheid tussen universele en IFC4-only types

## Scope

- Universele materiaaltypen voor beide schema's:
  - `IfcMaterial`
  - `IfcMaterialList`
  - `IfcMaterialLayerSet`
  - `IfcMaterialLayerSetUsage`
- IFC4-specifieke typen:
  - `IfcMaterialProfileSet`
  - `IfcMaterialConstituentSet`
- Geen geometrie-extractie
- Geen property- of hoeveelheidsextractie
- Geen exportlogica

## Kernproblemen

1. `material_object` kan verschillende IFC-entiteiten zijn
2. `material_raw_type` is de sleutel voor correcte dispatch
3. IFC4 introduceert nieuwe materiaalstructuren die alleen bij dat schema voorkomen
4. Materiaalrecord moet zowel menselijke naam als technische structuur bevatten

## Material Type Handlers

### IfcMaterial

- Lees `material.Name`
- Bouw een eenvoudig record:
  - `material_type = "IfcMaterial"`
  - `material_name`
  - `material_id`

### IfcMaterialList

- Iterate over `material.Materials`
- Maak subrecords per materiaal in de lijst
- Bewaar list-index of volgorde als metadata

### IfcMaterialLayerSet

- Iterate over `material.MaterialLayers`
- Per laag:
  - `layer.Material.Name`
  - `layer.LayerThickness`
  - `layer.MaterialLayerSet` context

### IfcMaterialLayerSetUsage

- Ga via `material.ForLayerSet`
- Extracteer lagen uit `ForLayerSet.MaterialLayers`
- Voeg `Usage` context toe:
  - `DirectionSense`
  - `OffsetFromReferenceLine`

### IfcMaterialProfileSet (IFC4)

- Alleen verwerken als `schema == "IFC4X3_ADD2"`
- Iterate over `material.MaterialProfiles`
- Per profiel:
  - `profile.Material.Name`
  - `profile.Profile` referentie
  - `profile.ProfileType` of `profile.ProfileName` indien beschikbaar

### IfcMaterialConstituentSet (IFC4)

- Alleen verwerken als `schema == "IFC4X3_ADD2"`
- Iterate over `material.MaterialConstituents`
- Per constituent:
  - `constituent.Material.Name`
  - `constituent.Fraction`
  - `constituent.PhysicalQuantity` indien aanwezig

## Architectuur

### Module: `src/material_type_extractor.py`

**Klasse**: `MaterialTypeExtractor`

**Verantwoordelijkheden**:
1. Ontvangen van Fase 4 materiaalrecords
2. Dispatchen op `material_raw_type`
3. Extractie uitvoeren per IFC-materiaaltype
4. Normaliseren naar uniforme outputstructuur
5. Statistieken genereren
6. Logging uitvoeren

### Class interface

```python
class MaterialTypeExtractor:
    def __init__(self, schema: str):
        self.logger = get_logger(__name__)
        self.schema = schema
        self.material_types = []
        self.statistics = {}

    def extract(self, material_mappings: List[Dict]) -> List[Dict]:
        """Extract detailed material type data from phase 4 mappings."""

    def _extract_single_material(self, mapping: Dict) -> Optional[Dict]:
        """Dispatch per raw IFC material type."""

    def _handle_ifc_material(self, material_obj: object, mapping: Dict) -> Dict:
        ...

    def _handle_ifc_material_list(self, material_obj: object, mapping: Dict) -> Dict:
        ...

    def _handle_ifc_material_layer_set(self, material_obj: object, mapping: Dict) -> Dict:
        ...

    def _handle_ifc_material_layer_set_usage(self, material_obj: object, mapping: Dict) -> Dict:
        ...

    def _handle_ifc_material_profile_set(self, material_obj: object, mapping: Dict) -> Dict:
        ...

    def _handle_ifc_material_constituent_set(self, material_obj: object, mapping: Dict) -> Dict:
        ...

    def _generate_statistics(self) -> Dict:
        ...
```

## Outputmodel

### Uniform materiaalrecord

```python
{
    'element_global_id': ...,
    'element_name': ...,
    'element_type': ...,
    'material_raw_type': ...,
    'material_type': ...,
    'material_name': ...,
    'material_id': ...,
    'material_details': {
        'layers': [...],
        'profiles': [...],
        'constituents': [...],
        'list_items': [...]
    },
    'schema': ...,
    'material_object': <ifcopenshell object>
}
```

### Detailstructuren per type

- `layers`: lijst van laagrecords
- `profiles`: lijst van profielrecords
- `constituents`: lijst van constituentrecords
- `list_items`: lijst van eenvoudige materieellijstrecs

## Werkwijze

1. Start met alle records uit Fase 4.
2. Voor elk record:
   - Als `material_object` ontbreekt, maak een lege materiaalrecord met `material_type = None`.
   - Anders dispatch op `material_raw_type`.
   - Gebruik `schema` voor schema-specifieke afhandeling.
3. Houd fouten lokaal:
   - Log eerste 5 fouten met context
   - Sla malformed items over zonder crash
4. Genereer statistieken:
   - `total_materials`
   - `types_per_schema`
   - `elements_with_detailed_material`
   - `elements_without_material`
   - `unsupported_material_types`

## Schema-awareness

- `IFC2X3`:
  - `IfcMaterial`
  - `IfcMaterialList`
  - `IfcMaterialLayerSet`
  - `IfcMaterialLayerSetUsage`
- `IFC4X3_ADD2`:
  - alle IFC2X3-types
  - `IfcMaterialProfileSet`
  - `IfcMaterialConstituentSet`

**Implementatiebeleid**: alleen IFC4-only types verwerken wanneer `schema == "IFC4X3_ADD2"`.

## Logging

- Start- en eindbanner voor Fase 5
- Per record geen verbose logging, alleen fouten en samenvatting
- Statistieken na extractie:
  - totaal verwerkte records
  - materiaaltypes per type
  - IFC4-only records
  - onbekende/unsupported material_types

## Integratie met `main.py`

- Voeg nieuwe fase-methode toe:
  - `_extract_material_types()`
- Workflow:
  1. `ifc_reader.read_file()`
  2. `element_extractor.extract()`
  3. `material_mapper.map()`
  4. `material_type_extractor.extract()`
  5. `quantity_extractor.extract()`
  6. `property_extractor.extract()`
  7. aggregatie + export

## Teststrategie

- Unit tests per handler:
  - `IfcMaterial`
  - `IfcMaterialList`
  - `IfcMaterialLayerSet`
  - `IfcMaterialLayerSetUsage`
  - `IfcMaterialProfileSet` (IFC4)
  - `IfcMaterialConstituentSet` (IFC4)
- Integratietest met representatieve `material_object` mocks
- Validatie met echte IFC testbestanden:
  - controleer dat `IfcMaterialConstituentSet` en `IfcMaterialProfileSet` correct worden verwerkt in `43BIM.ifc`
  - controleer dat IFC2X3 geen IFC4-only records maakt

## Exitcriteria

- `src/material_type_extractor.py` bestaat
- `docs/FASE_5_IMPLEMENTATION.md` beschrijft de architectuur en flow
- `main.py` kan Fase 5 in de pipeline aanroepen
- Outputrecords zijn gestandaardiseerd
- Statistieken tonen `material_type_distribution`
- Geen crash op onbekende material types

## Next phase

**Fase 6** wordt dan:
- Material properties en materiaaldichtheid koppelen
- Aggregatie van materiaaltypes naar naam, hoeveelheid en schema
- Voorbereiding op export
