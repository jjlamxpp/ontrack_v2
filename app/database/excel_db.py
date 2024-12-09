import pandas as pd
from pathlib import Path
from itertools import permutations
from typing import List, Dict
import numpy as np

class SurveyDatabase:
    def __init__(self, excel_path: str = '/Users/oscarsiu/Desktop/ontrack_v2/app/database/Database.xlsx'):
        self.excel_path = Path(excel_path)
        if not self.excel_path.exists():
            raise FileNotFoundError(f"Excel file not found at {excel_path}")
        
        try:
            # Read all required sheets
            self.df = pd.read_excel(
                self.excel_path, 
                sheet_name="Question pool",
                engine='openpyxl'
            )
            self.two_digit_df = pd.read_excel(
                self.excel_path, 
                sheet_name="Two digit",
                engine='openpyxl'
            )
            self.industry_df = pd.read_excel(
                self.excel_path, 
                sheet_name="Industry Insight",
                engine='openpyxl'
            )
            
            # Debug: Print actual columns from both sheets
            print("Two digit sheet columns:", list(self.two_digit_df.columns))
            print("Industry sheet columns:", list(self.industry_df.columns))
            
            # Updated required columns with variations
            required_columns = {
                'Question pool': ['questions:', 'category'],
                'Two digit': [
                    col for col in [
                        'Two digit code', 'Two Digit Code', 'Two-digit code',
                        'Role', 'role',
                        'icon_id', 'Icon ID', 'Icon id',
                        'Who you are?', 'Who You Are', 'Who you are',
                        'How This Combination Interpret', 'How This Combination Interprets',
                        'What You Might Enjoy', 'What you might enjoy',
                        'Your strength', 'Your Strength', 'Your strengths'
                    ] if col in self.two_digit_df.columns
                ],
                'Industry': [
                    col for col in [
                        'Three digital', 'Three Digital', 'Mapping Code',  # Common variations for mapping code
                        'Industry', 'industry',
                        'Overview', 'overview',
                        'Trending', 'trending',
                        'Insight', 'insight',
                        'Required Skills', 'Required skills', 'required skills',
                        'Example Role', 'Example role', 'example role',
                        'Jupas', 'JUPAS', 'jupas'
                    ] if col in self.industry_df.columns
                ]
            }
            
            # Check Industry sheet with detailed error message
            required_industry_types = {
                'mapping': ['Three digital', 'Three Digital', 'Mapping Code'],
                'industry': ['Industry', 'industry'],
                'overview': ['Overview', 'overview'],
                'trending': ['Trending', 'trending'],
                'insight': ['Insight', 'insight'],
                'skills': ['Required Skills', 'Required Skill', 'required skills'],
                'role': ['Example Role', 'Example role', 'example role'],
                'jupas': ['Jupas', 'JUPAS', 'jupas']
            }
            
            missing_industry_types = []
            for col_type, variants in required_industry_types.items():
                if not any(variant in self.industry_df.columns for variant in variants):
                    missing_industry_types.append(col_type)
            
            if missing_industry_types:
                print(f"Missing Industry column types: {missing_industry_types}")
                print("Available Industry columns:", list(self.industry_df.columns))
                raise ValueError(f"Missing required column types in Industry sheet: {missing_industry_types}")
            
            # Check Question pool sheet
            if not all(col in self.df.columns for col in required_columns['Question pool']):
                raise ValueError(f"Missing required columns in Question pool sheet")
            
            # Check Two digit sheet
            if not all(col in self.two_digit_df.columns for col in required_columns['Two digit']):
                raise ValueError(f"Missing required columns in Two digit sheet")
            
            # Check Industry sheet
            if not all(col in self.industry_df.columns for col in required_columns['Industry']):
                raise ValueError(f"Missing required columns in Industry sheet")
            
        except Exception as e:
            print(f"Error reading Excel file: {str(e)}")
            raise

    def get_all_questions(self):
        """Get all questions from the database"""
        if self.df is None:
            print("Database not properly initialized")
            return []
        
        questions = []
        try:
            for index, row in self.df.iterrows():
                if pd.isna(row['questions:']) or pd.isna(row['category']):
                    continue
                
                raw_question = str(row['questions:'])
                if "- question:" in raw_question:
                    question_text = raw_question.split("- question:")[1].strip().strip('"')
                else:
                    question_text = raw_question.strip().strip('"')
                
                question = {
                    'id': index + 1,
                    'question_text': question_text,
                    'category': row['category'],
                    'options': ["Yes", "No"]
                }
                questions.append(question)
        except Exception as e:
            print(f"Error processing questions: {str(e)}")
            return []
        
        return questions

    def _get_two_digit_mapping(self, two_digit_code: str) -> Dict:
        """Get description for two-digit code"""
        if self.two_digit_df is None:
            print("Two digit DataFrame is None")
            return {}
        
        try:
            # Debug print
            print(f"Looking for two digit code: {two_digit_code}")
            print("Available codes:", self.two_digit_df['Two digit code'].unique().tolist())
            
            # Find the row where the "Two digit code" column matches
            matching_row = self.two_digit_df[self.two_digit_df['Two digit code'] == two_digit_code]
            
            if matching_row.empty:
                print(f"No matching row found for code: {two_digit_code}")
                return {}
            
            row = matching_row.iloc[0]
            
            # Convert row to dict and ensure all numeric values are Python integers
            row_dict = {k: int(v) if isinstance(v, np.integer) else v for k, v in row.to_dict().items()}
            print(f"Found matching row: {row_dict}")
            
            # Handle the 'How This Combination Interpret' column with space at the end
            how_this_combination = row_dict.get('How This Combination Interpret ', '')  # Note the space at the end
            if not how_this_combination:  # Try without space if first attempt is empty
                how_this_combination = row_dict.get('How This Combination Interpret', '')
            
            # Split the fields that contain "//" into lists
            what_you_might_enjoy = [
                item.strip() 
                for item in str(row_dict.get('What You Might Enjoy', '')).split("//")
                if item.strip()
            ]
            
            your_strength = [
                item.strip() 
                for item in str(row_dict.get('Your strength', '')).split("//")
                if item.strip()
            ]
            
            result = {
                "code": two_digit_code,
                "role": row_dict.get('Role', ''),
                "icon_id": str(row_dict.get('icon_id', '')),
                "who_you_are": row_dict.get('Who you are?', ''),
                "how_this_combination": how_this_combination,
                "what_you_might_enjoy": what_you_might_enjoy,
                "your_strength": your_strength
            }
            
            # Debug print
            print("Returning result:", result)
            return result
            
        except Exception as e:
            print(f"Error getting two-digit mapping: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def _get_industry_insights(self, three_digit_codes: List[str]) -> List[Dict]:
        """Get industry insights for three-digit codes"""
        if self.industry_df is None:
            print("Industry DataFrame is None")
            return []
        
        insights = []
        try:
            # Debug print
            print(f"Looking for three digit codes: {three_digit_codes}")
            mapping_column = None
            
            # Find the correct mapping column name
            possible_columns = ['Three digital', 'Three Digital', 'Mapping Code']
            for col in possible_columns:
                if col in self.industry_df.columns:
                    mapping_column = col
                    break
                
            if not mapping_column:
                print("Could not find mapping column. Available columns:", self.industry_df.columns)
                return []
            
            print(f"Using mapping column: {mapping_column}")
            
            # Check each code against the mapping column
            for code in three_digit_codes:
                # Iterate through each row in the DataFrame
                for _, row in self.industry_df.iterrows():
                    # Get the mapping codes string and split it into individual codes
                    mapping_codes_str = str(row[mapping_column])
                    mapping_codes = [c.strip() for c in mapping_codes_str.split(',')]
                    
                    # Check if the current code exists in the mapping codes
                    if code in mapping_codes:
                        print(f"Found match for code {code} in row with codes: {mapping_codes}")
                        
                        # Convert row to dict and handle NaN values
                        row_dict = {k: ('' if pd.isna(v) else v) for k, v in row.to_dict().items()}
                        
                        # Split fields that contain "//" into lists
                        career_paths = [
                            path.strip() 
                            for path in str(row_dict.get('Example Role', '')).split("//")
                            if path.strip()
                        ]
                        
                        insight = {
                            "industry": row_dict.get('Industry', ''),
                            "description": row_dict.get('Overview', ''),
                            "trending": row_dict.get('Trending', ''),
                            "insight": row_dict.get('Insight', ''),
                            "skills_required": row_dict.get('Required Skills', ''),
                            "career_path": career_paths,
                            "education": row_dict.get('Jupas', ''),
                            "matching_code": code  # Add the matching code for reference
                        }
                        
                        # Remove any empty values
                        insight = {k: v for k, v in insight.items() if v}
                        
                        if any(insight.values()):  # Only append if there's at least one non-empty value
                            insights.append(insight)
                            print(f"Added insight for code {code}: {insight}")
                
        except Exception as e:
            print(f"Error getting industry insights: {e}")
            import traceback
            traceback.print_exc()
            
        return insights

    def process_basic_results(self, answers: List[str]) -> Dict:
        """Process survey answers and generate Holland codes with mappings"""
        # Initialize counters for each Holland code category
        category_counts = {
            'R': 0, 'I': 0, 'A': 0, 
            'S': 0, 'E': 0, 'C': 0
        }
        
        # Count answers for each category from the survey
        questions = self.get_all_questions()
        for q_idx, answer in enumerate(answers):
            if q_idx < len(questions) and answer.lower() == 'yes':
                category = questions[q_idx]['category']
                if category in category_counts:
                    category_counts[category] += 1

        # Convert numpy.int64 to regular Python int
        category_counts = {k: int(v) for k, v in category_counts.items()}

        # Find categories with maximum scores
        max_score = max(category_counts.values())
        max_cats = [cat for cat, count in category_counts.items() if count == max_score]
        
        # Find categories with second highest scores
        second_score = max(count for count in category_counts.values() if count < max_score)
        second_cats = [cat for cat, count in category_counts.items() if count == second_score]
        
        # Find categories with third highest scores
        remaining_scores = [count for count in category_counts.values() if count < second_score]
        third_score = max(remaining_scores) if remaining_scores else 0
        third_cats = [cat for cat, count in category_counts.items() if count == third_score]

        # Generate three-digit and two-digit codes
        three_digit_codes = self._generate_code(max_cats, second_cats, third_cats)
        two_digit_codes = self._generate_two_digit_code(max_cats, second_cats)

        # Get the mappings for both two-digit and three-digit codes
        personality_type = self._get_two_digit_mapping(two_digit_codes[0])
        industry_insights = self._get_industry_insights(three_digit_codes)

        # Ensure all numeric values are Python integers, not numpy types
        result = {
            "category_counts": category_counts,  # Already converted above
            "three_digit_codes": three_digit_codes,
            "two_digit_codes": two_digit_codes,
            "primary_code": max_cats[0] if max_cats else 'X',
            "personality_type": personality_type,
            "recommended_industries": industry_insights
        }

        # Debug print
        print("Final result:", result)
        
        return result

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