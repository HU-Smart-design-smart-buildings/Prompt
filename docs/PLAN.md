# Stappenplan: IFC Materiaalgegevens Extractor

## Projectdoel
Ontwikkelen van een geautomatiseerde Python-applicatie die betrouwbare materiaalgegevens uit BIM-modellen (IFC-bestanden versie 2.3, 4.3 en tussenliggende versies) extraheert. Het doel is inzicht te krijgen in logistieke materiaalstromen en de circulaire potentie van gebouwen.

## Aannames
1. De objectstructuur van het IFC-model overeenkomt met de fysieke opbouw van het gebouw
2. Materiaalinformatie is gekoppeld aan objecten in het model
3. Het detailniveau en structuur van BIM-modellen varieert sterk (geen gestandaardiseerde maatstaf)

## Architectuur
De applicatie is opgebouwd uit meerdere gespecialiseerde Python-modules:
- `ifc_reader.py` - IFC-bestanden inlezen en schema detecteren
- `element_extractor.py` - Bouwelementen ophalen
- `material_mapper.py` - Materiaalkoppelingen en types bepalen
- `quantity_extractor.py` - Hoeveelheden (volumes, oppervlakken) uitlezen
- `property_extractor.py` - Material properties en elementen properties ophalen
- `material_aggregator.py` - Materiaaldata samenvoegen en aggregeren
- `exporter.py` - Data exporteren naar CSV, Excel, JSON
- `main.py` - Orchestrator en entry point
- `config.py` - Configuratie en constanten
- `logger.py` - Logging en error handling

## IFC Format Analyse Resultaat

Twee test-files zijn geanalyseerd:
- **23BIM.ifc**: Schema = IFC2X3
- **43BIM.ifc**: Schema = IFC4X3_ADD2

### Material Entity Type Counts
| Type | IFC2X3 | IFC4X3 | Status |
|------|--------|---------|--------|
| IfcMaterial | 1,789 | 3,748 | ✓ Beide |
| IfcMaterialLayerSet | 1,531 | 177 | ✓ Beide |
| IfcMaterialLayerSetUsage | Present | Present | ✓ Beide |
| IfcMaterialConstituentSet | — | 831 | ⚠ Alleen IFC4 |
| IfcMaterialProfileSet | — | 36 | ⚠ Alleen IFC4 |
| IfcPropertySet | 13,307 | 47,741 | ✓ Beide |

### Universele Handlers (beide schemas)
| Handler | IFC2X3 | IFC4X3 | Doel |
|---------|--------|---------|------|
| IfcPropertySet | 13,307 | 47,741 | Eigenschappen/metadata |
| IfcElementQuantity | Present | Present | Volumes, oppervlakten |
| IfcRelDefinesByType | 968 | 1,105 | Type-definities |
| IfcRelAssociatesClassification | 47 | 49 | Categorisatie/tags |
| IfcProductDefinitionShape | 5,781 | 5,784 | Geometrie/dimensies |
| IfcExtrudedArea + Geometry | 7,506 | 7,476 | 3D vorm data |

**Conclusie**: IFC4X3 is backwards-compatible met IFC2X3, maar bevat extra materiaaltypen.
Zie `IFC_FORMAT_DIFFERENCES.md` en `IFC_UNIVERSAL_HANDLERS.md` voor volledige analyse en implementatie-richtlijnen.

### **Fase 1: Initialisatie & Setup**
- Projectstructuur opzetten met module-layout
- Afhankelijkheden installeren (ifcopenshell, pandas, openpyxl)
- Logging en error handling framework
- Basis configuratiebestand

### **Fase 2: IFC-bestanden inlezen & Schema detectie**
- **Stap 0**: IFC-bestand openen met ifcopenshell
  - Schema uit IFC-header uitlezen ("IFC2X3" of "IFC4")
  - Schema als flag meenemen door alle vervolgstappen
  - Validatie dat bestand geldig IFC-formaat is

### **Fase 3: Bouwelementen Extraheren**
- **Stap 1**: Alle fysieke bouwelementen ophalen
  - Gebruik `IfcElement` met `include_subtypes=True`
  - Per element: GlobalId, Name, werkelijke IFC-entiteitstype
  - Bewaar in gestructureerd formaat (dict/dataclass)

### **Fase 4: Materiaalkoppelingen Ophalen**
- **Stap 2**: Materiaalkoppelingen per element
  - Loop `element.HasAssociations`
  - Filter op `IfcRelAssociatesMaterial`
  - Verkrijg `rel.RelatingMaterial` als startpunt

