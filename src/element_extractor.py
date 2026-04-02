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

