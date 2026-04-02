# Fase 3: Bouwelementen Extraheren - Implementatie Plan

## Overzicht

**Doel**: Alle fysieke bouwelementen uit IFC-bestand ophalen
**Input**: IFC file object + Schema (van Fase 2)
**Output**: Gestructureerde lijst van elementen met ID, naam, type
**Dependencies**: Fase 2 (ifc_reader), Fase 1 (framework)

---

## Fase 3 Stap 1 Details

### **Wat moet gebeuren**

1. ✅ Query alle IfcElement objecten (inclusief subtypes)
2. ✅ Per element: GlobalId ophalen (unieke identifier)
3. ✅ Per element: Name ophalen (gebruiksnaam)
4. ✅ Per element: is_a() bepalen (werkelijk type)
5. ✅ Data structureren (dict of dataclass)
6. ✅ Filtering op validiteit (verwijder lege entries)
7. ✅ Aggregatie (groepeer per type)
8. ✅ Logging van alle stappen

### **Waarom Elementen Belangrijk Zijn**

Elementen zijn de "container" voor:
- Materiaalkoppelingen (Fase 4)
- Hoeveelheden (Fase 7)
- Properties (Fase 8)
- Geometrie (Fase 10)

Zonder elementen hebben we niets om material info aan vast te maken!

---

## Data Structuur

### **Element Object (Internal)**
```python
{
    'global_id': 'ABCD1234...',          # Unieke ID
    'name': 'Wall-001',                  # User-assigned name
    'type': 'IfcWall',                   # IFC entity type
    'object': <ifcopenshell_entity>,     # Direct reference
    'schema': 'IFC2X3',                  # For later use
}
```

### **Statistics**
```python
{
    'total_elements': 2381,
    'by_type': {
        'IfcWall': 125,
        'IfcSlab': 45,
        'IfcColumn': 78,
        # ...
    },
    'with_materials': 1234,              # Count with material associations
    'without_materials': 1147,           # Count without
    'schema': 'IFC2X3'
}
```

---

## Implementation Plan

### **File: src/element_extractor.py**

