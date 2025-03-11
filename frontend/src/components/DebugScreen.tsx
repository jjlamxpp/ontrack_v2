import { useContext, useEffect, useState } from 'react';
import { ApiContext } from '../App';

export function DebugScreen() {
  const apiConfig = useContext(ApiContext);
  const [testResults, setTestResults] = useState<any>(null);
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [submissionTest, setSubmissionTest] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function testApiConnection() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiConfig.apiBaseUrl}/survey/test`, {
        mode: 'cors',
        credentials: 'omit'
      });
      
      const data = await response.json();
      setTestResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  async function fetchDebugInfo() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${apiConfig.apiBaseUrl}/debug`, {
        mode: 'cors',
        credentials: 'omit'
      });
      
      const data = await response.json();
      setDebugInfo(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  }

  async function testSurveySubmission() {
    setLoading(true);
    setError(null);
    try {
      // Create a test survey with 42 "YES" answers
      const testAnswers = Array(42).fill("YES");
      
      // Log the request details
      console.log('Test submission URL:', `${apiConfig.apiBaseUrl}/survey/submit`);
      console.log('Test submission body:', JSON.stringify({ answers: testAnswers }));
      
      // Make the request
      const response = await fetch(`${apiConfig.apiBaseUrl}/survey/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({ answers: testAnswers }),
        mode: 'cors',
        credentials: 'include'
      });
      
      // Log the response status
      console.log('Test submission response status:', response.status);
      
      // Try to parse the response
      try {
        const data = await response.json();
        console.log('Test submission response:', data);
        setSubmissionTest({
          status: response.status,
          statusText: response.statusText,
          data: data
        });
      } catch (jsonError) {
        // If we can't parse JSON, try to get the text
        const text = await response.text();
        setSubmissionTest({
          status: response.status,
          statusText: response.statusText,
          text: text
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      setSubmissionTest({
        error: err instanceof Error ? err.message : 'Unknown error'
      });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    testApiConnection();
    fetchDebugInfo();
  }, [apiConfig.apiBaseUrl]);

  return (
    <div className="min-h-screen w-full bg-[#1B2541] text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">API Debug Screen</h1>
        
        <div className="bg-white/10 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">API Configuration</h2>
          <div className="space-y-2">
            <p><strong>API Base URL:</strong> {apiConfig.apiBaseUrl}</p>
            <p><strong>Window Location:</strong> {window.location.href}</p>
            <p><strong>Global API URL:</strong> {window.__API_BASE_URL || 'Not set'}</p>
            <p><strong>Environment Variables:</strong></p>
            <pre className="whitespace-pre-wrap text-sm bg-black/30 p-2 rounded">
              VITE_API_URL: {import.meta.env.VITE_API_URL || 'Not set'}
            </pre>
          </div>
        </div>
        
        <div className="bg-white/10 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">API Connection Test</h2>
          
          {loading && <p>Testing connection...</p>}
          
          {error && (
            <div className="bg-red-500/20 p-4 rounded mb-4">
              <p className="text-red-300">Error: {error}</p>
            </div>
          )}
          
          {testResults && (
            <div className="bg-green-500/20 p-4 rounded mb-4">
              <h3 className="font-medium mb-2">Test Results:</h3>
              <pre className="whitespace-pre-wrap text-sm">
                {JSON.stringify(testResults, null, 2)}
              </pre>
            </div>
          )}
          
          <button 
            onClick={testApiConnection}
            className="px-4 py-2 bg-blue-500 rounded hover:bg-blue-600 mt-4 mr-2"
          >
            Test Connection Again
          </button>
          
          <button 
            onClick={fetchDebugInfo}
            className="px-4 py-2 bg-blue-500 rounded hover:bg-blue-600 mt-4"
          >
            Fetch Debug Info
          </button>
        </div>
        
        {debugInfo && (
          <div className="bg-white/10 p-6 rounded-lg mb-6">
            <h2 className="text-xl font-semibold mb-4">Server Debug Info</h2>
            <pre className="whitespace-pre-wrap text-sm bg-black/30 p-2 rounded overflow-auto max-h-96">
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </div>
        )}
        
        <div className="bg-white/10 p-6 rounded-lg mb-6">
          <h2 className="text-xl font-semibold mb-4">Test Survey Submission</h2>
          <p className="mb-4">This will submit a test survey with 42 "YES" answers.</p>
          
          <button 
            onClick={testSurveySubmission}
            className="px-4 py-2 bg-green-500 rounded hover:bg-green-600 mb-4"
            disabled={loading}
          >
            {loading ? 'Testing...' : 'Test Survey Submission'}
          </button>
          
          {submissionTest && (
            <div className={`p-4 rounded mb-4 ${
              submissionTest.error ? 'bg-red-500/20' : 'bg-green-500/20'
            }`}>
              <h3 className="font-medium mb-2">Submission Test Results:</h3>
              <pre className="whitespace-pre-wrap text-sm">
                {JSON.stringify(submissionTest, null, 2)}
              </pre>
            </div>
          )}
        </div>
        
        <div className="bg-white/10 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Local Storage</h2>
          <div className="space-y-2">
            <p><strong>Survey Answers:</strong> {localStorage.getItem('surveyAnswers') ? 'Present' : 'Not found'}</p>
            <p><strong>Analysis Result:</strong> {localStorage.getItem('analysisResult') ? 'Present' : 'Not found'}</p>
          </div>
          <button 
            onClick={() => {
              localStorage.removeItem('surveyAnswers');
              localStorage.removeItem('analysisResult');
              window.location.reload();
            }}
            className="px-4 py-2 bg-red-500 rounded hover:bg-red-600 mt-4"
          >
            Clear Local Storage
          </button>
        </div>
        
        <div className="mt-6">
          <a 
            href="/"
            className="px-4 py-2 bg-gray-500 rounded hover:bg-gray-600 inline-block"
          >
            Back to Home
          </a>
        </div>
      </div>
    </div>
  );
}
