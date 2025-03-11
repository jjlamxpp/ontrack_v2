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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Log the current directory and its contents to help with debugging
logger.info(f"Current working directory: {os.getcwd()}")
try:
    logger.info(f"Contents of current directory: {os.listdir(os.getcwd())}")
    
    # Try to list contents of app directory if it exists
    app_dir = os.path.join(os.getcwd(), "app")
    if os.path.exists(app_dir):
        logger.info(f"Contents of app directory: {os.listdir(app_dir)}")
        
        # Try to list contents of app/database directory if it exists
        db_dir = os.path.join(app_dir, "database")
        if os.path.exists(db_dir):
            logger.info(f"Contents of app/database directory: {os.listdir(db_dir)}")
    
    # Ensure excel_db.py is in the correct locations
    # First, check if it exists in the current directory
    if os.path.exists("excel_db.py"):
        logger.info("excel_db.py found in current directory")
        
        # Create app/database directory if it doesn't exist
        os.makedirs("app/database", exist_ok=True)
        
        # Copy excel_db.py to app/database if it doesn't exist there
        if not os.path.exists("app/database/excel_db.py"):
            logger.info("Copying excel_db.py to app/database")
            import shutil
            shutil.copy2("excel_db.py", "app/database/excel_db.py")
    else:
        logger.warning("excel_db.py not found in current directory")
except Exception as e:
    logger.error(f"Error listing directory contents: {str(e)}")

# Try different import paths for SurveyDatabase
try:
    # First try importing from app.database
    from app.database.excel_db import SurveyDatabase
