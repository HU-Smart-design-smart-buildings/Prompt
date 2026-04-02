"""
Quantity Extractor - Fase 7 Implementation

Extracts metric quantities from IFC elements and normalizes them for aggregation.
"""

from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict

from logger import get_logger
from config import QUANTITY_TYPE_UNITS


# ============================================================================
# QUANTITY EXTRACTOR CLASS
# ============================================================================


class QuantityExtractor:
    """Extracts IFC Element quantity definitions into normalized records."""

    def __init__(self, schema: str):
        self.logger = get_logger(__name__)
        self.schema = schema
        self.quantity_records: List[Dict[str, Any]] = []
        self.statistics: Dict[str, Any] = {}

    def extract(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract quantities from all provided elements."""
        self.logger.info('=' * 70)
        self.logger.info('FASE 7: Extracting Quantities')
        self.logger.info('=' * 70)

        self.quantity_records = []
        errors = 0

        for element in elements:
            try:
                records = self._extract_element_quantities(element)
                self.quantity_records.extend(records)
            except Exception as e:
                errors += 1
                if errors <= 5:
                    self.logger.warning(
                        'Error extracting quantities for element %s: %s',
                        element.get('global_id'),
                        str(e)
                    )

        if errors > 5:
            self.logger.warning('... and %s more errors', errors - 5)

        self.statistics = self._generate_statistics()
        self._log_results()
        return self.quantity_records

    def _extract_element_quantities(self, element: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all quantity records for a single element."""
        elem_obj = element.get('object')
        if elem_obj is None:
            return []

        if not hasattr(elem_obj, 'IsDefinedBy') or not elem_obj.IsDefinedBy:
            return []

        records: List[Dict[str, Any]] = []
        for rel in getattr(elem_obj, 'IsDefinedBy') or []:
            if not hasattr(rel, 'is_a'):
                continue
            try:
                if rel.is_a('IfcRelDefinesByProperties'):
                    prop_def = getattr(rel, 'RelatingPropertyDefinition', None)
                    if prop_def is not None and getattr(prop_def, 'is_a', lambda x: False)('IfcElementQuantity'):
                        records.extend(self._extract_quantity_set(element, prop_def))
            except Exception:
                continue

        return records

    def _extract_quantity_set(self, element: Dict[str, Any], prop_def: object) -> List[Dict[str, Any]]:
        """Extract all quantities from a single IFC element quantity set."""
        quantity_set_name = getattr(prop_def, 'Name', None) or 'UnnamedQuantitySet'
        records: List[Dict[str, Any]] = []

        for qty in getattr(prop_def, 'Quantities') or []:
            normalized = self._normalize_quantity(qty)
            if normalized is None:
                continue

            records.append({
                'element_global_id': element.get('global_id'),
                'element_name': element.get('name'),
                'element_type': element.get('type'),
                'schema': element.get('schema'),
                'quantity_set_name': quantity_set_name,
                'quantity_name': normalized['quantity_name'],
                'quantity_type': normalized['quantity_type'],
                'quantity_value': normalized['quantity_value'],
                'quantity_unit': normalized['quantity_unit'],
                'quantity_description': normalized.get('quantity_description'),
                'quantity_object': qty,
            })

        return records

    def _normalize_quantity(self, qty_obj: object) -> Optional[Dict[str, Any]]:
        """Normalize a single IFC quantity object."""
        if qty_obj is None or not hasattr(qty_obj, 'is_a'):
            return None

        try:
            quantity_type = qty_obj.is_a()
        except Exception:
            quantity_type = None

        quantity_name = getattr(qty_obj, 'Name', None)
        if not quantity_name:
            quantity_name = getattr(qty_obj, 'ElementName', None)

        quantity_value = self._unwrap_value(getattr(qty_obj, 'wrappedValue', None))
        if quantity_value is None and hasattr(qty_obj, 'Value'):
            quantity_value = self._unwrap_value(getattr(qty_obj, 'Value', None))

        quantity_unit = self._get_quantity_unit(quantity_type)
        quantity_description = getattr(qty_obj, 'Description', None)

        return {
            'quantity_type': quantity_type,
            'quantity_name': quantity_name,
            'quantity_value': quantity_value,
            'quantity_unit': quantity_unit,
            'quantity_description': quantity_description,
        }

    def _unwrap_value(self, value_obj: Optional[object]) -> Any:
        if value_obj is None:
            return None

        if hasattr(value_obj, 'wrappedValue'):
            return getattr(value_obj, 'wrappedValue')

        return value_obj

    def _get_quantity_unit(self, quantity_type: Optional[str]) -> Optional[str]:
        if quantity_type is None:
            return None
        return QUANTITY_TYPE_UNITS.get(quantity_type)

    def _generate_statistics(self) -> Dict[str, Any]:
        elements_with_quantities = set()
        quantity_type_distribution = defaultdict(int)
        quantity_set_distribution = defaultdict(int)

        for record in self.quantity_records:
            elements_with_quantities.add(record.get('element_global_id'))
            quantity_type_distribution[record.get('quantity_type') or 'Unknown'] += 1
            quantity_set_distribution[record.get('quantity_set_name') or 'Unknown'] += 1

        return {
            'total_quantity_records': len(self.quantity_records),
            'elements_with_quantities': len(elements_with_quantities),
            'quantity_type_distribution': dict(sorted(quantity_type_distribution.items(), key=lambda x: x[1], reverse=True)),
            'quantity_set_distribution': dict(sorted(quantity_set_distribution.items(), key=lambda x: x[1], reverse=True)),
            'schema': self.schema,
        }

    def _log_results(self):
        self.logger.info('-' * 70)
        self.logger.info('QUANTITY EXTRACTION SUMMARY:')
        self.logger.info('  Total quantity records: %s', self.statistics.get('total_quantity_records'))
        self.logger.info('  Elements with quantities: %s', self.statistics.get('elements_with_quantities'))
        self.logger.info('  Quantity type distribution:')
        for quantity_type, count in list(self.statistics.get('quantity_type_distribution', {}).items())[:10]:
            self.logger.info('    - %s: %s', quantity_type, count)
        self.logger.info('  Quantity set distribution:')
        for quantity_set, count in list(self.statistics.get('quantity_set_distribution', {}).items())[:10]:
            self.logger.info('    - %s: %s', quantity_set, count)
        self.logger.info('-' * 70)

    def get_quantity_records(self) -> List[Dict[str, Any]]:
        return self.quantity_records

    def get_statistics(self) -> Dict[str, Any]:
        return self.statistics


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTION
# ============================================================================


def extract_quantities(elements: List[Dict[str, Any]], schema: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    extractor = QuantityExtractor(schema)
    records = extractor.extract(elements)
    return records, extractor.get_statistics()
