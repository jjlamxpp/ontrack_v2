import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { WelcomePage } from './components/WelcomePage';
import { SurveyPage } from './components/SurveyPage';
import { CareerAnalysis } from './components/result/CareerAnalysis';

function App() {
  return (
    <Router>
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
        {/* Important: Add this catch-all route */}
        <Route path="*" element={<Navigate to="/" />} />
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
