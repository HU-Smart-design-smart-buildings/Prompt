"""
Main orchestrator and entry point for the IFC Material Extractor application.
Coordinates the workflow across all modules and handles overall process execution.
"""

import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

from config import (
    PROJECT_ROOT, OUTPUT_DIR, LOGS_DIR,
    SUPPORTED_SCHEMAS, DEFAULT_EXPORT_FORMAT, EXPORT_FORMATS
)
from logger import get_logger, initialize_logging, IFCReadError


# ============================================================================
# MAIN APPLICATION CLASS
# ============================================================================
class IFCMaterialExtractor:
    """
    Main orchestrator for IFC material extraction workflow.
    
    Handles the complete pipeline from IFC file input to formatted export.
    """
    
    def __init__(self, input_file_path: str, output_dir: Optional[str] = None,
                 export_format: str = DEFAULT_EXPORT_FORMAT):
        """
        Initialize the IFC Material Extractor
        
        Args:
            input_file_path: Path to IFC file to process
            output_dir: Output directory for results (default: output/)
            export_format: Export format (csv, xlsx, json)
            
        Raises:
            FileNotFoundError: If input file doesn't exist
            ValueError: If export format is not supported
        """
        self.logger = get_logger(__name__)
        
        # Validate input file
        self.input_file = Path(input_file_path)
        if not self.input_file.exists():
            raise FileNotFoundError(f"IFC file not found: {self.input_file}")
        
        if self.input_file.suffix.lower() != '.ifc':
            self.logger.warning(f"File extension is {self.input_file.suffix}, expected .ifc")
        
        # Set output directory
        self.output_dir = Path(output_dir) if output_dir else OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate export format
        if export_format.lower() not in EXPORT_FORMATS:
            raise ValueError(f"Export format must be one of {EXPORT_FORMATS}")
        self.export_format = export_format.lower()
        
        # Initialize state
        self.ifc_file = None
        self.ifc_schema = None
        self.elements = []
        self.element_stats = {}
        self.materials = []
        self.aggregated_data = None
        self.extraction_time = None
        
        self.logger.info(f"Initialized extractor for {self.input_file.name}")
        self.logger.info(f"Export format: {self.export_format}")
        self.logger.info(f"Output directory: {self.output_dir}")
    
    def process(self) -> Dict:
        """
        Execute the complete extraction pipeline
        
        Phases:
        1. Load & detect schema (Fase 2)
        2. Extract elements (Fase 3)
        3. Extract materials (Fase 4-5-6)
        4. Extract quantities (Fase 7)
        5. Extract properties (Fase 8)
        6. Aggregate data (Fase 9)
        7. Export results (Fase 10)
        
        Returns:
            Dictionary with processing results and statistics
        """
        start_time = datetime.now()
        self.logger.info("="*70)
        self.logger.info("Starting IFC Material Extraction Pipeline")
        self.logger.info("="*70)
        
        try:
            # Fase 2: Load and detect schema
            self.logger.info("PHASE 2: Loading IFC file and detecting schema...")
            self._load_and_detect_schema()
            
            # Fase 3: Extract building elements
            self.logger.info("PHASE 3: Extracting building elements...")
            self._extract_elements()
            
            # Fase 4-6: Extract materials
            self.logger.info("PHASE 4-6: Extracting and mapping materials...")
            self._extract_materials()
            
            # Fase 7: Extract quantities
            self.logger.info("PHASE 7: Extracting quantities...")
            self._extract_quantities()
            
            # Fase 8: Extract properties
            self.logger.info("PHASE 8: Extracting properties...")
            self._extract_properties()
            
            # Fase 9: Aggregate data
            self.logger.info("PHASE 9: Aggregating material data...")
            self._aggregate_data()
            
            # Fase 10: Export
            self.logger.info("PHASE 10: Exporting results...")
            export_file = self._export_results()
            
            # Summary
            self.extraction_time = datetime.now() - start_time
            result = self._create_summary(export_file)
            
            self.logger.info("="*70)
            self.logger.info("Pipeline completed successfully!")
            self.logger.info(f"Processing time: {self.extraction_time.total_seconds():.2f} seconds")
            self.logger.info("="*70)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
            raise
    
    def _load_and_detect_schema(self):
        """Fase 2: Load IFC file and detect schema version"""
        from ifc_reader import load_ifc_file
        
        try:
            self.ifc_file, self.ifc_schema = load_ifc_file(str(self.input_file))
            
        except Exception as e:
            raise IFCReadError("Failed to load IFC file: {}".format(str(e)))
    
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
    
    def _extract_materials(self):
        """Fase 4-6: Extract and map materials from elements"""
        if not self.elements:
            self.logger.warning("No elements to extract materials from")
            return
        
        try:
            material_count = 0
            for elem_info in self.elements:
                elem = elem_info['object']
                if hasattr(elem, 'HasAssociations') and elem.HasAssociations:
                    for rel in elem.HasAssociations:
                        if rel.is_a("IfcRelAssociatesMaterial"):
                            material_count += 1
                            # Detailed extraction happens in Fase 9 aggregation
            
            self.logger.info(f"Found {material_count} material associations")
            
        except Exception as e:
            self.logger.warning(f"Error extracting materials: {str(e)}")
    
    def _extract_quantities(self):
        """Fase 7: Extract quantities (volumes, areas, etc.) from elements"""
        if not self.elements:
            self.logger.warning("No elements to extract quantities from")
            return
        
        try:
            qty_count = 0
            for elem_info in self.elements:
                elem = elem_info['object']
                if hasattr(elem, 'IsDefinedBy') and elem.IsDefinedBy:
                    for rel in elem.IsDefinedBy:
                        if rel.is_a("IfcRelDefinesByProperties"):
                            prop_def = rel.RelatingPropertyDefinition
                            if prop_def.is_a("IfcElementQuantity"):
                                qty_count += 1
            
            self.logger.info(f"Found {qty_count} quantity definitions")
            
        except Exception as e:
            self.logger.warning(f"Error extracting quantities: {str(e)}")
    
    def _extract_properties(self):
        """Fase 8: Extract properties from elements and materials"""
        if not self.elements:
            self.logger.warning("No elements to extract properties from")
            return
        
        try:
            pset_count = 0
            for elem_info in self.elements:
                elem = elem_info['object']
                if hasattr(elem, 'IsDefinedBy') and elem.IsDefinedBy:
                    for rel in elem.IsDefinedBy:
                        if rel.is_a("IfcRelDefinesByProperties"):
                            prop_def = rel.RelatingPropertyDefinition
                            if prop_def.is_a("IfcPropertySet"):
                                pset_count += 1
            
            self.logger.info(f"Found {pset_count} property sets")
            
        except Exception as e:
            self.logger.warning(f"Error extracting properties: {str(e)}")
    
    def _aggregate_data(self):
        """Fase 9: Aggregate and group material data"""
        # Placeholder for aggregation logic
        # Will be implemented in full phase implementations
        self.aggregated_data = {
            'elements_processed': len(self.elements),
            'schema': self.ifc_schema,
            'materials': []
        }
        self.logger.info(f"Aggregated data for {len(self.elements)} elements")
    
    def _export_results(self) -> Path:
        """Fase 10: Export results to specified format"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if self.export_format == 'csv':
                filename = self.output_dir / f"material_extraction_{timestamp}.csv"
            elif self.export_format == 'xlsx':
                filename = self.output_dir / f"material_extraction_{timestamp}.xlsx"
            elif self.export_format == 'json':
                filename = self.output_dir / f"material_extraction_{timestamp}.json"
            
            # Placeholder: actual export implementation in Fase 10
            filename.touch()  # Create empty file for now
            
            self.logger.info(f"Export file created: {filename}")
            return filename
            
        except Exception as e:
            raise Exception(f"Failed to export results: {str(e)}")
    
    def _create_summary(self, export_file: Path) -> Dict:
        """Create processing summary"""
        return {
            'status': 'success',
            'input_file': str(self.input_file),
            'ifc_schema': self.ifc_schema,
            'elements_processed': len(self.elements),
            'export_file': str(export_file),
            'export_format': self.export_format,
            'processing_time_seconds': self.extraction_time.total_seconds(),
            'timestamp': datetime.now().isoformat()
        }


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================
def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description='IFC Material Extractor - Extract material data from BIM models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py 23BIM.ifc
  python main.py 23BIM.ifc --output results/ --format xlsx
  python main.py 43BIM.ifc --format json --log-level DEBUG
        """
    )
    
    parser.add_argument('input_file',
                       help='Path to IFC file to process')
    
    parser.add_argument('--output', '-o',
                       default=None,
                       help='Output directory (default: output/)')
    
    parser.add_argument('--format', '-f',
                       choices=EXPORT_FORMATS,
                       default=DEFAULT_EXPORT_FORMAT,
                       help=f'Export format (default: {DEFAULT_EXPORT_FORMAT})')
    
    parser.add_argument('--log-level', '-l',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='Logging level (default: INFO)')
    
    args = parser.parse_args()
    
    # Initialize logging
    initialize_logging(LOGS_DIR, log_level=args.log_level)
    logger = get_logger(__name__)
    
    try:
        # Create and run extractor
        extractor = IFCMaterialExtractor(
            args.input_file,
            output_dir=args.output,
            export_format=args.format
        )
        
        result = extractor.process()
        
        # Print summary
        print("\n" + "="*70)
        print("EXTRACTION SUMMARY")
        print("="*70)
        print(f"Status: {result['status']}")
        print(f"Schema: {result['ifc_schema']}")
        print(f"Elements processed: {result['elements_processed']}")
        print(f"Export file: {result['export_file']}")
        print(f"Processing time: {result['processing_time_seconds']:.2f}s")
        print("="*70 + "\n")
        
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"\nERROR: {str(e)}\n")
        exit(1)


if __name__ == "__main__":
    main()