```python
"""
Element Extractor - Fase 3 Implementation

Extracts all building elements from IFC model.
Provides structured data for downstream processing.
"""

from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from logger import get_logger
from config import BUILDING_ELEMENT_TYPES

# ============================================================================
# ELEMENT EXTRACTOR CLASS
# ============================================================================

class ElementExtractor:
    """
    Extracts building elements from IFC file.
    
    Responsibilities:
    1. Query all IfcElement objects
    2. Extract key properties (GlobalId, Name, Type)
    3. Structure data for downstream processing
    4. Generate statistics
    5. Log all operations
    """
    
    def __init__(self, ifc_file: object, schema: str):
        """
        Initialize extractor
        
        Args:
            ifc_file: ifcopenshell file object (from Phase 2)
            schema: IFC schema string (e.g., "IFC2X3")
        """
        self.logger = get_logger(__name__)
        self.ifc_file = ifc_file
        self.schema = schema
        self.elements = []
        self.statistics = {}
    
    def extract(self) -> List[Dict]:
        """
        Extract all building elements
        
        Returns:
            List of element dictionaries
        """
        self.logger.info("="*70)
        self.logger.info("FASE 3: Extracting Building Elements")
        self.logger.info("="*70)
        
        # Step 1: Query all elements
        all_elements = self._query_elements()
        
        # Step 2: Extract per element
        self.elements = self._extract_element_data(all_elements)
        
        # Step 3: Generate statistics
        self.statistics = self._generate_statistics()
        
        # Step 4: Log results
        self._log_results()
        
        return self.elements
    
    def _query_elements(self) -> List:
        """
        Query all IfcElement objects from file
        
        Returns:
            List of ifcopenshell element objects
        """
        self.logger.info("Querying all IfcElement objects...")
        
        try:
            # This gets ALL physical objects (walls, doors, slabs, etc.)
            # include_subtypes=True means we get derived types too
            all_elements = self.ifc_file.by_type(
                "IfcElement",
                include_subtypes=True
            )
            
            self.logger.info("Found {} elements".format(len(all_elements)))
            return all_elements
            
        except Exception as e:
            self.logger.error("Failed to query elements: {}".format(str(e)))
            return []
    
    def _extract_element_data(self, elements: List) -> List[Dict]:
        """
        Extract key data from each element
        
        Args:
            elements: List of ifcopenshell element objects
            
        Returns:
            List of structured element dictionaries
        """
        self.logger.info("Extracting data for {} elements...".format(len(elements)))
        
        extracted = []
        errors = 0
        
        for elem in elements:
            try:
                element_info = self._extract_single_element(elem)
                if element_info:
                    extracted.append(element_info)
                    
            except Exception as e:
                errors += 1
                if errors <= 5:  # Log first 5 errors only
                    self.logger.warning(
                        "Error extracting element: {}".format(str(e))
                    )
        
        if errors > 5:
            self.logger.warning("... and {} more errors".format(errors - 5))
        
        self.logger.info("Successfully extracted {} elements".format(len(extracted)))
        
        return extracted
    
    def _extract_single_element(self, elem: object) -> Optional[Dict]:
        """
        Extract data from single element
        
        Args:
            elem: ifcopenshell element object
            
        Returns:
            Dictionary with element data, or None if invalid
        """
        # Get GlobalId (unique identifier)
        global_id = None
        if hasattr(elem, 'GlobalId'):
            global_id = elem.GlobalId
        
        # Get Name (user-friendly name)
        name = "Unknown"
        if hasattr(elem, 'Name') and elem.Name:
            name = elem.Name
        
        # Get type via is_a() method
        elem_type = elem.is_a()
        
        # Skip if critical data missing
        if not global_id:
            return None
        
        return {
            'global_id': global_id,
            'name': name,
            'type': elem_type,
            'object': elem,
            'schema': self.schema,
        }
    
    def _generate_statistics(self) -> Dict:
        """
        Generate extraction statistics
        
        Returns:
            Dictionary with stats
        """
        self.logger.info("Generating statistics...")
        
        # Count by element type
        by_type = defaultdict(int)
        for elem in self.elements:
            by_type[elem['type']] += 1
        
        # Aggregate stats
        stats = {
            'total_elements': len(self.elements),
            'by_type': dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)),
            'schema': self.schema,
            'with_names': sum(1 for e in self.elements if e['name'] != 'Unknown'),
            'without_names': sum(1 for e in self.elements if e['name'] == 'Unknown'),
        }
        
        return stats
    
    def _log_results(self):
        """Log extraction results"""
        self.logger.info("-" * 70)
        self.logger.info("EXTRACTION SUMMARY:")
        self.logger.info("  Total elements: {}".format(self.statistics['total_elements']))
        self.logger.info("  Elements with names: {}".format(self.statistics['with_names']))
        self.logger.info("  Top element types:")
        
        for elem_type, count in list(self.statistics['by_type'].items())[:10]:
            self.logger.info("    - {}: {}".format(elem_type, count))
        
        if len(self.statistics['by_type']) > 10:
            self.logger.info("    ... and {} more types".format(
                len(self.statistics['by_type']) - 10
            ))
        
        self.logger.info("-" * 70)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_elements(self) -> List[Dict]:
        """Get extracted elements"""
        return self.elements
    
    def get_statistics(self) -> Dict:
        """Get extraction statistics"""
        return self.statistics
    
    def count_by_type(self, element_type: str) -> int:
        """Count elements of specific type"""
        return sum(1 for e in self.elements if e['type'] == element_type)
    
    def filter_by_type(self, element_type: str) -> List[Dict]:
        """Get all elements of specific type"""
        return [e for e in self.elements if e['type'] == element_type]
    
    def get_element_by_id(self, global_id: str) -> Optional[Dict]:
        """Get specific element by GlobalId"""
        for elem in self.elements:
            if elem['global_id'] == global_id:
                return elem
        return None


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION
# ============================================================================

def extract_elements(ifc_file: object, schema: str) -> Tuple[List[Dict], Dict]:
    """
    Convenience function to extract elements in one call
    
    Usage:
        from element_extractor import extract_elements
        
        elements, stats = extract_elements(ifc_file, "IFC2X3")
        
    Args:
        ifc_file: ifcopenshell file object
        schema: IFC schema string
        
    Returns:
        Tuple of (elements_list, statistics_dict)
    """
    extractor = ElementExtractor(ifc_file, schema)
    elements = extractor.extract()
    stats = extractor.get_statistics()
    return elements, stats
```

