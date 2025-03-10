import type { Question, SurveyResponse, AnalysisResult } from '../types/survey';
import { config } from '../config';

// Use the API_URL from config with fallback to Digital Ocean URL
const API_BASE_URL = config.API_URL || 'https://ontrack-d4m7j.ondigitalocean.app/api';

console.log('API service initialized with base URL:', API_BASE_URL);
console.log('Environment variables available:', import.meta.env);

// Helper function to handle API errors
const handleApiError = async (response: Response, context: string) => {
    if (!response.ok) {
        let errorMessage = `${context} failed with status ${response.status}`;
        try {
            const errorText = await response.text();
            console.error(`Error response for ${context}:`, errorText);
            errorMessage += `: ${errorText}`;
        } catch (e) {
            console.error(`Could not parse error response for ${context}`);
        }
        throw new Error(errorMessage);
    }
    return response;
};

// Fetch questions from the API
export async function fetchQuestions(): Promise<Question[]> {
    try {
        const url = `${API_BASE_URL}/survey/questions`;
        console.log('Fetching questions from:', url);
        
        const response = await fetch(url);
        await handleApiError(response, 'Fetching questions');
        
        const data = await response.json();
        console.log('Questions received:', data);
        return data;
    } catch (error) {
        console.error('Error fetching questions:', error);
        throw error;
    }
}

// Submit survey and get analysis
export async function submitSurveyAndGetAnalysis(answers: string[]): Promise<AnalysisResult> {
    try {
        const url = `${API_BASE_URL}/survey/submit`;
        console.log('Submitting survey to:', url);
        console.log('Answers being submitted:', answers);
        
        // Add a timeout to the fetch request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ answers }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                let errorMessage = `Submitting survey failed with status ${response.status}`;
                try {
                    const errorText = await response.text();
                    console.error(`Error response for submitting survey:`, errorText);
                    errorMessage += `: ${errorText}`;
                } catch (e) {
                    console.error(`Could not parse error response for submitting survey`);
                }
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            console.log('Analysis result received:', data);
            
            // Validate the result structure
            if (!data.personality || !data.industries) {
                console.error('Invalid result structure:', data);
                throw new Error('Invalid result structure received from API');
            }
            
            return data;
        } catch (fetchError: any) {
            if (fetchError.name === 'AbortError') {
                console.error('Request timed out after 30 seconds');
                throw new Error('Request timed out. Please try again.');
            }
            throw fetchError;
        } finally {
            clearTimeout(timeoutId);
        }
    } catch (error) {
        console.error('Error submitting survey:', error);
        throw error;
    }
}

// Get character icon
export async function getCharacterIcon(iconId: string): Promise<string> {
    try {
        // Ensure iconId is properly formatted
        const cleanIconId = iconId.replace(/\D/g, ''); // Remove any non-digits
        const url = `${API_BASE_URL}/survey/icon/${cleanIconId}.png`; // Add .png extension
        
        console.log('Fetching icon from:', url);
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`Failed to load icon ${cleanIconId}, status: ${response.status}`);
            return '/fallback-icon.png';
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    } catch (error) {
        console.error('Error loading character icon:', error);
        return '/fallback-icon.png';
    }
}

// Get school logo with updated fallback path
export async function getSchoolLogo(school: string): Promise<string> {
    try {
        // Format school name properly
        const cleanSchool = school.toLowerCase().replace(/\s+/g, '-');
        const url = `${API_BASE_URL}/survey/school-icon/${cleanSchool}.png`;
        
        console.log('Fetching school logo from:', url);
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`Failed to load school logo for ${school}, status: ${response.status}`);
            return '/fallback-school-icon.png';
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    } catch (error) {
        console.error('Error loading school logo:', error);
        return '/fallback-school-icon.png';
    }
}

// Cleanup function for blob URLs
export function cleanupBlobUrl(url: string): void {
    if (url && url.startsWith('blob:')) {
        URL.revokeObjectURL(url);
    }
}
