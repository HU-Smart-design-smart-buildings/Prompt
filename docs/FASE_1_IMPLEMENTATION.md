# Fase 1: Initialisatie & Setup - Implementatie Plan

## Status quo
- ✅ Python modules aangemaakt (11 bestanden)
- ✅ Afhankelijkheden geïnstalleerd (ifcopenshell, pandas, openpyxl)
- ❌ Logging framework nog niet ingevuld
- ❌ Configuratiebestand nog niet ingevuld
- ❌ Basis project-orchestrator nog niet ingevuld

## Fase 1 Onderdelen

### 1. `logger.py` - Logging & Error Handling Framework

**Doel**: Centrale logging voor alle modules (info, warning, error, debug)

**Inhoud**:
```
- LoggerFactory class
  - Singleton pattern (1 logger per module)
  - Output: console + file (optional)
  - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
  
- Formatter
  - Timestamp
  - Module name
  - Log level
  - Message
  
- File handlers
  - Logs directory (logs/)
  - Daily rotation (logs_YYYY-MM-DD.log)
  
- Custom exceptions
  - IFCReadError
  - MaterialExtractionError
  - ExportError
  - ValidationError
```

**Gebruik in andere modules**:
```python
from logger import get_logger

logger = get_logger(__name__)
logger.info("Processing element: {}".format(element.Name))
logger.warning("Material density not found")
logger.error("Failed to extract quantities", exc_info=True)
```

---

### 2. `config.py` - Configuratie & Constanten

**Doel**: Centraal punt voor alle configuratie-waarden

**Inhoud**:

#### A. Pad-configuratie
```
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"
TEST_FILES_DIR = PROJECT_ROOT / "test_files"
```

#### B. IFC Schema Configuratie
```
SUPPORTED_SCHEMAS = ["IFC2X3", "IFC4X3_ADD2"]

# Material types per schema
MATERIAL_TYPES_IFC2X3 = [
    "IfcMaterial",
    "IfcMaterialList",
    "IfcMaterialLayerSet",
    "IfcMaterialLayerSetUsage"
]

MATERIAL_TYPES_IFC4X3 = [
    "IfcMaterial",
    "IfcMaterialList",
    "IfcMaterialLayerSet",
    "IfcMaterialLayerSetUsage",
    "IfcMaterialProfileSet",
    "IfcMaterialConstituentSet"
]

# Property Set names
COMMON_PSETS = [
    "Pset_BuildingElementProxyCommon",
    "Pset_SlabCommon",
    "Pset_WallCommon",
    "Pset_DoorCommon",
    "Pset_WindowCommon",
    "Pset_QuantityTakeOff"
]

# Quantity types (universeel)
QUANTITY_TYPES = [
    "IfcQuantityVolume",
    "IfcQuantityArea",
    "IfcQuantityLength",
    "IfcQuantityCount",
    "IfcQuantityWeight"
]
```

#### C. Element Type Configuratie
```
BUILDING_ELEMENT_TYPES = [
    "IfcWall",
    "IfcSlab",
    "IfcBeam",
    "IfcColumn",
    "IfcDoor",
    "IfcWindow",
    "IfcRoof",
    "IfcStair",
    "IfcRamp",
    "IfcFurniture"
]
```

#### D. Export Configuratie
```
EXPORT_FORMATS = ["csv", "xlsx", "json"]
DEFAULT_EXPORT_FORMAT = "xlsx"
CSV_ENCODING = "utf-8"
CSV_DELIMITER = ","
```

#### E. Processing Configuratie
```
# Toleranties
MIN_VOLUME_THRESHOLD = 0.001  # m³ (1 liter)
MIN_AREA_THRESHOLD = 0.001    # m²

# Batch processing
BATCH_SIZE = 100  # elements per batch

# Logging
LOG_LEVEL = "INFO"
LOG_TO_FILE = True
LOG_TO_CONSOLE = True
```

---

### 3. `main.py` - Entry Point & Orchestrator

**Doel**: Centraal controlepunt, orkestreert workflow door alle fases

**Inhoud**:

