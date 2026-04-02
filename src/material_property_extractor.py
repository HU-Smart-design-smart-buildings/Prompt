"""
Material Property Extractor - Fase 6 Implementation

Extracts detailed material properties from material records produced in Phase 5.
"""

from typing import Any, Dict, List, Optional
from collections import defaultdict

from logger import get_logger
from config import KEY_MATERIAL_PROPERTIES


# ============================================================================
# MATERIAL PROPERTY EXTRACTOR CLASS
# ============================================================================


class MaterialPropertyExtractor:
    """Extracts material properties from IFC material objects."""

    def __init__(self, schema: str):
        self.logger = get_logger(__name__)
        self.schema = schema
        self.material_records: List[Dict] = []
        self.statistics: Dict = {}

    def extract(self, material_types: List[Dict]) -> List[Dict]:
        """Extract material properties for each material record."""
        self.logger.info('=' * 70)
        self.logger.info('FASE 6: Extracting Material Properties')
        self.logger.info('=' * 70)

        self.material_records = []
        errors = 0

        for material_type in material_types:
            try:
                record = self._extract_single_material_record(material_type)
                if record is not None:
                    self.material_records.append(record)
            except Exception as e:
                errors += 1
                if errors <= 5:
                    self.logger.warning(
                        'Error extracting material properties for element %s: %s',
                        material_type.get('element_global_id'),
                        str(e)
                    )

        if errors > 5:
            self.logger.warning('... and %s more errors', errors - 5)

        self.statistics = self._generate_statistics()
        self._log_results()
        return self.material_records

    def _extract_single_material_record(self, material_type: Dict) -> Optional[Dict]:
        """Create a material record enriched with material property values."""
        material_obj = material_type.get('material_object')
        if material_obj is None:
            return self._build_material_record(material_type, {}, {}, [])

        property_sets, normalized_properties = self._extract_properties(material_obj)

        return self._build_material_record(
            material_type,
            normalized_properties,
            property_sets,
            self._extract_material_meta(material_obj)
        )

    def _extract_properties(self, material_obj: object) -> (Dict[str, Any], Dict[str, Any]):
        """Extract property sets and key material properties from the material object."""
        properties: Dict[str, Any] = {}
        property_sets: Dict[str, Dict[str, Any]] = {}

        if not hasattr(material_obj, 'HasProperties'):
            return property_sets, properties

        for prop in getattr(material_obj, 'HasProperties') or []:
            try:
                if prop.is_a('IfcPropertySet'):
                    pset_name = getattr(prop, 'Name', 'UnnamedPropertySet')
                    property_sets[pset_name] = self._extract_property_set(prop)
                    for prop_name, prop_value in property_sets[pset_name].items():
                        if prop_name in KEY_MATERIAL_PROPERTIES:
                            properties[prop_name] = prop_value
                elif prop.is_a('IfcPropertySingleValue'):
                    normalized = self._normalize_property_value(prop)
                    if normalized is not None:
                        properties[getattr(prop, 'Name', 'Unknown')] = normalized
            except Exception:
                continue

        return property_sets, properties

    def _extract_property_set(self, prop_set: object) -> Dict[str, Any]:
        """Extract all properties inside a single IfcPropertySet."""
        extracted: Dict[str, Any] = {}

        for prop in getattr(prop_set, 'HasProperties') or []:
            try:
                prop_name = getattr(prop, 'Name', None)
                if not prop_name:
                    continue

                prop_value = self._normalize_property_value(prop)
                extracted[prop_name] = prop_value
            except Exception:
                extracted[prop_name] = None

        return extracted

    def _normalize_property_value(self, prop: object) -> Any:
        """Normalize common IFC property types to raw Python values."""
        if prop.is_a('IfcPropertySingleValue'):
            nominal = getattr(prop, 'NominalValue', None)
            return self._unwrap_value(nominal)

        if prop.is_a('IfcPropertyEnumeratedValue'):
            values = getattr(prop, 'EnumerationValues', None)
            if not values:
                return None
            return [self._unwrap_value(v) for v in values]

        if prop.is_a('IfcPropertyBoundedValue'):
            lower = getattr(prop, 'LowerBoundValue', None)
            upper = getattr(prop, 'UpperBoundValue', None)
            return {
                'min': self._unwrap_value(lower),
                'max': self._unwrap_value(upper)
            }

        return None

    def _unwrap_value(self, value_obj: Optional[object]) -> Any:
        if value_obj is None:
            return None
        if hasattr(value_obj, 'wrappedValue'):
            return getattr(value_obj, 'wrappedValue')
        return value_obj

    def _extract_material_meta(self, material_obj: object) -> Dict[str, Any]:
        """Extract description and metadata from a material object."""
        return {
            'description': getattr(material_obj, 'Description', None),
            'long_name': getattr(material_obj, 'LongName', None)
        }

    def _build_material_record(
            self,
            material_type: Dict,
            normalized_properties: Dict[str, Any],
            property_sets: Dict[str, Any],
            material_meta: Dict[str, Any]
    ) -> Dict:
        return {
            'element_global_id': material_type.get('element_global_id'),
            'element_name': material_type.get('element_name'),
            'element_type': material_type.get('element_type'),
            'schema': material_type.get('schema'),
            'material_raw_type': material_type.get('material_raw_type'),
            'material_type': material_type.get('material_type'),
            'material_name': material_type.get('material_name'),
            'material_id': material_type.get('material_id'),
            'material_properties': normalized_properties,
            'property_sets': property_sets,
            'material_description': material_meta.get('description') or material_type.get('material_name'),
            'material_object': material_type.get('material_object'),
        }

    def _generate_statistics(self) -> Dict[str, Any]:
        stats = defaultdict(int)
        property_set_count = 0
        key_property_count = 0
        missing_materials = 0

        for record in self.material_records:
            if not record.get('material_object'):
                missing_materials += 1
                continue

            if record.get('material_properties'):
                key_property_count += 1

            property_set_count += len(record.get('property_sets', {}))
            stats[record.get('material_type') or 'Unknown'] += 1

        return {
            'total_material_records': len(self.material_records),
            'missing_material_objects': missing_materials,
            'records_with_key_properties': key_property_count,
            'property_set_count': property_set_count,
            'material_type_distribution': dict(sorted(stats.items(), key=lambda x: x[1], reverse=True)),
            'schema': self.schema,
        }

    def _log_results(self):
        self.logger.info('-' * 70)
        self.logger.info('MATERIAL PROPERTY EXTRACTION SUMMARY:')
        self.logger.info('  Total material records: %s', self.statistics.get('total_material_records'))
        self.logger.info('  Missing material objects: %s', self.statistics.get('missing_material_objects'))
        self.logger.info('  Records with key properties: %s', self.statistics.get('records_with_key_properties'))
        self.logger.info('  Property sets found: %s', self.statistics.get('property_set_count'))
        self.logger.info('  Material type distribution:')
        for material_type, count in list(self.statistics.get('material_type_distribution', {}).items())[:10]:
            self.logger.info('    - %s: %s', material_type, count)
        self.logger.info('-' * 70)

    def get_material_records(self) -> List[Dict]:
        return self.material_records

    def get_statistics(self) -> Dict[str, Any]:
        return self.statistics


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION
# ============================================================================


def extract_material_properties(material_types: List[Dict], schema: str) -> (List[Dict], Dict):
    extractor = MaterialPropertyExtractor(schema)
    records = extractor.extract(material_types)
    return records, extractor.get_statistics()
