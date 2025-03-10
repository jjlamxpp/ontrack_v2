from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from pathlib import Path
import logging
import sys
import os
import traceback
import re
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import pandas as pd
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.database.excel_db import SurveyDatabase

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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
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

# Mount static directories
static_dir = BASE_DIR / "static"
if not static_dir.exists():
    static_dir.mkdir(parents=True, exist_ok=True)
    
    # Create icon directories if they don't exist
    icon_dir = static_dir / "icon"
    school_icon_dir = static_dir / "school_icon"
    icon_dir.mkdir(exist_ok=True)
    school_icon_dir.mkdir(exist_ok=True)
    
    # Copy default icons from app/static if they exist
    app_static = BASE_DIR / "app" / "static"
    if app_static.exists():
        logger.info(f"Copying static files from {app_static} to {static_dir}")
        import shutil
        
        # Copy icon files
        app_icon_dir = app_static / "icon"
        if app_icon_dir.exists():
            for icon_file in app_icon_dir.glob("*.*"):
                target = icon_dir / icon_file.name
                if not target.exists():
                    shutil.copy2(icon_file, target)
        
        # Copy school icon files
        app_school_icon_dir = app_static / "school_icon"
        if app_school_icon_dir.exists():
            for icon_file in app_school_icon_dir.glob("*.*"):
                target = school_icon_dir / icon_file.name
                if not target.exists():
                    shutil.copy2(icon_file, target)

# Mount the static directory
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Also try to mount the app/static directory as a fallback
app_static_dir = BASE_DIR / "app" / "static"
if app_static_dir.exists() and app_static_dir != static_dir:
    app.mount("/app/static", StaticFiles(directory=str(app_static_dir)), name="app_static")

# Add middleware for SPA routing
class SPAMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip API routes - let them be handled normally
        if request.url.path.startswith("/api/"):
            logger.info(f"API route: {request.url.path}, handling normally")
            return await call_next(request)
        
        # Skip static file routes
        if request.url.path.startswith("/static/") or request.url.path.startswith("/assets/"):
            logger.info(f"Static route: {request.url.path}, handling normally")
            return await call_next(request)
        
        # For all other routes, try to serve the normal response first
        response = await call_next(request)
        
        # If the response is a 404, serve index.html instead
        if response.status_code == 404:
            logger.info(f"404 for route: {request.url.path}, serving index.html")
            
            # Try to find index.html in multiple possible locations
            possible_index_paths = [
                frontend_build_dir / "index.html",
                frontend_dir / "index.html",
                BASE_DIR / "frontend" / "dist" / "index.html",
                BASE_DIR / "frontend" / "index.html",
                BASE_DIR / "static" / "index.html"
            ]
            
            for index_path in possible_index_paths:
                if index_path.exists():
                    logger.info(f"Serving index.html from {index_path}")
                    return FileResponse(index_path)
            
            logger.warning("Could not find index.html in any expected location")
        
        return response

# Add the SPA middleware
app.add_middleware(SPAMiddleware)

# Add other middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including POST
    allow_headers=["*"],  # Allow all headers
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