#### A. Main Application Class
```python
class IFCMaterialExtractor:
    """
    Main orchestrator for IFC material extraction workflow
    """
    
    def __init__(self, input_file_path: str, output_dir: str = None):
        - Initialize logger
        - Validate input file exists
        - Store paths
        - Initialize modules
    
    def process(self):
        """Main processing pipeline"""
        1. Load & detect schema (Fase 2)
        2. Extract elements (Fase 3)
        3. Extract materials (Fase 4-5-6)
        4. Extract quantities (Fase 7)
        5. Extract properties (Fase 8)
        6. Aggregate data (Fase 9)
        7. Export results (Fase 10)
        8. Return summary
    
    def validate_output(self):
        """Quality checks on extracted data"""
        - Check for empty results
        - Validate data types
        - Log statistics
```

#### B. Command Line Interface
```
if __name__ == "__main__":
    parser = argparse.ArgumentParser(...)
    parser.add_argument("input_file", help="Path to IFC file")
    parser.add_argument("--output", default="output/")
    parser.add_argument("--format", choices=["csv","xlsx","json"], default="xlsx")
    parser.add_argument("--log-level", default="INFO")
    
    args = parser.parse_args()
    
    extractor = IFCMaterialExtractor(args.input_file, args.output)
    result = extractor.process()
```

---

### 4. Directory Structure Create

```
Prompt/
├── config.py                    ← Configuration constants
├── logger.py                    ← Logging framework
├── main.py                      ← Entry point & orchestrator
├── ifc_reader.py               ← Fase 2
├── element_extractor.py        ← Fase 3
├── material_mapper.py          ← Fase 4-5-6
├── quantity_extractor.py       ← Fase 7
├── property_extractor.py       ← Fase 8
├── material_aggregator.py      ← Fase 9
├── exporter.py                 ← Fase 10
├── requirements.txt            ← Dependencies
├── PLAN.md                     ← Project plan
├── data/                       ← Input IFC files
│   ├── 23BIM.ifc
│   └── 43BIM.ifc
├── output/                     ← Generated files
│   └── material_extraction_YYYY-MM-DD.xlsx
├── logs/                       ← Log files
│   └── logs_YYYY-MM-DD.log
└── test_files/                 ← Test data
```

---

## Implementatie Stappen

### Stap 1: `config.py` vullen
- Alle constanten definiëren
- Schema-specifieke mappings
- Pad-configuratie
- Validatie helper functions

### Stap 2: `logger.py` vullen
- LoggerFactory implementeren
- Custom exceptions
- Logging formatter
- File/console handlers

### Stap 3: Directories creëren
- `data/`, `output/`, `logs/` mappen aanmaken
- Bestandspermissies correct zetten

### Stap 4: `main.py` implementeren
- IFCMaterialExtractor klasse
- process() method
- CLI argument parsing
- Error handling

### Stap 5: Import structuur testen
```python
from config import SUPPORTED_SCHEMAS
from logger import get_logger, IFCReadError
from main import IFCMaterialExtractor

# Should work without errors
```

---

## Quality Checks voor Fase 1

- [ ] Alle imports werken (geen ModuleNotFoundError)
- [ ] config.py bevat alle noodzakelijke constanten
- [ ] logger.py logs naar console EN file
- [ ] main.py kan worden geïmporteerd
- [ ] Directories bestaan en schrijfbaar zijn
- [ ] CLI help werkt: `python main.py --help`
- [ ] Basis foutafhandeling werkt

---

## Dependencies Check

```
✅ ifcopenshell >= 0.7.0     (voor IFC file reading)
✅ pandas >= 1.5.0            (voor dataframing)
✅ openpyxl >= 3.0.0          (voor Excel export)
```

Optioneel toe te voegen (niet in requirements.txt):
- `python-dotenv` - Environment variabeles
- `tqdm` - Progress bars
- `pytest` - Testing

---

## Tijdlijn Fase 1

1. **config.py** → 15-20 min (constanten definiëren)
2. **logger.py** → 20-25 min (logging setup)
3. **Directories** → 5 min (create + validate)
4. **main.py** → 25-30 min (orchestrator + CLI)
5. **Testing** → 10-15 min (imports + basic runs)

**Totaal: ~75-95 minuten**

Na Fase 1 is de basis gereed voor Fase 2 (IFC reader).
