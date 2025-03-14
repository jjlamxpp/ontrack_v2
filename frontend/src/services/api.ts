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

// Submit survey and get analysis
export async function submitSurveyAndGetAnalysis(answers: string[]): Promise<AnalysisResult> {
    try {
        // Log the API base URL and environment
        console.log('API_BASE_URL:', API_BASE_URL);
        console.log('Current origin:', window.location.origin);
        console.log('Current pathname:', window.location.pathname);
        
        // Ensure all answers are strings and normalize them
        const normalizedAnswers = answers.map(answer => {
            if (typeof answer !== 'string') {
                console.warn('Non-string answer found:', answer);
                return 'NO'; // Default to NO for non-string answers
            }
            return answer.toUpperCase();
        });
        
        console.log('Normalized answers before submission:', normalizedAnswers);
        
        // Construct the URL for the survey submission endpoint
        const url = `${API_BASE_URL}/survey/submit`;
        console.log('Submitting survey to:', url);
        
        // Create the request body
        const requestBody = {
            answers: normalizedAnswers
        };
        
        console.log('Request body:', JSON.stringify(requestBody));
        
        // Make the request
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(requestBody),
            mode: 'cors',
            credentials: 'include'
        });
        
        console.log('Survey submission response status:', response.status);
        
        // Try to parse the response as JSON
        try {
            const data = await response.json();
            console.log('Response data received:', data);
            
            // Validate the result structure
            if (!data || typeof data !== 'object') {
                console.error('Invalid result format:', data);
                return getFallbackResult();
            }
            
            // Check if we have the expected fields
            if (!data.personality || !data.industries) {
                console.error('Missing required fields in result:', data);
                return getFallbackResult();
            }
            
            return data;
        } catch (jsonError) {
            console.error('Error parsing JSON response:', jsonError);
            return getFallbackResult();
        }
    } catch (error) {
        console.error('Error submitting survey:', error);
        return getFallbackResult();
    }
}

// Provide a fallback result in case of errors
function getFallbackResult(): AnalysisResult {
    console.log('Using fallback result');
    return {
        personality: {
            type: "RI",
            description: "You are a logical and analytical thinker with a strong interest in understanding how things work.",
            interpretation: "Your combination of Realistic and Investigative traits suggests you enjoy solving practical problems through analysis and research.",
            enjoyment: [
                "Working with technical systems",
                "Analyzing complex problems",
                "Learning new technical skills"
            ],
            your_strength: [
                "Logical thinking",
                "Problem-solving",
                "Technical aptitude"
            ],
            iconId: "1",
            riasecScores: {"R": 5, "I": 4, "A": 2, "S": 1, "E": 3, "C": 2}
        },
        industries: [{
            id: "RIA",
            name: "Engineering",
            overview: "Engineering involves applying scientific and mathematical principles to design and build systems, structures, and products.",
            trending: "Software engineering, biomedical engineering, and renewable energy engineering are rapidly growing fields.",
            insight: "Engineers are in high demand across various sectors, with opportunities for specialization and advancement.",
            examplePaths: [
                "Software Engineer",
                "Mechanical Engineer",
                "Civil Engineer"
            ],
            education: "Bachelor's degree in engineering or related field, with professional certification often required."
        }]
    };
}

// Get character icon
export async function getCharacterIcon(iconId: string): Promise<string> {
    try {
        const url = `${API_BASE_URL}/survey/icon/${iconId}`;
        console.log('Fetching character icon from:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`Failed to fetch icon with status ${response.status}`);
            throw new Error(`Failed to fetch icon with status ${response.status}`);
        }
        
        // Create a blob URL for the image
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        
        return blobUrl;
    } catch (error) {
        console.error('Error fetching character icon:', error);
        // Return a default icon or placeholder
        return '/default-icon.png';
    }
}

// Get school logo
export async function getSchoolLogo(school: string): Promise<string> {
    try {
        // Encode the school name for the URL
        const encodedSchool = encodeURIComponent(school);
        const url = `${API_BASE_URL}/survey/school-icon/${encodedSchool}`;
        console.log('Fetching school logo from:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`Failed to fetch school logo with status ${response.status}`);
            throw new Error(`Failed to fetch school logo with status ${response.status}`);
        }
        
        // Create a blob URL for the image
        const blob = await response.blob();
        const blobUrl = URL.createObjectURL(blob);
        
        return blobUrl;
    } catch (error) {
        console.error('Error fetching school logo:', error);
        // Return a default logo or placeholder
        return '/default-school-icon.png';
    }
}

// Cleanup function for blob URLs
export function cleanupBlobUrl(url: string): void {
    if (url && url.startsWith('blob:')) {
        URL.revokeObjectURL(url);
    }
}
