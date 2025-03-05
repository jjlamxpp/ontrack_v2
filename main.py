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
import pandas as pd

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
            sample_questions = [
                {
                    "id": 1,
                    "question_text": "I enjoy solving complex problems.",
                    "category": "analytical",
                    "options": ["Yes", "No"]
                },
                {
                    "id": 2,
                    "question_text": "I prefer working with people rather than data.",
                    "category": "social",
                    "options": ["Yes", "No"]
                },
                {
                    "id": 3,
                    "question_text": "I enjoy creative activities.",
                    "category": "artistic",
                    "options": ["Yes", "No"]
                },
                # Add more sample questions as needed
            ]
            
            logger.info(f"Returning {len(sample_questions)} sample questions")
            return sample_questions
        
        # Read questions from Excel file
        logger.info(f"Reading questions from Excel file: {excel_file}")
        try:
            # List all sheet names in the Excel file
            xls = pd.ExcelFile(excel_file)
            sheet_names = xls.sheet_names
            logger.info(f"Excel file sheets: {sheet_names}")
            
            # Try to read the 'Question pool' sheet
            sheet_name = 'Question pool'
            if sheet_name not in sheet_names:
                logger.warning(f"Sheet '{sheet_name}' not found. Available sheets: {sheet_names}")
                # Try to use the first sheet
                if sheet_names:
                    sheet_name = sheet_names[0]
                    logger.info(f"Using first available sheet: {sheet_name}")
                else:
                    raise ValueError("No sheets found in Excel file")
            
            # Read the sheet
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Log the columns and first few rows to help debug
            logger.info(f"Excel columns: {df.columns.tolist()}")
            logger.info(f"First row: {df.iloc[0].to_dict() if not df.empty else 'No data'}")
            
            # Check if DataFrame is empty
            if df.empty:
                logger.warning("Excel sheet is empty")
                raise ValueError("Excel sheet is empty")
            
            # Convert DataFrame to list of questions
            questions = []
            for index, row in df.iterrows():
                # Try to extract question text from the appropriate column
                question_text = None
                for col_name in ['Question', 'question', 'Question Text', 'question_text']:
                    if col_name in df.columns and not pd.isna(row.get(col_name, None)):
                        question_text = row[col_name]
                        break
                
                if question_text is None or pd.isna(question_text):
                    logger.warning(f"Skipping row {index} - no question text found")
                    continue
                
                # Try to extract category from the appropriate column
                category = "general"
                for cat_col in ['Category', 'category', 'Type', 'type']:
                    if cat_col in df.columns and not pd.isna(row.get(cat_col, None)):
                        category = str(row[cat_col])
                        break
                
                question = {
                    "id": int(index + 1),  # Use row index + 1 as ID
                    "question_text": str(question_text),
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
                    # ... industry data ...
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
    app.mount("/", StaticFiles(directory=str(frontend_build_dir), html=True))

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
