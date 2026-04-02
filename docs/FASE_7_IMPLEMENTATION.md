# Fase 7: Hoeveelheden Extraheren - Implementatie Plan

## Overzicht

**Doel**: Haal kwantitatieve informatie uit alle relevante IFC-elementen en zorg dat volumes, oppervlakten, lengtes, aantallen en gewichten gestructureerd beschikbaar zijn voor aggregatie.

## Input

- `elements` uit Fase 3
- `material_property_records` uit Fase 6
- `schema` uit Fase 2
- `ifc_file` object uit Fase 2

## Output

- `quantity_records` list met gestructureerde kwantiteitdata per element
- `quantity_stats` dict met statistieken over hoeveelheden
- `quantity_ready` data klaar voor aggregatie in Fase 9

## Scope

- Extractie van IFC-quantities via `IfcElementQuantity`
- Universele verwerking voor beide schema's:
  - IFC2X3
  - IFC4X3_ADD2
- Geen materiaaleigenschappen, geen export
- Geen geometrie-verwerking buiten de IFC quantity definitions
- Geen elementtype-filtering, wel focus op alle fysieke bouwobjecten met kwantiteiten

## Kerntaken

1. Loop alle elementen in de applicatie-output
2. Controleer `element.IsDefinedBy`
3. Filter op relaties met `IfcRelDefinesByProperties`
4. Selecteer `rel.RelatingPropertyDefinition.is_a("IfcElementQuantity")`
5. Voor elke quantity set:
   - Lees `Qtd.Name`
   - Itereer over `prop_def.Quantities`
   - Normaliseer per quantity:
     - `IfcQuantityVolume`
     - `IfcQuantityArea`
     - `IfcQuantityLength`
     - `IfcQuantityCount`
     - `IfcQuantityWeight`
6. Haal `wrappedValue` op voor de feitelijke numerieke waarde
7. Bewaar een record met:
   - element GUID
   - element name
   - element type
   - ifc schema
   - quantity set naam
   - quantity naam
   - quantity type
   - quantity waarde
   - quantity eenheid (indien beschikbaar)
8. Sla ontbrekende waarden op als `None`
9. Log samenvattende statistieken

## Implementatie-architectuur

### Module: `src/quantity_extractor.py`

**Klasse**: `QuantityExtractor`

**Verantwoordelijkheden**:
- Extractie van IFC-quantity data uit elementen
- Normalisatie van `IfcQuantity*` objecten
- Aggregatie van sets en count-statistieken
- Logging van status en fouten

### Interface

```python
class QuantityExtractor:
    def __init__(self, schema: str):
        ...

    def extract(self, elements: List[Dict]) -> List[Dict]:
        ...

    def _extract_element_quantities(self, element: object) -> List[Dict]:
        ...

    def _normalize_quantity(self, qty_obj: object) -> Dict[str, Any]:
        ...

    def get_statistics(self) -> Dict:
        ...
```

## Data model

### Quantity record

```python
{
    'element_global_id': '3Mfg_001',
    'element_name': 'Wall-A',
    'element_type': 'IfcWall',
    'schema': 'IFC2X3',
    'quantity_set_name': 'BaseQuantities',
    'quantity_name': 'NetVolume',
    'quantity_type': 'IfcQuantityVolume',
    'quantity_value': 12.34,
    'quantity_unit': 'm³',
    'quantity_definition': {
        'description': 'Net volume of element',
        'measurement_type': 'Volume'
    }
}
```

## Verwerkingslogica

1. Start met alle `elements` records uit Fase 3.
2. Voor elk element:
   - Als `element['object']` ontbreekt, sla over
   - Als `IsDefinedBy` ontbreekt of leeg is, registreer element met 0 quantity-records
3. Controleer relaties:
   - `rel.is_a("IfcRelDefinesByProperties")`
   - `prop_def.is_a("IfcElementQuantity")`
4. Extracteer de quantity set naam en body
5. Loop `prop_def.Quantities`:
   - `qty.is_a()` bepaalt subtype
   - `qty.Name` wordt de quantity label
   - `qty.wrappedValue` is de waarde
6. Normale units voor bekende types:
   - `IfcQuantityVolume` → `m³`
   - `IfcQuantityArea` → `m²`
   - `IfcQuantityLength` → `m`
   - `IfcQuantityCount` → `count`
   - `IfcQuantityWeight` → `kg`
7. Behandel onbekende quantity types generiek
8. Voeg schema en elementcontext toe aan elk record

## Statistieken

- `total_elements_processed`
- `elements_with_quantities`
- `elements_without_quantities`
- `total_quantity_records`
- `quantity_type_distribution`
- `quantity_set_distribution`

## Integratie in pipeline

- `src/main.py` krijgt een nieuwe fase-methode `_extract_quantities` of wordt uitgebreid met `QuantityExtractor`
- Aanroepen na Fase 6 en vóór Fase 8
- Resultaten worden opgeslagen als:
  - `self.quantity_records`
  - `self.quantity_stats`
- Gebruik `self.elements` als input

## Teststrategie

- Unit tests voor:
  - `IfcQuantityVolume`
  - `IfcQuantityArea`
  - `IfcQuantityLength`
  - `IfcQuantityCount`
  - `IfcQuantityWeight`
  - elementen zonder `IfcElementQuantity`
- Mock `ifc_file` objecten met `IsDefinedBy` relaties
- Validatie dat `wrappedValue` correct wordt omgezet
- Controleer dat ontbrekende values niet crashen

## Volgende stap

Nadat Fase 7 is geïmplementeerd kan Fase 8 beginnen met het samenvoegen van properties en quantities, waarna Fase 9 de aggregatie op detailniveau kan uitvoeren.
