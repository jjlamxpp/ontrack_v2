from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from pathlib import Path
import logging
import shutil
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent

# Create and configure static directories
static_dir = BASE_DIR / "static"
icon_dir = static_dir / "icons"
school_icon_dir = static_dir / "school_logos"

# Create directories if they don't exist
for directory in [static_dir, icon_dir, school_icon_dir]:
    directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created/verified directory: {directory}")

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Configure CORS for deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ontrack-v2.onrender.com",  # Production frontend URL
        "http://localhost:5173",            # Development frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handler for static files
@app.exception_handler(404)
async def custom_404_handler(request, exc):
    if request.url.path.startswith("/api/survey/icon/"):
        logger.warning(f"Icon not found: {request.url.path}")
        return JSONResponse(
            status_code=404,
            content={"detail": "Icon not found"}
        )
    elif request.url.path.startswith("/api/survey/school-icon/"):
        logger.warning(f"School icon not found: {request.url.path}")
        return JSONResponse(
            status_code=404,
            content={"detail": "School icon not found"}
        )
    return JSONResponse(
        status_code=404,
        content={"detail": "Not found"}
    )

# Root route
@app.get("/")
async def root():
    return {
        "message": "Welcome to OnTrack API",
        "version": "2.0",
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
    try:
        # Check if static directories exist and are accessible
        static_dirs = {
            "static": static_dir,
            "icons": icon_dir,
            "school_logos": school_icon_dir
        }
        
        status = {
            "status": "healthy",
            "directories": {}
        }
        
        for name, path in static_dirs.items():
            status["directories"][name] = {
                "exists": path.exists(),
                "is_dir": path.is_dir() if path.exists() else False,
                "path": str(path)
            }
            
        return status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Include routers
from routers import survey
app.include_router(
    survey.router,
    prefix="/api/survey",
    tags=["survey"]
)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up FastAPI application")
    logger.info(f"Static directory: {static_dir}")
    logger.info(f"Icon directory: {icon_dir}")
    logger.info(f"School icon directory: {school_icon_dir}")
    
    # Verify static files
    try:
        # Check for default icons
        default_icon = icon_dir / "default-icon.png"
        default_school = school_icon_dir / "default-school.png"
        
        if not default_icon.exists():
            logger.warning("Default icon not found")
        if not default_school.exists():
            logger.warning("Default school icon not found")
            
        # Log available icons
        icons = list(icon_dir.glob("*.png"))
        school_icons = list(school_icon_dir.glob("*.png"))
        
        logger.info(f"Found {len(icons)} icons: {[i.name for i in icons]}")
        logger.info(f"Found {len(school_icons)} school icons: {[i.name for i in school_icons]}")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down FastAPI application")

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    # Configure uvicorn logging
    log_config = uvicorn.config.LOGGING_CONFIG
    log_config["formatters"]["access"]["fmt"] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_config=log_config,
        reload=False  # Disable reload in production
    )
