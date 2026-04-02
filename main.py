#!/usr/bin/env python
"""
IFC Material Extractor - Main Entry Point

This is the main entry point script. The actual application code is in src/
"""

import sys
from pathlib import Path

# Add src directory to path so imports work
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

# Now we can import from src
from main import main

if __name__ == "__main__":
    main()
