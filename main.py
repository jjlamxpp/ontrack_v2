from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pathlib import Path
import logging
import sys
import os

# Add the app directory to Python path
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ontrack-v2.onrender.com",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handler
@app.exception_handler(404)
async def custom_404_handler(request, exc):
    if request.url.path.startswith("/api/survey/icon/"):
        logger.warning(f"Icon not found: {request.url.path}")
        return JSONResponse(
            status_code=404,
            content={"detail": "Icon not found"}
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
        "status": "running"
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "static_dirs": {
            "base": str(static_dir),
            "icons": str(icon_dir),
            "school_logos": str(school_icon_dir)
        }
    }

# Import routers
try:
    from app.routers import survey
    app.include_router(
        survey.router,
        prefix="/api/survey",
        tags=["survey"]
    )
    logger.info("Successfully loaded survey router")
except Exception as e:
    logger.error(f"Failed to load survey router: {e}")
    raise

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )
