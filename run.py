#!/usr/bin/env python3
"""
Simple runner for TFT Comp Analyzer
This avoids module import issues by running directly
"""
import sys
from pathlib import Path
import asyncio

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run
from src.tft_analyzer.main import main

if __name__ == "__main__":
    print("🎮 TFT Set 15 Composition Analyzer")
    print("=" * 40)
    asyncio.run(main())