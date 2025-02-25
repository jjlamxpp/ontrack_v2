import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { WelcomePage } from './components/WelcomePage';
import { SurveyPage } from './components/SurveyPage';
import { CareerAnalysis } from './components/result/CareerAnalysis';

function App() {
  // Get the base URL from environment or default to '/'
  const baseUrl = import.meta.env.BASE_URL || '/';

  return (
    <Router basename={baseUrl}>
      <Routes>
        <Route path="/" element={<WelcomePage />} />
        <Route path="/survey" element={<Navigate to="/survey/1" replace />} />
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
