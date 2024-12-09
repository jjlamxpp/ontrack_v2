from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pathlib import Path
import shutil
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "app" / "static"
logger.info(f"Base directory: {BASE_DIR}")
logger.info(f"Static directory: {STATIC_DIR}")

app = FastAPI(
    title="OnTrack API",
    description="API for OnTrack Career Assessment Platform",
    version="2.0.0"
)

# Create necessary directories
try:
    icon_dir = STATIC_DIR / "icon"
    school_icon_dir = STATIC_DIR / "school_icon"

    # Create directories if they don't exist
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    icon_dir.mkdir(parents=True, exist_ok=True)
    school_icon_dir.mkdir(parents=True, exist_ok=True)

    # Mount static files directory
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
except Exception as e:
    logger.error(f"Error setting up static directories: {str(e)}")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://ontrack-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
try:
    # Add app directory to Python path
    app_path = os.path.join(BASE_DIR, "app")
    if app_path not in sys.path:
        sys.path.append(str(app_path))
    logger.info(f"Added to Python path: {app_path}")
    
    from app.routers import survey
    logger.info("Successfully imported survey router")
    
    app.include_router(
        survey.router,
        prefix="/api/survey",
        tags=["survey"]
    )
except Exception as e:
    logger.error(f"Error including routers: {str(e)}")
    logger.error(f"Current directory: {os.getcwd()}")
    logger.error(f"Python path: {sys.path}")
    import traceback
    logger.error(traceback.format_exc())

# Error handler for generic exceptions
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Generic error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "detail": str(exc)
        }
    )

# Add root route
@app.get("/")
async def root():
    """
    Root endpoint that provides API information and available endpoints
    """
    return {
        "message": "Welcome to OnTrack API",
        "version": "2.0",
        "status": "active",
        "endpoints": {
            "survey": "/api/survey/questions",
            "submit": "/api/survey/submit",
            "icons": "/api/survey/icon/{icon_id}",
            "school_icons": "/api/survey/school-icon/{school}"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify API status
    """
    return {
        "status": "healthy",
        "version": "2.0"
    }

# Error handling for 404 Not Found
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "message": "Resource not found",
            "detail": str(exc)
        }
    )

# Validation error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

# Development server configuration
if __name__ == "__main__":
    import uvicorn
    # Get port from environment variable or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    # Configure logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=True,  # Enable auto-reload during development
        workers=1  # Single worker for debugging
    )
