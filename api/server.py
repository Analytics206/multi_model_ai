"""
FastAPI server setup for the Multi-Model AI API Integration System.
This module creates and configures the FastAPI application.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pathlib import Path
import time

from config import get_settings
from utils.logger import logger

# Path to templates directory
TEMPLATES_DIR = Path("templates")

def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application
    """
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.app_name,
        description="A system to facilitate API calls to multiple AI model providers",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.app_env == "development" else ["http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Setup templates if directory exists
    templates = None
    if TEMPLATES_DIR.exists():
        templates = Jinja2Templates(directory=TEMPLATES_DIR)
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log request details
        logger.info(
            f"{request.method} {request.url.path} "
            f"[{response.status_code}] "
            f"{process_time:.4f}s"
        )
        
        return response
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
    
    # Root endpoint for HTML interface
    @app.get("/")
    async def root(request: Request):
        if templates:
            return templates.TemplateResponse("index.html", {"request": request})
        else:
            return {"message": "Multi-Model AI API Integration System", "docs": "/api/docs"}
    
    # Health check endpoint
    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
            "environment": settings.app_env,
            "version": "0.1.0"
        }
    
    # Import and include API routes
    # Note: These imports are placed here to avoid circular imports
    # Will be implemented in future prompts
    """
    from api.routes.models import router as models_router
    from api.routes.prompts import router as prompts_router
    from api.routes.providers import router as providers_router
    
    app.include_router(models_router, prefix="/api/models", tags=["Models"])
    app.include_router(prompts_router, prefix="/api/prompts", tags=["Prompts"])
    app.include_router(providers_router, prefix="/api/providers", tags=["Providers"])
    """
    
    logger.info(f"FastAPI application created in {settings.app_env} environment")
    return app