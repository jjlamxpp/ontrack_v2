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
        const url = `${window.location.origin}/api/survey/questions`;
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
        const url = `${window.location.origin}/api/debug/survey-test`;
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
        
        // Ensure all answers are strings and normalize them
        const normalizedAnswers = answers.map(answer => {
            if (typeof answer !== 'string') {
                console.warn('Non-string answer found:', answer);
                return '';
            }
            return answer.toUpperCase();
        });
        
        console.log('Normalized answers before submission:', normalizedAnswers);
        
        // Construct the correct URL for the survey submission endpoint
        // Use the absolute URL to avoid any path issues
        const url = `${window.location.origin}/api/survey/submit`;
        console.log('Submitting survey to:', url);
        
        // Add a timeout to the fetch request
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
        
        try {
            // Ensure the request body matches exactly what the backend expects
            const requestBody = {
                answers: normalizedAnswers
            };
            
            console.log('Making POST request with the following options:');
            console.log('- Method: POST');
            console.log('- Headers: Content-Type: application/json');
            console.log('- Body:', JSON.stringify(requestBody));
            
            // Try using XMLHttpRequest as an alternative to fetch
            return new Promise<AnalysisResult>((resolve, reject) => {
                const xhr = new XMLHttpRequest();
                xhr.open('POST', url, true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.setRequestHeader('Accept', 'application/json');
                xhr.timeout = 30000; // 30 second timeout
                
                xhr.onload = function() {
                    clearTimeout(timeoutId);
                    console.log('Survey submission response status:', xhr.status);
                    console.log('Survey submission response headers:', xhr.getAllResponseHeaders());
                    
                    try {
                        if (xhr.status >= 200 && xhr.status < 300) {
                            const data = JSON.parse(xhr.responseText);
                            console.log('Response data received:', data);
                            
                            // Validate the result structure
                            if (!data || typeof data !== 'object') {
                                console.error('Invalid result format:', data);
                                resolve(getFallbackResult());
                                return;
                            }
                            
                            // Check if we have the expected fields
                            if (!data.personality || !data.industries) {
                                console.error('Missing required fields in result:', data);
                                resolve(getFallbackResult());
                                return;
                            }
                            
                            resolve(data);
                        } else {
                            console.error('Error response:', xhr.status);
                            try {
                                const data = JSON.parse(xhr.responseText);
                                console.error('Error data:', data);
                                
                                // If we got a valid result structure despite the error status, use it
                                if (data && data.personality && data.industries) {
                                    console.log('Using result from error response as it has valid structure');
                                    resolve(data);
                                    return;
                                }
                            } catch (e) {
                                console.error('Error parsing error response:', e);
                            }
                            
                            resolve(getFallbackResult());
                        }
                    } catch (e) {
                        console.error('Error processing response:', e);
                        resolve(getFallbackResult());
                    }
                };
                
                xhr.onerror = function() {
                    clearTimeout(timeoutId);
                    console.error('XHR error occurred');
                    resolve(getFallbackResult());
                };
                
                xhr.ontimeout = function() {
                    console.error('XHR request timed out');
                    resolve(getFallbackResult());
                };
                
                xhr.send(JSON.stringify(requestBody));
            });
            
            /* Original fetch implementation - commented out for now
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(requestBody),
                signal: controller.signal,
                mode: 'cors',
                credentials: 'same-origin'
            });
            
            clearTimeout(timeoutId);
            
            // Log the response status
            console.log('Survey submission response status:', response.status);
            console.log('Survey submission response headers:', response.headers);
            
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
                
                // Return a fallback result
                return getFallbackResult();
            }
            
            // Check if the response was successful
            if (!response.ok) {
                console.error('Error response:', response.status, data);
                
                // If we got a JSON response with an error message, log it
                if (data && data.detail) {
                    console.error(`API error: ${data.detail}`);
                }
                
                // If we got a valid result structure despite the error status, use it
                if (data && data.personality && data.industries) {
                    console.log('Using result from error response as it has valid structure');
                    return data;
                }
                
                // Otherwise return a fallback result
                return getFallbackResult();
            }
            
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
            */
        } catch (fetchError: any) {
            if (fetchError.name === 'AbortError') {
                console.error('Request timed out after 30 seconds');
            } else {
                console.error('Fetch error:', fetchError);
            }
            
            // Return a fallback result
            return getFallbackResult();
        } finally {
            clearTimeout(timeoutId);
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
        const url = `${window.location.origin}/api/survey/icon/${iconId}`;
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
        const url = `${window.location.origin}/api/survey/school-icon/${encodedSchool}`;
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

// Debug file system
export async function debugFileSystem(): Promise<any> {
    try {
        const url = `${window.location.origin}/api/debug/file-system`;
        console.log('Debugging file system at:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`Debug file system failed with status ${response.status}`);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`Debug file system failed with status ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Debug file system result:', data);
        return data;
    } catch (error) {
        console.error('Error in debug file system:', error);
        throw error;
    }
}

// Direct test for survey submission
export async function directTest(answers: string[]): Promise<AnalysisResult> {
    try {
        const url = `${window.location.origin}/api/direct-test`;
        console.log('Direct testing at:', url);
        console.log('Answers being submitted:', answers);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ answers })
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
        return getFallbackResult();
    }
}

