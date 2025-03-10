import pandas as pd
from pathlib import Path
from itertools import permutations
from typing import List, Dict
import numpy as np

class SurveyDatabase:
    def __init__(self, excel_path: str = '/app/database/Database.xlsx'):
        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found at {excel_path}")
        
        try:
            print(f"Loading Excel file from {excel_path}")
            
            # Read all required sheets with error handling
            try:
                self.df = pd.read_excel(
                    self.excel_path, 
                    sheet_name="Question pool",
                    engine='openpyxl'
                )
                print(f"Successfully loaded Question pool sheet with {len(self.df)} rows")
                print(f"Question pool columns: {self.df.columns.tolist()}")
            except Exception as e:
                print(f"Error loading Question pool sheet: {str(e)}")
                self.df = pd.DataFrame()  # Empty DataFrame as fallback
            
            try:
                self.two_digit_df = pd.read_excel(
                    self.excel_path, 
                    sheet_name="Two digit",
                    engine='openpyxl'
                )
                print(f"Successfully loaded Two digit sheet with {len(self.two_digit_df)} rows")
                print(f"Two digit columns: {self.two_digit_df.columns.tolist()}")
            except Exception as e:
                print(f"Error loading Two digit sheet: {str(e)}")
                self.two_digit_df = pd.DataFrame()  # Empty DataFrame as fallback
            
            try:
                self.industry_df = pd.read_excel(
                    self.excel_path, 
                    sheet_name="Industry Insight",
                    engine='openpyxl'
                )
                print(f"Successfully loaded Industry Insight sheet with {len(self.industry_df)} rows")
                print(f"Industry Insight columns: {self.industry_df.columns.tolist()}")
            except Exception as e:
                print(f"Error loading Industry Insight sheet: {str(e)}")
                self.industry_df = pd.DataFrame()  # Empty DataFrame as fallback
            
            # Check if any of the DataFrames are empty
            if self.df.empty:
                print("Warning: Question pool DataFrame is empty")
            if self.two_digit_df.empty:
                print("Warning: Two digit DataFrame is empty")
            if self.industry_df.empty:
                print("Warning: Industry Insight DataFrame is empty")
            
            # Instead of raising errors for missing columns, just log warnings
            # Check Industry sheet with detailed error message
            required_industry_types = {
                'mapping': ['Three digital', 'Three Digital', 'Mapping Code', 'Matching code'],
                'industry': ['Industry', 'industry'],
                'overview': ['Overview', 'overview', 'Description', 'description'],
                'trending': ['Trending', 'trending'],
                'insight': ['Insight', 'insight'],
                'skills': ['Required Skills', 'Required Skill', 'required skills'],
                'role': ['Example Role', 'Example role', 'example role', 'Career path'],
                'jupas': ['Jupas', 'JUPAS', 'jupas', 'Education', 'education']
            }
            
            missing_industry_types = []
            for col_type, variants in required_industry_types.items():
                if not any(variant in self.industry_df.columns for variant in variants):
                    missing_industry_types.append(col_type)
            
            if missing_industry_types:
                print(f"Warning: Missing Industry column types: {missing_industry_types}")
                print("Available Industry columns:", list(self.industry_df.columns))
            
            # Define required columns with variations
            required_columns = {
                'Question pool': ['questions:', 'Questions', 'questions', 'category', 'Category'],
                'Two digit': [
                    'Two digit code', 'Two Digit Code', 'Two-digit code',
                    'Role', 'role',
                    'icon_id', 'Icon ID', 'Icon id',
                    'Who you are?', 'Who You Are', 'Who you are',
                    'How This Combination Interpret', 'How This Combination Interprets',
                    'What You Might Enjoy', 'What you might enjoy',
                    'Your strength', 'Your Strength', 'Your strengths'
                ],
                'Industry': [
                    'Matching code', 'Three digital', 'Three Digital', 'Mapping Code',
                    'Industry', 'industry',
                    'Description', 'description', 'Overview', 'overview',
                    'Trending', 'trending',
                    'Insight', 'insight',
                    'Career path', 'Example Role', 'Example role',
                    'Education', 'education', 'Jupas', 'JUPAS'
                ]
            }
            
            # Check Question pool sheet - just log warnings
            missing_question_cols = []
            for col in ['questions:', 'Questions', 'questions']:
                if col in self.df.columns:
                    break
            else:
                missing_question_cols.append('questions')
            
            for col in ['category', 'Category']:
                if col in self.df.columns:
                    break
            else:
                missing_question_cols.append('category')
            
            if missing_question_cols:
                print(f"Warning: Missing required columns in Question pool sheet: {missing_question_cols}")
                print("Available Question pool columns:", list(self.df.columns))
            
            # Check Two digit sheet - just log warnings
            missing_two_digit_cols = []
            for col_group in [
                ['Two digit code', 'Two Digit Code', 'Two-digit code'],
                ['Role', 'role'],
                ['icon_id', 'Icon ID', 'Icon id'],
                ['Who you are?', 'Who You Are', 'Who you are'],
                ['How This Combination Interpret', 'How This Combination Interprets'],
                ['What You Might Enjoy', 'What you might enjoy'],
                ['Your strength', 'Your Strength', 'Your strengths']
            ]:
                if not any(col in self.two_digit_df.columns for col in col_group):
                    missing_two_digit_cols.append(col_group[0])
            
            if missing_two_digit_cols:
                print(f"Warning: Missing required columns in Two digit sheet: {missing_two_digit_cols}")
                print("Available Two digit columns:", list(self.two_digit_df.columns))
            
            # Check Industry sheet - just log warnings
            missing_industry_cols = []
            for col_group in [
                ['Matching code', 'Three digital', 'Three Digital', 'Mapping Code'],
                ['Industry', 'industry'],
                ['Description', 'description', 'Overview', 'overview'],
                ['Trending', 'trending'],
                ['Insight', 'insight'],
                ['Career path', 'Example Role', 'Example role'],
                ['Education', 'education', 'Jupas', 'JUPAS']
            ]:
                if not any(col in self.industry_df.columns for col in col_group):
                    missing_industry_cols.append(col_group[0])
            
            if missing_industry_cols:
                print(f"Warning: Missing required columns in Industry sheet: {missing_industry_cols}")
                print("Available Industry columns:", list(self.industry_df.columns))
            
        except Exception as e:
            print(f"Error reading Excel file: {str(e)}")
            import traceback
            print(traceback.format_exc())
            # Initialize empty DataFrames as fallback
            self.df = pd.DataFrame()
            self.two_digit_df = pd.DataFrame()
            self.industry_df = pd.DataFrame()

    def get_all_questions(self):
        """Get all questions from the database"""
        try:
            questions = []
            
            # Check if the DataFrame is loaded
            if self.df is None or self.df.empty:
                print("Warning: Question pool DataFrame is empty or None")
                return []
            
            # Log the columns in the DataFrame
            print(f"Question pool columns: {self.df.columns.tolist()}")
            
            # Check if required columns exist
            if 'questions:' not in self.df.columns:
                print("Warning: 'questions:' column not found in DataFrame")
                # Try to find a similar column
                question_cols = [col for col in self.df.columns if 'question' in col.lower()]
                if question_cols:
                    print(f"Found alternative question column: {question_cols[0]}")
                    question_col = question_cols[0]
                else:
                    print("No question column found")
                    return []
            else:
                question_col = 'questions:'
            
            # Check if category column exists
            if 'category' not in self.df.columns:
                print("Warning: 'category' column not found in DataFrame")
                # Try to find a similar column
                category_cols = [col for col in self.df.columns if 'category' in col.lower() or 'type' in col.lower()]
                if category_cols:
                    print(f"Found alternative category column: {category_cols[0]}")
                    category_col = category_cols[0]
                else:
                    print("No category column found, using default category")
                    category_col = None
            else:
                category_col = 'category'
            
            # Process each row in the DataFrame
            for index, row in self.df.iterrows():
                question_text = row.get(question_col, '')
                
                # Skip empty questions
                if not question_text or pd.isna(question_text):
                    continue
                
                # Parse the question text
                if isinstance(question_text, str):
                    # Try to extract the actual question text
                    import re
                    match = re.search(r'"([^"]*)"', question_text)
                    if match:
                        question_text = match.group(1)
                    else:
                        # Try with single quotes if double quotes not found
                        match = re.search(r"'([^']*)'", question_text)
                        if match:
                            question_text = match.group(1)
                        else:
                            # If no quotes found, try to extract after "question:"
                            parts = question_text.split("question:")
                            if len(parts) > 1:
                                question_text = parts[1].strip().strip('"').strip("'")
                
                # Get category
                category = row.get(category_col, 'general') if category_col else 'general'
                if pd.isna(category):
                    category = 'general'
                
                # Create question object
                question = {
                    "id": int(index + 1),  # Use row index + 1 as ID
                    "question_text": question_text,
                    "category": category,
                    "options": ["Yes", "No"]
                }
                
                questions.append(question)
            
            print(f"Loaded {len(questions)} questions from database")
            return questions
            
        except Exception as e:
            print(f"Error in get_all_questions: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return []

    def _get_two_digit_mapping(self, two_digit_code: str) -> Dict:
        """Get the mapping for a two-digit code"""
        try:
            print(f"Looking up two-digit code: {two_digit_code}")
            
            # Ensure we have a valid code
            if not two_digit_code or len(two_digit_code) != 2:
                print(f"Warning: Invalid two-digit code: {two_digit_code}")
                return self._get_default_personality()
            
            # Try to find the exact code
            for _, row in self.two_digit_df.iterrows():
                # Get the code from the row, handling different column names
                code = None
                for col_name in ['Two digit code', 'Two Digit Code', 'Two-digit code']:
                    if col_name in self.two_digit_df.columns:
                        code = row.get(col_name)
                        if code:
                            break
                
                if not code:
                    continue
                
                # Normalize the code for comparison
                if isinstance(code, str) and code.strip() == two_digit_code:
                    print(f"Found exact match for code: {two_digit_code}")
                    return self._extract_personality_from_row(row)
            
            # If no exact match, try to find a code with the same characters in any order
            for _, row in self.two_digit_df.iterrows():
                code = None
                for col_name in ['Two digit code', 'Two Digit Code', 'Two-digit code']:
                    if col_name in self.two_digit_df.columns:
                        code = row.get(col_name)
                        if code:
                            break
                
                if not code:
                    continue
                
                # Check if the code contains the same characters (in any order)
                if isinstance(code, str) and sorted(code.strip()) == sorted(two_digit_code):
                    print(f"Found match with same characters for code: {two_digit_code}")
                    return self._extract_personality_from_row(row)
            
            # If still no match, return a default personality
            print(f"No match found for code: {two_digit_code}, using default")
            return self._get_default_personality()
            
        except Exception as e:
            print(f"Error in _get_two_digit_mapping: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return self._get_default_personality()
    
    def _extract_personality_from_row(self, row) -> Dict:
        """Extract personality information from a row in the two_digit_df"""
        try:
            # Initialize with default values
            personality = {
                "code": "XX",
                "role": "Default Role",
                "who_you_are": "Default description",
                "how_this_combination": "Default interpretation",
                "what_you_might_enjoy": [],
                "your_strength": [],
                "icon_id": "1"
            }
            
            # Try to extract the code
            for col_name in ['Two digit code', 'Two Digit Code', 'Two-digit code']:
                if col_name in self.two_digit_df.columns and row.get(col_name):
                    personality["code"] = str(row.get(col_name)).strip()
                    break
            
            # Try to extract the role
            for col_name in ['Role', 'role']:
                if col_name in self.two_digit_df.columns and row.get(col_name):
                    personality["role"] = str(row.get(col_name))
                    break
            
            # Try to extract the icon ID
            for col_name in ['icon_id', 'Icon ID', 'Icon id']:
                if col_name in self.two_digit_df.columns and row.get(col_name):
                    personality["icon_id"] = str(row.get(col_name))
                    break
            
            # Try to extract the description
            for col_name in ['Who you are?', 'Who You Are', 'Who you are']:
                if col_name in self.two_digit_df.columns and row.get(col_name):
                    personality["who_you_are"] = str(row.get(col_name))
                    break
            
            # Try to extract the interpretation
            for col_name in ['How This Combination Interpret', 'How This Combination Interprets']:
                if col_name in self.two_digit_df.columns and row.get(col_name):
                    personality["how_this_combination"] = str(row.get(col_name))
                    break
            
            # Try to extract what you might enjoy
            for col_name in ['What You Might Enjoy', 'What you might enjoy']:
                if col_name in self.two_digit_df.columns and row.get(col_name):
                    value = row.get(col_name)
                    if isinstance(value, str):
                        # Split by newlines or bullet points
                        items = [item.strip() for item in value.replace('•', '\n').split('\n') if item.strip()]
                        personality["what_you_might_enjoy"] = items
                    break
            
            # Try to extract your strengths
            for col_name in ['Your strength', 'Your Strength', 'Your strengths']:
                if col_name in self.two_digit_df.columns and row.get(col_name):
                    value = row.get(col_name)
                    if isinstance(value, str):
                        # Split by newlines or bullet points
                        items = [item.strip() for item in value.replace('•', '\n').split('\n') if item.strip()]
                        personality["your_strength"] = items
                    break
            
            return personality
            
        except Exception as e:
            print(f"Error extracting personality from row: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return self._get_default_personality()
    
    def _get_default_personality(self) -> Dict:
        """Return a default personality when no match is found"""
        return {
            "code": "XX",
            "role": "Explorer",
            "who_you_are": "You are a versatile individual with a unique combination of interests and skills.",
            "how_this_combination": "Your profile suggests you have diverse interests that allow you to adapt to various situations.",
            "what_you_might_enjoy": [
                "Exploring different fields and interests",
                "Learning new skills",
                "Adapting to changing environments"
            ],
            "your_strength": [
                "Versatility",
                "Adaptability",
                "Curiosity"
            ],
            "icon_id": "1"
        }

    def _get_industry_insights(self, three_digit_codes: List[str]) -> List[Dict]:
        """Get industry insights for three-digit codes"""
        try:
            print(f"Looking up industry insights for codes: {three_digit_codes}")
            
            if not three_digit_codes:
                print("Warning: No three-digit codes provided")
                return [self._get_default_industry()]
            
            # Initialize results list
            results = []
            
            # Try to find matching industries for each code
            for code in three_digit_codes:
                # Ensure we have a valid code
                if not code or len(code) != 3:
                    print(f"Warning: Invalid three-digit code: {code}")
                    continue
                
                # Try to find exact matches first
                found_match = False
                for _, row in self.industry_df.iterrows():
                    # Get the matching code from the row
                    matching_code = row.get('Matching code', '')
                    
                    if not isinstance(matching_code, str):
                        continue
                    
                    # Check for exact match
                    if matching_code.strip() == code:
                        print(f"Found exact match for code: {code}")
                        industry_info = self._extract_industry_from_row(row, code)
                        results.append(industry_info)
                        found_match = True
                
                # If no exact match, try to find partial matches
                if not found_match:
                    for _, row in self.industry_df.iterrows():
                        matching_code = row.get('Matching code', '')
                        
                        if not isinstance(matching_code, str):
                            continue
                        
                        # Check if the first two characters match
                        if len(matching_code) >= 2 and len(code) >= 2 and matching_code[:2] == code[:2]:
                            print(f"Found partial match for code: {code} with {matching_code}")
                            industry_info = self._extract_industry_from_row(row, code)
                            results.append(industry_info)
                            found_match = True
                            break
                
                # If still no match, try to find any match with the first character
                if not found_match:
                    for _, row in self.industry_df.iterrows():
                        matching_code = row.get('Matching code', '')
                        
                        if not isinstance(matching_code, str):
                            continue
                        
                        # Check if the first character matches
                        if len(matching_code) >= 1 and len(code) >= 1 and matching_code[0] == code[0]:
                            print(f"Found first-character match for code: {code} with {matching_code}")
                            industry_info = self._extract_industry_from_row(row, code)
                            results.append(industry_info)
                            found_match = True
                            break
            
            # If no matches found, return a default industry
            if not results:
                print("No industry matches found, using default")
                results.append(self._get_default_industry())
            
            return results
            
        except Exception as e:
            print(f"Error in _get_industry_insights: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return [self._get_default_industry()]
    
    def _extract_industry_from_row(self, row, matching_code: str) -> Dict:
        """Extract industry information from a row in the industry_df"""
        try:
            # Initialize with default values
            industry = {
                "matching_code": matching_code,
                "industry": "Default Industry",
                "description": "Default industry description",
                "trending": "Default trending information",
                "insight": "Default industry insight",
                "career_path": [],
                "education": ""
            }
            
            # Extract industry name
            if 'Industry' in self.industry_df.columns and row.get('Industry'):
                industry["industry"] = str(row.get('Industry'))
            
            # Extract description
            if 'Description' in self.industry_df.columns and row.get('Description'):
                industry["description"] = str(row.get('Description'))
            
            # Extract trending information
            if 'Trending' in self.industry_df.columns and row.get('Trending'):
                industry["trending"] = str(row.get('Trending'))
            
            # Extract insight
            if 'Insight' in self.industry_df.columns and row.get('Insight'):
                industry["insight"] = str(row.get('Insight'))
            
            # Extract career path
            if 'Career path' in self.industry_df.columns and row.get('Career path'):
                value = row.get('Career path')
                if isinstance(value, str):
                    # Split by newlines or bullet points
                    items = [item.strip() for item in value.replace('•', '\n').split('\n') if item.strip()]
                    industry["career_path"] = items
            
            # Extract education
            if 'Education' in self.industry_df.columns and row.get('Education'):
                industry["education"] = str(row.get('Education'))
            
            return industry
            
        except Exception as e:
            print(f"Error extracting industry from row: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return self._get_default_industry()
    
    def _get_default_industry(self) -> Dict:
        """Return a default industry when no match is found"""
        return {
            "matching_code": "XXX",
            "industry": "General Career Path",
            "description": "This is a general career path that encompasses various industries and roles.",
            "trending": "Various fields are growing in today's economy, including technology, healthcare, and renewable energy.",
            "insight": "Consider exploring different industries to find what aligns with your interests and strengths.",
            "career_path": [
                "Entry-level positions in various fields",
                "Mid-level specialist roles",
                "Management or leadership positions"
            ],
            "education": "Education requirements vary by field. Consider starting with a broad education and specializing based on your interests."
        }

    def process_basic_results(self, answers):
        """Process survey answers and return basic results"""
        try:
            # Initialize category counts
            category_counts = {
                'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0
            }
            
            # Count answers for each category from the survey
            questions = self.get_all_questions()
            
            # Log the answers and questions for debugging
            print(f"Processing {len(answers)} answers for {len(questions)} questions")
            
            # Ensure we have questions to process
            if not questions:
                print("Warning: No questions found in the database")
                raise ValueError("No questions found in the database")
            
            # Ensure answers is a list of strings
            if not isinstance(answers, list):
                print(f"Error: answers is not a list, it's a {type(answers)}")
                raise ValueError(f"Expected answers to be a list, got {type(answers)}")
            
            # Ensure we have the right number of answers
            if len(answers) < len(questions):
                print(f"Warning: Not enough answers ({len(answers)}) for questions ({len(questions)})")
                # Pad with empty answers
                answers = answers + [''] * (len(questions) - len(answers))
            elif len(answers) > len(questions):
                print(f"Warning: Too many answers ({len(answers)}) for questions ({len(questions)})")
                # Truncate extra answers
                answers = answers[:len(questions)]
            
            # Process each answer
            for q_idx, answer in enumerate(answers):
                if q_idx < len(questions):
                    question = questions[q_idx]
                    category = question.get('category', '')
                    
                    # Validate the answer
                    if not isinstance(answer, str):
                        print(f"Warning: Answer at index {q_idx} is not a string: {answer}")
                        continue
                    
                    # Only count 'Yes' answers (case insensitive)
                    if answer.upper() in ['YES', 'Y'] and category in category_counts:
                        category_counts[category] += 1
                        print(f"Question {q_idx+1} (Category {category}): {answer} -> Count: {category_counts[category]}")

            # Convert numpy.int64 to regular Python int
            category_counts = {k: int(v) for k, v in category_counts.items()}
            print(f"Final category counts: {category_counts}")

            # Find categories with maximum scores
            if any(category_counts.values()):  # Check if any category has a score
                max_score = max(category_counts.values())
                max_cats = [cat for cat, count in category_counts.items() if count == max_score]
                
                # Find categories with second highest scores
                second_score = 0
                second_cats = []
                scores = sorted(set(category_counts.values()), reverse=True)
                if len(scores) > 1:
                    second_score = scores[1]
                    second_cats = [cat for cat, count in category_counts.items() if count == second_score]
                
                # Find categories with third highest scores
                third_score = 0
                third_cats = []
                if len(scores) > 2:
                    third_score = scores[2]
                    third_cats = [cat for cat, count in category_counts.items() if count == third_score]
            else:
                # If all categories have zero score, assign default values
                max_cats = ['R']
                second_cats = ['I']
                third_cats = ['A']
                print("Warning: All categories have zero score, using default values")

            print(f"Top categories: {max_cats}, Second: {second_cats}, Third: {third_cats}")

            # Generate three-digit and two-digit codes
            three_digit_codes = self._generate_code(max_cats, second_cats, third_cats)
            two_digit_codes = self._generate_two_digit_code(max_cats, second_cats)
            
            print(f"Generated codes - Three-digit: {three_digit_codes}, Two-digit: {two_digit_codes}")

            # Get the mappings for both two-digit and three-digit codes
            personality_type = self._get_two_digit_mapping(two_digit_codes[0])
            industry_insights = self._get_industry_insights(three_digit_codes)

            # Ensure all numeric values are Python integers, not numpy types
            result = {
                "category_counts": category_counts,
                "three_digit_codes": three_digit_codes,
                "two_digit_codes": two_digit_codes,
                "primary_code": max_cats[0] if max_cats else 'X',
                "personality_type": personality_type,
                "recommended_industries": industry_insights
            }
            
            print(f"Final result keys: {result.keys()}")
            print(f"Personality type: {personality_type.get('role', 'Unknown')}")
            print(f"Industries count: {len(industry_insights)}")
            
            return result
        except Exception as e:
            import traceback
            print(f"Error in process_basic_results: {str(e)}")
            print(traceback.format_exc())
            # Return a default result instead of raising an exception
            return {
                "category_counts": {'R': 1, 'I': 1, 'A': 1, 'S': 1, 'E': 1, 'C': 1},
                "three_digit_codes": ["RIA"],
                "two_digit_codes": ["RI"],
                "primary_code": 'R',
                "personality_type": self._get_default_personality(),
                "recommended_industries": [self._get_default_industry()]
            }

    def _generate_code(self, max_cats: List[str], second_cats: List[str], third_cats: List[str]) -> List[str]:
        """Generate three-digit Holland code combinations"""
        codes = []
        
        if len(max_cats) >= 3:
            # If we have 3 or more categories with the same (highest) score
            for combo in permutations(max_cats, 3):
                codes.append(''.join(combo))
        else:
            # Fill remaining slots with second and third highest categories
            remaining_slots = 3 - len(max_cats)
            if remaining_slots > 0:
                if len(second_cats) >= remaining_slots:
                    for second_combo in permutations(second_cats, remaining_slots):
                        code = ''.join(max_cats + list(second_combo))
                        codes.append(code)
                else:
                    # Need to use some third highest categories
                    needed_from_third = remaining_slots - len(second_cats)
                    if needed_from_third > 0 and third_cats:
                        for third_combo in permutations(third_cats, needed_from_third):
                            code = ''.join(max_cats + second_cats + list(third_combo))
                            codes.append(code)

        return sorted(set(codes)) if codes else ['XXX']  # Return unique codes or placeholder

    def _generate_two_digit_code(self, max_cats: List[str], second_cats: List[str]) -> List[str]:
        """Generate two-digit Holland code combinations"""
        codes = []
        
        if len(max_cats) >= 2:
            # If we have 2 or more categories with the same (highest) score
            for combo in permutations(max_cats, 2):
                codes.append(''.join(combo))
        elif len(max_cats) == 1 and second_cats:
            # One highest category, use second highest for second digit
            for second_cat in second_cats:
                codes.append(f"{max_cats[0]}{second_cat}")

        return sorted(set(codes)) if codes else ['XX']  # Return unique codes or placeholder
