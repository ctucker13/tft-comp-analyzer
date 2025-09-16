#!/usr/bin/env python3
"""
FastAPI Server Runner

Run the TFT Composition Analyzer FastAPI backend server.
"""

import uvicorn
import os
from pathlib import Path

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

if __name__ == "__main__":
    print("🚀 Starting TFT Composition Analyzer FastAPI Backend...")
    print("📍 API Documentation will be available at: http://127.0.0.1:8000/docs")
    print("🔄 Auto-reload enabled for development")
    print()

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )