from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from pathlib import Path
import logging
import shutil
import sys
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get base directory and app directory
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"

# Define static directories within app folder
app_static_dir = APP_DIR / "static"
app_icon_dir = app_static_dir / "icon"
app_school_icon_dir = app_static_dir / "school_icon"

# Mount static files directory directly from app folder
app.mount("/static", StaticFiles(directory=str(app_static_dir)), name="static")

# Mount the frontend dist directory
frontend_dir = BASE_DIR / "frontend" / "src"
app.mount("/assets", StaticFiles(directory=str(frontend_dir / "assets")), name="assets")

# Configure CORS for both development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ontrack-v2-1.onrender.com",  # Production frontend URL
        "http://localhost:5173",              # Development frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add root route
@app.get("/")
async def root():
    # For API root requests
    if "accept" in app.state.request_headers and "application/json" in app.state.request_headers["accept"]:
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
    # For frontend requests, serve the index.html
    return FileResponse(str(frontend_dir / "index.html"))

# Health check endpoint
@app.get("/health")
async def health_check():
    try:
        return {
            "status": "healthy",
            "static_directories": {
                "app_static": str(app_static_dir),
                "icon": str(app_icon_dir),
                "school_icon": str(app_school_icon_dir)
            },
            "directories_exist": {
                "app_static": app_static_dir.exists(),
                "icon": app_icon_dir.exists(),
                "school_icon": app_school_icon_dir.exists()
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Check static files endpoint
@app.get("/check-static")
async def check_static():
    return {
        "icon_dir_exists": app_icon_dir.exists(),
        "school_icon_dir_exists": app_school_icon_dir.exists(),
        "icon_files": [str(f.name) for f in app_icon_dir.glob("*") if f.is_file()],
        "school_icon_files": [str(f.name) for f in app_school_icon_dir.glob("*") if f.is_file()],
        "icon_dir_path": str(app_icon_dir),
        "school_icon_dir_path": str(app_school_icon_dir)
    }

# Direct icon handling routes
@app.get("/api/survey/icon/{icon_id}")
async def get_icon(icon_id: str):
    try:
        # Clean the icon_id
        clean_id = icon_id.replace('icon_', '').strip()
        logger.info(f"Looking for icon with ID: {clean_id}")
        logger.info(f"Searching in directory: {app_icon_dir}")
        
        # List all files in the directory for debugging
        logger.info(f"Available files in icon directory: {list(app_icon_dir.glob('*'))}")
        
        # Try different extensions
        for ext in ['.png', '.jpg', '.jpeg']:
            icon_path = app_icon_dir / f"{clean_id}{ext}"
            logger.info(f"Trying path: {icon_path}")
            if icon_path.exists():
                logger.info(f"Found icon at: {icon_path}")
                return FileResponse(
                    path=str(icon_path),
                    media_type=f"image/{ext.replace('.', '')}"
                )
        
        # If no icon found, try default
        default_icon = app_icon_dir / "default-icon.png"
        if default_icon.exists():
            logger.info("Using default icon")
            return FileResponse(
                path=str(default_icon),
                media_type="image/png"
            )
        
        logger.error(f"No icon found for ID {clean_id}")
        raise HTTPException(status_code=404, detail="Icon not found")
    except Exception as e:
        logger.error(f"Error serving icon {icon_id}: {str(e)}")
        raise HTTPException(status_code=404, detail="Icon not found")

@app.get("/api/survey/school-icon/{school}")
async def get_school_icon(school: str):
    try:
        # Clean the school name
        clean_school = school.lower().strip()
        logger.info(f"Looking for school icon: {clean_school}")
        logger.info(f"Searching in directory: {app_school_icon_dir}")
        
        # List all files in the directory for debugging
        logger.info(f"Available files in school_icon directory: {list(app_school_icon_dir.glob('*'))}")
        
        # Try with different possible filenames
        possible_names = [
            f"{clean_school}.png",
            f"{clean_school.replace(' ', '-')}.png",
            f"{clean_school.replace(' ', '_')}.png"
        ]
        
        for filename in possible_names:
            school_path = app_school_icon_dir / filename
            logger.info(f"Trying path: {school_path}")
            if school_path.exists():
                logger.info(f"Found school icon at: {school_path}")
                return FileResponse(
                    path=str(school_path),
                    media_type="image/png"
                )
        
        # If no school icon found, try default
        default_school = app_school_icon_dir / "default-school.png"
        if default_school.exists():
            logger.info("Using default school icon")
            return FileResponse(
                path=str(default_school),
                media_type="image/png"
            )
        
        logger.error(f"No school icon found for {school}")
        raise HTTPException(status_code=404, detail="School icon not found")
    except Exception as e:
        logger.error(f"Error serving school icon {school}: {str(e)}")
        raise HTTPException(status_code=404, detail="School icon not found")

# Catch-all route for the SPA - must be defined AFTER API routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Skip for API routes and static asset routes
    if full_path.startswith("api/") or full_path.startswith("static/") or full_path.startswith("assets/"):
        raise HTTPException(status_code=404, detail="Not found")
    
    # Return the index.html file for all other routes
    logger.info(f"Serving frontend for path: {full_path}")
    return FileResponse(str(frontend_dir / "index.html"))

# Include routers
try:
    # Add the project root to Python path
    sys.path.append(str(BASE_DIR))
    
    from app.routers import survey
    app.include_router(
        survey.router,
        prefix="/api/survey",
        tags=["survey"]
    )
    logger.info("Successfully loaded survey router")
except Exception as e:
    logger.error(f"Failed to load survey router: {str(e)}")
    raise

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Disable reload in production
    )