---

## Integration met main.py (Fase 1)

In `src/main.py`, methode `_extract_elements()`:

```python
def _extract_elements(self):
    """Fase 3: Extract all building elements"""
    from element_extractor import extract_elements
    
    if not self.ifc_file:
        raise IFCReadError("IFC file not loaded")
    
    try:
        self.elements, self.element_stats = extract_elements(
            self.ifc_file,
            self.ifc_schema
        )
        
        self.logger.info("Extracted {} elements".format(len(self.elements)))
        
    except Exception as e:
        self.logger.warning("Error extracting elements: {}".format(str(e)))
```

---

## Expected Output Data

### **Element List (Example)**
```python
[
    {
        'global_id': '0cuI7KggD11h_tIjgK$8_10',
        'name': 'Wall-001',
        'type': 'IfcWall',
        'object': <ifcopenshell.entity>,
        'schema': 'IFC2X3',
    },
    {
        'global_id': '0cuI7KggD11h_tIjgK$8_11',
        'name': 'Slab-Ground',
        'type': 'IfcSlab',
        'object': <ifcopenshell.entity>,
        'schema': 'IFC2X3',
    },
    # ... 2379 more elements
]
```

### **Statistics (Example)**
```python
{
    'total_elements': 2381,
    'by_type': {
        'IfcWall': 892,
        'IfcDoor': 145,
        'IfcSlab': 234,
        'IfcColumn': 78,
        # ...
    },
    'with_names': 2341,
    'without_names': 40,
    'schema': 'IFC2X3',
}
```

### **Logging Output**
```
2026-04-02 XX:XX:XX - element_extractor - INFO - ======================================================================
2026-04-02 XX:XX:XX - element_extractor - INFO - FASE 3: Extracting Building Elements
2026-04-02 XX:XX:XX - element_extractor - INFO - ======================================================================
2026-04-02 XX:XX:XX - element_extractor - INFO - Querying all IfcElement objects...
2026-04-02 XX:XX:XX - element_extractor - INFO - Found 2381 elements
2026-04-02 XX:XX:XX - element_extractor - INFO - Extracting data for 2381 elements...
2026-04-02 XX:XX:XX - element_extractor - INFO - Successfully extracted 2381 elements
2026-04-02 XX:XX:XX - element_extractor - INFO - Generating statistics...
2026-04-02 XX:XX:XX - element_extractor - INFO - -----------------------------------------------------------------------
2026-04-02 XX:XX:XX - element_extractor - INFO - EXTRACTION SUMMARY:
2026-04-02 XX:XX:XX - element_extractor - INFO -   Total elements: 2381
2026-04-02 XX:XX:XX - element_extractor - INFO -   Elements with names: 2341
2026-04-02 XX:XX:XX - element_extractor - INFO -   Top element types:
2026-04-02 XX:XX:XX - element_extractor - INFO -     - IfcWall: 892
2026-04-02 XX:XX:XX - element_extractor - INFO -     - IfcSlab: 234
2026-04-02 XX:XX:XX - element_extractor - INFO -     - IfcDoor: 145
2026-04-02 XX:XX:XX - element_extractor - INFO - -----------------------------------------------------------------------
```

---

## Testing Strategy

