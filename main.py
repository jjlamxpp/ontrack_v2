from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import logging
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
frontend_dir = BASE_DIR / "frontend" 

# Define static directories within app folder
app_static_dir = APP_DIR / "static"
app_icon_dir = app_static_dir / "icon"
app_school_icon_dir = app_static_dir / "school_icon"

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you might want to restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory from app folder
app.mount("/static", StaticFiles(directory=str(app_static_dir)), name="static")

# Only mount assets if the directory exists
assets_dir = frontend_dir / "assets"
if assets_dir.exists():
    logger.info(f"Mounting assets directory: {assets_dir}")
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
else:
    logger.warning(f"Assets directory not found at {assets_dir}")

# Add API routes
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

# Serve index.html for the root
@app.get("/")
async def root():
    if frontend_dir.exists() and (frontend_dir / "index.html").exists():
        return FileResponse(str(frontend_dir / "index.html"))
    else:
        logger.error(f"Frontend index.html not found at {frontend_dir / 'index.html'}")
        return {"message": "Frontend not built or not found"}

# Universal catch-all route for SPA - MUST be after all API routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Skip API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # For all frontend routes, serve the index.html file
    logger.info(f"Serving SPA for route: {full_path}")
    if frontend_dir.exists() and (frontend_dir / "index.html").exists():
        return FileResponse(str(frontend_dir / "index.html"))
    else:
        logger.error(f"Frontend index.html not found at {frontend_dir / 'index.html'}")
        raise HTTPException(status_code=404, detail="Frontend not built or not found")

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
