#!/usr/bin/env python3
"""
FastAPI Backend for TFT Composition Analyzer

Modern REST API providing access to TFT strategic analysis, meta data,
and AI-powered recommendations.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
from pathlib import Path
import os

# Add project root to Python path to access existing modules
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import Settings
    # Try to initialize settings, but handle missing API keys gracefully
    settings = Settings()
except Exception as e:
    print(f"Warning: Could not load settings: {e}")
    print("API will run with limited functionality")
    settings = None

# Import routers
from .routers import chat, meta, database, ml

# Initialize FastAPI app
app = FastAPI(
    title="TFT Composition Analyzer API",
    description="AI-powered strategic analysis API for Teamfight Tactics Set 15: K.O. Coliseum",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",  # Next.js often uses 3001
        "http://127.0.0.1:3001"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with simpler paths for frontend
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(meta.router, prefix="/api/meta", tags=["meta"])
app.include_router(database.router, prefix="/api/database", tags=["database"])
app.include_router(ml.router, prefix="/api/ml", tags=["ml"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "TFT Composition Analyzer API",
        "version": "0.3.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Quick validation of core components
        from src.tft_analyzer.data.meta_data_manager import TFTMetaDataManager
        from src.tft_analyzer.data.riot_official_units_with_traits import riot_official_db_with_traits

        data_manager = TFTMetaDataManager()
        meta_info = data_manager.get_meta_info()
        compositions_df = data_manager.get_compositions_df()

        return {
            "status": "healthy",
            "timestamp": meta_info.get("last_updated", "unknown"),
            "champions": len(riot_official_db_with_traits.unit_names),
            "traits": len(riot_official_db_with_traits.get_trait_distribution()),
            "compositions": len(compositions_df) if not compositions_df.is_empty() else 0,
            "api_keys": {
                "anthropic": bool(settings.anthropic_api_key),
                "openai": bool(settings.openai_api_key),
                "riot": bool(settings.riot_api_key)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )