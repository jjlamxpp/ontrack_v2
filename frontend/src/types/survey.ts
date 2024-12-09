// Define types matching your backend schemas
export interface Question {
  id: number;
  question_text: string;
  category: string;
  options: string[];
}

export interface SurveyResponse {
  answers: string[];
}

export interface PersonalityAnalysis {
  type: string;
  description: string;
  interpretation: string;
  enjoyment: string[];
  your_strength: string[];
  iconId: string;
  riasecScores: {
    [key: string]: number;
  };
}

export interface JupasInfo {
  subject: string;
  jupasCode: string;
  school: string;
  averageScore: string;
  requirements?: string[];
  careerProspects?: string;
}

export interface IndustryRecommendation {
  id: string;
  name: string;
  overview: string;
  trending: string;
  insight: string;
  examplePaths: string[];
  education?: string;
  jupasInfo?: {
    subject: string;
    jupasCode: string;
    school: string;
    averageScore: string;
  };
}

export interface AnalysisResult {
  personality: PersonalityAnalysis;
  industries: IndustryRecommendation[];
}