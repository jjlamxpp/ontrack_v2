import React, { useState, useEffect } from "react"
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts"
import { Card, CardContent } from "@/components/ui/card"
import type { PersonalityAnalysis } from '../../types/survey'

interface Props {
  analysis: PersonalityAnalysis;
}

export function CareerPersonalityAnalysis({ analysis }: Props) {
  const [iconUrl, setIconUrl] = useState<string>('');
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

  useEffect(() => {
    if (analysis?.iconId) {
      fetch(`${API_BASE_URL}/survey/icon/${analysis.iconId}`)
        .then(response => {
          if (!response.ok) throw new Error('Failed to load icon');
          return response.blob();
        })
        .then(blob => {
          const url = URL.createObjectURL(blob);
          setIconUrl(url);
        })
        .catch(error => {
          console.error('Error loading icon:', error);
          setIconUrl('/fallback-icon.png');
        });
    }
    
    // Cleanup
    return () => {
      if (iconUrl) URL.revokeObjectURL(iconUrl);
    };
  }, [analysis?.iconId]);

  if (!analysis) {
    return (
      <div className="text-center p-8">
        <p>No personality analysis available.</p>
      </div>
    );
  }

  const radarData = [
    { subject: 'Realistic', score: analysis.riasecScores?.R || 0 },
    { subject: 'Investigative', score: analysis.riasecScores?.I || 0 },
    { subject: 'Artistic', score: analysis.riasecScores?.A || 0 },
    { subject: 'Social', score: analysis.riasecScores?.S || 0 },
    { subject: 'Enterprising', score: analysis.riasecScores?.E || 0 },
    { subject: 'Conventional', score: analysis.riasecScores?.C || 0 },
  ];

  return (
    <div className="space-y-6">
      <Card className="bg-white text-black p-6">
        <CardContent className="p-0">
          <div className="grid md:grid-cols-2">
            <div className="flex flex-col items-center justify-center p-8 h-[400px]">
              {iconUrl && (
                <div className="relative w-full h-full">
                  <img
                    src={iconUrl}
                    alt="Character Icon"
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.src = '/fallback-icon.png';
                    }}
                  />
                </div>
              )}
            </div>
            
            <div className="h-[400px] p-8">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" />
                  <PolarRadiusAxis angle={30} domain={[0, 1]} />
                  <Radar
                    name="RIASEC"
                    dataKey="score"
                    stroke="#3B82F6"
                    fill="#3B82F6"
                    fillOpacity={0.6}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-white text-black p-6">
        <CardContent>
          <h3 className="text-xl font-bold text-[#1B2541] mb-4">Who you are?</h3>
          <p>{analysis.description}</p>
        </CardContent>
      </Card>

      <Card className="bg-white text-black p-6">
        <CardContent>
          <h3 className="text-xl font-bold text-[#1B2541] mb-4">How this combination interpret?</h3>
          <p>{analysis.interpretation}</p>
        </CardContent>
      </Card>

      <Card className="bg-white text-black p-6">
        <CardContent>
          <h3 className="text-xl font-bold text-[#1B2541] mb-4">What you might enjoy?</h3>
          <ul className="list-disc pl-5 space-y-2">
            {analysis.enjoyment.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card className="bg-white text-black p-6">
        <CardContent>
          <h3 className="text-xl font-bold text-[#1B2541] mb-4">Your strength might be</h3>
          <ul className="list-disc pl-5 space-y-2">
            {analysis.your_strength.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
