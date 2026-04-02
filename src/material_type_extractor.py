"""
Material Type Extractor - Fase 5 Implementation

Determines explicit material types from the material mappings produced in Phase 4.
"""

from typing import List, Dict, Optional
from collections import defaultdict

from logger import get_logger
from config import MATERIAL_TYPES_BY_SCHEMA


# ============================================================================
# MATERIAL TYPE EXTRACTOR CLASS
# ============================================================================


class MaterialTypeExtractor:
    """Extracts detailed material type information from Phase 4 output."""

    def __init__(self, schema: str):
        self.logger = get_logger(__name__)
        self.schema = schema
        self.material_types: List[Dict] = []
        self.statistics: Dict = {}
        self.supported_types = MATERIAL_TYPES_BY_SCHEMA.get(schema, [])

    def extract(self, material_mappings: List[Dict]) -> List[Dict]:
        """Extract detailed material types for each material mapping."""
        self.logger.info('=' * 70)
        self.logger.info('FASE 5: Determining Material Types')
        self.logger.info('=' * 70)

        self.material_types = []
        errors = 0

        for mapping in material_mappings:
            try:
                material_type = self._extract_single_material(mapping)
                if material_type is not None:
                    self.material_types.append(material_type)
            except Exception as e:
                errors += 1
                if errors <= 5:
                    self.logger.warning(
                        'Error extracting material type for element %s: %s',
                        mapping.get('element_global_id'),
                        str(e)
                    )

        if errors > 5:
            self.logger.warning('... and %s more errors', errors - 5)

        self.statistics = self._generate_statistics()
        self._log_results()

        return self.material_types

    def _extract_single_material(self, mapping: Dict) -> Optional[Dict]:
        """Dispatch material extraction on raw IFC material type."""
        material_obj = mapping.get('material_object')
        material_raw_type = mapping.get('material_raw_type')

        if material_obj is None:
            return self._build_missing_material(mapping)

        if material_raw_type == 'IfcMaterial':
            return self._handle_ifc_material(material_obj, mapping)

        if material_raw_type == 'IfcMaterialList':
            return self._handle_ifc_material_list(material_obj, mapping)

        if material_raw_type == 'IfcMaterialLayerSet':
            return self._handle_ifc_material_layer_set(material_obj, mapping)

        if material_raw_type == 'IfcMaterialLayerSetUsage':
            return self._handle_ifc_material_layer_set_usage(material_obj, mapping)

        if material_raw_type == 'IfcMaterialProfileSet':
            return self._handle_ifc_material_profile_set(material_obj, mapping)

        if material_raw_type == 'IfcMaterialConstituentSet':
            return self._handle_ifc_material_constituent_set(material_obj, mapping)

        return self._build_unknown_material(mapping, material_raw_type)

    def _handle_ifc_material(self, material_obj: object, mapping: Dict) -> Dict:
        return self._build_material_record(
            mapping,
            material_type='IfcMaterial',
            material_name=self._safe_name(material_obj),
            material_id=self._safe_global_id(material_obj),
            material_details={
                'description': self._safe_description(material_obj)
            }
        )

    def _handle_ifc_material_list(self, material_obj: object, mapping: Dict) -> Dict:
        materials = []
        for index, item in enumerate(getattr(material_obj, 'Materials', []) or []):
            materials.append({
                'index': index,
                'material_name': self._safe_name(item),
                'material_id': self._safe_global_id(item),
                'material_raw_type': self._safe_raw_type(item),
            })

        return self._build_material_record(
            mapping,
            material_type='IfcMaterialList',
            material_name=self._safe_name(material_obj) or 'IfcMaterialList',
            material_id=self._safe_global_id(material_obj),
            material_details={
                'list_items': materials
            }
        )

    def _handle_ifc_material_layer_set(self, material_obj: object, mapping: Dict) -> Dict:
        layers = []
        for index, layer in enumerate(getattr(material_obj, 'MaterialLayers', []) or []):
            layers.append({
                'index': index,
                'layer_name': self._safe_name(getattr(layer, 'Material', None)),
                'material_id': self._safe_global_id(getattr(layer, 'Material', None)),
                'layer_thickness': getattr(layer, 'LayerThickness', None),
                'layer_type': self._safe_raw_type(layer),
            })

        return self._build_material_record(
            mapping,
            material_type='IfcMaterialLayerSet',
            material_name=self._safe_name(material_obj) or 'IfcMaterialLayerSet',
            material_details={
                'layers': layers
            }
        )

    def _handle_ifc_material_layer_set_usage(self, material_obj: object, mapping: Dict) -> Dict:
        layer_set = getattr(material_obj, 'ForLayerSet', None)
        layers = []

        if layer_set is not None:
            for index, layer in enumerate(getattr(layer_set, 'MaterialLayers', []) or []):
                layers.append({
                    'index': index,
                    'layer_name': self._safe_name(getattr(layer, 'Material', None)),
                    'material_id': self._safe_global_id(getattr(layer, 'Material', None)),
                    'layer_thickness': getattr(layer, 'LayerThickness', None),
                    'layer_type': self._safe_raw_type(layer),
                })

        return self._build_material_record(
            mapping,
            material_type='IfcMaterialLayerSetUsage',
            material_name=self._safe_name(material_obj) or 'IfcMaterialLayerSetUsage',
            material_details={
                'usage': {
                    'direction_sense': getattr(material_obj, 'DirectionSense', None),
                    'offset_from_reference_line': getattr(material_obj, 'OffsetFromReferenceLine', None)
                },
                'layers': layers
            }
        )

    def _handle_ifc_material_profile_set(self, material_obj: object, mapping: Dict) -> Dict:
        profiles = []
        for index, profile in enumerate(getattr(material_obj, 'MaterialProfiles', []) or []):
            profiles.append({
                'index': index,
                'profile_name': self._safe_name(getattr(profile, 'Material', None)),
                'material_id': self._safe_global_id(getattr(profile, 'Material', None)),
                'profile_reference': getattr(profile, 'Profile', None),
                'profile_type': getattr(profile, 'ProfileType', None),
            })

        return self._build_material_record(
            mapping,
            material_type='IfcMaterialProfileSet',
            material_name=self._safe_name(material_obj) or 'IfcMaterialProfileSet',
            material_details={
                'profiles': profiles
            }
        )

    def _handle_ifc_material_constituent_set(self, material_obj: object, mapping: Dict) -> Dict:
        constituents = []
        for index, constituent in enumerate(getattr(material_obj, 'MaterialConstituents', []) or []):
            constituents.append({
                'index': index,
                'material_name': self._safe_name(getattr(constituent, 'Material', None)),
                'material_id': self._safe_global_id(getattr(constituent, 'Material', None)),
                'fraction': getattr(constituent, 'Fraction', None),
                'physical_quantity': getattr(constituent, 'PhysicalQuantity', None)
            })

        return self._build_material_record(
            mapping,
            material_type='IfcMaterialConstituentSet',
            material_name=self._safe_name(material_obj) or 'IfcMaterialConstituentSet',
            material_details={
                'constituents': constituents
            }
        )

    def _build_missing_material(self, mapping: Dict) -> Dict:
        return self._build_material_record(
            mapping,
            material_type=None,
            material_name=None,
            material_id=None,
            material_details={}
        )

    def _build_unknown_material(self, mapping: Dict, material_raw_type: Optional[str]) -> Dict:
        return self._build_material_record(
            mapping,
            material_type=material_raw_type or 'Unknown',
            material_name=self._safe_name(mapping.get('material_object')),
            material_id=self._safe_global_id(mapping.get('material_object')),
            material_details={
                'unsupported_raw_type': material_raw_type
            }
        )

    def _build_material_record(
            self,
            mapping: Dict,
            material_type: Optional[str],
            material_name: Optional[str],
            material_id: Optional[str],
            material_details: Dict
    ) -> Dict:
        return {
            'element_global_id': mapping.get('element_global_id'),
            'element_name': mapping.get('element_name'),
            'element_type': mapping.get('element_type'),
            'schema': mapping.get('schema'),
            'material_raw_type': mapping.get('material_raw_type'),
            'material_type': material_type,
            'material_name': material_name,
            'material_id': material_id,
            'material_details': material_details,
            'material_object': mapping.get('material_object'),
        }

    def _safe_name(self, obj: Optional[object]) -> Optional[str]:
        if obj is None:
            return None
        if hasattr(obj, 'Name') and obj.Name:
            return obj.Name
        if hasattr(obj, 'LongName') and obj.LongName:
            return obj.LongName
        return None

    def _safe_description(self, obj: Optional[object]) -> Optional[str]:
        if obj is None:
            return None
        if hasattr(obj, 'Description') and obj.Description:
            return obj.Description
        return None

    def _safe_global_id(self, obj: Optional[object]) -> Optional[str]:
        if obj is None:
            return None
        if hasattr(obj, 'GlobalId') and obj.GlobalId:
            return obj.GlobalId
        return None

    def _safe_raw_type(self, obj: Optional[object]) -> Optional[str]:
        if obj is None:
            return None
        try:
            return obj.is_a()
        except Exception:
            return None

    def _generate_statistics(self) -> Dict:
        by_type = defaultdict(int)
        unsupported = defaultdict(int)
        with_material = 0
        without_material = 0

        for record in self.material_types:
            if record['material_type']:
                with_material += 1
                by_type[record['material_type']] += 1
                if record['material_raw_type'] not in self.supported_types:
                    unsupported[record['material_raw_type']] += 1
            else:
                without_material += 1

        return {
            'total_material_records': len(self.material_types),
            'elements_with_material': with_material,
            'elements_without_material': without_material,
            'material_type_distribution': dict(sorted(by_type.items(), key=lambda x: x[1], reverse=True)),
            'unsupported_material_types': dict(sorted(unsupported.items(), key=lambda x: x[1], reverse=True)),
            'schema': self.schema,
        }

    def _log_results(self):
        self.logger.info('-' * 70)
        self.logger.info('MATERIAL TYPE EXTRACTION SUMMARY:')
        self.logger.info('  Total material records: %s', self.statistics.get('total_material_records'))
        self.logger.info('  Elements with material: %s', self.statistics.get('elements_with_material'))
        self.logger.info('  Elements without material: %s', self.statistics.get('elements_without_material'))
        self.logger.info('  Material types:')

        for material_type, count in list(self.statistics.get('material_type_distribution', {}).items())[:10]:
            self.logger.info('    - %s: %s', material_type, count)

        if self.statistics.get('unsupported_material_types'):
            self.logger.info('  Unsupported material types:')
            for unsupported_type, count in list(self.statistics.get('unsupported_material_types', {}).items())[:10]:
                self.logger.info('    - %s: %s', unsupported_type, count)

        self.logger.info('-' * 70)

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_material_types(self) -> List[Dict]:
        return self.material_types

    def get_statistics(self) -> Dict:
        return self.statistics

    def count_by_type(self, material_type: str) -> int:
        return sum(1 for m in self.material_types if m['material_type'] == material_type)

    def filter_by_type(self, material_type: str) -> List[Dict]:
        return [m for m in self.material_types if m['material_type'] == material_type]


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION
# ============================================================================


def extract_material_types(material_mappings: List[Dict], schema: str) -> (List[Dict], Dict):
    extractor = MaterialTypeExtractor(schema)
    material_types = extractor.extract(material_mappings)
    return material_types, extractor.get_statistics()