### **Fase 5: Materiaaltypen Bepalen**
- **Stap 3**: Expliciete materiaaltype bepaling (geen aannames)
  - **ANALYSE RESULTAAT**: Beide formats ondersteund (zie IFC_FORMAT_DIFFERENCES.md)
  - Controleer type van `RelatingMaterial` met `is_a()`
  - Verwerk per geval apart:
    - `IfcMaterial` → .Name uitlezen (1789x IFC2X3, 3748x IFC4X3)
    - `IfcMaterialList` → itereer .Materials (beide versies)
    - `IfcMaterialLayerSet` → .MaterialLayers (1531x IFC2X3, 177x IFC4X3)
    - `IfcMaterialLayerSetUsage` → .ForLayerSet.MaterialLayers met dikte (beide)
    - `IfcMaterialProfileSet` (IFC4 ONLY) → .MaterialProfiles met profiel (36x in 43BIM)
    - `IfcMaterialConstituentSet` (IFC4 ONLY) → .MaterialConstituents met fractie (831x in 43BIM)
  - Onbekende typen loggen zonder te crashen
  - **Schema-awareness**: Wrap IFC4-specific types in conditional checks

### **Fase 6: Schema-specifieke Correcties**
- **Stap 4**: Type-conflicten vermijden op basis van schema
  - **ANALYSE RESULTAAT**: 
    - IFC2X3: IfcMaterialConstituentSet NIET beschikbaar
    - IFC4X3: IfcMaterialProfileSet en IfcMaterialConstituentSet WEL beschikbaar
  - Detect schema versie in Fase 2 en bewaar als metadata
  - IFC2X3: Alleen query IfcMaterial, IfcMaterialList, IfcMaterialLayerSet, IfcMaterialLayerSetUsage
  - IFC4X3: Inclusief IfcMaterialProfileSet en IfcMaterialConstituentSet
  - Verwerk alleen entities die in het schema aanwezig zijn
  - Geen try/except als vervanging voor schemakennis - weet van tevoren wat mogelijk is

### **Fase 7: Hoeveelheden Extraheren**
- **Stap 5**: Kwantiteiten per element
  - **UNIVERSELE HANDLER**: IfcElementQuantity (beide schemas)
  - Loop `element.IsDefinedBy`
  - Filter op `IfcRelDefinesByProperties`
  - Controleer `rel.RelatingPropertyDefinition.is_a("IfcElementQuantity")`
  - Lees beschikbare kwantiteiten: NetVolume, GrossVolume, NetArea, GrossArea, Length
  - Beschikbare Quantity Types (beide versies):
    - `IfcQuantityVolume` (m³)
    - `IfcQuantityArea` (m²)  
    - `IfcQuantityLength` (m)
    - `IfcQuantityCount` (items)
    - `IfcQuantityWeight` (kg)
  - Gebruik `.wrappedValue` voor werkelijke waarden
  - Ontbrekende waarden als None, niet als 0

### **Fase 8: Properties Extraheren**
- **Stap 6**: Relevante material- en element-properties
  - **UNIVERSELE HANDLERS** (beide schemas):
    1. **IfcPropertySet** (13,307x IFC2X3, 47,741x IFC4X3)
       - Via `IfcRelDefinesByProperties` in `IsDefinedBy`-loop
       - Property types: IfcPropertySingleValue, IfcPropertyEnumeratedValue, IfcPropertyBoundedValue
       - Interessante Psets: Pset_BuildingElementProxyCommon, Pset_SlabCommon, Pset_WallCommon, Pset_DoorCommon, Pset_WindowCommon
    
    2. **IfcRelDefinesByType** (968x IFC2X3, 1,105x IFC4X3)
       - Parametrische type-definities per element
       - Extract type properties voor use als defaults
    
    3. **IfcRelAssociatesClassification** (47x IFC2X3, 49x IFC4X3)
       - Categorisatie/Uniformat info
       - ItemReference en ReferencedSource
    
    4. **Material Properties** (via material.HasProperties)
       - MassDensity (kg/m³), YoungModulus, ThermalConductivity, Cost
  
  - Per property: `prop.NominalValue.wrappedValue` voor SingleValue
  - EnumeratedValue: iterate .EnumerationValues (list)
  - BoundedValue: .LowerBoundValue / .UpperBoundValue
  - Geen default-waarden invullen

### **Fase 9: Materiaallijsten Aggregeren**
- **Stap 7**: Data samenvoegen en groeperen
  - Groepeer op materiaalNaam + ifcType
  - Aggregeer hoeveelheden (som volumes/oppervlakten) per groep
  - Bewaar aantal elementen per combinatie
  - Optioneel: GlobalIds list voor herleidbaarheid

### **Fase 10: Exporteren**
- **Stap 8**: Output in meerdere formaten
  - CSV-export (agile/eenvoudig)
  - Excel-export (beter voor analyse)
  - JSON-export (voor web/scripts)
  - Voeg altijd IFC-schema kolom toe (traceerbaar)
  - Exporteer ook detail-versie: 1 rij per element-materiaal combinatie met GUID

### **Fase 11: Testing & Validatie**
- Unit tests per module
- Integratie tests met test-IFC-bestanden
- Kwaliteitscontrole op output
- Edge cases (ontbrekende data, onstandaardige structuren)

### **Fase 12: Documentatie & Afronding**
- Gebruikershandleiding
- Technische documentatie
- API-documentatie per module
- Best practices en troubleshooting
