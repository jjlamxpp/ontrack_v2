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
        # Get the basic results from your database
        basic_result = db.process_basic_results(response.answers)
        
        # Get personality type data
        personality_data = basic_result.get("personality_type", {})
        
        # Calculate RIASEC scores (normalized between 0 and 1)
        category_counts = basic_result.get("category_counts", {})
        max_score = max(category_counts.values()) if category_counts.values() else 1
        riasec_scores = {
            category: count / max_score
            for category, count in category_counts.items()
        }

        # Get unique industries based on industry name
        seen_industries = set()
        unique_industries = []
        for industry in basic_result.get("recommended_industries", []):
            industry_name = industry.get("industry")
            if industry_name and industry_name not in seen_industries:
                seen_industries.add(industry_name)
                unique_industries.append(industry)

        def parse_jupas_info(jupas_str):
            try:
                if not jupas_str:
                    return None
                    
                # Remove extra whitespace and split by '//'
                parts = [part.strip() for part in jupas_str.split('//') if part.strip()]
                
                if len(parts) >= 4:  # We expect 4 parts: subject, code, school, score
                    jupas_info = {
                        "subject": parts[0],
                        "jupasCode": parts[1],
                        "school": parts[2],
                        "averageScore": f"{parts[3]}/7.0"
                    }
                    return jupas_info
                else:
                    return None
                    
            except Exception as e:
                return None

        def parse_career_paths(career_paths):
            if not career_paths:
                return []
            
            # If it's already a list, return it directly
            if isinstance(career_paths, list):
                return [path.strip() for path in career_paths if path.strip()]
            
            # If it's a string, split it by '//'
            if isinstance(career_paths, str):
                return [path.strip() for path in career_paths.split('//') if path.strip()]
            
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
                    "overview": industry.get("description", "No overview available"),
                    "trending": industry.get("trending", "No trending information available"),
                    "insight": industry.get("insight", "No insight available"),
                    "examplePaths": parse_career_paths(industry.get("career_path", [])),
                    "education": industry.get("education", ""),
                    "jupasInfo": parse_jupas_info(industry.get("education", ""))
                }
                for idx, industry in enumerate(unique_industries)
            ]
        }

        return analysis_result

    except Exception as e:
        import traceback
        traceback.print_exc()  # This will print the full stack trace
        raise HTTPException(
            status_code=500,
            detail=f"Error processing survey: {str(e)}"
        )

@router.get("/icon/{filename}")
async def get_icon(filename: str):
    try:
        # Ensure filename ends with .png
        if not filename.endswith('.png'):
            filename = f"{filename}.png"
            
        # Clean the filename
        clean_filename = filename.replace(' ', '').replace('HTTP', '').strip()
        
        # Construct the full path
        icon_path = BASE_DIR / "app" / "static" / "icon" / clean_filename
        default_icon = BASE_DIR / "app" / "static" / "icon" / "default.png"
        
        print(f"Looking for icon at: {icon_path}")
        
        if icon_path.exists():
            return FileResponse(
                path=str(icon_path),
                media_type="image/png",
                filename=clean_filename
            )
        else:
            print(f"Icon not found at {icon_path}, using default")
            if default_icon.exists():
                return FileResponse(
                    path=str(default_icon),
                    media_type="image/png",
                    filename="default.png"
                )
            raise HTTPException(status_code=404, detail="Icon not found")
            
    except Exception as e:
        print(f"Error serving icon: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/school-icon/{filename}")
async def get_school_logo(filename: str):
    try:
        # Ensure filename ends with .png
        if not filename.endswith('.png'):
            filename = f"{filename}.png"
            
        # Clean the filename
        clean_filename = filename.lower().replace(' ', '-').replace('http', '').strip()
        
        # Construct the full path
        logo_path = BASE_DIR / "app" / "static" / "school_icon" / clean_filename
        default_logo = BASE_DIR / "app" / "static" / "school_icon" / "default.png"
        
        print(f"Looking for school logo at: {logo_path}")
        
        if logo_path.exists():
            return FileResponse(
                path=str(logo_path),
                media_type="image/png",
                filename=clean_filename
            )
        else:
            print(f"School logo not found at {logo_path}, using default")
            if default_logo.exists():
                return FileResponse(
                    path=str(default_logo),
                    media_type="image/png",
                    filename="default.png"
                )
            raise HTTPException(status_code=404, detail="School logo not found")
            
    except Exception as e:
        print(f"Error serving school logo: {e}")
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
