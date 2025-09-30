"""Vercel Serverless Function entry point"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import asyncio
from src.__main__ import create_app

# Initialize the app once
_app = None

def get_or_create_app():
    global _app
    if _app is None:
        _app = asyncio.run(create_app())
    return _app

# Export the ASGI app for Vercel
app = get_or_create_app()