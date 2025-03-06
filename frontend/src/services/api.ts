import type { Question, SurveyResponse, AnalysisResult } from '../types/survey';

// Always use relative URL for API endpoints
const API_BASE_URL = '/api';

console.log('API service initialized with base URL:', API_BASE_URL);

// Fetch questions from the API
export async function fetchQuestions(): Promise<Question[]> {
    try {
        const url = `${API_BASE_URL}/survey/questions`;
        console.log('Fetching questions from:', url);
        
        const response = await fetch(url, {
            headers: {
                'Accept': 'application/json',
            },
            cache: 'no-cache',
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Error response (${response.status}): ${errorText}`);
            throw new Error(`HTTP error! Status: ${response.status}. Details: ${errorText}`);
        }
        
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
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            },
            body: JSON.stringify({ answers }),
        });
        
        if (!response.ok) {
            console.error(`Error response: ${response.status} ${response.statusText}`);
            const text = await response.text();
            console.error('Response body:', text);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Analysis result received:', result);
        
        // Validate the result structure
        if (!result.personality || !result.industries) {
            console.error('Invalid result structure:', result);
            throw new Error('Invalid result structure received from API');
        }
        
        return result;
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
