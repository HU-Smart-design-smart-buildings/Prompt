# Fase 6: Materiaalproperties & Detaildata - Implementatie Plan

## Overzicht

**Doel**: Verwerf gedetailleerde materiaalproperties voor elk gedetermineerd materiaaltype en zorg dat material records worden verrijkt met key eigenschappen zoals dichtheid, gewicht, en relevante projectmeta-data.

## Input

- `material_types` output uit Fase 5
- `schema` van Fase 2
- `ifc_file` object uit Fase 2
- `elements` output uit Fase 3 (voor elementcontext)

## Output

- `material_properties` list met verrijkte materiaalrecords
- `material_property_stats` dict met statistieken van properties
- `material_records` klaar voor aggregatie in Fase 9

## Scope

- Extractie van materiaalproperties uit:
  - `material_object.HasProperties`
  - gekoppelde `IfcPropertySet` records op het materiaalobject
- Focus op universele materiaalproperties:
  - `MassDensity`
  - `ThermalConductivity`
  - `YoungModulus`
  - `Cost`
  - `SurfaceRoughness`
  - `Flammability`
- Voeg ook relevante IFC meta-data toe:
  - Material description
  - Classification tags
  - PropertySet herkomst
- Geen nieuwe material type detectie
- Geen geometrie of hoeveelheidsextractie

## Kerntaken

1. Verwerk alle `material_types` records uit Fase 5
2. Detecteer `material_object` en lees `HasProperties`
3. Loop relevante `IfcPropertySet` items uit materiaalobjecten
4. Normaliseer propertywaarden naar `wrappedValue`
5. Bewaar `None` voor ontbrekende waarden, crash niet
6. Verbind elk materiaalrecord met:
   - `material_name`
   - `material_type`
   - `schema`
   - `material_properties`
   - `property_sets`
   - `material_description`
7. Produceer samenvattende statistieken voor:
   - totaal verwerkte materialen
   - materialen met dichtheid
   - materialen met kosteninformatie
   - ontbrekende propertysets

## Implementatie-architectuur

### Module: `src/material_property_extractor.py`

**Klasse**: `MaterialPropertyExtractor`

**Verantwoordelijkheden**:
- Verwerken van Fase 5 materiaalrecords
- Queryen van `material_object.HasProperties`
- Normaliseren van `IfcPropertySingleValue`, `IfcPropertyEnumeratedValue` en `IfcPropertyBoundedValue`
- Maken van extensible outputrecord per materiaal
- Genereren van diagnostische statistieken

### Interface

```python
class MaterialPropertyExtractor:
    def __init__(self, schema: str):
        ...

    def extract(self, material_types: List[Dict]) -> List[Dict]:
        ...

    def _extract_properties(self, material_obj: object) -> Dict:
        ...

    def _extract_property_set(self, prop_set: object) -> Dict:
        ...

    def _normalize_property_value(self, prop: object) -> Any:
        ...

    def get_statistics(self) -> Dict:
        ...
```

## Data model

### Material property record

```python
{
    'element_global_id': ...,
    'material_name': ...,
    'material_type': ...,
    'material_id': ...,
    'schema': ...,
    'material_description': ...,
    'material_properties': {
        'MassDensity': 7850,
        'ThermalConductivity': 50.2,
        'YoungModulus': 210000,
        'Cost': 12.5,
        'SurfaceRoughness': 0.2,
        'Flammability': False,
    },
    'property_sets': {
        'Pset_MaterialCommon': {
            'MassDensity': 7850,
            'Cost': 12.5
        }
    },
    'material_object': <ifcopenshell object>
}
```

## Verwerkingslogica

1. Controleer of `material_object` bestaat.
2. Als `material_object.HasProperties` beschikbaar is, loop elk property item.
3. Als een propertyset `IfcPropertySet` is, lees alle `HasProperties`.
4. Maak per property een value:
   - `NominalValue.wrappedValue` voor `IfcPropertySingleValue`
   - lijst van `wrappedValue` voor `IfcPropertyEnumeratedValue`
   - dict met `min`/`max` voor `IfcPropertyBoundedValue`
5. Houd propertysets met lege of onbekende waarden bij als `None`.
6. Voeg extra metadata toe op basis van `material_obj.Description`, of `Name` als fallback.

## Schema- en typebewustzijn

- Alle schema's gebruiken universele propertyextractie
- IFC4-only gedrag:
  - mogelijk meer extra material propertysets aanwezig
  - `IfcMaterialProfileSet` of `IfcMaterialConstituentSet` materialen kunnen nog steeds `HasProperties` bevatten
- Geen speciale hardcoded schema-verwerking noodzakelijk, maar de extractor moet flexibel zijn voor extra `PropertySet` types

## Integratie in pipeline

- `src/main.py` krijgt nieuwe methode `_extract_material_properties`
- Deze wordt aangeroepen na Fase 5 en vóór Fase 7
- Output wordt opgeslagen in:
  - `self.material_property_records`
  - `self.material_property_stats`

## Validatie en tests

- Unit tests per property-extractiepatroon:
  - `IfcPropertySingleValue`
  - `IfcPropertyEnumeratedValue`
  - `IfcPropertyBoundedValue`
  - material objects zonder propertysets
- Integratietest met mock materiaalrecords
- Controleer dat ontbrekende waarden geen fouten veroorzaken
- Controleer dat `material_properties` correcte type-conversies krijgt

## Volgende stap

Fase 7 kan daarna de hoeveelheidsextractie uitvoeren op basis van `elements` en `material_property_records`, terwijl Fase 8 verder bouwt op zowel element- als materiaalproperties.
