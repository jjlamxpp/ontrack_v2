import type { Question, SurveyResponse, AnalysisResult } from '../types/survey';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Fetch questions from the API
export async function fetchQuestions(): Promise<Question[]> {
    try {
        console.log('Fetching questions from:', `${API_BASE_URL}/survey/questions`);
        const response = await fetch(`${API_BASE_URL}/survey/questions`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
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
        throw new Error('Failed to load questions. Please try again later.');
    }
}

// Submit survey answers and get analysis
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
        
        const data = await response.json();
        console.log('Analysis result:', data);
        return data;
    } catch (error) {
        console.error('Error submitting survey:', error);
        throw new Error('Failed to submit survey. Please try again.');
    }
}

// Fetch character icon
export async function getCharacterIcon(iconId: string): Promise<string> {
    try {
        console.log('Fetching character icon:', iconId);
        const response = await fetch(`${API_BASE_URL}/survey/icon/${iconId}`, {
            method: 'GET',
            headers: {
                'Access-Control-Allow-Origin': '*'
            },
        });

        if (!response.ok) {
            throw new Error(`Failed to load character icon: ${response.status}`);
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    } catch (error) {
        console.error('Error loading character icon:', error);
        return '/fallback-icon.png';
    }
}

// Fetch school logo
export async function getSchoolLogo(school: string): Promise<string> {
    try {
        console.log('Fetching school logo:', school);
        const response = await fetch(`${API_BASE_URL}/survey/school-icon/${school}`, {
            method: 'GET',
            headers: {
                'Access-Control-Allow-Origin': '*'
            },
        });

        if (!response.ok) {
            throw new Error(`Failed to load school logo: ${response.status}`);
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    } catch (error) {
        console.error('Error loading school logo:', error);
        return '/fallback-school-icon.png';
    }
}

// Clean up blob URLs
export function cleanupBlobUrl(url: string): void {
    if (url && url.startsWith('blob:')) {
        URL.revokeObjectURL(url);
    }
}

// Helper function to handle API errors
export function handleApiError(error: unknown): never {
    if (error instanceof Error) {
        throw new Error(error.message);
    }
    throw new Error('An unexpected error occurred');
}

// Validate API response
export function validateApiResponse<T>(data: unknown): T {
    if (!data) {
        throw new Error('Invalid API response: No data received');
    }
    return data as T;
}
