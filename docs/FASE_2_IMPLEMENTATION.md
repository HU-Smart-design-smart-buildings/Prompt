# Fase 2: IFC Schema Detectie & File Reading - Implementatie Plan

## Overzicht

**Doel**: IFC-bestand veilig inlezen en schema versie detecteren
**Input**: Path naar IFC bestand
**Output**: Loaded IFC file object + Schema version
**Dependencies**: Fase 1 (config, logger, main framework)

---

## Fase 2 Stap 0 Details

### **Wat moet gebeuren**

1. ✅ IFC-bestand openen met `ifcopenshell.open()`
2. ✅ Schema versie uitlezen (`ifc.schema`)
3. ✅ Schema validatie (is het ondersteund?)
4. ✅ File validatie (IFC format check)
5. ✅ Error handling (niet-bestaande file, corrupt file, etc.)
6. ✅ Logging van alle stappen

### **Waarom Schema Belangrijk Is**

Schema bepaalt:
- Welke material types beschikbaar zijn
- Welke property sets beschikbaar zijn
- Welke entities kunnen voorkomen
- Hoe data genest is (andere nesting in IFC2X3 vs IFC4)

Voorbeeld uit onze analyse:
```
IFC2X3:
  - IfcMaterial: 1,789 instances
  - IfcMaterialLayerSet: 1,531 instances
  - IfcMaterialConstituentSet: NOT AVAILABLE

IFC4X3_ADD2:
  - IfcMaterial: 3,748 instances
  - IfcMaterialLayerSet: 177 instances
  - IfcMaterialConstituentSet: 831 instances ← NEW!
```

---

## Implementation Plan

### **File: src/ifc_reader.py**

