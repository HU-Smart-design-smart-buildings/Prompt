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

## Projectfases

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
  - Controleer type van `RelatingMaterial` met `is_a()`
  - Verwerk per geval apart:
    - `IfcMaterial` → .Name uitlezen
    - `IfcMaterialList` → itereer .Materials
    - `IfcMaterialLayerSetUsage` → .ForLayerSet.MaterialLayers met dikte
    - `IfcMaterialLayerSet` → .MaterialLayers
    - `IfcMaterialProfileSet` (IFC4) → .MaterialProfiles met profiel
    - `IfcMaterialConstituentSet` (IFC4) → .MaterialConstituents met fractie
  - Onbekende typen loggen zonder te crashen

### **Fase 6: Schema-specifieke Correcties**
- **Stap 4**: Type-conflicten vermijden op basis van schema
  - IFC2X3: Geen IfcMaterialConstituentSet beschikbaar
  - IFC4: Andere nesting van IfcMaterialLayerSetUsage
  - Verwerk alleen entities die in het schema aanwezig zijn
  - Geen try/except als vervanging voor schemakennis

### **Fase 7: Hoeveelheden Extraheren**
- **Stap 5**: Kwantiteiten per element
  - Loop `element.IsDefinedBy`
  - Filter op `IfcRelDefinesByProperties`
  - Controleer `rel.RelatingPropertyDefinition.is_a("IfcElementQuantity")`
  - Lees beschikbare kwantiteiten: NetVolume, GrossVolume, NetArea, GrossArea, Length
  - Gebruik `.wrappedValue` voor werkelijke waarden
  - Ontbrekende waarden als None, niet als 0

### **Fase 8: Properties Extraheren**
- **Stap 6**: Relevante material- en element-properties
  - Via `IfcPropertySet` in `IsDefinedBy`-loop
  - Per property: `prop.NominalValue.wrappedValue`
  - Belangrijk: Pset_MaterialCommon (MassDensity), element-specifieke Psets
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
