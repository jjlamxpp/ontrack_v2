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
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# Add these Pydantic models for your API
class Question(BaseModel):
    id: int
    question_text: str
    category: str
    options: List[str]

class SurveyResponse(BaseModel):
    answers: List[str]

class PersonalityAnalysis(BaseModel):
    type: str
    description: str
    interpretation: str
    enjoyment: List[str]
    your_strength: List[str]
    iconId: str
    riasecScores: Dict[str, float]

class IndustryRecommendation(BaseModel):
    id: str
    name: str
    overview: str
    trending: str
    insight: str
    examplePaths: List[str]
    education: Optional[str] = None

class AnalysisResult(BaseModel):
    personality: PersonalityAnalysis
    industries: List[IndustryRecommendation]

# Set up logging with more verbose output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Export BASE_DIR as a global variable for other modules to use
BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR / "app"
frontend_dir = BASE_DIR / "frontend"
frontend_build_dir = frontend_dir / "dist"  # Vite builds to 'dist' by default

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
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=False,  # Set to False when using credentials: 'omit'
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define static directories
app_static_dir = APP_DIR / "static"
logger.info(f"app_static_dir: {app_static_dir}")
logger.info(f"frontend_build_dir: {frontend_build_dir}")

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

# Mount the frontend build directory with proper MIME types
if frontend_build_dir.exists():
    logger.info(f"Mounting / to {frontend_build_dir}")
    app.mount("/assets", StaticFiles(directory=str(frontend_build_dir / "assets"), name="assets", html=False))
    
    # Ensure JavaScript files are served with the correct MIME type
    @app.middleware("http")
    async def add_js_mime_type(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.endswith(".js"):
            response.headers["Content-Type"] = "application/javascript; charset=utf-8"
        elif path.endswith(".css"):
            response.headers["Content-Type"] = "text/css; charset=utf-8"
        return response

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
    
    # Add direct API routes for survey functionality
    @app.get("/api/survey/questions", response_model=List[Question])
    async def get_survey_questions():
        """Return the list of survey questions"""
        try:
            # Path to the questions JSON file
            questions_file = APP_DIR / "data" / "questions.json"
            
            # Check if file exists
            if not questions_file.exists():
                logger.error(f"Questions file not found: {questions_file}")
                # Create a sample questions file for testing
                sample_questions = [
                    {
                        "id": i,
                        "question_text": f"Sample question {i}?",
                        "category": "sample",
                        "options": ["YES", "NO"]
                    }
                    for i in range(1, 31)
                ]
                
                # Ensure directory exists
                questions_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write sample questions
                with open(questions_file, "w") as f:
                    json.dump(sample_questions, f, indent=2)
                
                logger.info(f"Created sample questions file at {questions_file}")
                return sample_questions
            
            # Read questions from file
            with open(questions_file, "r") as f:
                questions = json.load(f)
            
            logger.info(f"Loaded {len(questions)} questions from {questions_file}")
            return questions
            
        except Exception as e:
            logger.error(f"Error loading questions: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to load questions: {str(e)}")
    
    @app.post("/api/survey/submit", response_model=AnalysisResult)
    async def submit_survey(survey_response: SurveyResponse):
        """Process survey answers and return analysis"""
        try:
            logger.info(f"Received survey submission with {len(survey_response.answers)} answers")
            
            # Path to the sample analysis result file
            analysis_file = APP_DIR / "data" / "sample_analysis.json"
            
            # Check if file exists, if not create a sample one
            if not analysis_file.exists():
                # Create a sample analysis result
                sample_analysis = {
                    "personality": {
                        "type": "Innovator",
                        "description": "You are creative and analytical, with a strong drive to solve complex problems.",
                        "interpretation": "Your combination of creativity and analytical thinking makes you well-suited for roles that require innovation and problem-solving.",
                        "enjoyment": [
                            "Solving complex problems",
                            "Learning new technologies",
                            "Working on creative projects"
                        ],
                        "your_strength": [
                            "Creative thinking",
                            "Analytical skills",
                            "Adaptability"
                        ],
                        "iconId": "1",
                        "riasecScores": {
                            "R": 0.6,
                            "I": 0.8,
                            "A": 0.7,
                            "S": 0.4,
                            "E": 0.5,
                            "C": 0.3
                        }
                    },
                    "industries": [
                        {
                            "id": "tech",
                            "name": "Technology",
                            "overview": "The technology industry is rapidly evolving with new innovations emerging constantly.",
                            "trending": "AI, machine learning, and cloud computing are among the fastest-growing areas.",
                            "insight": "Technology roles often require continuous learning and adaptation to new tools and methodologies.",
                            "examplePaths": [
                                "Software Developer → Senior Developer → Technical Lead → CTO",
                                "Data Analyst → Data Scientist → AI Specialist → Research Director"
                            ],
                            "education": "Computer Science // JS6963 // HKUST // 5.5"
                        },
                        {
                            "id": "finance",
                            "name": "Finance",
                            "overview": "The finance industry involves managing money, investments, and financial systems.",
                            "trending": "Fintech, blockchain, and algorithmic trading are transforming traditional finance.",
                            "insight": "Finance careers often combine technical skills with business acumen.",
                            "examplePaths": [
                                "Financial Analyst → Investment Banker → Portfolio Manager → CFO",
                                "Risk Analyst → Risk Manager → Chief Risk Officer"
                            ],
                            "education": "Finance // JS6482 // HKU // 5.8"
                        }
                    ]
                }
                
                # Ensure directory exists
                analysis_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write sample analysis
                with open(analysis_file, "w") as f:
                    json.dump(sample_analysis, f, indent=2)
                
                logger.info(f"Created sample analysis file at {analysis_file}")
            
            # Read analysis from file
            with open(analysis_file, "r") as f:
                analysis = json.load(f)
            
            logger.info(f"Returning analysis result")
            return analysis
            
        except Exception as e:
            logger.error(f"Error processing survey: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to process survey: {str(e)}")
    
    @app.get("/api/survey/icon/{icon_id}")
    async def get_character_icon(icon_id: str):
        """Return character icon image"""
        try:
            # Clean the icon_id to prevent path traversal
            clean_id = re.sub(r'[^0-9]', '', icon_id)
            
            # Check for file extension
            if not clean_id.endswith('.png'):
                clean_id = f"{clean_id}.png"
            
            # Path to icons directory
            icons_dir = APP_DIR / "static" / "icon"
            
            # Ensure directory exists
            icons_dir.mkdir(parents=True, exist_ok=True)
            
            # Path to the requested icon
            icon_path = icons_dir / clean_id
            
            # Check if icon exists
            if not icon_path.exists():
                # Use default icon
                icon_path = icons_dir / "default.png"
                
                # If default doesn't exist, create a simple one
                if not icon_path.exists():
                    # Create a simple default icon (this requires PIL)
                    try:
                        from PIL import Image, ImageDraw
                        
                        # Create a simple colored square
                        img = Image.new('RGB', (200, 200), color=(73, 109, 137))
                        d = ImageDraw.Draw(img)
                        d.text((20, 70), "Default Icon", fill=(255, 255, 0))
                        
                        # Save the image
                        img.save(icon_path)
                        logger.info(f"Created default icon at {icon_path}")
                    except ImportError:
                        logger.warning("PIL not available, cannot create default icon")
                        raise HTTPException(status_code=404, detail="Icon not found and cannot create default")
            
            logger.info(f"Serving icon from {icon_path}")
            return FileResponse(icon_path)
            
        except Exception as e:
            logger.error(f"Error serving icon: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to serve icon: {str(e)}")
    
    @app.get("/api/survey/school-icon/{school_name}")
    async def get_school_logo(school_name: str):
        """Return school logo image"""
        try:
            # Clean the school name to prevent path traversal
            clean_name = re.sub(r'[^a-zA-Z0-9\-]', '', school_name)
            
            # Check for file extension
            if not clean_name.endswith('.png'):
                clean_name = f"{clean_name}.png"
            
            # Path to school icons directory
            school_icons_dir = APP_DIR / "static" / "school_icon"
            
            # Ensure directory exists
            school_icons_dir.mkdir(parents=True, exist_ok=True)
            
            # Path to the requested school icon
            icon_path = school_icons_dir / clean_name
            
            # Check if icon exists
            if not icon_path.exists():
                # Use default icon
                icon_path = school_icons_dir / "default.png"
                
                # If default doesn't exist, create a simple one
                if not icon_path.exists():
                    # Create a simple default icon (this requires PIL)
                    try:
                        from PIL import Image, ImageDraw
                        
                        # Create a simple colored square
                        img = Image.new('RGB', (200, 200), color=(200, 200, 200))
                        d = ImageDraw.Draw(img)
                        d.text((20, 70), "School Logo", fill=(0, 0, 0))
                        
                        # Save the image
                        img.save(icon_path)
                        logger.info(f"Created default school icon at {icon_path}")
                    except ImportError:
                        logger.warning("PIL not available, cannot create default school icon")
                        raise HTTPException(status_code=404, detail="School icon not found and cannot create default")
            
            logger.info(f"Serving school icon from {icon_path}")
            return FileResponse(icon_path)
            
        except Exception as e:
            logger.error(f"Error serving school icon: {str(e)}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to serve school icon: {str(e)}")
    
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
    index_path = frontend_build_dir / "index.html"
    if index_path.exists():
        logger.info(f"Serving root index.html from {index_path}")
        return FileResponse(str(index_path))
    else:
        error_msg = f"Frontend index.html not found at {index_path}"
        logger.error(error_msg)
        return JSONResponse(status_code=404, content={"detail": error_msg})

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
    
    # First try to serve the file directly from the build directory
    file_path = frontend_build_dir / full_path
    if file_path.exists() and file_path.is_file():
        logger.info(f"Serving file: {file_path}")
        return FileResponse(str(file_path))
    
    # If not found, serve index.html for client-side routing
    index_path = frontend_build_dir / "index.html"
    if index_path.exists():
        logger.info(f"Serving index.html for path: {full_path}")
        return FileResponse(str(index_path))
    
    # If we get here, we couldn't find index.html
    logger.error(f"Could not find index.html in any expected location")
    
    return JSONResponse(
        status_code=404,
        content={"detail": "Frontend index.html not found"}
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
