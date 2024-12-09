'use client'

import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { fetchQuestions, submitSurveyAndGetAnalysis } from '../services/api';
import type { Question } from '../types/survey';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

export function SurveyPage() {
  const navigate = useNavigate();
  const { questionId } = useParams();
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const currentPage = questionId ? parseInt(questionId) : 1;

  useEffect(() => {
    const loadQuestions = async () => {
      try {
        setLoading(true);
        const data = await fetchQuestions();
        setQuestions(data);
        const savedAnswers = localStorage.getItem('surveyAnswers');
        if (savedAnswers) {
          setAnswers(JSON.parse(savedAnswers));
        } else {
          setAnswers(new Array(data.length).fill(''));
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load questions');
      } finally {
        setLoading(false);
      }
    };

    loadQuestions();
  }, []);

  useEffect(() => {
    if (answers.length > 0) {
      localStorage.setItem('surveyAnswers', JSON.stringify(answers));
    }
  }, [answers]);

  const handleAnswer = (index: number, answer: string) => {
    const newAnswers = [...answers];
    newAnswers[index] = answer;
    setAnswers(newAnswers);
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      navigate(`/survey/${currentPage - 1}`);
    }
  };

  const handleNextPage = () => {
    navigate(`/survey/${currentPage + 1}`);
  };

  const handleSubmit = async () => {
    try {
      console.log('Starting submission...');
      const allQuestionsAnswered = answers.every(answer => answer !== '');
      if (!allQuestionsAnswered) {
        setError('Please answer all questions before submitting');
        return;
      }

      const result = await submitSurveyAndGetAnalysis(answers);
      console.log('Analysis result:', result);
      
      // Save the result in localStorage before navigating
      localStorage.setItem('analysisResult', JSON.stringify(result));
      localStorage.removeItem('surveyAnswers');
      
      navigate('/result');
    } catch (err) {
      console.error('Submission error:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit survey');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen w-full bg-[#1B2541] text-white flex items-center justify-center">
        <div className="text-xl">Loading questions...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen w-full bg-[#1B2541] text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl text-red-500 mb-4">Error: {error}</div>
          <button 
            onClick={() => setError(null)} 
            className="px-4 py-2 bg-blue-500 rounded hover:bg-blue-600"
          >
            Dismiss
          </button>
        </div>
      </div>
    );
  }

  const questionsPerPage = 10;
  const startIndex = (currentPage - 1) * questionsPerPage;
  const currentQuestions = questions.slice(startIndex, startIndex + questionsPerPage);

  const isLastPage = currentPage === Math.ceil(questions.length / questionsPerPage);
  const isFirstPage = currentPage === 1;

  return (
    <div className="min-h-screen w-full bg-[#1B2541] text-white">
      <div className="max-w-4xl mx-auto px-4 py-8 min-h-screen flex flex-col">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold mb-6">
            <span className="text-[#3B82F6]">On</span>Track
          </h1>
          <Progress value={(currentPage / 4) * 100} className="mb-4" />
          <p className="text-sm text-gray-400">
            Questions {startIndex + 1}-{Math.min(startIndex + currentQuestions.length, questions.length)} of {questions.length}
          </p>
        </div>

        <div className="flex-grow space-y-6 mb-8">
          {currentQuestions.map((question, index) => (
            <div 
              key={question.id} 
              className="bg-white/10 rounded-lg p-6 shadow-lg hover:bg-white/15 transition-colors"
            >
              <p className="text-lg mb-4">{question.question_text}</p>
              <div className="flex gap-4">
                <button
                  className={`flex-1 py-3 rounded-lg transition-colors ${
                    answers[startIndex + index] === 'YES'
                      ? 'bg-[#3B82F6] hover:bg-[#2563EB]'
                      : 'bg-white/20 hover:bg-[#3B82F6]/70'
                  }`}
                  onClick={() => handleAnswer(startIndex + index, 'YES')}
                >
                  YES
                </button>
                <button
                  className={`flex-1 py-3 rounded-lg transition-colors ${
                    answers[startIndex + index] === 'NO'
                      ? 'bg-[#F87171] hover:bg-[#EF4444]'
                      : 'bg-white/20 hover:bg-[#F87171]/70'
                  }`}
                  onClick={() => handleAnswer(startIndex + index, 'NO')}
                >
                  NO
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="flex justify-center gap-4 mt-auto pb-8">
          {!isFirstPage && (
            <button
              className="px-8 py-3 rounded-full bg-gray-500 hover:bg-gray-600 transition-colors"
              onClick={handlePreviousPage}
            >
              Back
            </button>
          )}
          
          {!isLastPage ? (
            <button
              className={`px-8 py-3 rounded-full transition-colors ${
                currentQuestions.every((_, index) => answers[startIndex + index] !== '')
                  ? 'bg-[#3B82F6] hover:bg-[#2563EB]'
                  : 'bg-gray-500 cursor-not-allowed'
              }`}
              onClick={handleNextPage}
              disabled={!currentQuestions.every((_, index) => answers[startIndex + index] !== '')}
            >
              Next Page
            </button>
          ) : (
            <button
              className={`px-8 py-3 rounded-full transition-colors ${
                answers.every(answer => answer !== '')
                  ? 'bg-green-500 hover:bg-green-600'
                  : 'bg-gray-500 cursor-not-allowed'
              }`}
              onClick={handleSubmit}
              disabled={!answers.every(answer => answer !== '')}
            >
              Submit Survey ({answers.filter(a => a !== '').length}/{questions.length})
            </button>
          )}
        </div>
      </div>
    </div>
  );
}