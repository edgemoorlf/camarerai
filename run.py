#!/usr/bin/env python3
"""
Entry point for CamareraI
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run
from camarerai import main
