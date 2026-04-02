"""
Configuration constants and settings for the IFC Material Extractor application.
"""

from pathlib import Path
from enum import Enum

# ============================================================================
# PROJECT PATHS
# ============================================================================
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
LOGS_DIR = PROJECT_ROOT / "logs"
TEST_FILES_DIR = PROJECT_ROOT / "test_files"

# Create directories if they don't exist
for directory in [DATA_DIR, OUTPUT_DIR, LOGS_DIR, TEST_FILES_DIR]:
    directory.mkdir(exist_ok=True)

# ============================================================================
# IFC SCHEMA CONFIGURATION
# ============================================================================
SUPPORTED_SCHEMAS = ["IFC2X3", "IFC4X3_ADD2"]

# Material types per schema version
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

# Map schema strings to material type lists
MATERIAL_TYPES_BY_SCHEMA = {
    "IFC2X3": MATERIAL_TYPES_IFC2X3,
    "IFC2X4": MATERIAL_TYPES_IFC2X3,  # Similar to 2X3
    "IFC4X3_ADD2": MATERIAL_TYPES_IFC4X3,
    "IFC4": MATERIAL_TYPES_IFC4X3,
    "IFC4X0": MATERIAL_TYPES_IFC4X3,
}

# ============================================================================
# PROPERTY SET CONFIGURATION
# ============================================================================
COMMON_PSETS = [
    "Pset_BuildingElementProxyCommon",
    "Pset_SlabCommon",
    "Pset_WallCommon",
    "Pset_DoorCommon",
    "Pset_WindowCommon",
    "Pset_QuantityTakeOff",
    "Pset_ReinforcementBarPitchOfSlab"
]

# Key property names to extract
KEY_MATERIAL_PROPERTIES = [
    "MassDensity",
    "YoungModulus",
    "ThermalConductivity",
    "Cost",
    "Flammability",
    "SurfaceRoughness"
]

# ============================================================================
# QUANTITY TYPES CONFIGURATION (UNIVERSAL - both schemas)
# ============================================================================
QUANTITY_TYPES = [
    "IfcQuantityVolume",      # m³
    "IfcQuantityArea",        # m²
    "IfcQuantityLength",      # m
    "IfcQuantityCount",       # count
    "IfcQuantityWeight"       # kg
]

QUANTITY_TYPE_UNITS = {
    "IfcQuantityVolume": "m³",
    "IfcQuantityArea": "m²",
    "IfcQuantityLength": "m",
    "IfcQuantityCount": "count",
    "IfcQuantityWeight": "kg"
}

# ============================================================================
# BUILDING ELEMENT TYPES
# ============================================================================
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
    "IfcFurniture",
    "IfcSpace",
    "IfcOpeningElement"
]

# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================
EXPORT_FORMATS = ["csv", "xlsx", "json"]
DEFAULT_EXPORT_FORMAT = "xlsx"
CSV_ENCODING = "utf-8"
CSV_DELIMITER = ","

# Excel sheet names
EXCEL_SHEET_AGGREGATED = "Material Summary"
EXCEL_SHEET_DETAILED = "Element Details"
EXCEL_SHEET_METADATA = "Metadata"

# ============================================================================
# PROCESSING CONFIGURATION
# ============================================================================
# Tolerances
MIN_VOLUME_THRESHOLD = 0.001      # m³ (1 liter)
MIN_AREA_THRESHOLD = 0.001        # m²

# Batch processing
BATCH_SIZE = 100                  # elements per batch

# Validation
VALIDATE_OUTPUT = True

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================
LOG_LEVEL = "INFO"
LOG_TO_FILE = True
LOG_TO_CONSOLE = True
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============================================================================
# OUTPUT COLUMNS CONFIGURATION
# ============================================================================
AGGREGATED_OUTPUT_COLUMNS = [
    "material_name",
    "ifc_element_type",
    "ifc_schema",
    "element_count",
    "total_volume_m3",
    "total_area_m2",
    "total_weight_kg",
    "element_ids_sample",
    "extraction_date"
]

DETAILED_OUTPUT_COLUMNS = [
    "element_guid",
    "element_name",
    "element_type",
    "material_name",
    "material_type",
    "volume_m3",
    "area_m2",
    "weight_kg",
    "ifc_schema",
    "extraction_date"
]
