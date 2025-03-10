import type { Question, SurveyResponse, AnalysisResult } from '../types/survey';
import { config } from '../config';

// Use the API_URL from config with a fallback to the current origin
const API_BASE_URL = config.API_URL.startsWith('http') 
    ? config.API_URL 
    : `${window.location.origin}${config.API_URL}`;

console.log('API service initialized with base URL:', API_BASE_URL);
console.log('Current origin:', window.location.origin);
console.log('Config API_URL:', config.API_URL);

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

// Add a debug function to test the API
export async function debugSurveyTest(): Promise<any> {
    try {
        const url = `${API_BASE_URL}/debug/survey-test`;
        console.log('Testing survey API at:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`Debug test failed with status ${response.status}`);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`Debug test failed with status ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Debug test result:', data);
        return data;
    } catch (error) {
        console.error('Error in debug test:', error);
        throw error;
    }
}

// Submit survey and get analysis
export async function submitSurveyAndGetAnalysis(answers: string[]): Promise<AnalysisResult> {
    try {
        // Log the API base URL and environment
        console.log('API_BASE_URL:', API_BASE_URL);
        console.log('Current origin:', window.location.origin);
        console.log('Current pathname:', window.location.pathname);
        
        // Try the regular endpoint first
        const url = `${API_BASE_URL}/survey/submit`;
        console.log('Submitting survey to:', url);
        console.log('Answers being submitted:', answers);
        
        // Add a timeout to the fetch request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 second timeout
        
        try {
            // Make the request with a longer timeout
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ answers }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            // Log the response status
            console.log('Survey submission response status:', response.status);
            
            // Try to parse the response as JSON regardless of status code
            let data;
            try {
                data = await response.json();
                console.log('Response data received:', data);
            } catch (jsonError) {
                console.error('Error parsing JSON response:', jsonError);
                
                // Try to get the response text
                try {
                    const text = await response.text();
                    console.error('Response text:', text);
                } catch (textError) {
                    console.error('Error getting response text:', textError);
                }
                
                throw new Error('Failed to parse API response as JSON');
            }
            
            // Check if the response was successful
            if (!response.ok) {
                console.error('Error response:', response.status, data);
                
                // If we got a JSON response with an error message, use it
                if (data && data.detail) {
                    throw new Error(`API error: ${data.detail}`);
                } else {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
            }
            
            // Validate the result structure
            if (!data || typeof data !== 'object') {
                console.error('Invalid result format:', data);
                throw new Error('Invalid result format received from API');
            }
            
            // Check if we have the expected fields
            if (!data.personality || !data.industries) {
                console.error('Missing required fields in result:', data);
                throw new Error('Missing required fields in result from API');
            }
            
            return data;
        } catch (fetchError: any) {
            if (fetchError.name === 'AbortError') {
                console.error('Request timed out after 60 seconds');
                throw new Error('Request timed out. Please try again.');
            }
            
            // If the regular endpoint fails, try the test endpoint as fallback
            console.log('Regular endpoint failed, trying test endpoint as fallback');
            const testUrl = `${API_BASE_URL}/test-submit`;
            console.log('Trying test submission endpoint:', testUrl);
            
            const testResponse = await fetch(testUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ answers }),
            });
            
            if (testResponse.ok) {
                const testData = await testResponse.json();
                console.log('Test submission successful:', testData);
                return testData;
            } else {
                console.error('Test submission also failed');
                throw fetchError;
            }
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

// Add a function to check the file system
export async function debugFileSystem(): Promise<any> {
    try {
        const url = `${API_BASE_URL}/debug/file-system`;
        console.log('Checking file system at:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`File system check failed with status ${response.status}`);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`File system check failed with status ${response.status}`);
        }
        
        const data = await response.json();
        console.log('File system check result:', data);
        return data;
    } catch (error) {
        console.error('Error in file system check:', error);
        throw error;
    }
}

// Add a function to use the direct test endpoint
export async function directTest(answers: string[]): Promise<AnalysisResult> {
    try {
        const url = `${API_BASE_URL}/direct-test`;
        console.log('Using direct test endpoint:', url);
        console.log('Answers being submitted:', answers);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ answers }),
        });
        
        if (!response.ok) {
            console.error(`Direct test failed with status ${response.status}`);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`Direct test failed with status ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Direct test result:', data);
        return data;
    } catch (error) {
        console.error('Error in direct test:', error);
        throw error;
    }
}
