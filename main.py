from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse
from pathlib import Path
import logging
import sys
import os
import shutil

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Get base directory
BASE_DIR = Path(__file__).resolve().parent

# Create necessary directories
static_dir = BASE_DIR / "static"
icon_dir = static_dir / "icons"  # Changed from "icon" to "icons" for consistency
school_icon_dir = static_dir / "school_logos"  # Changed from "school_icon" to "school_logos"

# Create directories if they don't exist
for directory in [static_dir, icon_dir, school_icon_dir]:
    directory.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created/verified directory: {directory}")

# Mount static files directory
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Configure CORS for both development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ontrack-v2-1.onrender.com",  # Production frontend URL
        "http://localhost:5173",            # Development frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add root route
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
        return {
            "status": "healthy",
            "static_directories": {
                "static": str(static_dir),
                "icons": str(icon_dir),
                "school_logos": str(school_icon_dir)
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/survey/icon/{icon_id}")
async def get_icon(icon_id: str):
    try:
        # Clean the icon_id
        clean_id = icon_id.replace('icon_', '').strip()
        logger.info(f"Looking for icon with ID: {clean_id}")
        logger.info(f"Searching in directory: {icon_dir}")
        
        # List all files in the directory for debugging
        logger.info(f"Available files in icon directory: {list(icon_dir.glob('*'))}")
        
        # Try different extensions
        for ext in ['.png', '.jpg', '.jpeg']:
            icon_path = icon_dir / f"{clean_id}{ext}"
            logger.info(f"Trying path: {icon_path}")
            if icon_path.exists():
                logger.info(f"Found icon at: {icon_path}")
                return FileResponse(
                    path=str(icon_path),
                    media_type=f"image/{ext.replace('.', '')}"
                )
        
        # If no icon found, try default
        default_icon = icon_dir / "default-icon.png"
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
        logger.info(f"Searching in directory: {school_icon_dir}")
        
        # List all files in the directory for debugging
        logger.info(f"Available files in school_icon directory: {list(school_icon_dir.glob('*'))}")
        
        # Try with different possible filenames
        possible_names = [
            f"{clean_school}.png",
            f"{clean_school.replace(' ', '-')}.png",
            f"{clean_school.replace(' ', '_')}.png"
        ]
        
        for filename in possible_names:
            school_path = school_icon_dir / filename
            logger.info(f"Trying path: {school_path}")
            if school_path.exists():
                logger.info(f"Found school icon at: {school_path}")
                return FileResponse(
                    path=str(school_path),
                    media_type="image/png"
                )
        
        # If no school icon found, try default
        default_school = school_icon_dir / "default-school.png"
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
# Include routers
try:
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
