import { useState, useEffect, useContext } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchQuestions, submitSurveyAndGetAnalysis, checkApiHealth } from '../services/api';
import type { Question } from '../types/survey';
import { Progress } from '@/components/ui/progress';
import { ApiContext } from '../App';

export function SurveyPage() {
  const navigate = useNavigate();
  const { questionId } = useParams();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [testFallbackVisible, setTestFallbackVisible] = useState(false);
  const apiConfig = useContext(ApiContext);
  
  // Get current page number with validation
  const currentPage = (() => {
    const page = parseInt(questionId || '1');
    return isNaN(page) || page < 1 ? 1 : page;
  })();

  // Load questions on component mount and when page changes
  useEffect(() => {
    let mounted = true;

    const loadQuestions = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('Attempting to fetch questions from API...');
        console.log('Using API base URL:', apiConfig.apiBaseUrl);
        
        const data = await fetchQuestions();
        
        if (!mounted) return;

        if (!Array.isArray(data)) {
          console.error('Invalid response format:', data);
          throw new Error('Invalid response format - expected an array of questions');
        }
        
        console.log(`Successfully loaded ${data.length} questions`);
        setQuestions(data);
        
        // Check for saved answers in localStorage
        const savedAnswers = localStorage.getItem('surveyAnswers');
        if (savedAnswers) {
          console.log('Found saved answers in localStorage');
          setAnswers(JSON.parse(savedAnswers));
        } else {
          // Initialize empty answers array
          console.log('Initializing empty answers array');
          setAnswers(new Array(data.length).fill(''));
        }
        
        // Validate current page against total questions
        const maxPages = Math.ceil(data.length / 10);
        if (currentPage > maxPages) {
          console.log(`Current page (${currentPage}) exceeds max pages (${maxPages}), redirecting to page 1`);
          navigate('/survey/1', { replace: true });
        }
      } catch (err) {
        if (!mounted) return;
        console.error('Error loading questions:', err);
        setError(err instanceof Error ? err.message : 'Failed to load questions');
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadQuestions();

    // Cleanup function
    return () => {
      mounted = false;
    };
  }, [apiConfig.apiBaseUrl, currentPage, navigate]);

  // Save answers to localStorage whenever they change
  useEffect(() => {
    if (answers.length > 0) {
      localStorage.setItem('surveyAnswers', JSON.stringify(answers));
    }
  }, [answers]);

  const questionsPerPage = 10;
  const startIndex = (currentPage - 1) * questionsPerPage;
  const currentQuestions = questions.slice(startIndex, startIndex + questionsPerPage);
  const maxPages = Math.ceil(questions.length / questionsPerPage);

  const handleAnswer = (index: number, answer: string) => {
    const newAnswers = [...answers];
    newAnswers[startIndex + index] = answer;
    setAnswers(newAnswers);
  };

  const handlePrevious = () => {
    if (currentPage > 1) {
      navigate(`/survey/${currentPage - 1}`);
    }
  };

  const handleNext = () => {
    if (currentPage < maxPages) {
      navigate(`/survey/${currentPage + 1}`);
    }
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Log the current state of answers
      console.log('Current answers state:', answers);
      
      // Validate that we have all answers
      const missingAnswers = questions.filter((_, index) => !answers[index]);
      if (missingAnswers.length > 0) {
        console.log('Missing answers for questions:', missingAnswers);
        setError('Please answer all questions before submitting.');
        setLoading(false);
        return;
      }
      
      // Normalize answers to uppercase
      const normalizedAnswers = answers.map(answer => answer.toUpperCase());
      console.log('Normalized answers:', normalizedAnswers);
      
      // Submit the survey and get analysis
      console.log('Submitting survey...');
      try {
        const result = await submitSurveyAndGetAnalysis(normalizedAnswers);
        console.log('Survey submission successful:', result);
        
        // Store the result in localStorage
        localStorage.setItem('analysisResult', JSON.stringify(result));
        
        // Clear the survey answers
        localStorage.removeItem('surveyAnswers');
        
        // Navigate to the result page
        navigate('/result');
      } catch (submitError) {
        console.error('Error during survey submission:', submitError);
        
        // Even if there's an error, we'll still try to get a result
        // The API service should now return a fallback result
        const result = await submitSurveyAndGetAnalysis(normalizedAnswers);
        
        // Store the result in localStorage
        localStorage.setItem('analysisResult', JSON.stringify(result));
        
        // Clear the survey answers
        localStorage.removeItem('surveyAnswers');
        
        // Navigate to the result page
        navigate('/result');
      }
    } catch (error) {
      console.error('Unhandled error in handleSubmit:', error);
      setError('An error occurred while submitting your survey. Please try again or use one of the debug options below.');
      setLoading(false);
    }
  };

  // Add a test function to verify API connectivity
  const testApiConnection = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Test the basic API endpoint
      const testUrl = `${apiConfig.apiBaseUrl}/test`;
      console.log('Testing API connection at:', testUrl);
      
      const response = await fetch(testUrl);
      const data = await response.json();
      
      console.log('API test response:', data);
      
      if (data.status === 'ok') {
        alert('API connection successful! The API is working.');
      } else {
        alert(`API test failed: ${data.message || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('API test error:', error);
      alert(`API test error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };
  
  // Add a test function to verify survey submission
  const testSurveySubmission = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Test the survey submission endpoint
      const testUrl = `${apiConfig.apiBaseUrl}/test-submit`;
      console.log('Testing survey submission at:', testUrl);
      
      const response = await fetch(testUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ answers: Array(42).fill('YES') }),
      });
      
      const data = await response.json();
      console.log('Test survey submission response:', data);
      
      if (data.personality && data.industries) {
        // Store the result in localStorage
        localStorage.setItem('analysisResult', JSON.stringify(data));
        
        // Navigate to result page
        navigate('/result');
      } else {
        alert('Test survey submission failed: Invalid response format');
      }
    } catch (error) {
      console.error('Test survey submission error:', error);
      alert(`Test survey submission error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  // Add a debug function to test the API
  const debugApi = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Import the debug function
      const { debugSurveyTest } = await import('../services/api');
      
      // Run the debug test
      const result = await debugSurveyTest();
      
      // Show the result in an alert
      alert('Debug test completed. Check the console for details.');
      console.log('Debug test result:', result);
      
      // If the test was successful, show a more detailed alert
      if (result.test_processing && result.test_processing.success) {
        alert(`Test processing successful!\nPersonality type: ${result.test_processing.personality_type}\nIndustries: ${result.test_processing.industries_count}`);
      }
    } catch (error) {
      console.error('Error in debug test:', error);
      setError(error instanceof Error ? error.message : 'An error occurred during the debug test');
    } finally {
      setLoading(false);
    }
  };

  // Add a function to check the file system
  const checkFileSystem = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Import the debug function
      const { debugFileSystem } = await import('../services/api');
      
      // Run the file system check
      const result = await debugFileSystem();
      
      // Show the result in an alert
      alert('File system check completed. Check the console for details.');
      console.log('File system check result:', result);
      
      // If the database file exists, show more details
      if (result.database_checks && result.database_checks.file_exists !== false) {
        if (result.database_checks.initialization === 'success') {
          alert(`Database check successful!\nQuestions count: ${result.database_checks.questions_count}\nTest result keys: ${result.database_checks.test_result_keys.join(', ')}`);
        } else {
          alert(`Database file exists but initialization failed: ${result.database_checks.initialization_error}`);
        }
      } else {
        alert('Database file does not exist. Check the console for more details.');
      }
    } catch (error) {
      console.error('Error in file system check:', error);
      setError(error instanceof Error ? error.message : 'An error occurred during the file system check');
    } finally {
      setLoading(false);
    }
  };

  // Add a function to use the direct test endpoint
  const useDirectTest = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Import the direct test function
      const { directTest } = await import('../services/api');
      
      // Convert all answers to uppercase for consistency
      const normalizedAnswers = answers.map(answer => answer.toUpperCase());
      console.log('Normalized answers for direct test:', normalizedAnswers);
      
      // Use the direct test endpoint
      const result = await directTest(normalizedAnswers);
      console.log('Direct test successful, received result:', result);
      
      // Store the result in localStorage
      localStorage.setItem('analysisResult', JSON.stringify(result));
      console.log('Analysis result stored in localStorage');
      
      // Clear survey answers after successful submission
      localStorage.removeItem('surveyAnswers');
      
      // Navigate to result page
      console.log('Navigating to result page...');
      navigate('/result');
    } catch (error) {
      console.error('Error in direct test:', error);
      setError(error instanceof Error ? error.message : 'An error occurred during the direct test');
    } finally {
      setLoading(false);
    }
  };

  const checkHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Checking API health...');
      const healthData = await checkApiHealth();
      
      // Display the health check result
      alert(JSON.stringify(healthData, null, 2));
      
      setLoading(false);
    } catch (error) {
      console.error('Error checking API health:', error);
      setError('Failed to check API health. See console for details.');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen w-full bg-[#1B2541] text-white flex items-center justify-center">
        <div className="text-xl">Loading questions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen w-full bg-[#1B2541] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-500 mb-4">Error: {error}</div>
          <div className="flex gap-4 justify-center">
            <button 
              onClick={() => window.location.reload()} 
              className="px-4 py-2 bg-blue-500 rounded hover:bg-blue-600"
            >
              Retry
            </button>
            
            {testFallbackVisible && (
              <button 
                onClick={testSurveySubmission} 
                className="px-4 py-2 bg-purple-500 rounded hover:bg-purple-600"
              >
                Use Test Data
              </button>
            )}
            
            <button 
              onClick={debugApi} 
              className="px-4 py-2 bg-yellow-500 rounded hover:bg-yellow-600"
            >
              Debug API
            </button>
            
            <button 
              onClick={checkFileSystem} 
              className="px-4 py-2 bg-orange-500 rounded hover:bg-orange-600"
            >
              Check Files
            </button>
            
            <button 
              onClick={useDirectTest} 
              className="px-4 py-2 bg-red-500 rounded hover:bg-red-600"
            >
              Direct Test
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen w-full bg-[#1B2541] text-white">
      <div className="max-w-4xl mx-auto px-4 py-8 min-h-screen flex flex-col">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-6">
            <span className="text-[#3B82F6]">On</span>Track
          </h1>
          <Progress value={(currentPage / maxPages) * 100} className="mb-4" />
          <p className="text-sm text-gray-400">
            Questions {startIndex + 1}-{Math.min(startIndex + currentQuestions.length, questions.length)} of {questions.length}
          </p>
        </div>

        <div className="flex-grow space-y-6 mb-8">
          {currentQuestions.map((question, index) => (
            <div 
              key={question.id} 
              className="bg-white/10 rounded-lg p-6 shadow-lg hover:bg-white/15 transition-colors"
            >
              <p className="text-lg mb-4">{question.question_text}</p>
              <div className="flex gap-4">
                <button
                  className={`flex-1 py-3 rounded-lg transition-colors ${
                    answers[startIndex + index] === 'YES'
                      ? 'bg-[#3B82F6] hover:bg-[#2563EB]'
                      : 'bg-white/20 hover:bg-[#3B82F6]/70'
                  }`}
                  onClick={() => handleAnswer(index, 'YES')}
                >
                  YES
                </button>
                <button
                  className={`flex-1 py-3 rounded-lg transition-colors ${
                    answers[startIndex + index] === 'NO'
                      ? 'bg-[#F87171] hover:bg-[#EF4444]'
                      : 'bg-white/20 hover:bg-[#F87171]/70'
                  }`}
                  onClick={() => handleAnswer(index, 'NO')}
                >
                  NO
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-center gap-4 mt-auto pb-8">
          {currentPage > 1 && (
            <button
              className="px-8 py-3 rounded-full bg-gray-500 hover:bg-gray-600 transition-colors"
              onClick={handlePrevious}
            >
              Back
            </button>
          )}
          
          {currentPage < maxPages ? (
            <button
              className={`px-8 py-3 rounded-full transition-colors ${
                currentQuestions.every((_, index) => answers[startIndex + index] !== '')
                  ? 'bg-[#3B82F6] hover:bg-[#2563EB]'
                  : 'bg-gray-500 cursor-not-allowed'
              }`}
              onClick={handleNext}
              disabled={!currentQuestions.every((_, index) => answers[startIndex + index] !== '')}
            >
              Next Page
            </button>
          ) : (
            <>
              <button
                className={`px-8 py-3 rounded-full transition-colors ${
                  answers.every(answer => answer !== '')
                    ? 'bg-green-500 hover:bg-green-600'
                    : 'bg-gray-500 cursor-not-allowed'
                }`}
                onClick={handleSubmit}
                disabled={!answers.every(answer => answer !== '')}
              >
                Submit Survey ({answers.filter(a => a !== '').length}/{questions.length})
              </button>
              
              {/* Add a test button for debugging */}
              <button
                className="px-8 py-3 rounded-full bg-purple-500 hover:bg-purple-600 transition-colors"
                onClick={testSurveySubmission}
              >
                Test Submit
              </button>
              
              {/* Add a debug button */}
              <button
                className="px-8 py-3 rounded-full bg-yellow-500 hover:bg-yellow-600 transition-colors"
                onClick={debugApi}
              >
                Debug API
              </button>
              
              {/* Add a file system check button */}
              <button
                className="px-8 py-3 rounded-full bg-orange-500 hover:bg-orange-600 transition-colors"
                onClick={checkFileSystem}
              >
                Check Files
              </button>
              
              {/* Add a direct test button */}
              <button
                className="px-8 py-3 rounded-full bg-red-500 hover:bg-red-600 transition-colors"
                onClick={useDirectTest}
              >
                Direct Test
              </button>
            </>
          )}
        </div>

        <div className="flex justify-between mt-8">
          <button
            onClick={handlePrevious}
            className={`bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded ${
              currentPage === 0 ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            disabled={currentPage === 0 || loading}
          >
            Previous
          </button>
          
          {currentPage < maxPages - 1 ? (
            <button
              onClick={handleNext}
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
              disabled={loading}
            >
              Next
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                onClick={checkHealth}
                className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
                disabled={loading}
              >
                Check Health
              </button>
              <button
                onClick={handleSubmit}
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
                disabled={loading}
              >
                {loading ? 'Submitting...' : 'Submit'}
              </button>
            </div>
          )}
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
            <strong className="font-bold">Error: </strong>
            <span className="block sm:inline">{error}</span>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                onClick={checkHealth}
                className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
              >
                Check Health
              </button>
              <button
                onClick={checkFileSystem}
                className="bg-orange-500 hover:bg-orange-700 text-white font-bold py-2 px-4 rounded"
              >
                Check Files
              </button>
              <button
                onClick={debugApi}
                className="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded"
              >
                Debug API
              </button>
              <button
                onClick={useDirectTest}
                className="bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded"
              >
                Direct Test
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
