import type { Question, SurveyResponse, AnalysisResult } from '../types/survey';

// IMPORTANT: FIXED BACKEND API URL - DO NOT MODIFY
const BACKEND_API_URL = 'https://ontrack-v2.onrender.com/api';

// Get API base URL from the global configuration or use the fixed backend URL
const API_BASE_URL = window.__API_BASE_URL || BACKEND_API_URL;

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
            credentials: 'omit',
            mode: 'cors'
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
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ answers }),
            credentials: 'omit',
            mode: 'cors'
        });
        
        if (!response.ok) {
            console.error(`Error response: ${response.status} ${response.statusText}`);
            const text = await response.text();
            console.error('Response body:', text);
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('Analysis result received');
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
        const response = await fetch(url, {
            mode: 'cors',
            credentials: 'omit'
        });
        
        if (!response.ok) {
            console.error(`Failed to load icon ${cleanIconId}, status: ${response.status}`);
            return '/static/icon/default.png';
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    } catch (error) {
        console.error('Error loading character icon:', error);
        return '/static/icon/default.png';
    }
}

// Get school logo with updated fallback path
export async function getSchoolLogo(school: string): Promise<string> {
    try {
        // Format school name properly
        const cleanSchool = school.toLowerCase().replace(/\s+/g, '-');
        const url = `${API_BASE_URL}/survey/school-icon/${cleanSchool}.png`;
        
        console.log('Fetching school logo from:', url);
        const response = await fetch(url, {
            mode: 'cors',
            credentials: 'omit'
        });
        
        if (!response.ok) {
            console.error(`Failed to load school logo for ${school}, status: ${response.status}`);
            return '/static/school_icon/default.png';
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    } catch (error) {
        console.error('Error loading school logo:', error);
        return '/static/school_icon/default.png';
    }
}

// Cleanup function for blob URLs
export function cleanupBlobUrl(url: string): void {
    if (url && url.startsWith('blob:')) {
        URL.revokeObjectURL(url);
    }
}

// Runtime check to ensure correct API URL
(() => {
  if (API_BASE_URL !== BACKEND_API_URL) {
    console.warn('⚠️ API_BASE_URL differs from BACKEND_API_URL');
    console.warn(`Using: ${API_BASE_URL}`);
    console.warn(`Fixed backend URL is: ${BACKEND_API_URL}`);
  }
})();
