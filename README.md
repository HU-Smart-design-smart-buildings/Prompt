# IFC Material Extractor

Geautomatiseerde methode voor het extraheren van betrouwbare materiaalgegevens uit BIM-modellen (IFC-bestanden versie 2.3 en 4.3).

## Project Structuur

```
Prompt/
├── src/                          # Source code modules
│   ├── config.py                # Configuration & constants
│   ├── logger.py                # Logging framework
│   ├── main.py                  # Entry point & orchestrator
│   ├── ifc_reader.py            # IFC file reading (Fase 2)
│   ├── element_extractor.py     # Element extraction (Fase 3)
│   ├── material_mapper.py       # Material mapping (Fase 4-6)
│   ├── quantity_extractor.py    # Quantity extraction (Fase 7)
│   ├── property_extractor.py    # Property extraction (Fase 8)
│   ├── material_aggregator.py   # Data aggregation (Fase 9)
│   └── exporter.py              # Export functionality (Fase 10)
│
├── docs/                         # Documentation
│   ├── PLAN.md                  # Complete project plan
│   ├── PHASE_1_COMPLETE.md      # Phase 1 status
│   ├── FASE_1_IMPLEMENTATION.md # Phase 1 implementation details
│   ├── IFC_FORMAT_DIFFERENCES.md # IFC 2.3 vs 4.3 comparison
│   └── IFC_UNIVERSAL_HANDLERS.md # Universal extraction patterns
│
├── data/                         # Input IFC files
│   ├── 23BIM.ifc                # IFC 2.3 test file
│   └── 43BIM.ifc                # IFC 4.3 test file
│
├── output/                       # Export results (CSV, Excel, JSON)
├── logs/                         # Application logs
├── test_files/                   # Test data (empty)
│
├── main.py                       # Wrapper entry point
├── README.md                     # This file
└── requirements.txt              # Python dependencies
```

## Installatie

### 1. Afhankelijkheden installeren

```bash
pip install -r requirements.txt
```

Dit installeert:
- `ifcopenshell` - IFC file reading
- `pandas` - Data processing
- `openpyxl` - Excel export

### 2. Project verificatie

```python
python -c "from src.config import SUPPORTED_SCHEMAS; print(SUPPORTED_SCHEMAS)"
```

## Gebruik

### Via Commando Lijn

```bash
# Basis gebruik
python main.py data/23BIM.ifc

# Met opties
python main.py data/23BIM.ifc --output results/ --format xlsx --log-level INFO

# Help weergeven
python main.py --help
```

### Via Python Script

```python
import sys
from pathlib import Path

# Setup path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from config import LOGS_DIR
from logger import initialize_logging, get_logger
from main import IFCMaterialExtractor

# Initialize
initialize_logging(LOGS_DIR, log_level="INFO")
logger = get_logger(__name__)

# Run extraction
extractor = IFCMaterialExtractor("data/23BIM.ifc", export_format="xlsx")
result = extractor.process()

print(result)
```

## Documentatie

Lees de documentatie bestanden in de `docs/` map:

1. **PLAN.md** - Compleet project plan met alle 12 fases
2. **PHASE_1_COMPLETE.md** - Status fase 1 (framework setup)
3. **FASE_1_IMPLEMENTATION.md** - Implementatie details van fase 1
4. **IFC_FORMAT_DIFFERENCES.md** - Verschillen IFC2.3 vs IFC4.3 met counts
5. **IFC_UNIVERSAL_HANDLERS.md** - Universele extraction patterns

## Configuratie

Alle configuratie is centraal in `src/config.py`:

- **Paden**: DATA_DIR, OUTPUT_DIR, LOGS_DIR
- **Schemas**: SUPPORTED_SCHEMAS, MATERIAL_TYPES_BY_SCHEMA
- **Property sets**: COMMON_PSETS, KEY_MATERIAL_PROPERTIES
- **Quantity types**: QUANTITY_TYPES
- **Export**: EXPORT_FORMATS, DEFAULT_EXPORT_FORMAT

## Logging

Logs worden automatisch aangemaakt in `logs/` map:

```
logs/
└── logs_2026-04-02.log    # Daily rotation
```

Log format: `TIMESTAMP - MODULE - LEVEL - MESSAGE`

Voorbeeld:
```
2026-04-02 11:19:08 - main - INFO - Initialized extractor for 23BIM.ifc
2026-04-02 11:19:09 - main - INFO - IFC schema detected: IFC2X3
```

## Ondersteunde Formaten

### Input
- IFC 2.3 (IFC2X3)
- IFC 4.3 (IFC4X3_ADD2)

### Output
- **CSV** - Comma-separated values
- **Excel** - .xlsx format (recommended)
- **JSON** - JSON format

## Project Fases

- [x] **Fase 1** - Initialisatie & Setup (COMPLEET)
- [ ] **Fase 2** - IFC Schema Detectie
- [ ] **Fase 3** - Element Extraction
- [ ] **Fase 4-6** - Material Mapping
- [ ] **Fase 7** - Quantity Extraction
- [ ] **Fase 8** - Property Extraction
- [ ] **Fase 9** - Data Aggregation
- [ ] **Fase 10** - Export Functionality
- [ ] **Fase 11** - Testing & Validatie
- [ ] **Fase 12** - Documentatie & Afronding

## Voorbeeld Output

### Aggregated Material Summary
```
material_name | element_type | ifc_schema | element_count | total_volume_m3 | total_area_m2
Concrete      | IfcSlab     | IFC2X3     | 45            | 1250.5          | 2500.0
Steel         | IfcColumn   | IFC2X3     | 12            | 15.3            | 45.6
Brick         | IfcWall     | IFC2X3     | 120           | 450.0           | 1200.0
```

### Element Details
```
element_guid | element_name | element_type | material_name | volume_m3 | area_m2 | ifc_schema
ABC123...    | Slab-1      | IfcSlab      | Concrete      | 27.8      | 55.6    | IFC2X3
```

## Aannames

1. **Objectstructuur** - Overeenkomt met fysieke opbouw gebouw
2. **Materiaalinformatie** - Is gekoppeld aan objecten in model
3. **Detailniveau** - Varieert per model (geen gestandaardiseerde maatstaf)

## Vereisten

- Python 3.8+
- ifcopenshell 0.7.0+
- pandas 1.5.0+
- openpyxl 3.0.0+

## Status

**Phase 1: COMPLEET** ✅
- Framework setup
- Configuration system
- Logging framework
- Entry point
- Organized project structure

**Ready for**: Phase 2 (IFC Schema Detection)

## Licentie & Contact

IFC Material Extractor - BIM Material Data Extraction Tool

---

Zie `docs/` map voor volledige project documentatie.
