import type { Question, SurveyResponse, AnalysisResult } from '../types/survey';

// Use the current window location to determine the API URL
// Add fallback for production environment
const API_BASE_URL = (() => {
  // Check if we're in a production environment (like render.com)
  const isProduction = window.location.hostname !== 'localhost' && 
                      !window.location.hostname.includes('127.0.0.1');
  
  if (isProduction) {
    // In production, use the same origin for API calls
    return `${window.location.origin}/api`;
  } else {
    // In development, use localhost:8000
    return 'http://localhost:8000/api';
  }
})();

console.log('Using API base URL:', API_BASE_URL);

// Fetch questions from the API
export async function fetchQuestions(): Promise<Question[]> {
    try {
        const url = `${API_BASE_URL}/survey/questions`;
        console.log('Fetching questions from:', url);
        
        // Add more detailed debugging
        console.log('Current location:', window.location.href);
        
        const response = await fetch(url, {
            headers: {
                'Accept': 'application/json',
            },
            // Add cache control to prevent caching issues
            cache: 'no-cache',
            // Add credentials to include cookies if needed
            credentials: 'include',
        });
        
        console.log('Response status:', response.status);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Error response (${response.status}): ${errorText}`);
            
            // For debugging in production - add more context
            if (response.status === 404) {
                console.error('API endpoint not found. Check server routes configuration.');
                console.error('Current API base:', API_BASE_URL);
            }
            
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
            credentials: 'include',
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
        const response = await fetch(url);
        
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
        const response = await fetch(url);
        
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
