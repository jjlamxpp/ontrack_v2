import os
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SurveyDatabase:
    """Class to handle survey data processing using Excel database."""
    
    def __init__(self, excel_path: str = "/app/database/Database.xlsx"):
        """
        Initialize the database with the Excel file.
        
        Args:
            excel_path: Path to the Excel database file
        """
        self.excel_path = excel_path
        logger.info(f"Initializing SurveyDatabase with path: {excel_path}")
        
        # Check if the file exists
        if not os.path.exists(excel_path):
            logger.error(f"Excel file not found at {excel_path}")
            # Try to list files in the directory to help debug
            try:
                parent_dir = os.path.dirname(excel_path)
                if os.path.exists(parent_dir):
                    logger.info(f"Files in {parent_dir}: {os.listdir(parent_dir)}")
                else:
                    logger.error(f"Parent directory {parent_dir} does not exist")
            except Exception as e:
                logger.error(f"Error listing directory contents: {str(e)}")
            
            raise FileNotFoundError(f"Excel file not found at {excel_path}")
        
        try:
            # Load the Excel file with different possible sheet names
            logger.info(f"Loading Excel file from {excel_path}")
            
            # Get all sheet names in the Excel file
            all_sheets = pd.ExcelFile(excel_path).sheet_names
            logger.info(f"Available sheets in Excel file: {all_sheets}")
            
            # Try different possible sheet names for questions
            question_sheet_names = ["Questions", "Question pool", "Survey Questions"]
            self.df_questions = None
            for sheet_name in question_sheet_names:
                if sheet_name in all_sheets:
                    logger.info(f"Loading questions from sheet: {sheet_name}")
                    self.df_questions = pd.read_excel(excel_path, sheet_name=sheet_name)
                    break
            
            if self.df_questions is None:
                logger.error("Could not find a valid questions sheet")
                raise ValueError("No valid questions sheet found in Excel file")
            
            # Try different possible sheet names for personality
            personality_sheet_names = ["Personality", "Two digit", "Two Digit", "Personality Types"]
            self.df_personality = None
            for sheet_name in personality_sheet_names:
                if sheet_name in all_sheets:
                    logger.info(f"Loading personality data from sheet: {sheet_name}")
                    self.df_personality = pd.read_excel(excel_path, sheet_name=sheet_name)
                    break
            
            if self.df_personality is None:
                logger.error("Could not find a valid personality sheet")
                raise ValueError("No valid personality sheet found in Excel file")
            
            # Try different possible sheet names for industries
            industry_sheet_names = ["Industries", "Industry Insight", "Industry", "Career"]
            self.df_industries = None
            for sheet_name in industry_sheet_names:
                if sheet_name in all_sheets:
                    logger.info(f"Loading industry data from sheet: {sheet_name}")
                    self.df_industries = pd.read_excel(excel_path, sheet_name=sheet_name)
                    break
            
            if self.df_industries is None:
                logger.error("Could not find a valid industries sheet")
                raise ValueError("No valid industries sheet found in Excel file")
            
            logger.info("Excel file loaded successfully")
            
            # Log some basic info about the loaded data
            logger.info(f"Loaded {len(self.df_questions)} questions")
            logger.info(f"Loaded {len(self.df_personality)} personality types")
            logger.info(f"Loaded {len(self.df_industries)} industries")
            
            # Log column names to help with debugging
            logger.info(f"Questions sheet columns: {list(self.df_questions.columns)}")
            logger.info(f"Personality sheet columns: {list(self.df_personality.columns)}")
            logger.info(f"Industries sheet columns: {list(self.df_industries.columns)}")
            
        except Exception as e:
            logger.error(f"Error loading Excel file: {str(e)}")
            logger.exception("Exception details:")
            raise
    
    def process_survey(self, answers: List[str]) -> Dict[str, Any]:
        """
        Process survey answers and return personality analysis.
        
        Args:
            answers: List of survey answers (A, B, C, etc.)
            
        Returns:
            Dictionary with personality analysis and matching industries
        """
        try:
            logger.info(f"Processing survey with {len(answers)} answers")
            
            # Validate answers
            if not answers:
                logger.error("No answers provided")
                raise ValueError("No answers provided")
            
            # Normalize answers to uppercase
            answers = [a.upper() if isinstance(a, str) else a for a in answers]
            logger.info(f"Normalized answers: {answers}")
            
            # Check if we should use the ontrack_zh approach (yes/no answers)
            if all(a in ['YES', 'NO', 'Yes', 'No', 'yes', 'no'] for a in answers if isinstance(a, str)):
                logger.info("Using yes/no answer processing approach")
                return self._process_yes_no_survey(answers)
            
            # Calculate RIASEC scores
            riasec_scores = self._calculate_riasec_scores(answers)
            logger.info(f"Calculated RIASEC scores: {riasec_scores}")
            
            # Get top personality types
            personality_type = self._get_personality_type(riasec_scores)
            logger.info(f"Determined personality type: {personality_type}")
            
            # Get matching industries
            matching_industries = self._get_matching_industries(personality_type)
            logger.info(f"Found {len(matching_industries)} matching industries")
            
            # Return the result
            return {
                "personality": personality_type,
                "industries": matching_industries
            }
        except Exception as e:
            logger.error(f"Error processing survey: {str(e)}")
            logger.exception("Exception details:")
            raise
    
    def _process_yes_no_survey(self, answers: List[str]) -> Dict[str, Any]:
        """
        Process survey with yes/no answers (similar to ontrack_zh approach).
        
        Args:
            answers: List of survey answers (YES, NO, etc.)
            
        Returns:
            Dictionary with personality analysis and matching industries
        """
        try:
            # Initialize counters for each Holland code category
            category_counts = {
                'R': 0, 'I': 0, 'A': 0, 
                'S': 0, 'E': 0, 'C': 0
            }
            
            # Get questions with their categories
            questions = []
            for idx, row in self.df_questions.iterrows():
                # Try different possible column names for question text
                question_text = None
                for col in ['question_text', 'questions:', 'Question', 'questions', 'Questions']:
                    if col in self.df_questions.columns:
                        question_text = row[col]
                        break
                
                # Try different possible column names for category
                category = None
                for col in ['category', 'Category', 'holland_code', 'Holland Code', 'type']:
                    if col in self.df_questions.columns:
                        category = row[col]
                        break
                
                if question_text and category:
                    questions.append({
                        'id': idx,
                        'question_text': question_text,
                        'category': category
                    })
            
            # Count answers for each category from the survey
            for q_idx, answer in enumerate(answers):
                if q_idx < len(questions) and answer.upper() in ['YES', 'Y']:
                    category = questions[q_idx]['category']
                    if category in category_counts:
                        category_counts[category] += 1
            
            logger.info(f"Category counts: {category_counts}")
            
            # Find categories with maximum scores
            max_score = max(category_counts.values())
            max_cats = [cat for cat, count in category_counts.items() if count == max_score]
            
            # Find categories with second highest scores
            second_score = 0
            second_cats = []
            remaining_scores = [count for count in category_counts.values() if count < max_score]
            if remaining_scores:
                second_score = max(remaining_scores)
                second_cats = [cat for cat, count in category_counts.items() if count == second_score]
            
            # Find categories with third highest scores
            third_score = 0
            third_cats = []
            remaining_scores = [count for count in category_counts.values() if count < second_score]
            if remaining_scores:
                third_score = max(remaining_scores)
                third_cats = [cat for cat, count in category_counts.items() if count == third_score]
            
            # Generate two-digit code
            two_digit_code = ''.join(max_cats[:2]) if len(max_cats) >= 2 else (max_cats[0] + second_cats[0] if second_cats else max_cats[0] + 'X')
            
            # Get personality type based on two-digit code
            personality_type = self._get_personality_type_by_code(two_digit_code)
            
            # Calculate normalized RIASEC scores
            total_score = sum(category_counts.values())
            normalized_scores = {
                cat: count / max(1, max_score)  # Avoid division by zero
                for cat, count in category_counts.items()
            }
            
            # Add normalized scores to personality type
            personality_type['riasecScores'] = normalized_scores
            
            # Get matching industries
            matching_industries = self._get_matching_industries(personality_type)
            
            # Return the result
            return {
                "personality": personality_type,
                "industries": matching_industries
            }
        except Exception as e:
            logger.error(f"Error processing yes/no survey: {str(e)}")
            logger.exception("Exception details:")
            raise
    
    def _get_personality_type_by_code(self, code: str) -> Dict[str, Any]:
        """
        Get personality type information based on a two-digit code.
        
        Args:
            code: Two-digit Holland code (e.g., 'RI', 'SE', etc.)
            
        Returns:
            Dictionary with personality type information
        """
        try:
            # Try different possible column names for the code
            code_column = None
            for col in ['code', 'Code', 'Two digit code', 'Two Digit Code', 'Two-digit code', 'holland_code']:
                if col in self.df_personality.columns:
                    code_column = col
                    break
            
            if not code_column:
                logger.error("Could not find code column in personality dataframe")
                return self._get_default_personality()
            
            # Find the row with the matching code
            matching_rows = self.df_personality[self.df_personality[code_column].str.upper() == code.upper()]
            
            if matching_rows.empty:
                logger.warning(f"No personality type found for code: {code}")
                return self._get_default_personality()
            
            # Get the first matching row
            row = matching_rows.iloc[0]
            
            # Try different possible column names for each field
            personality = {}
            
            # Type/Role
            for col in ['type', 'Type', 'role', 'Role']:
                if col in self.df_personality.columns:
                    personality['type'] = row[col]
                    break
            if 'type' not in personality:
                personality['type'] = f"Holland Code: {code}"
            
            # Description
            for col in ['description', 'Description', 'who_you_are', 'Who you are', 'Who You Are']:
                if col in self.df_personality.columns:
                    personality['description'] = row[col]
                    break
            if 'description' not in personality:
                personality['description'] = "No description available"
            
            # Interpretation
            for col in ['interpretation', 'Interpretation', 'how_this_combination', 'How This Combination Interpret']:
                if col in self.df_personality.columns:
                    personality['interpretation'] = row[col]
                    break
            if 'interpretation' not in personality:
                personality['interpretation'] = "No interpretation available"
            
            # Enjoyment
            for col in ['enjoyment', 'Enjoyment', 'what_you_might_enjoy', 'What You Might Enjoy']:
                if col in self.df_personality.columns:
                    enjoyment_text = row[col]
                    if isinstance(enjoyment_text, str):
                        personality['enjoyment'] = self._parse_list(enjoyment_text)
                    else:
                        personality['enjoyment'] = ["No enjoyment data available"]
                    break
            if 'enjoyment' not in personality:
                personality['enjoyment'] = ["No enjoyment data available"]
            
            # Strengths
            for col in ['strengths', 'Strengths', 'your_strength', 'Your Strength', 'Your strengths']:
                if col in self.df_personality.columns:
                    strengths_text = row[col]
                    if isinstance(strengths_text, str):
                        personality['your_strength'] = self._parse_list(strengths_text)
                    else:
                        personality['your_strength'] = ["No strength data available"]
                    break
            if 'your_strength' not in personality:
                personality['your_strength'] = ["No strength data available"]
            
            # Icon ID
            for col in ['icon_id', 'Icon ID', 'Icon id', 'iconId']:
                if col in self.df_personality.columns:
                    personality['iconId'] = str(row[col])
                    break
            if 'iconId' not in personality:
                personality['iconId'] = "1"  # Default icon
            
            return personality
        except Exception as e:
            logger.error(f"Error getting personality type by code: {str(e)}")
            logger.exception("Exception details:")
            return self._get_default_personality()
    
    def _get_default_personality(self) -> Dict[str, Any]:
        """
        Get a default personality type when no match is found.
        
        Returns:
            Dictionary with default personality type information
        """
        return {
            "type": "Default Type",
            "description": "We couldn't determine your specific personality type based on your answers.",
            "interpretation": "Your answers indicate a unique combination of interests and preferences.",
            "enjoyment": ["Exploring different career options", "Learning about your strengths and interests"],
            "your_strength": ["Adaptability", "Unique perspective"],
            "iconId": "1"
        }
    
    def _calculate_riasec_scores(self, answers: List[str]) -> Dict[str, int]:
        """
        Calculate RIASEC scores based on survey answers.
        
        Args:
            answers: List of survey answers
            
        Returns:
            Dictionary with RIASEC scores
        """
        try:
            # Initialize scores
            scores = {"R": 0, "I": 0, "A": 0, "S": 0, "E": 0, "C": 0}
            
            # Map answers to questions
            for i, answer in enumerate(answers):
                if i >= len(self.df_questions):
                    logger.warning(f"Answer index {i} exceeds number of questions {len(self.df_questions)}")
                    continue
                    
                question = self.df_questions.iloc[i]
                
                # Get the RIASEC category for this question
                category = question.get('Category', '')
                if not category or category not in scores:
                    logger.warning(f"Invalid category '{category}' for question {i+1}")
                    continue
                
                # Map answer to score
                if answer == 'A':
                    scores[category] += 2
                elif answer == 'B':
                    scores[category] += 1
                # C and D don't add points
                
            return scores
        except Exception as e:
            logger.error(f"Error calculating RIASEC scores: {str(e)}")
            raise
    
    def _get_personality_type(self, riasec_scores: Dict[str, int]) -> Dict[str, Any]:
        """
        Get personality type based on RIASEC scores.
        
        Args:
            riasec_scores: Dictionary with RIASEC scores
            
        Returns:
            Dictionary with personality type information
        """
        try:
            # Sort scores to get top categories
            sorted_scores = sorted(riasec_scores.items(), key=lambda x: x[1], reverse=True)
            top_categories = ''.join([cat for cat, _ in sorted_scores[:2]])
            
            # Find matching personality type
            personality_match = self.df_personality[self.df_personality['Type'] == top_categories]
            
            if len(personality_match) == 0:
                logger.warning(f"No personality type found for {top_categories}, trying reversed")
                # Try reversed order
                reversed_top = top_categories[::-1]
                personality_match = self.df_personality[self.df_personality['Type'] == reversed_top]
                
                if len(personality_match) == 0:
                    logger.error(f"No personality type found for {top_categories} or {reversed_top}")
                    # Return a default personality type
                    return {
                        "type": top_categories,
                        "description": "You have a unique combination of traits.",
                        "interpretation": "Your personality profile shows a blend of different strengths.",
                        "enjoyment": ["Problem-solving", "Learning new skills"],
                        "your_strength": ["Adaptability", "Versatility"],
                        "iconId": "1",
                        "riasecScores": riasec_scores
                    }
            
            # Get the first match
            personality = personality_match.iloc[0]
            
            # Convert to dictionary
            return {
                "type": personality.get('Type', top_categories),
                "description": personality.get('Description', ''),
                "interpretation": personality.get('Interpretation', ''),
                "enjoyment": self._parse_list(personality.get('Enjoyment', '')),
                "your_strength": self._parse_list(personality.get('Your Strength', '')),
                "iconId": str(personality.get('IconId', 1)),
                "riasecScores": riasec_scores
            }
        except Exception as e:
            logger.error(f"Error getting personality type: {str(e)}")
            raise
    
    def _get_matching_industries(self, personality: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get industries that match the personality type.
        
        Args:
            personality: Dictionary with personality type information
            
        Returns:
            List of dictionaries with industry information
        """
        try:
            logger.info(f"Finding matching industries for personality type: {personality.get('type', 'Unknown')}")
            
            # Get the personality type code
            personality_type = personality.get('type', '').upper()
            
            # Try to extract a code from the personality type if it's embedded
            code_match = None
            if 'riasecScores' in personality:
                # Get the top two categories based on scores
                scores = personality['riasecScores']
                sorted_cats = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
                code_match = ''.join(sorted_cats[:2]) if len(sorted_cats) >= 2 else None
            
            # If we couldn't extract a code, try to find it in the personality data
            if not code_match:
                # Look for common code patterns in the personality type
                code_patterns = [
                    r'([RIASEC]{2})',  # Look for two consecutive RIASEC letters
                    r'Type: ([RIASEC]{2})',  # Look for "Type: XX"
                    r'Code: ([RIASEC]{2})'   # Look for "Code: XX"
                ]
                
                for pattern in code_patterns:
                    match = re.search(pattern, personality_type)
                    if match:
                        code_match = match.group(1)
                        break
            
            # If we still don't have a code, use the first two letters of the personality type
            if not code_match and len(personality_type) >= 2:
                first_two = personality_type[:2]
                if all(c in 'RIASEC' for c in first_two):
                    code_match = first_two
            
            # Get all industries
            industries = []
            
            # Try different approaches to match industries
            
            # 1. Try to match by code
            if code_match:
                logger.info(f"Matching industries by code: {code_match}")
                
                # Try different possible column names for the code
                code_columns = ['code', 'Code', 'holland_code', 'Holland Code', 'personality_code']
                
                for code_col in code_columns:
                    if code_col in self.df_industries.columns:
                        # Find industries with matching codes
                        matching_industries = self.df_industries[
                            self.df_industries[code_col].str.contains(code_match, case=False, na=False)
                        ]
                        
                        if not matching_industries.empty:
                            logger.info(f"Found {len(matching_industries)} industries matching code {code_match}")
                            break
                
                # If we found matching industries, process them
                if 'matching_industries' in locals() and not matching_industries.empty:
                    for _, row in matching_industries.iterrows():
                        industry = self._extract_industry_data(row)
                        if industry:
                            industries.append(industry)
            
            # 2. If we didn't find any industries by code, get the top N industries
            if not industries:
                logger.info("No industries matched by code, getting top industries")
                top_n = 3  # Number of industries to return
                
                for _, row in self.df_industries.head(top_n).iterrows():
                    industry = self._extract_industry_data(row)
                    if industry:
                        industries.append(industry)
            
            # If we still don't have any industries, return a default one
            if not industries:
                logger.warning("No industries found, returning default industry")
                industries = [{
                    "id": "1",
                    "name": "General Career Path",
                    "overview": "Based on your personality type, you might enjoy a variety of career paths.",
                    "trending": "Many fields are growing and offer opportunities for someone with your interests.",
                    "insight": "Consider exploring different industries to find what resonates with your personal values and strengths.",
                    "examplePaths": ["Research careers that match your interests", "Speak with a career counselor", "Try internships in different fields"],
                    "education": "Various educational paths can lead to fulfilling careers."
                }]
            
            logger.info(f"Returning {len(industries)} matching industries")
            return industries
            
        except Exception as e:
            logger.error(f"Error getting matching industries: {str(e)}")
            logger.exception("Exception details:")
            
            # Return a default industry
            return [{
                "id": "1",
                "name": "General Career Path",
                "overview": "Based on your personality type, you might enjoy a variety of career paths.",
                "trending": "Many fields are growing and offer opportunities for someone with your interests.",
                "insight": "Consider exploring different industries to find what resonates with your personal values and strengths.",
                "examplePaths": ["Research careers that match your interests", "Speak with a career counselor", "Try internships in different fields"],
                "education": "Various educational paths can lead to fulfilling careers."
            }]
    
    def _extract_industry_data(self, row) -> Dict[str, Any]:
        """
        Extract industry data from a DataFrame row.
        
        Args:
            row: DataFrame row with industry data
            
        Returns:
            Dictionary with industry information
        """
        try:
            industry = {}
            
            # Try different possible column names for each field
            
            # ID
            for col in ['id', 'ID', 'industry_id']:
                if col in row.index:
                    industry['id'] = str(row[col])
                    break
            if 'id' not in industry:
                industry['id'] = str(row.name + 1)  # Use row index + 1 as ID
            
            # Name
            for col in ['name', 'Name', 'industry', 'Industry']:
                if col in row.index:
                    industry['name'] = row[col]
                    break
            if 'name' not in industry:
                industry['name'] = "Unknown Industry"
            
            # Overview
            for col in ['overview', 'Overview', 'description', 'Description']:
                if col in row.index:
                    industry['overview'] = row[col]
                    break
            if 'overview' not in industry:
                industry['overview'] = "No overview available"
            
            # Trending
            for col in ['trending', 'Trending']:
                if col in row.index:
                    industry['trending'] = row[col]
                    break
            if 'trending' not in industry:
                industry['trending'] = "No trending information available"
            
            # Insight
            for col in ['insight', 'Insight', 'insights', 'Insights']:
                if col in row.index:
                    industry['insight'] = row[col]
                    break
            if 'insight' not in industry:
                industry['insight'] = "No insight available"
            
            # Example Paths
            for col in ['examplePaths', 'example_paths', 'career_path', 'Career Path', 'career_paths']:
                if col in row.index:
                    paths_text = row[col]
                    if isinstance(paths_text, str):
                        industry['examplePaths'] = self._parse_list(paths_text)
                    else:
                        industry['examplePaths'] = ["No example paths available"]
                    break
            if 'examplePaths' not in industry:
                industry['examplePaths'] = ["No example paths available"]
            
            # Education
            for col in ['education', 'Education']:
                if col in row.index:
                    industry['education'] = row[col]
                    break
            if 'education' not in industry:
                industry['education'] = "No education information available"
            
            return industry
            
        except Exception as e:
            logger.error(f"Error extracting industry data: {str(e)}")
            return None
    
    def _parse_list(self, text: str) -> List[str]:
        """
        Parse a string into a list of items.
        
        Args:
            text: String to parse
            
        Returns:
            List of strings
        """
        if not text or not isinstance(text, str):
            return []
        
        # Try different delimiters
        delimiters = ['\n', '//', '\\n', ';', ',']
        
        for delimiter in delimiters:
            if delimiter in text:
                # Split by delimiter and clean up each item
                items = [item.strip() for item in text.split(delimiter) if item.strip()]
                if items:
                    return items
        
        # If no delimiter was found, return the text as a single item
        return [text.strip()] 