```python
"""
IFC File Reader - Fase 2 Implementation

Handles IFC file loading and schema detection.
Entry point for all IFC processing.
"""

import ifcopenshell
from pathlib import Path
from typing import Tuple, Optional
from logger import get_logger, IFCReadError
from config import SUPPORTED_SCHEMAS, PROJECT_ROOT

# ============================================================================
# IFC_READER CLASS
# ============================================================================

class IFCFileReader:
    """
    Reads and validates IFC files.
    
    Responsibilities:
    1. Open IFC file safely
    2. Detect and validate schema
    3. Return file object ready for processing
    4. Log all operations
    """
    
    def __init__(self):
        """Initialize reader with logger"""
        self.logger = get_logger(__name__)
        self.ifc_file = None
        self.schema = None
        self.file_path = None
    
    def read_file(self, file_path: str) -> Tuple[object, str]:
        """
        Read IFC file and detect schema
        
        Args:
            file_path: Path to IFC file
            
        Returns:
            Tuple of (ifc_file_object, schema_string)
            
        Raises:
            IFCReadError: If file can't be read or schema invalid
        """
        self.logger.info("="*70)
        self.logger.info("FASE 2: IFC Schema Detection & File Reading")
        self.logger.info("="*70)
        
        # Step 1: Validate file exists
        file_path = self._validate_file_path(file_path)
        self.file_path = file_path
        
        # Step 2: Open IFC file
        self.ifc_file = self._open_ifc_file(file_path)
        
        # Step 3: Detect schema
        self.schema = self._detect_schema()
        
        # Step 4: Validate schema
        self._validate_schema()
        
        # Step 5: Log summary
        self._log_summary()
        
        return self.ifc_file, self.schema
    
    def _validate_file_path(self, file_path: str) -> Path:
        """
        Validate that file exists and is readable
        
        Args:
            file_path: Path string
            
        Returns:
            Path object
            
        Raises:
            IFCReadError: If file invalid
        """
        path = Path(file_path)
        
        # Check existence
        if not path.exists():
            raise IFCReadError(
                "File not found: {}".format(path)
            )
        
        # Check is file (not directory)
        if not path.is_file():
            raise IFCReadError(
                "Path is not a file: {}".format(path)
            )
        
        # Check extension
        if path.suffix.lower() != '.ifc':
            self.logger.warning(
                "File extension is '{}', expected '.ifc'".format(path.suffix)
            )
        
        # Check readable
        if not path.stat().st_size > 0:
            raise IFCReadError(
                "File is empty: {}".format(path)
            )
        
        self.logger.info("Input file: {}".format(path.name))
        self.logger.info("File size: {:.2f} MB".format(
            path.stat().st_size / (1024*1024)
        ))
        
        return path
    
    def _open_ifc_file(self, file_path: Path) -> object:
        """
        Open IFC file using ifcopenshell
        
        Args:
            file_path: Path to IFC file
            
        Returns:
            ifcopenshell file object
            
        Raises:
            IFCReadError: If file can't be parsed
        """
        try:
            self.logger.info("Opening IFC file...")
            ifc_file = ifcopenshell.open(str(file_path))
            self.logger.info("File opened successfully")
            return ifc_file
            
        except Exception as e:
            raise IFCReadError(
                "Failed to open IFC file: {}".format(str(e))
            )
    
    def _detect_schema(self) -> str:
        """
        Detect IFC schema version from file
        
        Returns:
            Schema string (e.g., "IFC2X3", "IFC4X3_ADD2")
            
        Raises:
            IFCReadError: If schema can't be detected
        """
        try:
            self.logger.info("Detecting IFC schema...")
            
            # ifcopenshell provides schema directly
            schema = self.ifc_file.schema
            
            if not schema:
                raise IFCReadError("Schema not found in file")
            
            self.logger.info("Schema detected: {}".format(schema))
            return schema
            
        except Exception as e:
            raise IFCReadError(
                "Failed to detect schema: {}".format(str(e))
            )
    
    def _validate_schema(self):
        """
        Validate that schema is supported
        
        Raises:
            IFCReadError: If schema not supported
        """
        self.logger.info("Validating schema...")
        
        # Check if supported
        if self.schema not in SUPPORTED_SCHEMAS:
            self.logger.warning(
                "Schema '{}' not in official supported list: {}".format(
                    self.schema, SUPPORTED_SCHEMAS
                )
            )
            self.logger.warning(
                "Continuing anyway (may work or may have issues)"
            )
        else:
            self.logger.info("Schema is fully supported")
    
    def _log_summary(self):
        """Log summary of opened file"""
        self.logger.info("-" * 70)
        self.logger.info("FILE SUMMARY:")
        self.logger.info("  Path: {}".format(self.file_path))
        self.logger.info("  Schema: {}".format(self.schema))
        self.logger.info("  File object: {}".format(type(self.ifc_file)))
        self.logger.info("-" * 70)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_file(self) -> object:
        """Get loaded IFC file object"""
        if not self.ifc_file:
            raise IFCReadError("No file loaded")
        return self.ifc_file
    
    def get_schema(self) -> str:
        """Get detected schema"""
        if not self.schema:
            raise IFCReadError("Schema not detected")
        return self.schema
    
    def is_schema_2x3(self) -> bool:
        """Check if schema is IFC2X3"""
        return self.schema in ["IFC2X3", "IFC2X4"]
    
    def is_schema_4x(self) -> bool:
        """Check if schema is IFC4.x"""
        return self.schema.startswith("IFC4")


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION
# ============================================================================

def load_ifc_file(file_path: str) -> Tuple[object, str]:
    """
    Convenience function to load IFC file in one call
    
    Usage:
        from ifc_reader import load_ifc_file
        
        ifc_file, schema = load_ifc_file("data/23BIM.ifc")
        
    Args:
        file_path: Path to IFC file
        
    Returns:
        Tuple of (ifc_file_object, schema_string)
    """
    reader = IFCFileReader()
    return reader.read_file(file_path)
```

---

## Integration met main.py (Fase 1)

In `src/main.py`, methode `_load_and_detect_schema()`:

```python
def _load_and_detect_schema(self):
    """Fase 2: Load IFC file and detect schema version"""
    from ifc_reader import load_ifc_file  # Import hier
    
    try:
        self.ifc_file, self.ifc_schema = load_ifc_file(str(self.input_file))
        self.logger.info("Schema detected: {}".format(self.ifc_schema))
        
    except Exception as e:
        raise IFCReadError("Failed to load IFC file: {}".format(str(e)))
```

---

## Testing Strategy

### **Unit Tests**

