import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { WelcomePage } from './components/WelcomePage';
import { SurveyPage } from './components/SurveyPage';
import { CareerAnalysis } from './components/result/CareerAnalysis';
import { DebugScreen } from './components/DebugScreen';
import { useEffect, createContext, useState } from 'react';

// Create a global context for API configuration
export const ApiContext = createContext({
  apiBaseUrl: 'https://ontrack-v2.onrender.com/api'
});

function App() {
  // Set up API configuration
  const [apiConfig] = useState({
    apiBaseUrl: 'https://ontrack-v2.onrender.com/api'
  });

  // Log important information on app mount
  useEffect(() => {
    console.log('App mounted, current URL:', window.location.href);
    console.log('Path:', window.location.pathname);
    console.log('Storage has analysis result:', !!localStorage.getItem('analysisResult'));
    
    // Log API configuration
    console.log('Using API base URL:', apiConfig.apiBaseUrl);
    
    // Override any incorrect API URL settings that might be in other files
    window.__API_BASE_URL = apiConfig.apiBaseUrl;
    
    // Check if we're using the correct API URL
    if (window.location.hostname !== 'localhost' && 
        window.location.hostname !== '127.0.0.1' && 
        !window.__API_BASE_URL?.includes('ontrack-v2.onrender.com')) {
      console.error('⚠️ WARNING: API URL is not set to the backend server!');
      console.error('Current API URL:', window.__API_BASE_URL);
      console.error('Should be:', apiConfig.apiBaseUrl);
      
      // Force correct URL
      window.__API_BASE_URL = apiConfig.apiBaseUrl;
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
  const result = localStorage.getItem('analysisResult');
  if (!result) {
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
