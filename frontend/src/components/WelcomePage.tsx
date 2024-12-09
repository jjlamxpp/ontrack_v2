import { useNavigate } from 'react-router-dom';
import { useEffect } from 'react';
import { Button } from '@/components/ui/button';

export const WelcomePage = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Clear any previous results when landing on welcome page
    localStorage.removeItem('analysisResult');
    localStorage.removeItem('surveyAnswers');
  }, []);

  return (
    <main className="min-h-screen bg-[#1B2541] text-white flex flex-col items-center justify-center p-4">
      <div className="max-w-2xl w-full text-center space-y-8">
        <div className="space-y-2">
          <h1 className="text-4xl font-bold">
            <span className="text-[#3B82F6]">On</span>Track
          </h1>
          <p className="text-lg">
            Your journey starts here! Take the first step toward a brighter future by
            completing our quick and insightful OnTrack survey.
          </p>
        </div>

        <div className="space-y-4">
          <h2 className="text-xl font-semibold">How It Works</h2>
          <ol className="space-y-2 text-left">
            <li>1. Take the Survey: Answer 40 quick questions designed to reveal your interests and skills.</li>
            <li>2. Get Your Report: Receive a detailed analysis of your career preferences.</li>
            <li>3. Plan Your Path: Use expert recommendations to explore careers and plan your next steps.</li>
          </ol>
        </div>

        <Button 
          size="lg"
          className="bg-[#3B82F6] hover:bg-[#2563EB] text-white text-xl px-12 py-6 rounded-full relative"
          onClick={() => navigate('/survey/1')}
        >
          <span className="relative z-10">START</span>
          <div className="absolute inset-0 rounded-full bg-[#3B82F6] blur-lg opacity-50" />
        </Button>
      </div>
    </main>
  );
};