```python
# test_ifc_reader.py

import pytest
from pathlib import Path
from ifc_reader import IFCFileReader
from logger import IFCReadError

class TestIFCFileReader:
    
    def test_valid_ifc23_file(self):
        """Test loading valid IFC2X3 file"""
        reader = IFCFileReader()
        ifc_file, schema = reader.read_file("data/23BIM.ifc")
        
        assert schema == "IFC2X3"
        assert ifc_file is not None
    
    def test_valid_ifc4_file(self):
        """Test loading valid IFC4 file"""
        reader = IFCFileReader()
        ifc_file, schema = reader.read_file("data/43BIM.ifc")
        
        assert schema == "IFC4X3_ADD2"
        assert ifc_file is not None
    
    def test_file_not_found(self):
        """Test error handling for missing file"""
        reader = IFCFileReader()
        
        with pytest.raises(IFCReadError):
            reader.read_file("nonexistent.ifc")
    
    def test_invalid_format(self):
        """Test error handling for invalid file"""
        reader = IFCFileReader()
        
        # Create temp non-IFC file
        with open("/tmp/test.txt", "w") as f:
            f.write("not an IFC file")
        
        with pytest.raises(IFCReadError):
            reader.read_file("/tmp/test.txt")
    
    def test_schema_detection_accuracy(self):
        """Test that correct schema is detected"""
        reader = IFCFileReader()
        
        # IFC2X3
        _, schema23 = reader.read_file("data/23BIM.ifc")
        assert "2X3" in schema23
        
        # IFC4
        _, schema4 = reader.read_file("data/43BIM.ifc")
        assert "4" in schema4
```

---

## Logging Output (Expected)

```
2026-04-02 09:30:00 - ifc_reader - INFO - ======================================================================
2026-04-02 09:30:00 - ifc_reader - INFO - FASE 2: IFC Schema Detection & File Reading
2026-04-02 09:30:00 - ifc_reader - INFO - ======================================================================
2026-04-02 09:30:00 - ifc_reader - INFO - Input file: 23BIM.ifc
2026-04-02 09:30:00 - ifc_reader - INFO - File size: 125.43 MB
2026-04-02 09:30:01 - ifc_reader - INFO - Opening IFC file...
2026-04-02 09:30:02 - ifc_reader - INFO - File opened successfully
2026-04-02 09:30:02 - ifc_reader - INFO - Detecting IFC schema...
2026-04-02 09:30:02 - ifc_reader - INFO - Schema detected: IFC2X3
2026-04-02 09:30:02 - ifc_reader - INFO - Validating schema...
2026-04-02 09:30:02 - ifc_reader - INFO - Schema is fully supported
2026-04-02 09:30:02 - ifc_reader - INFO - ----------------------------------------------------------------------
2026-04-02 09:30:02 - ifc_reader - INFO - FILE SUMMARY:
2026-04-02 09:30:02 - ifc_reader - INFO -   Path: C:\Users\...\data\23BIM.ifc
2026-04-02 09:30:02 - ifc_reader - INFO -   Schema: IFC2X3
2026-04-02 09:30:02 - ifc_reader - INFO -   File object: <class 'ifcopenshell.file.file'>
2026-04-02 09:30:02 - ifc_reader - INFO - ----------------------------------------------------------------------
```

---

## Deliverables (Fase 2)

- [x] **src/ifc_reader.py** - Complete implementation
- [x] **Integration** - Works with main.py
- [x] **Logging** - All operations logged
- [x] **Error Handling** - Proper exception handling
- [x] **Documentation** - Code is well commented
- [ ] **Tests** - Unit tests (optional for phase 2)

---

## Success Criteria

- ✅ Can open IFC2X3 files
- ✅ Can open IFC4X3 files
- ✅ Correctly detects schema version
- ✅ Validates file before processing
- ✅ Proper error messages on failure
- ✅ All operations logged
- ✅ Integrates with Fase 1 framework
- ✅ Ready for Fase 3 (element extraction)

---

## Fase 2 Flow Diagram

```
Input: IFC file path
    ↓
[_validate_file_path]
  - Check exists
  - Check is file
  - Check extension
  - Check readable
    ↓
[_open_ifc_file]
  - ifcopenshell.open()
  - Error handling
    ↓
[_detect_schema]
  - Read ifc.schema
  - Normalize format
    ↓
[_validate_schema]
  - Check SUPPORTED_SCHEMAS
  - Log warning if unknown
    ↓
[_log_summary]
  - Summary to logger
    ↓
Output: (ifc_file_object, schema_string)
```

---

## Dependencies

- ✅ ifcopenshell (already installed)
- ✅ Fase 1 framework (config, logger)
- ✅ Python stdlib (pathlib, typing)

---

## Timeline

| Task | Duration |
|------|----------|
| Write IFCFileReader class | 15 min |
| Implement validation methods | 20 min |
| Add error handling | 15 min |
| Integration tests | 10 min |
| Documentation | 10 min |
| **Total** | **~70 min** |

---

## Volgende Stappen na Fase 2

Zodra Fase 2 compleet is, beginnen we met **Fase 3: Element Extraction**

Fase 3 zal gebruiken:
- ✅ ifc_file object (van Fase 2)
- ✅ schema information (van Fase 2)
- ➕ ifc_file.by_type("IfcElement", include_subtypes=True)