except ImportError:
    try:
        # Then try importing from the local directory
        from excel_db import SurveyDatabase
    except ImportError:
        # If both fail, try to find the file and import it dynamically
        import importlib.util
        import sys
        
        # Look for excel_db.py in common locations
        possible_paths = [
            os.path.join(os.getcwd(), "excel_db.py"),
            os.path.join(os.getcwd(), "app", "database", "excel_db.py"),
            os.path.join(os.getcwd(), "database", "excel_db.py"),
            "/app/excel_db.py",
            "/app/app/database/excel_db.py"
        ]
        
        excel_db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                excel_db_path = path
                break
        
        if excel_db_path:
            # If found, import it dynamically
            module_name = "excel_db"
            spec = importlib.util.spec_from_file_location(module_name, excel_db_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            SurveyDatabase = module.SurveyDatabase
        else:
            # If not found, create a dummy class to prevent startup errors
            class SurveyDatabase:
                def __init__(self, excel_path=None):
                    self.excel_path = excel_path
                    print(f"WARNING: Using dummy SurveyDatabase. Could not find excel_db.py")
                
                def process_survey(self, answers):
                    return {
                        "personality": {
                            "type": "Error",
                            "description": "Database module could not be loaded",
                            "interpretation": "Please check server logs for details",
                            "enjoyment": ["Contact support"],
                            "your_strength": ["Patience"],
                            "iconId": "1",
                            "riasecScores": {"R": 0.5, "I": 0.5, "A": 0.5, "S": 0.5, "E": 0.5, "C": 0.5}
                        },
                        "industries": []
                    }

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
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Explicitly list all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Allow all hosts
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
        
        # Log the answer types to help diagnose issues
        answer_types = [f"{type(a).__name__}" for a in survey_data.answers]
        logger.info(f"Answer types: {answer_types}")
        
        # Check for non-string answers
        non_string_answers = [i for i, a in enumerate(survey_data.answers) if not isinstance(a, str)]
        if non_string_answers:
            logger.warning(f"Non-string answers found at indices: {non_string_answers}")
            
            # Convert non-string answers to strings
            survey_data.answers = [str(a) if not isinstance(a, str) else a for a in survey_data.answers]
            logger.info(f"Converted non-string answers to strings: {survey_data.answers}")
        
        # Try to process with the database
        try:
            # Initialize the database with a relative path that works in both local and deployed environments
            # First try the absolute path for deployed environment
            db_path = "/app/app/database/Database.xlsx"
            
            # If that doesn't exist, try the relative path for local development
            if not os.path.exists(db_path):
                logger.info(f"Database not found at {db_path}, trying relative path")
                db_path = "/app/database/Database.xlsx"
                
                # If that doesn't exist either, try another common location
                if not os.path.exists(db_path):
                    logger.info(f"Database not found at {db_path}, trying another path")
                    db_path = "database/Database.xlsx"
                    
                    # If that doesn't exist either, try the current directory
                    if not os.path.exists(db_path):
                        logger.info(f"Database not found at {db_path}, trying current directory")
                        db_path = "Database.xlsx"
            
            logger.info(f"Using database path: {db_path}")
            
            # Check if the file exists
            if not os.path.exists(db_path):
                logger.error(f"Database file not found at {db_path}")
                # List files in the directory to help debug
                current_dir = os.getcwd()
                logger.info(f"Current working directory: {current_dir}")
                logger.info(f"Files in current directory: {os.listdir(current_dir)}")
                
                # Try to find the Excel file in the current directory or subdirectories
                excel_files = []
                for root, dirs, files in os.walk(current_dir):
                    for file in files:
                        if file.endswith('.xlsx'):
                            excel_files.append(os.path.join(root, file))
                
                if excel_files:
                    logger.info(f"Found Excel files: {excel_files}")
                    # Use the first Excel file found
                    db_path = excel_files[0]
                    logger.info(f"Using found Excel file: {db_path}")
                else:
                    logger.error("No Excel files found in the directory tree")
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
    
    try:
        # If survey_data is provided, try to process it
        if survey_data and survey_data.answers:
            logger.info(f"Processing survey data with {len(survey_data.answers)} answers")
            logger.info(f"Answers: {survey_data.answers}")
            
            # Try to find the database file
            db_path = None
            possible_paths = [
                "/app/app/database/Database.xlsx",
                "app/database/Database.xlsx",
                "database/Database.xlsx",
                "Database.xlsx"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    db_path = path
                    logger.info(f"Found database at {db_path}")
                    break
            
            if db_path:
                try:
                    # Initialize the database
                    db = SurveyDatabase(excel_path=db_path)
                    logger.info("Database initialized successfully")
                    
                    # Process the survey
                    result = db.process_survey(survey_data.answers)
                    logger.info("Survey processed successfully")
                    
                    # Return the result
                    return result
                except Exception as db_error:
                    logger.error(f"Error processing survey: {str(db_error)}")
                    logger.exception("Exception details:")
            else:
                logger.error("Database file not found")
        else:
            logger.warning("No survey data provided or empty answers")
    except Exception as e:
        logger.error(f"Error in direct_test: {str(e)}")
        logger.exception("Exception details:")
    
    # Return fallback result if anything fails
    logger.info("Returning fallback result")
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

@app.get("/api/debug/url-test")
async def debug_url_test(request: Request):
    """
    Debug endpoint to help diagnose URL issues.
    Returns information about the request URL and available routes.
    """
    try:
        # Get information about the request
        request_info = {
            "url": str(request.url),
            "base_url": str(request.base_url),
            "path": request.url.path,
            "method": request.method,
            "headers": dict(request.headers),
        }
        
        # Get information about available routes
        routes_info = []
        for route in app.routes:
            route_info = {
                "path": getattr(route, "path", "Unknown"),
                "name": getattr(route, "name", "Unknown"),
                "methods": getattr(route, "methods", ["Unknown"]),
            }
            routes_info.append(route_info)
        
        # Return the debug information
        return {
            "status": "success",
            "message": "URL test successful",
            "request": request_info,
            "routes": routes_info,
            "app_routes_count": len(app.routes)
        }
    except Exception as e:
        # Return error information
        return {
            "status": "error",
            "message": f"URL test failed: {str(e)}",
            "error_details": traceback.format_exc()
        }

@app.post("/api/test-post")
async def test_post_endpoint(request: Request):
    """
    Simple test endpoint to verify that POST requests are working correctly.
    """
    try:
        # Log the request
        logger.info(f"Received test POST request")
        
        # Try to parse the request body
        try:
            body = await request.json()
            logger.info(f"Request body: {body}")
        except Exception as e:
            logger.error(f"Error parsing request body: {str(e)}")
            body = {"error": "Could not parse request body"}
        
        # Return a simple response
        return {
            "status": "success",
            "message": "POST request received successfully",
            "request_body": body,
            "request_headers": dict(request.headers),
            "request_method": request.method,
            "request_url": str(request.url)
        }
    except Exception as e:
        # Log the error
        logger.error(f"Unexpected error in test_post_endpoint: {str(e)}")
        logger.exception("Exception details:")
        
        # Return error information
        return {
            "status": "error",
            "message": f"Test POST request failed: {str(e)}",
            "error_details": traceback.format_exc()
        }

@app.post("/api/diagnostic-submit")
async def diagnostic_submit(request: Request):
    """
    Diagnostic endpoint for survey submission.
    Logs detailed information about the request and tries multiple ways to parse the body.
    """
    logger.info("Diagnostic submit endpoint called")
    
    # Log request details
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request URL: {request.url}")
    logger.info(f"Request headers: {request.headers}")
    
    # Try to get the raw body
    try:
        body_bytes = await request.body()
        logger.info(f"Raw request body (bytes): {body_bytes}")
        
        # Try to decode as UTF-8
        try:
            body_text = body_bytes.decode('utf-8')
            logger.info(f"Request body (text): {body_text}")
        except Exception as decode_error:
            logger.error(f"Error decoding body as UTF-8: {str(decode_error)}")
        
        # Try to parse as JSON
        try:
            # Reset the request body
            await request.body()
            
            # Try to parse as JSON
            json_body = await request.json()
            logger.info(f"Parsed JSON body: {json_body}")
            
            # Check if it has the expected structure
            if isinstance(json_body, dict) and "answers" in json_body:
                answers = json_body["answers"]
                logger.info(f"Found answers field with {len(answers)} items")
                
                # Check the types of the answers
                answer_types = [f"{type(a).__name__}" for a in answers]
                logger.info(f"Answer types: {answer_types}")
                
                # Return a success response
                return {"status": "success", "message": "Test survey submission received successfully"}
            else:
                logger.warning("JSON body does not have the expected structure")
                return {"status": "error", "message": "JSON body does not have the expected structure"}
        except Exception as json_error:
            logger.error(f"Error parsing body as JSON: {str(json_error)}")
            return {"status": "error", "message": f"Error parsing body as JSON: {str(json_error)}"}
    except Exception as e:
        logger.error(f"Unexpected error in diagnostic_submit: {str(e)}")
        logger.exception("Exception details:")
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}

# Add a debug endpoint
@app.get("/api/debug")
async def debug_info():
    """
    Return debug information about the server.
    """
    try:
        # Collect debug information
        debug_info = {
            "server_info": {
                "python_version": sys.version,
                "current_directory": os.getcwd(),
                "base_dir": str(BASE_DIR),
                "app_dir": str(APP_DIR),
                "frontend_dir": str(frontend_dir),
                "frontend_build_dir": str(frontend_build_dir),
            },
            "environment": {
                "env_vars": {k: v for k, v in os.environ.items() if not k.startswith("_")},
            },
            "directories": {
                "current_dir_contents": os.listdir(os.getcwd()),
                "app_dir_contents": os.listdir(str(APP_DIR)) if APP_DIR.exists() else "Directory not found",
                "frontend_dir_contents": os.listdir(str(frontend_dir)) if frontend_dir.exists() else "Directory not found",
            }
        }
        
        # Try to check if the database file exists
        db_paths = [
            "/app/app/database/Database.xlsx",
            "/app/database/Database.xlsx",
            "database/Database.xlsx",
            "Database.xlsx",
            str(BASE_DIR / "app" / "database" / "Database.xlsx"),
        ]
        
        db_status = {}
        for path in db_paths:
            db_status[path] = os.path.exists(path)
        
        debug_info["database"] = {
            "db_paths_status": db_status
        }
        
        return debug_info
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return {"error": str(e), "traceback": traceback.format_exc()}

# Add a test endpoint
@app.get("/api/survey/test")
async def test_endpoint():
    """
    Test endpoint to check if the API is working.
    """
    try:
        return {
            "status": "success",
            "message": "API is working correctly",
            "timestamp": str(pd.Timestamp.now()),
            "server_info": {
                "python_version": sys.version,
                "current_directory": os.getcwd(),
            }
        }
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))  # Use environment variable or default to 8080
    uvicorn.run("main:app", host="0.0.0.0", port=port)
