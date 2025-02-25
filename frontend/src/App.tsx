import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { WelcomePage } from './components/WelcomePage';
import { SurveyPage } from './components/SurveyPage';
import { CareerAnalysis } from './components/result/CareerAnalysis';
import { useParams } from 'react-router-dom';

function App() {
  return (
    <Router>
      <Routes>
        {/* Default route redirects to welcome page */}
        <Route path="/" element={<WelcomePage />} />
        <Route path="/survey" element={<Navigate to="/survey/1" replace />} />
        <Route path="/survey/:questionId" element={<RequireSurvey><SurveyPage /></RequireSurvey>} />
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

// Add a new helper component to validate survey routes
function RequireSurvey({ children }: { children: React.ReactNode }) {
  const { questionId } = useParams();
  const pageNum = parseInt(questionId || '1');

  if (isNaN(pageNum) || pageNum < 1) {
    return <Navigate to="/survey/1" replace />;
  }

  return <>{children}</>;
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
