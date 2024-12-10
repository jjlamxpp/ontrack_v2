import type { Question, SurveyResponse, AnalysisResult } from '../types/survey';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Fetch questions from the API
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

// Submit survey and get analysis
export async function submitSurveyAndGetAnalysis(answers: string[]): Promise<AnalysisResult> {
    try {
        const response = await fetch(`${API_BASE_URL}/survey/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ answers }),
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Analysis result:', result);
        return result;
    } catch (error) {
        console.error('Error submitting survey:', error);
        throw error;
    }
}

// Get character icon with proper error handling
export async function getCharacterIcon(iconId: string): Promise<string> {
    try {
        // Convert iconId to proper format (e.g., "icon_23" instead of just "23")
        const formattedIconId = `icon_${iconId}`;
        console.log('Fetching icon:', formattedIconId);
        
        const response = await fetch(`${API_BASE_URL}/survey/icon/${formattedIconId}`);
        
        if (!response.ok) {
            console.error(`Failed to load icon ${formattedIconId}, status: ${response.status}`);
            return '/icons/default-personality.png'; // Fallback icon
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    } catch (error) {
        console.error('Error loading character icon:', error);
        return '/icons/default-personality.png'; // Fallback icon
    }
}

// Get school logo
export async function getSchoolLogo(school: string): Promise<string> {
    try {
        const formattedSchool = school.toLowerCase().replace(/\s+/g, '-');
        const response = await fetch(`${API_BASE_URL}/survey/school-icon/${formattedSchool}`);
        
        if (!response.ok) {
            return '/icons/default-school.png'; // Fallback school icon
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    } catch (error) {
        console.error('Error loading school logo:', error);
        return '/icons/default-school.png'; // Fallback school icon
    }
}

// Cleanup function for blob URLs
export function cleanupBlobUrl(url: string): void {
    if (url && url.startsWith('blob:')) {
        URL.revokeObjectURL(url);
    }
}
