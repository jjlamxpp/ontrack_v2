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

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Load environment variables
load_dotenv()

app = FastAPI(
    title="OnTrack API",
    description="API for OnTrack Career Assessment Platform",
    version="2.0.0"
)

# Create necessary directories
try:
    static_dir = Path("static")
    icon_dir = static_dir / "icon"
    school_icon_dir = static_dir / "school_icon"

    # Create directories if they don't exist
    static_dir.mkdir(parents=True, exist_ok=True)
    icon_dir.mkdir(parents=True, exist_ok=True)
    school_icon_dir.mkdir(parents=True, exist_ok=True)

    # Mount static files directory
    app.mount("/static", StaticFiles(directory="static"), name="static")
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
    # Check if routers directory exists
    routers_path = os.path.join(current_dir, "routers")
    if not os.path.exists(routers_path):
        logger.error(f"Routers directory not found at: {routers_path}")
        raise ImportError("Routers directory not found")

    # Try to import the survey router
    from routers import survey
    logger.info("Successfully imported survey router")
    
    app.include_router(
        survey.router,
        prefix="/api/survey",
        tags=["survey"]
    )
except Exception as e:
    logger.error(f"Error including routers: {str(e)}")
    logger.error(f"Current directory: {current_dir}")
    logger.error(f"Python path: {sys.path}")
    import traceback
    logger.error(traceback.format_exc())

# Rest of your route handlers remain the same
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

@app.get("/")
async def root():
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

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0"
    }

@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "message": "Resource not found",
            "detail": str(exc)
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(levelname)s - %(message)s"
    
    uvicorn.run(
        app,  # Changed from "main:app" to app
        host="0.0.0.0",
        port=port,
        reload=True,
        log_config=log_config,
        workers=1  # Reduced workers for debugging
    )