# IMPORTANT: Define API routes BEFORE mounting static files
# Create a router for survey-related endpoints
@app.get("/api/survey/questions", response_model=List[Question])
async def get_survey_questions():
    """Return list of survey questions"""
    try:
        logger.info("Fetching survey questions")
        
        # Path to the Excel file
        excel_file = BASE_DIR / "app" / "database" / "Database.xlsx"
        logger.info(f"Looking for Excel file at: {excel_file}")
        
        # Check if file exists
        if not excel_file.exists():
            logger.warning(f"Excel file not found at {excel_file}")
            
            # List directory contents to help debug
            parent_dir = excel_file.parent
            if parent_dir.exists():
                logger.info(f"Contents of {parent_dir}: {list(parent_dir.glob('*'))}")
            else:
                logger.warning(f"Directory {parent_dir} does not exist")
                
            # Create a sample questions list as fallback
            fallback_questions = [
                {"id": i, "question_text": f"Sample Question {i}", "category": "general", 
                 "options": ["Yes", "No"]}
                for i in range(1, 11)  # Create 10 sample questions
            ]
            
            logger.info(f"Returning {len(fallback_questions)} sample questions")
            return fallback_questions
        
        # Read questions from Excel file
        logger.info(f"Reading questions from Excel file: {excel_file}")
        try:
            # Read the 'Question pool' sheet
            df = pd.read_excel(excel_file, sheet_name='Question pool')
            
            # Log the columns to help debug
            logger.info(f"Excel columns: {df.columns.tolist()}")
            
            # Convert DataFrame to list of questions
            questions = []
            for index, row in df.iterrows():
                # Extract question text from the 'questions:' column
                question_text_raw = row.get('questions:', '')
                
                # Parse the question text from the YAML-like format
                # Format is: "- question: \"Actual question text\""
                if isinstance(question_text_raw, str) and "question:" in question_text_raw:
                    # Extract the text between quotes
                    import re
                    match = re.search(r'"([^"]*)"', question_text_raw)
                    if match:
                        question_text = match.group(1)
                    else:
                        # Try with single quotes if double quotes not found
                        match = re.search(r"'([^']*)'", question_text_raw)
                        if match:
                            question_text = match.group(1)
                        else:
                            # If no quotes found, try to extract after "question:"
                            parts = question_text_raw.split("question:")
                            if len(parts) > 1:
                                question_text = parts[1].strip().strip('"').strip("'")
                            else:
                                logger.warning(f"Could not parse question text from: {question_text_raw}")
                                continue
                else:
                    logger.warning(f"Row {index} has invalid question format: {question_text_raw}")
                    continue
                
                # Get category
                category = row.get('category', 'general')
                
                question = {
                    "id": int(index + 1),  # Use row index + 1 as ID
                    "question_text": question_text,
                    "category": category,
                    "options": ["Yes", "No"]
                }
                questions.append(question)
            
            logger.info(f"Loaded {len(questions)} questions from Excel file")
            
            # If no questions were loaded, use fallback
            if not questions:
                logger.warning("No valid questions found in Excel file, using fallback")
                fallback_questions = [
                    {"id": i, "question_text": f"Sample Question {i}", "category": "general", 
                     "options": ["Yes", "No"]}
                    for i in range(1, 11)  # Create 10 sample questions
                ]
                return fallback_questions
            
            return questions
            
        except Exception as excel_error:
            logger.error(f"Error reading Excel file: {str(excel_error)}")
            logger.error(traceback.format_exc())
            
            # Return a simple set of questions as fallback
            fallback_questions = [
                {"id": i, "question_text": f"Fallback Question {i}", "category": "general", 
                 "options": ["Yes", "No"]}
                for i in range(1, 43)  # Create 42 questions
            ]
            
            logger.info(f"Returning {len(fallback_questions)} fallback questions")
            return fallback_questions
        
    except Exception as e:
        logger.error(f"Error loading questions: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to load questions: {str(e)}")

# Add a debug endpoint to check API functionality
@app.get("/api/debug")
async def api_debug():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "methods": getattr(route, "methods", ["GET"])
        })
    
    return {
        "status": "API is working", 
        "routes": routes,
        "base_dir": str(BASE_DIR),
        "app_dir": str(APP_DIR)
    }

# Add a debug endpoint to check Excel file
@app.get("/api/debug/excel")
async def debug_excel():
    """Debug endpoint to check Excel file"""
    try:
        # Path to the Excel file
        excel_file = BASE_DIR / "app" / "database" / "Database.xlsx"
        
        # Check if file exists
        file_exists = excel_file.exists()
        
        result = {
            "file_path": str(excel_file),
            "file_exists": file_exists,
        }
        
        if file_exists:
            # Get file size
            result["file_size"] = os.path.getsize(excel_file)
            
            # List sheet names
            try:
                xls = pd.ExcelFile(excel_file)
                result["sheet_names"] = xls.sheet_names
                
                # Get sample data from each sheet
                sheets_data = {}
                for sheet in xls.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet)
                    sheets_data[sheet] = {
                        "columns": df.columns.tolist(),
                        "row_count": len(df),
                        "sample_row": df.iloc[0].to_dict() if not df.empty else "No data"
                    }
                result["sheets_data"] = sheets_data
            except Exception as e:
                result["excel_error"] = str(e)
        else:
            # List directory contents
            parent_dir = excel_file.parent
            if parent_dir.exists():
                result["parent_dir_contents"] = [str(p) for p in parent_dir.glob("*")]
            else:
                result["parent_dir_exists"] = False
        
        return result
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}

