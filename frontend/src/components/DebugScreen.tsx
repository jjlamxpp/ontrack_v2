import { useState, useEffect } from 'react';

export function DebugScreen() {
  const [apiStatus, setApiStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    async function testApi() {
      try {
        setLoading(true);
        
        // Test backend health
        const healthResponse = await fetch('/api-test');
        const healthData = await healthResponse.json();
        
        // Test survey API specifically
        const surveyTestResponse = await fetch('/api/survey/test');
        const surveyTestData = await surveyTestResponse.json();
        
        setApiStatus({
          health: healthData,
          surveyApi: surveyTestData,
          location: window.location,
          localStorage: {
            hasAnalysisResult: !!localStorage.getItem('analysisResult')
          }
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    }
    
    testApi();
  }, []);
  
  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">OnTrack Debug Screen</h1>
      
      {loading && <p>Loading diagnostic information...</p>}
      
      {error && (
        <div className="p-4 bg-red-100 border border-red-300 rounded mb-4">
          <h2 className="font-bold text-red-700">Error</h2>
          <p>{error}</p>
        </div>
      )}
      
      {apiStatus && (
        <div>
          <h2 className="text-xl font-semibold mb-2">System Status</h2>
          <pre className="bg-gray-100 p-4 rounded overflow-auto">
            {JSON.stringify(apiStatus, null, 2)}
          </pre>
          
          <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 border rounded">
              <h3 className="font-semibold">Navigation Tests</h3>
              <div className="flex flex-col gap-2 mt-2">
                <a href="/" className="text-blue-500 hover:underline">Home</a>
                <a href="/survey/1" className="text-blue-500 hover:underline">Survey Question 1</a>
                <a href="/result" className="text-blue-500 hover:underline">Results Page</a>
              </div>
            </div>
            
            <div className="p-4 border rounded">
              <h3 className="font-semibold">API Tests</h3>
              <div className="flex flex-col gap-2 mt-2">
                <button 
                  onClick={() => window.open('/api/survey/questions', '_blank')}
                  className="text-blue-500 hover:underline text-left"
                >
                  Test Questions API
                </button>
                <button 
                  onClick={() => window.open('/api/survey/test', '_blank')}
                  className="text-blue-500 hover:underline text-left"
                >
                  Test Survey API
                </button>
                <button 
                  onClick={() => window.open('/api-test', '_blank')}
                  className="text-blue-500 hover:underline text-left"
                >
                  Test General API
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