### **Unit Tests**
```python
# test_element_extractor.py

import pytest
from element_extractor import ElementExtractor, extract_elements

class TestElementExtractor:
    
    def test_extract_elements_ifc23(self, ifc_file_23):
        """Test extracting elements from IFC2X3"""
        extractor = ElementExtractor(ifc_file_23, "IFC2X3")
        elements = extractor.extract()
        
        assert len(elements) > 0
        assert all('global_id' in e for e in elements)
        assert all('name' in e for e in elements)
        assert all('type' in e for e in elements)
    
    def test_extract_elements_ifc4(self, ifc_file_4):
        """Test extracting elements from IFC4"""
        extractor = ElementExtractor(ifc_file_4, "IFC4X3_ADD2")
        elements = extractor.extract()
        
        assert len(elements) > 0
    
    def test_statistics_generated(self, ifc_file_23):
        """Test that statistics are generated"""
        extractor = ElementExtractor(ifc_file_23, "IFC2X3")
        extractor.extract()
        
        stats = extractor.get_statistics()
        assert 'total_elements' in stats
        assert 'by_type' in stats
        assert stats['total_elements'] > 0
    
    def test_element_has_all_fields(self, ifc_file_23):
        """Test element structure"""
        extractor = ElementExtractor(ifc_file_23, "IFC2X3")
        elements = extractor.extract()
        
        required_fields = ['global_id', 'name', 'type', 'object', 'schema']
        for elem in elements[:10]:
            for field in required_fields:
                assert field in elem
    
    def test_filter_by_type(self, ifc_file_23):
        """Test type filtering"""
        extractor = ElementExtractor(ifc_file_23, "IFC2X3")
        extractor.extract()
        
        walls = extractor.filter_by_type("IfcWall")
        assert len(walls) > 0
        assert all(e['type'] == 'IfcWall' for e in walls)
    
    def test_get_element_by_id(self, ifc_file_23):
        """Test ID-based lookup"""
        extractor = ElementExtractor(ifc_file_23, "IFC2X3")
        elements = extractor.extract()
        
        if elements:
            first_id = elements[0]['global_id']
            found = extractor.get_element_by_id(first_id)
            assert found is not None
            assert found['global_id'] == first_id
```

---

## Deliverables (Fase 3)

- [x] **src/element_extractor.py** - Complete implementation
- [x] **Integration** - Works with main.py and Phase 2
- [x] **Logging** - All operations logged
- [x] **Error Handling** - Proper exception handling
- [x] **Documentation** - Code is well commented
- [ ] **Tests** - Unit tests (optional for phase 3)

---

## Success Criteria

- ✅ Extract all IfcElement objects
- ✅ Get GlobalId, Name, Type for each
- ✅ Structure data as dictionaries
- ✅ Generate statistics by type
- ✅ Handle elements without names
- ✅ Log all operations
- ✅ Integrates with Fase 2 output
- ✅ Ready for Fase 4 (material extraction)
- ✅ Works with both IFC2X3 and IFC4X3

---

## Fase 3 Flow Diagram

```
Input: ifc_file (from Phase 2), schema
    ↓
[_query_elements]
  - ifc_file.by_type("IfcElement", include_subtypes=True)
  - Returns ~2000-3000 elements
    ↓
[_extract_element_data]
  - Loop through each element
  - Extract GlobalId, Name, Type
  - Create structured dictionary
    ↓
[_extract_single_element]
  - Global_id check (required)
  - Name extraction (with fallback)
  - Type via is_a()
    ↓
[_generate_statistics]
  - Count total elements
  - Group by type
  - Count with/without names
    ↓
[_log_results]
  - Summary to logger
  - Top 10 types
    ↓
Output: (elements_list, statistics_dict)
```

---

## Dependencies

- ✅ Phase 2 output (ifc_file, schema)
- ✅ Fase 1 framework (logger, config)
- ✅ Python stdlib (typing, collections)

---

## Performance Notes

| Metric | Expected Value |
|--------|---|
| Query time | 100-500ms |
| Extraction time | 500-2000ms (per 2000 elements) |
| Memory per element | ~500 bytes |
| Total memory (2000 elems) | ~1MB |

---

## Timeline

| Task | Duration |
|------|----------|
| Write ElementExtractor class | 20 min |
| Implement extraction methods | 25 min |
| Statistics generation | 15 min |
| Error handling | 10 min |
| Integration & testing | 15 min |
| Documentation | 10 min |
| **Total** | **~95 min** |

---

## Volgende Stappen na Fase 3

Zodra Fase 3 compleet is, beginnen we met **Fase 4: Materiaalkoppelingen Ophalen**

Fase 4 zal gebruiken:
- ✅ elements list (van Fase 3)
- ➕ elem.HasAssociations (loop)
- ➕ rel.is_a("IfcRelAssociatesMaterial")
- ➕ rel.RelatingMaterial (parse)
