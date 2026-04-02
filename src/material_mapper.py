"""
Material Mapper - Fase 4 Implementation

Maps building elements to material relationships.
Queries IfcRelAssociatesMaterial for each element.
"""

from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from logger import get_logger


# ============================================================================
# MATERIAL MAPPER CLASS
# ============================================================================

class MaterialMapper:
    """
    Maps elements to material relationships via IfcRelAssociatesMaterial.
    
    Responsibilities:
    1. Query HasAssociations for each element
    2. Find IfcRelAssociatesMaterial relationship
    3. Extract RelatingMaterial object
    4. Structure material data with element context
    5. Generate statistics
    6. Log all operations
    """
    
    def __init__(self, ifc_file: object, schema: str):
        """
        Initialize mapper
        
        Args:
            ifc_file: ifcopenshell file object (from Phase 2)
            schema: IFC schema string (e.g., "IFC2X3")
        """
        self.logger = get_logger(__name__)
        self.ifc_file = ifc_file
        self.schema = schema
        self.materials = []
        self.statistics = {}
    
    def map(self, elements: List[Dict]) -> List[Dict]:
        """
        Map materials for all elements
        
        Args:
            elements: List of element dicts from Phase 3
            
        Returns:
            List of material mapping dicts
        """
        self.logger.info("="*70)
        self.logger.info("FASE 4: Mapping Material Relationships")
        self.logger.info("="*70)
        
        # Step 1: Map each element
        self.materials = self._map_all_elements(elements)
        
        # Step 2: Generate statistics
        self.statistics = self._generate_statistics()
        
        # Step 3: Log results
        self._log_results()
        
        return self.materials
    
    def _map_all_elements(self, elements: List[Dict]) -> List[Dict]:
        """
        Map all elements to their materials
        
        Args:
            elements: List of element dicts from Phase 3
            
        Returns:
            List of material mapping dicts
        """
        self.logger.info("Mapping materials for {} elements...".format(len(elements)))
        
        materials = []
        errors = 0
        
        for elem in elements:
            try:
                result = self._map_single_element(elem)
                if result:
                    materials.append(result)
                    
            except Exception as e:
                errors += 1
                if errors <= 5:
                    self.logger.warning(
                        "Error mapping element: {}".format(str(e))
                    )
        
        if errors > 5:
            self.logger.warning("... and {} more errors".format(errors - 5))
        
        self.logger.info("Successfully mapped {} elements".format(len(materials)))
        
        return materials
    
    def _map_single_element(self, element: Dict) -> Optional[Dict]:
        """
        Map a single element to its material
        
        Args:
            element: Element dict from Phase 3
            
        Returns:
            Material mapping dict, or None if invalid
        """
        # Get element reference object
        elem_obj = element.get('object')
        if not elem_obj:
            return None
        
        # Step 1: Find IfcRelAssociatesMaterial
        material_rel = self._get_material_relationship(elem_obj)
        
        if not material_rel:
            # Element has no material relationship
            return {
                'element_global_id': element['global_id'],
                'element_name': element['name'],
                'element_type': element['type'],
                'material_global_id': None,
                'material_object': None,
                'material_raw_type': None,
                'schema': element['schema'],
            }
        
        # Step 2: Extract RelatingMaterial
        try:
            material = material_rel.RelatingMaterial
        except Exception as e:
            self.logger.warning("Failed to get RelatingMaterial: {}".format(str(e)))
            return None
        
        # Step 3: Get material GlobalId (if exists)
        material_global_id = None
        if hasattr(material, 'GlobalId'):
            try:
                material_global_id = material.GlobalId
            except:
                pass
        
        # Step 4: Get material raw type
        material_raw_type = None
        try:
            material_raw_type = material.is_a()
        except:
            pass
        
        return {
            'element_global_id': element['global_id'],
            'element_name': element['name'],
            'element_type': element['type'],
            'material_global_id': material_global_id,
            'material_object': material,
            'material_raw_type': material_raw_type,
            'schema': element['schema'],
        }
    
    def _get_material_relationship(self, element_obj: object) -> Optional[object]:
        """
        Find IfcRelAssociatesMaterial in element.HasAssociations
        
        HasAssociations can contain:
        - IfcRelAssociatesMaterial (what we want)
        - IfcRelAssociatesClassification
        - IfcRelAssociatesConstraint
        - Others
        
        Args:
            element_obj: ifcopenshell element object
            
        Returns:
            IfcRelAssociatesMaterial object, or None
        """
        # Check if element has HasAssociations
        if not hasattr(element_obj, 'HasAssociations'):
            return None
        
        associations = element_obj.HasAssociations
        if not associations:
            return None
        
        # Loop through associations to find IfcRelAssociatesMaterial
        for assoc in associations:
            try:
                if assoc.is_a() == "IfcRelAssociatesMaterial":
                    return assoc
            except:
                # Skip malformed associations
                pass
        
        return None
    
    def _generate_statistics(self) -> Dict:
        """
        Generate extraction statistics
        
        Returns:
            Dictionary with stats
        """
        self.logger.info("Generating statistics...")
        
        # Count by material type
        by_type = defaultdict(int)
        with_material = 0
        without_material = 0
        
        for mapping in self.materials:
            if mapping['material_raw_type']:
                with_material += 1
                by_type[mapping['material_raw_type']] += 1
            else:
                without_material += 1
        
        # Aggregate stats
        stats = {
            'total_elements_mapped': len(self.materials),
            'elements_with_material': with_material,
            'elements_without_material': without_material,
            'material_type_distribution': dict(sorted(
                by_type.items(),
                key=lambda x: x[1],
                reverse=True
            )),
            'schema': self.schema,
        }
        
        return stats
    
    def _log_results(self):
        """Log mapping results"""
        self.logger.info("-" * 70)
        self.logger.info("MAPPING SUMMARY:")
        self.logger.info("  Total elements mapped: {}".format(
            self.statistics['total_elements_mapped']
        ))
        self.logger.info("  Elements with material: {} ({:.1f}%)".format(
            self.statistics['elements_with_material'],
            100.0 * self.statistics['elements_with_material'] / max(1, self.statistics['total_elements_mapped'])
        ))
        self.logger.info("  Elements without material: {} ({:.1f}%)".format(
            self.statistics['elements_without_material'],
            100.0 * self.statistics['elements_without_material'] / max(1, self.statistics['total_elements_mapped'])
        ))
        self.logger.info("  Material type distribution:")
        
        for mat_type, count in list(self.statistics['material_type_distribution'].items())[:10]:
            self.logger.info("    - {}: {}".format(mat_type, count))
        
        if len(self.statistics['material_type_distribution']) > 10:
            self.logger.info("    ... and {} more types".format(
                len(self.statistics['material_type_distribution']) - 10
            ))
        
        self.logger.info("-" * 70)
    
    # ========================================================================
    # UTILITY METHODS
    # ========================================================================
    
    def get_materials(self) -> List[Dict]:
        """Get mapped materials"""
        return self.materials
    
    def get_statistics(self) -> Dict:
        """Get mapping statistics"""
        return self.statistics
    
    def count_by_type(self, material_type: str) -> int:
        """Count materials of specific type"""
        return sum(1 for m in self.materials if m['material_raw_type'] == material_type)
    
    def filter_by_type(self, material_type: str) -> List[Dict]:
        """Get all materials of specific type"""
        return [m for m in self.materials if m['material_raw_type'] == material_type]
    
    def get_by_element_id(self, element_global_id: str) -> Optional[Dict]:
        """Get material mapping for specific element"""
        for mapping in self.materials:
            if mapping['element_global_id'] == element_global_id:
                return mapping
        return None
    
    def get_elements_with_material(self) -> List[Dict]:
        """Get all elements that have a material"""
        return [m for m in self.materials if m['material_object'] is not None]
    
    def get_elements_without_material(self) -> List[Dict]:
        """Get all elements that don't have a material"""
        return [m for m in self.materials if m['material_object'] is None]


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION
# ============================================================================

def map_materials(elements: List[Dict], ifc_file: object, schema: str) \
    -> Tuple[List[Dict], Dict]:
    """
    Convenience function to map materials in one call
    
    Usage:
        from material_mapper import map_materials
        
        materials, stats = map_materials(elements, ifc_file, "IFC2X3")
        
    Args:
        elements: List of element dicts from Phase 3
        ifc_file: ifcopenshell file object
        schema: IFC schema string
        
    Returns:
        Tuple of (materials_list, statistics_dict)
    """
    mapper = MaterialMapper(ifc_file, schema)
    materials = mapper.map(elements)
    stats = mapper.get_statistics()
    return materials, stats
