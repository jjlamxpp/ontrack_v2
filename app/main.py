from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pathlib import Path
import shutil
import os

app = FastAPI()

# Create necessary directories
static_dir = Path("static")
icon_dir = static_dir / "icon"
school_icon_dir = static_dir / "school_icon"

static_dir.mkdir(parents=True, exist_ok=True)
icon_dir.mkdir(parents=True, exist_ok=True)
school_icon_dir.mkdir(parents=True, exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add root route
@app.get("/")
async def root():
    # Redirect to your frontend URL or return API information
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

# Include your routers
from routers import survey
app.include_router(
    survey.router,
    prefix="/api/survey",
    tags=["survey"]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)