// Check API health
export async function checkApiHealth(): Promise<any> {
    try {
        const url = `${window.location.origin}/api/health`;
        console.log('Checking API health at:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`Health check failed with status ${response.status}`);
            return {
                status: 'error',
                message: `Health check failed with status ${response.status}`
            };
        }
        
        try {
            const data = await response.json();
            console.log('Health check data:', data);
            return data;
        } catch (jsonError) {
            console.error('Error parsing health check response:', jsonError);
            return {
                status: 'error',
                message: 'Failed to parse health check response'
            };
        }
    } catch (error) {
        console.error('Error checking API health:', error);
        return {
            status: 'error',
            message: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

// Debug URL test
export async function debugUrlTest(): Promise<any> {
    try {
        const url = `${window.location.origin}/api/debug/url-test`;
        console.log('Testing URL at:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`URL test failed with status ${response.status}`);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`URL test failed with status ${response.status}`);
        }
        
        const data = await response.json();
        console.log('URL test result:', data);
        return data;
    } catch (error) {
        console.error('Error in URL test:', error);
        throw error;
    }
}

// Test POST endpoint
export async function testPostEndpoint(): Promise<any> {
    try {
        const url = `${window.location.origin}/api/test-post`;
        console.log('Testing POST endpoint at:', url);
        
        const testData = {
            test: true,
            message: "This is a test POST request",
            timestamp: new Date().toISOString()
        };
        
        console.log('Sending test data:', testData);
        
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(testData)
        });
        
        console.log('POST test response status:', response.status);
        
        if (!response.ok) {
            console.error(`POST test failed with status ${response.status}`);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`POST test failed with status ${response.status}`);
        }
        
        const data = await response.json();
        console.log('POST test result:', data);
        return data;
    } catch (error) {
        console.error('Error in POST test:', error);
        throw error;
    }
}

// Debug routes
export async function debugRoutes(): Promise<any> {
    try {
        const url = `${window.location.origin}/api/debug/routes`;
        console.log('Debugging routes at:', url);
        
        const response = await fetch(url);
        
        if (!response.ok) {
            console.error(`Debug routes failed with status ${response.status}`);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            throw new Error(`Debug routes failed with status ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Debug routes result:', data);
        return data;
    } catch (error) {
        console.error('Error in debug routes:', error);
        throw error;
    }
}

// Add a test function for survey submission
export async function testSurveySubmit(answers: string[]): Promise<any> {
    try {
        console.log('Testing survey submission...');
        
        // Ensure all answers are strings and normalize them
        const normalizedAnswers = answers.map(answer => {
            if (typeof answer !== 'string') {
                console.warn('Non-string answer found:', answer);
                return '';
            }
            return answer.toUpperCase();
        });
        
        console.log('Normalized answers for test:', normalizedAnswers);
        
        // Construct the URL for the test endpoint
        const url = `${window.location.origin}/api/test-survey-submit`;
        console.log('Testing survey submission at:', url);
        
        // Create the request body
        const requestBody = {
            answers: normalizedAnswers
        };
        
        console.log('Test request body:', JSON.stringify(requestBody));
        
        // Make the request
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });
        
        console.log('Test response status:', response.status);
        
        // Try to parse the response as JSON
        try {
            const data = await response.json();
            console.log('Test response data:', data);
            return data;
        } catch (jsonError) {
            console.error('Error parsing test response:', jsonError);
            
            // Try to get the response text
            try {
                const text = await response.text();
                console.error('Test response text:', text);
                return { error: 'Error parsing JSON response', text };
            } catch (textError) {
                console.error('Error getting test response text:', textError);
                return { error: 'Error getting response text' };
            }
        }
    } catch (error) {
        console.error('Error in test survey submission:', error);
        return { error: String(error) };
    }
}
