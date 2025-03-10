import { useState, useEffect, useContext } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchQuestions, submitSurveyAndGetAnalysis } from '../services/api';
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

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      navigate(`/survey/${currentPage - 1}`);
    }
  };

  const handleNextPage = () => {
    if (currentPage < maxPages) {
      navigate(`/survey/${currentPage + 1}`);
    }
  };

  const handleSubmit = async () => {
    try {
      if (!answers.every(answer => answer !== '')) {
        setError('Please answer all questions before submitting');
        return;
      }

      setLoading(true);
      console.log('Submitting survey answers...');
      console.log('Total answers:', answers.length);
      console.log('Answers:', answers);
      
      // Clear any previous errors
      setError(null);
      
      try {
        // Convert all answers to uppercase for consistency
        const normalizedAnswers = answers.map(answer => answer.toUpperCase());
        console.log('Normalized answers:', normalizedAnswers);
        
        // Add a delay to ensure the loading state is visible
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // Submit the survey and get the analysis
        console.log('Calling submitSurveyAndGetAnalysis...');
        const result = await submitSurveyAndGetAnalysis(normalizedAnswers);
        console.log('Survey submitted successfully, received analysis result:', result);
        
        // Validate the result structure
        if (!result.personality || !result.industries) {
          console.error('Invalid result structure:', result);
          throw new Error('Invalid result structure received from API');
        }
        
        // Store the result in localStorage
        localStorage.setItem('analysisResult', JSON.stringify(result));
        console.log('Analysis result stored in localStorage');
        
        // Clear survey answers after successful submission
        localStorage.removeItem('surveyAnswers');
        
        // Navigate to result page
        console.log('Navigating to result page...');
        navigate('/result');
      } catch (submitError) {
        console.error('Error during survey submission:', submitError);
        
        // Show a more user-friendly error message
        if (submitError instanceof Error) {
          if (submitError.message.includes('timed out')) {
            setError('The request timed out. Please check your internet connection and try again.');
          } else if (submitError.message.includes('API error')) {
            setError(`Server error: ${submitError.message}`);
          } else if (submitError.message.includes('parse')) {
            setError('There was a problem processing the server response. Please try again.');
          } else {
            setError(`Failed to submit survey: ${submitError.message}`);
          }
        } else {
          setError('An unknown error occurred. Please try again.');
        }
        
        // Add a button to try the test submission as fallback
        setTestFallbackVisible(true);
      }
    } catch (err) {
      console.error('Unexpected error in handleSubmit:', err);
      setError(err instanceof Error ? err.message : 'An unexpected error occurred. Please try again.');
      // Add a button to try the test submission as fallback
      setTestFallbackVisible(true);
    } finally {
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
              onClick={handlePreviousPage}
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
              onClick={handleNextPage}
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
            </>
          )}
        </div>
      </div>
    </div>
  );
}
