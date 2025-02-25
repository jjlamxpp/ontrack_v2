import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { WelcomePage } from './components/WelcomePage';
import { SurveyPage } from './components/SurveyPage';
import { CareerAnalysis } from './components/result/CareerAnalysis';

function App() {
  return (
    <Router>
      <Routes>
        {/* Default route redirects to welcome page */}
        <Route path="/" element={<WelcomePage />} />
        <Route path="/survey/:questionId" element={<SurveyPage />} />
        <Route path="/survey" element={<Navigate to="/survey/1" replace />} />
        <Route 
          path="/result" 
          element={
            <RequireAnalysis>
              <CareerAnalysis />
            </RequireAnalysis>
          } 
        />
        {/* Catch all other routes and redirect to welcome */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}

// Helper component to check if analysis data exists
function RequireAnalysis({ children }: { children: React.ReactNode }) {
  const result = localStorage.getItem('analysisResult');
  
  if (!result) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

export default App;
