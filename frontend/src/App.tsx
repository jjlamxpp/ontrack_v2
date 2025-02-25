import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { WelcomePage } from './components/WelcomePage';
import { SurveyPage } from './components/SurveyPage';
import { CareerAnalysis } from './components/result/CareerAnalysis';
import { DebugScreen } from './components/DebugScreen';
import { useEffect } from 'react';

function App() {
  // Log important information on app mount
  useEffect(() => {
    console.log('App mounted, current URL:', window.location.href);
    console.log('Path:', window.location.pathname);
    console.log('Storage has analysis result:', !!localStorage.getItem('analysisResult'));
  }, []);

  return (
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
  );
}

function RequireAnalysis({ children }: { children: React.ReactNode }) {
  const result = localStorage.getItem('analysisResult');
  if (!result) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

export default App;
