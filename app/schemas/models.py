from pydantic import BaseModel
from typing import List, Dict

class Question(BaseModel):
    id: int
    question_text: str
    category: str
    options: List[str]

class SurveyResponse(BaseModel):
    answers: List[str]

class PersonalityTrait(BaseModel):
    subject: str
    value: float

class PersonalityAnalysis(BaseModel):
    type: str
    description: str
    traits: List[PersonalityTrait]
    interpretation: str
    enjoyment: List[str]
    your_strength: List[str]

class ExamplePath(BaseModel):
    name: str
    score: float
    logo: str

class IndustryRecommendation(BaseModel):
    id: str
    name: str
    overview: str
    trending: str
    insight: str
    examplePaths: List[ExamplePath]

class AnalysisResult(BaseModel):
    personality: PersonalityAnalysis
    industries: List[IndustryRecommendation]