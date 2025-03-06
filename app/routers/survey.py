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

router = APIRouter()

# Use environment variable for database path
database_path = "app/database/Database.xlsx"
db = SurveyDatabase(database_path)

# Get BASE_DIR from environment variable
BASE_DIR = Path(os.environ.get("BASE_DIR", ".")).resolve()

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

# Add this line at the top to initialize the logger
logger = logging.getLogger(__name__)

@router.get("/questions")
async def get_questions():
    try:
        logger.info(f"Attempting to get questions from database at {database_path}")
        logger.info(f"Database file exists: {os.path.exists(database_path)}")
        
        # Try to open the database file to verify access
        try:
            with open(database_path, 'rb') as f:
                logger.info(f"Successfully opened database file, size: {len(f.read())} bytes")
        except Exception as e:
            logger.error(f"Failed to open database file: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": f"Failed to open database file: {str(e)}"}
            )
        
        # Try both methods to be safe
        try:
            # First try get_all_questions (your original method)
            questions = db.get_all_questions()
        except AttributeError:
            # If that fails, try direct pandas access as a fallback
            try:
                logger.info("Falling back to direct Excel access")
                df = pd.read_excel(database_path, sheet_name='Questions')
                questions = df.to_dict('records')
                
                # Add id field if not present
                for i, q in enumerate(questions):
                    if 'id' not in q:
                        q['id'] = i + 1
            except Exception as excel_err:
                logger.error(f"Failed to read Excel file directly: {str(excel_err)}")
                raise excel_err
        
        logger.info(f"Successfully fetched {len(questions)} questions")
        return questions
    except Exception as e:
        logger.error(f"Error fetching questions: {str(e)}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error fetching questions: {str(e)}"}
        )

# Add a debug endpoint to check database access
@router.get("/debug-db")
async def debug_database():
    try:
        result = {
            "database_path": database_path,
            "database_exists": os.path.exists(database_path),
            "database_size": None,
            "db_methods": dir(db),
            "excel_sheets": None
        }
        
        # Check if file exists and get size
        if os.path.exists(database_path):
            result["database_size"] = os.path.getsize(database_path)
            
            # Try to read Excel sheets
            try:
                xls = pd.ExcelFile(database_path)
                result["excel_sheets"] = xls.sheet_names
                
                # Try to read Questions sheet
                if 'Questions' in xls.sheet_names:
                    df = pd.read_excel(database_path, sheet_name='Questions')
                    result["questions_count"] = len(df)
                    result["questions_columns"] = df.columns.tolist()
                    result["sample_question"] = df.iloc[0].to_dict() if not df.empty else None
            except Exception as e:
                result["excel_error"] = str(e)
        
        return result
    except Exception as e:
        logger.error(f"Debug database error: {str(e)}")
        return {"error": str(e), "traceback": traceback.format_exc()}

@router.post("/submit")
async def submit_survey(response: SurveyResponse):
    try:
        # Log the received answers
        logger.info(f"Received survey answers: {response.answers}")
        
        # Get the basic results from your database
        basic_result = db.process_basic_results(response.answers)
        
        # Log the basic result for debugging
        logger.info(f"Basic result keys: {basic_result.keys()}")
        
        # Get personality type data
        personality_data = basic_result.get("personality_type", {})
        logger.info(f"Personality data: {personality_data}")
        
        # Calculate RIASEC scores (normalized between 0 and 1)
        category_counts = basic_result.get("category_counts", {})
        max_score = max(category_counts.values()) if category_counts.values() else 1
        riasec_scores = {
            category: count / max_score
            for category, count in category_counts.items()
        }
        logger.info(f"RIASEC scores: {riasec_scores}")

        # Get unique industries based on industry name
        seen_industries = set()
        unique_industries = []
        for industry in basic_result.get("recommended_industries", []):
            industry_name = industry.get("industry")
            if industry_name and industry_name not in seen_industries:
                seen_industries.add(industry_name)
                unique_industries.append(industry)
        
        logger.info(f"Found {len(unique_industries)} unique industries")

        def parse_career_paths(career_paths):
            if not career_paths:
                return []
            
            # If it's already a list, return it directly
            if isinstance(career_paths, list):
                return [path.strip() for path in career_paths if path.strip()]
            
            # If it's a string, split it by '//'
            if isinstance(career_paths, str):
                paths = [path.strip() for path in career_paths.split('//') if path.strip()]
                logger.info(f"Parsed {len(paths)} career paths from string")
                return paths
            
            logger.warning(f"Unexpected career_paths type: {type(career_paths)}")
            return []

        # Format the analysis result
        analysis_result = {
            "personality": {
                "type": personality_data.get("role", "Default Type"),
                "description": personality_data.get("who_you_are", "Default description"),
                "interpretation": personality_data.get("how_this_combination", "Default interpretation"),
                "enjoyment": parse_career_paths(personality_data.get("what_you_might_enjoy", ["No enjoyment data available"])),
                "your_strength": parse_career_paths(personality_data.get("your_strength", ["No strength data available"])),
                "iconId": personality_data.get("icon_id", "1"),
                "riasecScores": riasec_scores
            },
            "industries": [
                {
                    "id": str(idx + 1),
                    "name": industry.get("industry", "Unknown Industry"),
                    "overview": industry.get("overview", "No overview available"),
                    "trending": industry.get("trending", "No trending information available"),
                    "insight": industry.get("insight", "No insight available"),
                    "examplePaths": parse_career_paths(industry.get("example_role", [])),
                    "education": industry.get("jupas", "")
                }
                for idx, industry in enumerate(unique_industries)
            ]
        }

        # Log the final analysis result structure
        logger.info(f"Analysis result structure: {list(analysis_result.keys())}")
        logger.info(f"Personality keys: {list(analysis_result['personality'].keys())}")
        logger.info(f"Industries count: {len(analysis_result['industries'])}")
        
        return analysis_result

    except Exception as e:
        import traceback
        logger.error(f"Error processing survey: {str(e)}")
        logger.error(traceback.format_exc())  # Log the full stack trace
        raise HTTPException(
            status_code=500,
            detail=f"Error processing survey: {str(e)}"
        )

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
        db_methods = [method for method in dir(db) if not method.startswith('__')]
        
        # Check if get_questions or get_all_questions exists
        has_get_questions = 'get_questions' in db_methods
        has_get_all_questions = 'get_all_questions' in db_methods
        
        # Try to get question count safely
        question_count = 0
        try:
            if has_get_all_questions:
                question_count = len(db.get_all_questions())
            elif has_get_questions:
                question_count = len(db.get_questions())
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