# Add a debug endpoint for API testing
@app.get("/api/debug/test-api")
async def test_api():
    """Test endpoint to verify API functionality"""
    logger.info("API test endpoint called")
    
    # Check for survey router
    routers = [r for r in app.routes if hasattr(r, "path") and "/api/survey" in r.path]
    
    return {
        "status": "ok",
        "api_routes": [str(r.path) for r in app.routes if "/api/" in str(r.path)],
        "survey_routes_count": len(routers),
        "environment": {
            "python_version": sys.version,
            "working_directory": os.getcwd(),
            "app_directory": str(APP_DIR),
            "base_directory": str(BASE_DIR),
        }
    }

# IMPORTANT: Define all API routes BEFORE mounting static files
# This ensures that API routes are not blocked by static file handling

# Add a simple test endpoint that always returns a success response
@app.get("/api/test")
async def test_api():
    """Test endpoint to verify API connectivity"""
    logger.info("Test API endpoint called")
    return {"status": "ok", "message": "API is working"}

# Add a test endpoint for survey submission
@app.post("/api/test-submit")
async def test_submit():
    """Test endpoint to verify survey submission"""
    logger.info("Test submit endpoint called")
    return {
        "personality": {
            "type": "RI",
            "description": "You are a logical and analytical thinker with a strong interest in understanding how things work.",
            "interpretation": "Your combination of Realistic and Investigative traits suggests you enjoy solving practical problems through analysis and research.",
            "enjoyment": [
                "Working with technical systems",
                "Analyzing complex problems",
                "Learning new technical skills"
            ],
            "your_strength": [
                "Logical thinking",
                "Problem-solving",
                "Technical aptitude"
            ],
            "iconId": "1",
            "riasecScores": {"R": 5, "I": 4, "A": 2, "S": 1, "E": 3, "C": 2}
        },
        "industries": [{
            "id": "RIA",
            "name": "Engineering",
            "overview": "Engineering involves applying scientific and mathematical principles to design and build systems, structures, and products.",
            "trending": "Software engineering, biomedical engineering, and renewable energy engineering are rapidly growing fields.",
            "insight": "Engineers are in high demand across various sectors, with opportunities for specialization and advancement.",
            "examplePaths": [
                "Software Engineer",
                "Mechanical Engineer",
                "Civil Engineer"
            ],
            "education": "Bachelor's degree in engineering or related field, with professional certification often required."
        }]
    }

