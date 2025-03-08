import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { WelcomePage } from './components/WelcomePage';
import { SurveyPage } from './components/SurveyPage';
import { CareerAnalysis } from './components/result/CareerAnalysis';
import { DebugScreen } from './components/DebugScreen';
import { useEffect, createContext, useState } from 'react';

// Create a global context for API configuration
export const ApiContext = createContext({
  apiBaseUrl: '/api'
});

function App() {
  // Set up API configuration - use window.location to determine the base URL
  const [apiConfig] = useState(() => {
    // Always use relative URL for API
    const apiBaseUrl = '/api';
    
    // Set global variable for other components
    window.__API_BASE_URL = apiBaseUrl;
    
    return { apiBaseUrl };
  });

  // Log important information on app mount
  useEffect(() => {
    console.log('App mounted, current URL:', window.location.href);
    console.log('Path:', window.location.pathname);
    console.log('Storage has analysis result:', !!localStorage.getItem('analysisResult'));
    
    // Log API configuration
    console.log('Using API base URL:', apiConfig.apiBaseUrl);
    
    // Handle page refresh - check if we're on a "not found" page
    // This helps recover from 404 errors when refreshing non-root routes
    const isNotFoundPage = document.body.textContent?.trim().toLowerCase() === 'not found';
    if (isNotFoundPage) {
      console.log('Detected "Not Found" page, redirecting to home');
      window.location.href = '/';
    }
  }, [apiConfig.apiBaseUrl]);

  return (
    <ApiContext.Provider value={apiConfig}>
      <Router>
        <Routes>
          <Route path="/" element={<WelcomePage />} />
          <Route path="/survey/:questionId" element={<SurveyPage />} />
          <Route 
            path="/result" 
            element={
              <RequireAnalysis>
                <CareerAnalysis />
              </RequireAnalysis>
            } 
          />
          {/* Add debug route */}
          <Route path="/debug" element={<DebugScreen />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </ApiContext.Provider>
  );
}

function RequireAnalysis({ children }: { children: React.ReactNode }) {
  const [isValid, setIsValid] = useState<boolean | null>(null);
  
  useEffect(() => {
    const result = localStorage.getItem('analysisResult');
    if (!result) {
      setIsValid(false);
      return;
    }
    
    try {
      const parsed = JSON.parse(result);
      // Validate the result structure
      setIsValid(!!parsed.personality && !!parsed.industries);
    } catch (e) {
      console.error('Error parsing analysis result:', e);
      setIsValid(false);
    }
  }, []);
  
  if (isValid === null) {
    // Still checking
    return <div className="min-h-screen w-full bg-[#1B2541] text-white flex items-center justify-center">
      <div className="text-xl">Loading...</div>
    </div>;
  }
  
  if (!isValid) {
    return <Navigate to="/" replace />;
  }
  
  return <>{children}</>;
}

// Add this to the global Window interface
declare global {
  interface Window {
    __API_BASE_URL?: string;
  }
}

export default App;
