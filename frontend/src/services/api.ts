import type { Question, SurveyResponse, AnalysisResult } from '../types/survey';
import { config } from '../config/env';

const API_BASE_URL = config.API_URL;

export async function fetchQuestions(): Promise<Question[]> {
    try {
        const response = await fetch(`${API_BASE_URL}/survey/questions`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching questions:', error);
        throw error;
    }
}

export async function submitSurveyAndGetAnalysis(answers: string[]): Promise<AnalysisResult> {
    try {
        console.log('Submitting answers:', answers);
        const response = await fetch(`${API_BASE_URL}/survey/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ answers }),
        });
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            throw new Error(
                errorData?.message || 
                `HTTP error! status: ${response.status}`
            );
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error submitting survey:', error);
        throw error;
    }
}
