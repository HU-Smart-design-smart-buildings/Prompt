"""
Logging and error handling utilities for the IFC Material Extractor application.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================
class IFCExtractorException(Exception):
    """Base exception for IFC Extractor"""
    pass


class IFCReadError(IFCExtractorException):
    """Error reading or parsing IFC file"""
    pass


class MaterialExtractionError(IFCExtractorException):
    """Error extracting material information"""
    pass


class ExportError(IFCExtractorException):
    """Error exporting data"""
    pass


class ValidationError(IFCExtractorException):
    """Error validating data"""
    pass


# ============================================================================
# LOGGER FACTORY
# ============================================================================
class LoggerFactory:
    """Factory for creating consistent loggers across application"""
    
    _loggers = {}
    _initialized = False
    _log_dir = None
    _console_handler = None
    _file_handler = None
    
    @classmethod
    def initialize(cls, log_dir: Path, log_level: str = "INFO", 
                   to_console: bool = True, to_file: bool = True):
        """
        Initialize logging system
        
        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            to_console: Whether to log to console
            to_file: Whether to log to file
        """
        cls._log_dir = log_dir
        log_dir.mkdir(exist_ok=True)
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        if to_console:
            cls._console_handler = logging.StreamHandler(sys.stdout)
            cls._console_handler.setLevel(getattr(logging, log_level))
            cls._console_handler.setFormatter(formatter)
        
        # File handler with daily rotation
        if to_file:
            log_file = log_dir / f"logs_{datetime.now().strftime('%Y-%m-%d')}.log"
            cls._file_handler = logging.FileHandler(log_file, encoding='utf-8')
            cls._file_handler.setLevel(getattr(logging, log_level))
            cls._file_handler.setFormatter(formatter)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get or create a logger with the given name
        
        Args:
            name: Logger name (typically __name__)
            
        Returns:
            Configured logger instance
        """
        if not cls._initialized:
            raise RuntimeError("LoggerFactory not initialized. Call initialize() first.")
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)  # Capture all, handlers filter
            
            # Remove existing handlers
            logger.handlers.clear()
            
            # Add handlers
            if cls._console_handler:
                logger.addHandler(cls._console_handler)
            if cls._file_handler:
                logger.addHandler(cls._file_handler)
            
            cls._loggers[name] = logger
        
        return cls._loggers[name]


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================
def get_logger(name: str) -> logging.Logger:
    """
    Get logger for a module
    
    Usage:
        from logger import get_logger
        logger = get_logger(__name__)
        logger.info("Processing element")
    """
    return LoggerFactory.get_logger(name)


def initialize_logging(log_dir: Path, log_level: str = "INFO",
                       to_console: bool = True, to_file: bool = True):
    """
    Initialize the logging system
    
    Usage:
        from pathlib import Path
        from logger import initialize_logging
        
        initialize_logging(Path("logs"))
    """
    LoggerFactory.initialize(log_dir, log_level, to_console, to_file)

