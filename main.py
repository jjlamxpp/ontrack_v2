from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import logging
import sys
import os
import traceback
import re

# Set up logging with more verbose output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Export BASE_DIR as a global variable for other modules to use
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"
frontend_dir = BASE_DIR / "frontend" / "src"

# Log important directories
logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"APP_DIR: {APP_DIR}")
logger.info(f"frontend_dir: {frontend_dir}")
logger.info(f"Frontend directory exists: {frontend_dir.exists()}")
if frontend_dir.exists():
    logger.info(f"Frontend directory contents: {list(frontend_dir.iterdir())}")

app = FastAPI()

# Add exception handlers for better error reporting
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )

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

# Check for frontend assets directory and mount it if it exists
assets_dir = frontend_dir / "assets"
if assets_dir.exists():
    logger.info(f"Mounting /assets to {assets_dir}")
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
else:
    logger.warning(f"Assets directory not found: {assets_dir}")
    if frontend_dir.exists():
        logger.info(f"Frontend directory contents: {list(frontend_dir.glob('*'))}")

# Add API routes - IMPORTANT: This must come BEFORE the catch-all route
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
    
    # Log all registered routes for debugging
    for route in app.routes:
        logger.info(f"Registered route: {route.path} ({route.name})")
        
except Exception as e:
    logger.error(f"Failed to load survey router: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# Add a more comprehensive API debug endpoint
@app.get("/api/debug")
async def api_debug():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": getattr(route, "methods", ["GET"])
        })
    
    return {
        "status": "API is working", 
        "routes": routes,
        "base_dir": str(BASE_DIR),
        "app_dir": str(APP_DIR)
    }

# Middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    path = request.url.path
    logger.info(f"Request path: {path}")
    
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code} for {path}")
        return response
    except Exception as e:
        logger.error(f"Error during request processing: {str(e)}")
        logger.error(traceback.format_exc())
        raise

# Root route - serve index.html
@app.get("/")
async def root():
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        logger.info(f"Serving root index.html from {index_path}")
        return FileResponse(str(index_path))
    else:
        logger.error(f"Frontend index.html not found at {index_path}")
        return JSONResponse(
            status_code=404,
            content={"detail": f"Frontend index.html not found at {index_path}"}
        )

# IMPORTANT: Define explicit routes for SPA paths that need refresh support
@app.get("/survey/{path_param:path}")
async def serve_survey_route(path_param: str):
    """Handle all survey routes by serving the index.html file"""
    logger.info(f"Survey route handler for: /survey/{path_param}")
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        logger.info(f"Serving index.html for survey route")
        return FileResponse(str(index_path))
    else:
        error_msg = f"Frontend index.html not found at {index_path}"
        logger.error(error_msg)
        return JSONResponse(status_code=404, content={"detail": error_msg})

@app.get("/result")
async def serve_result_route():
    """Handle the result route by serving the index.html file"""
    logger.info(f"Result route handler")
    index_path = frontend_dir / "index.html"
    if index_path.exists():
        logger.info(f"Serving index.html for result route")
        return FileResponse(str(index_path))
    else:
        error_msg = f"Frontend index.html not found at {index_path}"
        logger.error(error_msg)
        return JSONResponse(status_code=404, content={"detail": error_msg})

# Catch-all route should be LAST
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    # Skip API routes
    if full_path.startswith("api/"):
        logger.info(f"API route not handled by catch-all: {full_path}")
        raise HTTPException(status_code=404, detail=f"API route not found: {full_path}")
    
    logger.info(f"Serving frontend for path: {full_path}")
    
    # Try multiple possible locations for index.html
    possible_paths = [
        frontend_dir / "index.html",
        BASE_DIR / "frontend" / "src" / "index.html",
        BASE_DIR / "frontend" / "index.html",
        BASE_DIR / "frontend" / "dist" / "index.html"
    ]
    
    # Log all possible paths
    for idx, path in enumerate(possible_paths):
        logger.info(f"Checking path {idx+1}: {path} (exists: {path.exists()})")
    
    # Try each path in order
    for path in possible_paths:
        if path.exists():
            logger.info(f"Found index.html at {path}, serving for {full_path}")
            return FileResponse(str(path))
    
    # If we get here, we couldn't find index.html
    logger.error(f"Could not find index.html in any expected location")
    
    # Return a more helpful error
    return JSONResponse(
        status_code=404,
        content={
            "detail": "Frontend index.html not found",
            "checked_paths": [str(p) for p in possible_paths],
            "current_path": full_path,
            "frontend_dir": str(frontend_dir),
            "base_dir": str(BASE_DIR)
        }
    )

# Add a more comprehensive health check
@app.get("/debug/health")
async def health_check():
    # Check for index.html in various locations
    index_locations = [
        frontend_dir / "index.html",
        frontend_dir / "dist" / "index.html",
        BASE_DIR / "frontend" / "index.html",
        BASE_DIR / "frontend" / "dist" / "index.html"
    ]
    
    index_exists = {str(path): path.exists() for path in index_locations}
    
    # Check directory contents
    directory_contents = {
        "frontend_dir": list(map(str, frontend_dir.glob("*"))) if frontend_dir.exists() else "directory not found",
        "frontend_dist": list(map(str, (frontend_dir / "dist").glob("*"))) if (frontend_dir / "dist").exists() else "directory not found",
        "base_dir": list(map(str, BASE_DIR.glob("*"))) if BASE_DIR.exists() else "directory not found"
    }
    
    return {
        "status": "ok", 
        "frontend_dir_exists": frontend_dir.exists(),
        "index_html_locations": index_exists,
        "directory_contents": directory_contents,
        "python_version": sys.version,
        "working_directory": os.getcwd(),
        "app_directory": str(APP_DIR),
        "base_directory": str(BASE_DIR),
        "environment_variables": {k: v for k, v in os.environ.items() if k in ["BASE_DIR", "PORT", "PATH"]}
    }

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting server on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Disable reload in production
    )
