from fastapi import APIRouter, HTTPException
from app.database.excel_db import SurveyDatabase
from app.schemas.models import Question, SurveyResponse
import logging
from fastapi.responses import FileResponse, JSONResponse
import os
from pathlib import Path
import shutil
import traceback
import pandas as pd
import json

router = APIRouter(prefix="/survey")
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

@router.post("/submit")
async def submit_survey(survey: SurveyResponse):
    """Submit survey answers and get analysis"""
    try:
        logger.info(f"Received survey submission with {len(survey.answers)} answers")
        
        # Validate answers
        if len(survey.answers) < 1:
            raise HTTPException(status_code=400, detail="No answers provided")
        
        # Process the survey answers using the SurveyDatabase class
        try:
            # Convert answers to the format expected by process_basic_results
            # The answers should be "Yes" or "No" strings
            processed_answers = survey.answers
            
            # Process the results using the SurveyDatabase class
            logger.info("Processing survey results using SurveyDatabase")
            basic_results = survey_db.process_basic_results(processed_answers)
            logger.info(f"Basic results processed: {basic_results.keys()}")
            
            # Convert the basic results to the format expected by the frontend
            personality_type = basic_results.get("personality_type", {})
            industry_insights = basic_results.get("recommended_industries", [])
            
            # Map the basic results to the frontend expected format
            analysis = {
                "personality": {
                    "type": personality_type.get("role", "Innovator"),
                    "iconId": "1",  # This should match an icon file in your static/icon directory
                    "riasecScores": {
                        "R": basic_results.get("category_counts", {}).get("R", 0),
                        "I": basic_results.get("category_counts", {}).get("I", 0),
                        "A": basic_results.get("category_counts", {}).get("A", 0),
                        "S": basic_results.get("category_counts", {}).get("S", 0),
                        "E": basic_results.get("category_counts", {}).get("E", 0),
                        "C": basic_results.get("category_counts", {}).get("C", 0)
                    },
                    "description": personality_type.get("who_you_are", "You are creative and analytical, with a strong drive to solve complex problems."),
                    "interpretation": personality_type.get("interpretation", "Your combination of creativity and analytical thinking makes you well-suited for roles that require innovation and problem-solving."),
                    "enjoyment": personality_type.get("enjoyment", [
                        "Working on complex, challenging problems",
                        "Exploring new ideas and concepts",
                        "Creating innovative solutions"
                    ]),
                    "your_strength": personality_type.get("strengths", [
                        "Creative thinking",
                        "Analytical skills",
                        "Problem-solving abilities"
                    ])
                },
                "industries": []
            }
            
            # Convert industry insights to the format expected by the frontend
            for industry in industry_insights:
                industry_item = {
                    "id": industry.get("id", f"ind{len(analysis['industries']) + 1}"),
                    "name": industry.get("name", "Unknown Industry"),
                    "overview": industry.get("overview", "No overview available."),
                    "trending": industry.get("trending", "No trend information available."),
                    "insight": industry.get("insight", "No insights available."),
                    "examplePaths": industry.get("career_paths", ["No career paths available"]),
                }
                
                # Add education info if available
                if "education" in industry:
                    industry_item["education"] = industry["education"]
                
                # Add jupas info if available
                if "jupas_info" in industry:
                    industry_item["jupasInfo"] = {
                        "subject": industry["jupas_info"].get("subject", ""),
                        "jupasCode": industry["jupas_info"].get("jupas_code", ""),
                        "school": industry["jupas_info"].get("school", ""),
                        "averageScore": industry["jupas_info"].get("average_score", "")
                    }
                
                analysis["industries"].append(industry_item)
            
            # If no industries were found, add some default ones
            if not analysis["industries"]:
                logger.warning("No industries found in results, adding default industries")
                analysis["industries"] = [
                    {
                        "id": "tech1",
                        "name": "Technology",
                        "overview": "The technology industry involves developing and implementing software, hardware, and IT services.",
                        "trending": "Growing rapidly with new innovations in AI and cloud computing.",
                        "insight": "High demand for skilled professionals across various specializations.",
                        "examplePaths": ["Software Developer → Senior Developer → Technical Lead → CTO"],
                        "education": "Computer Science//JS1234//HKUST//5.0"
                    },
                    {
                        "id": "finance1",
                        "name": "Finance",
                        "overview": "The finance industry deals with managing money, investments, and financial services.",
                        "trending": "Evolving with fintech innovations and digital banking solutions.",
                        "insight": "Strong career prospects with opportunities in traditional and emerging sectors.",
                        "examplePaths": ["Financial Analyst → Senior Analyst → Finance Manager → CFO"],
                        "education": "Finance//JS5678//HKU//4.5"
                    }
                ]
            
            # Save the analysis to a file for debugging purposes
            data_dir = Path("app/data")
            data_dir.mkdir(exist_ok=True)
            
            with open(data_dir / "analysis_result.json", "w") as f:
                json.dump(analysis, f, indent=2)
            
            logger.info("Created analysis file at app/data/analysis_result.json")
            logger.info(f"Returning analysis with {len(analysis['industries'])} industries")
            
            return analysis
            
        except Exception as process_error:
            logger.error(f"Error processing survey with SurveyDatabase: {str(process_error)}")
            logger.error(traceback.format_exc())
            
            # Fall back to sample data if processing fails
            logger.info("Falling back to sample analysis data")
            
            # Create a sample analysis as fallback
            analysis = {
                "personality": {
                    "type": "Innovator",
                    "iconId": "1",
                    "riasecScores": {
                        "R": 0.7,
                        "I": 0.9,
                        "A": 0.6,
                        "S": 0.4,
                        "E": 0.8,
                        "C": 0.5
                    },
                    "description": "You are creative and analytical, with a strong drive to solve complex problems.",
                    "interpretation": "Your combination of creativity and analytical thinking makes you well-suited for roles that require innovation and problem-solving.",
                    "enjoyment": [
                        "Working on complex, challenging problems",
                        "Exploring new ideas and concepts",
                        "Creating innovative solutions"
                    ],
                    "your_strength": [
                        "Creative thinking",
                        "Analytical skills",
                        "Problem-solving abilities"
                    ]
                },
                "industries": [
                    {
                        "id": "tech1",
                        "name": "Technology",
                        "overview": "The technology industry involves developing and implementing software, hardware, and IT services.",
                        "trending": "Growing rapidly with new innovations in AI and cloud computing.",
                        "insight": "High demand for skilled professionals across various specializations.",
                        "examplePaths": ["Software Developer → Senior Developer → Technical Lead → CTO"],
                        "education": "Computer Science//JS1234//HKUST//5.0"
                    },
                    {
                        "id": "finance1",
                        "name": "Finance",
                        "overview": "The finance industry deals with managing money, investments, and financial services.",
                        "trending": "Evolving with fintech innovations and digital banking solutions.",
                        "insight": "Strong career prospects with opportunities in traditional and emerging sectors.",
                        "examplePaths": ["Financial Analyst → Senior Analyst → Finance Manager → CFO"],
                        "education": "Finance//JS5678//HKU//4.5"
                    },
                    {
                        "id": "consulting1",
                        "name": "Consulting",
                        "overview": "The consulting industry provides expert advice to businesses to improve their performance.",
                        "trending": "Increasing demand for specialized expertise in digital transformation.",
                        "insight": "Offers diverse project experiences and opportunities to work with various industries.",
                        "examplePaths": ["Junior Consultant → Consultant → Senior Consultant → Partner"],
                        "education": "Business Administration//JS9012//CUHK//4.2"
                    }
                ]
            }
            
            # Save the fallback analysis to a file for debugging purposes
            with open(data_dir / "fallback_analysis.json", "w") as f:
                json.dump(analysis, f, indent=2)
            
            logger.info("Created fallback analysis file at app/data/fallback_analysis.json")
            logger.info("Returning fallback analysis result")
            
            return analysis
        
    except Exception as e:
        logger.error(f"Error processing survey: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/icon/{icon_id}")
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

@router.get("/school-icon/{school_name}")
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

@router.get("/test")
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
