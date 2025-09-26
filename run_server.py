#!/usr/bin/env python3
"""
Simple script to run the FastAPI application.
Usage: uv run python run_server.py
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "__init__:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
