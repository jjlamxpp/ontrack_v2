import type { Question, SurveyResponse, AnalysisResult } from '../types/survey';

// Determine the API base URL - use the current origin if in production
const API_BASE_URL = (() => {
  // Check if we're in production (assume we are if not using localhost)
  const isProduction = !window.location.hostname.includes('localhost');
  
  if (isProduction) {
    // In production, use the same origin as the current page
    return `${window.location.origin}/api`;
  }
  
  // In development, use the env variable or fallback
  return import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
})();

console.log('Using API base URL:', API_BASE_URL);

// Fetch questions from the API
export async function fetchQuestions(): Promise<Question[]> {
    try {
        console.log('Fetching questions from:', `${API_BASE_URL}/survey/questions`);
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
        // Ensure iconId is properly formatted
        const cleanIconId = iconId.replace(/\D/g, ''); // Remove any non-digits
        const url = `${API_BASE_URL}/survey/icon/${cleanIconId}.png`; // Add .png extension
        
        console.log('Fetching icon from:', url);
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`Failed to load icon ${cleanIconId}, status: ${response.status}`);
            return '/default-icon.png';
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    } catch (error) {
        console.error('Error loading character icon:', error);
        return '/default-icon.png';
    }
}

// Get school logo
export async function getSchoolLogo(school: string): Promise<string> {
    try {
        // Format school name properly
        const cleanSchool = school.toLowerCase().replace(/\s+/g, '-');
        const url = `${API_BASE_URL}/survey/school-icon/${cleanSchool}.png`; // Add .png extension
        
        console.log('Fetching school logo from:', url);
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`Failed to load school logo for ${school}, status: ${response.status}`);
            return '/default-school.png';
        }

        const blob = await response.blob();
        return URL.createObjectURL(blob);
    } catch (error) {
        console.error('Error loading school logo:', error);
        return '/default-school.png';
    }
}

// Cleanup function for blob URLs
export function cleanupBlobUrl(url: string): void {
    if (url && url.startsWith('blob:')) {
        URL.revokeObjectURL(url);
    }
}
