from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import logging
import sys
import os

# Set up logging with more verbose output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Export BASE_DIR as a global variable for other modules to use
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"
frontend_dir = BASE_DIR / "frontend"  # Updated: Direct frontend directory

# Log important directories
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"APP_DIR: {APP_DIR}")
logger.info(f"frontend_dir: {frontend_dir}")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define static directories
app_static_dir = APP_DIR / "static"
logger.info(f"app_static_dir: {app_static_dir}")

# Create app static directory if it doesn't exist
if not app_static_dir.exists():
    logger.info(f"Creating app_static_dir: {app_static_dir}")
    app_static_dir.mkdir(parents=True, exist_ok=True)

# Mount static files directory from app folder if it exists
if app_static_dir.exists():
    logger.info(f"Mounting /static to {app_static_dir}")
    app.mount("/static", StaticFiles(directory=str(app_static_dir)), name="static")
else:
    logger.warning(f"Static directory not found: {app_static_dir}")

# Check for frontend assets directory
assets_dir = frontend_dir / "assets"
if assets_dir.exists():
    logger.info(f"Mounting /assets to {assets_dir}")
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
else:
    logger.warning(f"Assets directory not found: {assets_dir}")
    # Log available files in frontend dir for debugging
    if frontend_dir.exists():
        logger.info(f"Frontend directory exists. Available files: {list(frontend_dir.glob('*'))}")

# Add API routes
try:
    # Add the project root to Python path
    sys.path.append(str(BASE_DIR))
    
    # Make BASE_DIR available in other modules
    os.environ["BASE_DIR"] = str(BASE_DIR)
    
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

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request path: {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response

# Root route - serve index.html
@app.get("/")
async def root():
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        logger.info(f"Serving root index.html from {index_path}")
        return FileResponse(str(index_path))
    else:
        logger.error(f"Frontend index.html not found at {index_path}")
        return {"message": "Frontend index.html not found"}

# Serve static files directly from frontend directory
@app.get("/src/{file_path:path}")
async def serve_frontend_src(file_path: str):
    file_full_path = frontend_dir / "src" / file_path
    if file_full_path.exists() and file_full_path.is_file():
        return FileResponse(str(file_full_path))
    raise HTTPException(status_code=404, detail="File not found")

# Universal catch-all route for SPA
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Skip API routes and certain static file patterns
    if full_path.startswith(("api/", "assets/", "static/")):
        logger.info(f"Skipping SPA handler for API/asset path: {full_path}")
        raise HTTPException(status_code=404, detail="Not found")
    
    # First check if this is a direct file in the frontend directory
    direct_path = frontend_dir / full_path
    if direct_path.exists() and direct_path.is_file():
        logger.info(f"Serving direct file: {direct_path}")
        return FileResponse(str(direct_path))
    
    # For all other routes, serve index.html to enable client-side routing
    logger.info(f"Serving SPA for route: {full_path}")
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        logger.info(f"Serving index.html from {index_path}")
        return FileResponse(str(index_path))
    else:
        logger.error(f"Frontend index.html not found at {index_path}")
        raise HTTPException(status_code=404, detail="Frontend index.html not found")

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
