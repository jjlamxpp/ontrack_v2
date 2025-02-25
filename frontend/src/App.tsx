import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { WelcomePage } from './components/WelcomePage';
import { SurveyPage } from './components/SurveyPage';
import { CareerAnalysis } from './components/result/CareerAnalysis';
import { useEffect } from 'react';

function App() {
  // Add this to debug routing issues
  useEffect(() => {
    console.log('App mounted, pathname:', window.location.pathname);
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
        {/* Catch-all route */}
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
