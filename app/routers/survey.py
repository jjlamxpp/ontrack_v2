from fastapi import APIRouter, HTTPException
from app.database.excel_db import SurveyDatabase
from app.schemas.models import Question, SurveyResponse, AnalysisResult
import logging
from fastapi.responses import FileResponse, JSONResponse
import os
from pathlib import Path
import shutil
import traceback
import pandas as pd
import json
from pydantic import BaseModel
from typing import List
import sys

# Add the parent directory to sys.path to allow importing from app.database
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Change the prefix to be empty since we're mounting at /api
router = APIRouter()
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize the database
database_path = BASE_DIR / "app" / "database" / "Database.xlsx"
survey_db = SurveyDatabase(database_path)

# Initialize icon directories
def init_icon_directories():
    # Updated paths without double 'app'
    static_dir = Path("static")
    icon_dir = static_dir / "icon"
    school_icon_dir = static_dir / "school_icon"

    # Create directories if they don't exist
    static_dir.mkdir(parents=True, exist_ok=True)
    icon_dir.mkdir(parents=True, exist_ok=True)
    school_icon_dir.mkdir(parents=True, exist_ok=True)

    # Copy default icons if they don't exist
    default_icon_path = icon_dir / "default.png"
    default_school_icon_path = school_icon_dir / "default.png"

    # Updated backup path
    backup_icon_dir = Path("backup/icons")
    if backup_icon_dir.exists():
        for icon_file in backup_icon_dir.glob("*.png"):
            target_path = icon_dir / icon_file.name
            if not target_path.exists():
                shutil.copy2(icon_file, target_path)

# Initialize directories when the module loads
init_icon_directories()

# Define the request model
class SurveyRequest(BaseModel):
    answers: List[str]

# Define the response models
class PersonalityAnalysis(BaseModel):
    type: str
    description: str
    interpretation: str
    enjoyment: List[str]
    your_strength: List[str]
    iconId: str
    riasecScores: dict

class IndustryRecommendation(BaseModel):
    id: str
    name: str
    overview: str
    trending: str
    insight: str
    examplePaths: List[str]
    education: str = None

class AnalysisResult(BaseModel):
    personality: PersonalityAnalysis
    industries: List[IndustryRecommendation]

# REMOVED: The submit_survey endpoint has been moved to main.py

@router.get("/survey/icon/{icon_id}")
async def get_icon(icon_id: str):
    """Get character icon by ID"""
    try:
        # Clean the icon_id to prevent path traversal
        clean_id = ''.join(c for c in icon_id if c.isalnum())
        
        # Try multiple possible locations for the icon
        possible_paths = [
            BASE_DIR / "static" / "icon" / f"{clean_id}.png",
            BASE_DIR / "app" / "static" / "icon" / f"{clean_id}.png",
            BASE_DIR / "static" / "icon" / "default.png",
            BASE_DIR / "app" / "static" / "icon" / "default.png"
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Serving icon from: {path}")
                return FileResponse(
                    path=str(path),
                    media_type="image/png",
                    filename=f"{clean_id}.png"
                )
        
        # If no icon found, return a 404
        logger.error(f"No icon found for ID: {clean_id}")
        logger.error(f"Searched paths: {[str(p) for p in possible_paths]}")
        raise HTTPException(status_code=404, detail="Icon not found")
            
    except Exception as e:
        logger.error(f"Error serving icon: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/survey/school-icon/{school_name}")
async def get_school_icon(school_name: str):
    """Get school icon by name"""
    try:
        # Clean the school name to prevent path traversal
        clean_name = school_name.lower().replace(' ', '-')
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c == '-')
        
        # Try multiple possible locations for the school icon
        possible_paths = [
            BASE_DIR / "static" / "school_icon" / f"{clean_name}.png",
            BASE_DIR / "app" / "static" / "school_icon" / f"{clean_name}.png",
            BASE_DIR / "static" / "school_icon" / "default.png",
            BASE_DIR / "app" / "static" / "school_icon" / "default.png"
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Serving school icon from: {path}")
                return FileResponse(
                    path=str(path),
                    media_type="image/png",
                    filename=f"{clean_name}.png"
                )
        
        # If no icon found, return a 404
        logger.error(f"No school icon found for: {clean_name}")
        logger.error(f"Searched paths: {[str(p) for p in possible_paths]}")
        raise HTTPException(status_code=404, detail="School icon not found")
            
    except Exception as e:
        logger.error(f"Error serving school icon: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/survey/test")
async def test_survey_api():
    """Test endpoint to verify API connectivity"""
    logger.info("Test survey API endpoint called")
    try:
        # Try to access the database
        db_methods = [method for method in dir(survey_db) if not method.startswith('__')]
        
        # Check if get_questions or get_all_questions exists
        has_get_questions = 'get_questions' in db_methods
        has_get_all_questions = 'get_all_questions' in db_methods
        
        # Try to get question count safely
        question_count = 0
        try:
            if has_get_all_questions:
                question_count = len(survey_db.get_all_questions())
            elif has_get_questions:
                question_count = len(survey_db.get_questions())
            else:
                # Direct Excel access as fallback
                df = pd.read_excel(database_path, sheet_name='Questions')
                question_count = len(df)
        except Exception as count_err:
            logger.error(f"Error getting question count: {str(count_err)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok",
                "message": "Survey API is working",
                "question_count": question_count,
                "database_path": database_path,
                "database_exists": os.path.exists(database_path),
                "available_methods": db_methods,
                "has_get_questions": has_get_questions,
                "has_get_all_questions": has_get_all_questions
            }
        )
    except Exception as e:
        logger.error(f"Test API error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "database_path": database_path,
                "database_exists": os.path.exists(database_path),
                "traceback": traceback.format_exc()
            }
        )
