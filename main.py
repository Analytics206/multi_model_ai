#!/usr/bin/env python3
"""
Multi-Model AI API Integration System
Main application entry point that initializes and starts the API server.
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Internal imports
from utils.logger import setup_logging
from config import get_settings
from database.connection import init_db
from api.server import create_app

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging()

def main():
    """
    Main function to initialize and start the application
    """
    # Get application settings
    settings = get_settings()
    
    # Initialize the database
    logger.info("Initializing database...")
    init_db()
    
    # Create the FastAPI application
    logger.info("Creating FastAPI application...")
    app = create_app()
    
    # Mount static files
    if os.path.exists("static"):
        app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Start the server
    logger.info(f"Starting server on {settings.app_host}:{settings.app_port}")
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )
    
    return app

# This allows the application to be imported for testing or run directly
app = main() if __name__ == "__main__" else create_app()