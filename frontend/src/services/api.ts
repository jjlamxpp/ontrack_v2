import type { Question, AnalysisResult } from '../types/survey';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export async function fetchQuestions(): Promise<Question[]> {
  try {
    console.log('Fetching questions from:', `${API_BASE_URL}/survey/questions`);
    const response = await fetch(`${API_BASE_URL}/survey/questions`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        // Add CORS headers if needed
        'Access-Control-Allow-Origin': '*'
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Received questions:', data);
    return data;
  } catch (error) {
    console.error('Error fetching questions:', error);
    throw new Error('Failed to fetch questions. Please check your connection and try again.');
  }
}

export async function submitSurveyAndGetAnalysis(answers: string[]): Promise<AnalysisResult> {
  try {
    console.log('Submitting answers:', answers);
    const response = await fetch(`${API_BASE_URL}/survey/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({ answers }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log('Received analysis:', result);
    return result;
  } catch (error) {
    console.error('Error submitting survey:', error);
    throw new Error('Failed to submit survey. Please try again.');
  }
}