# NOW mount static files AFTER all API routes are defined
# AFTER defining all API routes, THEN mount static files
if frontend_build_dir.exists():
    logger.info(f"Mounting / to {frontend_build_dir}")
    
    # List contents of the dist directory to find asset folders
    dist_contents = list(frontend_build_dir.glob("*"))
    logger.info(f"Dist directory contents: {dist_contents}")
    
    # Try to mount common asset directories
    for asset_dir in ["assets", "static", "js", "css"]:
        asset_path = frontend_build_dir / asset_dir
        if asset_path.exists() and asset_path.is_dir():
            logger.info(f"Mounting /{asset_dir} to {asset_path}")
            try:
                app.mount(f"/{asset_dir}", StaticFiles(directory=str(asset_path), html=False))
            except TypeError:
                app.mount(f"/{asset_dir}", StaticFiles(directory=str(asset_path)))
    
    # Mount the root directory for index.html and other files
    # IMPORTANT: This must be the LAST mount to avoid blocking API routes
    app.mount("/", StaticFiles(directory=str(frontend_build_dir), html=True), name="frontend")

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
async def serve_index():
    """Serve the index.html file"""
    index_path = frontend_build_dir / "index.html"
    if index_path.exists():
        logger.info(f"Serving index.html from {index_path}")
        return FileResponse(index_path)
    
    # Try alternative locations
    alt_index_path = frontend_dir / "index.html"
    if alt_index_path.exists():
        logger.info(f"Serving index.html from alternative location: {alt_index_path}")
        return FileResponse(alt_index_path)
    
    logger.error("index.html not found in any expected location")
    return JSONResponse(
        status_code=404,
        content={"detail": "Frontend index.html not found"}
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

# Import necessary modules for survey processing
from pydantic import BaseModel
from typing import List
from app.database.excel_db import SurveyDatabase
import traceback
from fastapi import HTTPException, Request
from fastapi.routing import APIRoute

# Define the request model for survey submission
class SurveyRequest(BaseModel):
    answers: List[str]

# Add a direct endpoint for survey submission
@app.post("/api/survey/submit")
async def submit_survey(survey_data: SurveyRequest):
    """
    Submit survey answers and get personality analysis result.
    Always returns a valid result, even if there are database issues.
    """
    try:
        # Log the request
        logger.info(f"Received survey submission with {len(survey_data.answers)} answers")
        logger.info(f"Answers: {survey_data.answers}")
        
        # Try to process with the database
        try:
            # Initialize the database
            db_path = "/app/database/Database.xlsx"
            logger.info(f"Initializing database with path: {db_path}")
            
            # Check if the file exists
            if not os.path.exists(db_path):
                logger.error(f"Database file not found at {db_path}")
                # List files in the directory to help debug
                parent_dir = os.path.dirname(db_path)
                if os.path.exists(parent_dir):
                    logger.info(f"Files in {parent_dir}: {os.listdir(parent_dir)}")
                else:
                    logger.error(f"Parent directory {parent_dir} does not exist")
                
                # Return fallback result
                return get_fallback_result()
            
            # Initialize the database
            db = SurveyDatabase(excel_path=db_path)
            logger.info("Database initialized successfully")
            
            # Process the survey
            result = db.process_survey(survey_data.answers)
            logger.info("Survey processed successfully")
            
            # Return the result
            return result
        except Exception as db_error:
            # Log the database error
            logger.error(f"Database error: {str(db_error)}")
            logger.exception("Exception details:")
            
            # Return fallback result
            return get_fallback_result()
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in submit_survey: {str(e)}")
        logger.exception("Exception details:")
        
        # Return fallback result
        return get_fallback_result()

def get_fallback_result():
    """
    Return a fallback result when the database is not available.
    """
    logger.info("Using fallback result")
    return {
        "personality": {
            "type": "RI",
            "description": "You are a logical and analytical thinker with a strong interest in understanding how things work.",
            "interpretation": "Your combination of Realistic and Investigative traits suggests you enjoy solving practical problems through analysis and research.",
            "enjoyment": [
                "Working with technical systems",
                "Analyzing complex problems",
                "Learning new technical skills"
            ],
            "your_strength": [
                "Logical thinking",
                "Problem-solving",
                "Technical aptitude"
            ],
            "iconId": "1",
            "riasecScores": {"R": 5, "I": 4, "A": 2, "S": 1, "E": 3, "C": 2}
        },
        "industries": [{
            "id": "RIA",
            "name": "Engineering",
            "overview": "Engineering involves applying scientific and mathematical principles to design and build systems, structures, and products.",
            "trending": "Software engineering, biomedical engineering, and renewable energy engineering are rapidly growing fields.",
            "insight": "Engineers are in high demand across various sectors, with opportunities for specialization and advancement.",
            "examplePaths": [
                "Software Engineer",
                "Mechanical Engineer",
                "Civil Engineer"
            ],
            "education": "Bachelor's degree in engineering or related field, with professional certification often required."
        }]
    }

# Add a test endpoint to verify API functionality
@app.get("/api/survey/test")
async def test_survey_api():
    """Test endpoint to verify API connectivity"""
    logger.info("Test survey API endpoint called")
    return {"status": "ok", "message": "Survey API is working"}

# Add a debug endpoint to list all routes
@app.get("/debug/routes")
async def debug_routes():
    """List all registered routes for debugging"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": getattr(route, "path", "Unknown"),
            "name": getattr(route, "name", "Unknown"),
            "methods": getattr(route, "methods", ["Unknown"])
        })
    return {"routes": routes}

# IMPORTANT: Make sure this code appears BEFORE any static file mounts or catch-all routes
# Import the survey router
from app.routers.survey import router as survey_router

# Mount the survey router with the correct prefix
app.include_router(
    survey_router,
    prefix="/api",  # This will make the endpoint available at /api/survey/questions
    tags=["survey"]
)

# Add a catch-all route for OPTIONS requests to handle CORS preflight
@app.options("/{full_path:path}")
async def options_route(full_path: str):
    """Handle OPTIONS requests for CORS preflight"""
    logger.info(f"OPTIONS request for /{full_path}")
    return {}

# IMPORTANT: This must be the LAST route in your file - update to handle SPA routing
@app.get("/{full_path:path}")
async def serve_spa_routes(full_path: str):
    """Serve the frontend for any path not matched by API routes"""
    # Log the requested path
    logger.info(f"Catch-all route handling: /{full_path}")
    
    # Skip API routes - they should have been handled by their own endpoints
    if full_path.startswith("api/"):
        logger.warning(f"API route not found: /{full_path}")
        return JSONResponse(
            status_code=404,
            content={"error": "API endpoint not found"}
        )
    
    # For all other paths, serve index.html to support SPA routing
    # Try multiple possible locations for index.html
    possible_index_paths = [
        frontend_build_dir / "index.html",
        frontend_dir / "index.html",
        BASE_DIR / "frontend" / "dist" / "index.html",
        BASE_DIR / "frontend" / "index.html",
        BASE_DIR / "static" / "index.html"
    ]
    
    for index_path in possible_index_paths:
        if index_path.exists():
            logger.info(f"Serving index.html from {index_path} for SPA route: /{full_path}")
            return FileResponse(index_path)
    
    # If we can't find the frontend, return a 404
    logger.warning(f"Frontend not found in any of the expected locations")
    return JSONResponse(
        status_code=404,
        content={"detail": "Frontend not found"}
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

@app.post("/api/test-post")
async def test_post_method(request: Request):
    """Test endpoint to verify POST method works"""
    try:
        body = await request.json()
        logger.info(f"POST test endpoint called with body: {body}")
        return {"status": "ok", "message": "POST method is working", "received": body}
    except Exception as e:
        logger.error(f"Error in test POST endpoint: {str(e)}")
        return {"status": "error", "message": str(e)}

# Add a debug endpoint to check the database status
@app.get("/api/debug/database")
async def debug_database():
    """Debug endpoint to check the database status"""
    try:
        # Try to find the Excel file in different possible locations
        excel_path = Path("/app/database/Database.xlsx")
        logger.info(f"Looking for Excel file at: {excel_path}")
        
        result = {
            "file_exists": excel_path.exists(),
            "file_path": str(excel_path),
            "absolute_path": str(excel_path.absolute()),
            "current_directory": os.getcwd(),
            "database_directory_exists": (Path("/app/database")).exists(),
        }
        
        if excel_path.exists():
            # Initialize the database
            logger.info(f"Initializing database with Excel file: {excel_path}")
            from app.database.excel_db import SurveyDatabase
            db = SurveyDatabase(str(excel_path))
            logger.info("Database initialized successfully")
            
            # Get questions
            questions = db.get_all_questions()
            result["questions_count"] = len(questions)
            result["first_question"] = questions[0] if questions else None
            
            # Test processing
            test_answers = ["YES"] * len(questions)
            test_result = db.process_basic_results(test_answers)
            result["test_processing"] = {
                "success": True,
                "result_keys": list(test_result.keys()),
                "personality_type": test_result.get("personality_type", {}).get("role", "Unknown"),
                "industries_count": len(test_result.get("recommended_industries", [])),
            }
        else:
            # List all files in the app/database directory to help debug
            database_dir = Path("/app/database")
            if database_dir.exists():
                result["database_dir_contents"] = [str(p) for p in database_dir.glob("*")]
            else:
                result["database_dir_exists"] = False
                
                # List all files in the current directory to help debug
                result["current_dir_contents"] = [str(p) for p in Path(".").glob("*")]
                
                # List all files in the app directory to help debug
                app_dir = Path("/app")
                if app_dir.exists():
                    result["app_dir_contents"] = [str(p) for p in app_dir.glob("*")]
                else:
                    result["app_dir_exists"] = False
        
        return result
    except Exception as e:
        logger.error(f"Error in debug_database: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

# Add a comprehensive test endpoint to diagnose the survey submission issue
@app.get("/api/debug/survey-test")
async def debug_survey_test():
    """Comprehensive test endpoint to diagnose the survey submission issue"""
    try:
        result = {
            "environment": {
                "current_directory": os.getcwd(),
                "python_version": sys.version,
                "platform": sys.platform,
                "base_dir": str(BASE_DIR),
                "app_dir": str(APP_DIR),
            },
            "file_system": {},
            "database": {},
            "test_processing": {}
        }
        
        # Check file system
        paths_to_check = [
            "app",
            "app/database",
            "app/database/Database.xlsx",
            "frontend",
            "frontend/dist",
            "frontend/dist/index.html"
        ]
        
        for path in paths_to_check:
            p = Path(path)
            result["file_system"][path] = {
                "exists": p.exists(),
                "is_file": p.is_file() if p.exists() else None,
                "is_dir": p.is_dir() if p.exists() else None,
                "absolute_path": str(p.absolute()),
                "size": os.path.getsize(p) if p.exists() and p.is_file() else None
            }
            
            # List directory contents if it's a directory
            if p.exists() and p.is_dir():
                result["file_system"][path]["contents"] = [str(f.name) for f in p.glob("*")]
        
        # Check database
        excel_path = Path("/app/database/Database.xlsx")
        result["database"]["excel_path"] = str(excel_path)
        result["database"]["excel_exists"] = excel_path.exists()
        
        if excel_path.exists():
            # Try to initialize the database
            try:
                from app.database.excel_db import SurveyDatabase
                db = SurveyDatabase(str(excel_path))
                result["database"]["initialization"] = "success"
                
                # Try to get questions
                try:
                    questions = db.get_all_questions()
                    result["database"]["questions_count"] = len(questions)
                    result["database"]["first_question"] = questions[0] if questions else None
                    
                    # Try to process test answers
                    try:
                        test_answers = ["YES"] * len(questions)
                        test_result = db.process_basic_results(test_answers)
                        result["test_processing"]["success"] = True
                        result["test_processing"]["result_keys"] = list(test_result.keys())
                        result["test_processing"]["personality_type"] = test_result.get("personality_type", {}).get("role", "Unknown")
                        result["test_processing"]["industries_count"] = len(test_result.get("recommended_industries", []))
                        
                        # Format the test result as it would be returned to the frontend
                        personality_type = test_result.get("personality_type", {})
                        personality = {
                            "type": personality_type.get("code", "XX"),
                            "description": personality_type.get("who_you_are", ""),
                            "interpretation": personality_type.get("how_this_combination", ""),
                            "enjoyment": personality_type.get("what_you_might_enjoy", []),
                            "your_strength": personality_type.get("your_strength", []),
                            "iconId": personality_type.get("icon_id", ""),
                            "riasecScores": test_result.get("category_counts", {})
                        }
                        
                        industries = []
                        for industry in test_result.get("recommended_industries", []):
                            industries.append({
                                "id": industry.get("matching_code", ""),
                                "name": industry.get("industry", ""),
                                "overview": industry.get("description", ""),
                                "trending": industry.get("trending", ""),
                                "insight": industry.get("insight", ""),
                                "examplePaths": industry.get("career_path", []),
                                "education": industry.get("education", "")
                            })
                        
                        result["test_processing"]["formatted_result"] = {
                            "personality": personality,
                            "industries": industries
                        }
                    except Exception as process_err:
                        result["test_processing"]["success"] = False
                        result["test_processing"]["error"] = str(process_err)
                        result["test_processing"]["traceback"] = traceback.format_exc()
                except Exception as questions_err:
                    result["database"]["questions_error"] = str(questions_err)
                    result["database"]["questions_traceback"] = traceback.format_exc()
            except Exception as db_err:
                result["database"]["initialization_error"] = str(db_err)
                result["database"]["initialization_traceback"] = traceback.format_exc()
        
        return result
    except Exception as e:
        logger.error(f"Error in debug_survey_test: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

# Add a special debug endpoint to check file system and database access
@app.get("/api/debug/file-system")
async def debug_file_system():
    """Debug endpoint to check file system and database access"""
    try:
        result = {
            "environment": {
                "current_directory": os.getcwd(),
                "python_version": sys.version,
                "platform": sys.platform,
                "user": os.getenv("USER", "unknown"),
                "home": os.getenv("HOME", "unknown"),
                "path": os.getenv("PATH", "unknown"),
            },
            "file_system": {},
            "database_checks": {}
        }
        
        # Check various paths
        paths_to_check = [
            "/",
            "/app",
            "/app/database",
            "/app/database/Database.xlsx",
            "app",
            "app/database",
            "app/database/Database.xlsx",
            "./app",
            "./app/database",
            "./app/database/Database.xlsx",
            "../app",
            "../app/database",
            "../app/database/Database.xlsx",
        ]
        
        for path in paths_to_check:
            p = Path(path)
            result["file_system"][path] = {
                "exists": p.exists(),
                "is_file": p.is_file() if p.exists() else None,
                "is_dir": p.is_dir() if p.exists() else None,
                "absolute_path": str(p.absolute()),
            }
            
            # If it's a directory, list contents
            if p.exists() and p.is_dir():
                try:
                    result["file_system"][path]["contents"] = [str(f.name) for f in p.glob("*")]
                except Exception as e:
                    result["file_system"][path]["error"] = str(e)
        
        # Try to read the database file directly
        excel_path = Path("/app/database/Database.xlsx")
        if excel_path.exists():
            try:
                # Get file stats
                stats = os.stat(excel_path)
                result["database_checks"]["file_stats"] = {
                    "size": stats.st_size,
                    "mode": stats.st_mode,
                    "uid": stats.st_uid,
                    "gid": stats.st_gid,
                    "atime": stats.st_atime,
                    "mtime": stats.st_mtime,
                    "ctime": stats.st_ctime,
                }
                
                # Try to read the file
                with open(excel_path, "rb") as f:
                    first_bytes = f.read(100)
                    result["database_checks"]["first_bytes_hex"] = first_bytes.hex()
                    result["database_checks"]["can_read"] = True
                
                # Try to initialize the database
                try:
                    from app.database.excel_db import SurveyDatabase
                    db = SurveyDatabase(str(excel_path))
                    result["database_checks"]["initialization"] = "success"
                    
                    # Try to get questions
                    questions = db.get_all_questions()
                    result["database_checks"]["questions_count"] = len(questions)
                    
                    # Try a simple test
                    test_answers = ["YES"] * len(questions)
                    test_result = db.process_basic_results(test_answers)
                    result["database_checks"]["test_result_keys"] = list(test_result.keys())
                except Exception as db_err:
                    result["database_checks"]["initialization_error"] = str(db_err)
                    result["database_checks"]["initialization_traceback"] = traceback.format_exc()
            except Exception as e:
                result["database_checks"]["error"] = str(e)
                result["database_checks"]["traceback"] = traceback.format_exc()
        else:
            result["database_checks"]["file_exists"] = False
        
        return result
    except Exception as e:
        logger.error(f"Error in debug_file_system: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }

# Add a direct test endpoint that will always return a valid result
@app.post("/api/direct-test")
async def direct_test(survey_data: SurveyRequest = None):
    """Direct test endpoint that will always return a valid result"""
    logger.info("Direct test endpoint called")
    return {
        "personality": {
            "type": "RI",
            "description": "You are a logical and analytical thinker with a strong interest in understanding how things work.",
            "interpretation": "Your combination of Realistic and Investigative traits suggests you enjoy solving practical problems through analysis and research.",
            "enjoyment": [
                "Working with technical systems",
                "Analyzing complex problems",
                "Learning new technical skills"
            ],
            "your_strength": [
                "Logical thinking",
                "Problem-solving",
                "Technical aptitude"
            ],
            "iconId": "1",
            "riasecScores": {"R": 5, "I": 4, "A": 2, "S": 1, "E": 3, "C": 2}
        },
        "industries": [{
            "id": "RIA",
            "name": "Engineering",
            "overview": "Engineering involves applying scientific and mathematical principles to design and build systems, structures, and products.",
            "trending": "Software engineering, biomedical engineering, and renewable energy engineering are rapidly growing fields.",
            "insight": "Engineers are in high demand across various sectors, with opportunities for specialization and advancement.",
            "examplePaths": [
                "Software Engineer",
                "Mechanical Engineer",
                "Civil Engineer"
            ],
            "education": "Bachelor's degree in engineering or related field, with professional certification often required."
        }]
    }

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint to verify the API is working.
    """
    try:
        # Check if the database directory exists
        db_path = "/app/database/Database.xlsx"
        db_dir = os.path.dirname(db_path)
        
        # Prepare response
        response = {
            "status": "ok",
            "message": "API is running",
            "database": {
                "path": db_path,
                "directory_exists": os.path.exists(db_dir),
                "file_exists": os.path.exists(db_path)
            }
        }
        
        # If the directory exists, list its contents
        if os.path.exists(db_dir):
            try:
                response["database"]["directory_contents"] = os.listdir(db_dir)
            except Exception as e:
                response["database"]["directory_error"] = str(e)
        
        return response
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
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
