import React, { useState, useEffect } from "react"
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts"
import { Card, CardContent } from "@/components/ui/card"
import type { PersonalityAnalysis } from '../../types/survey'

interface Props {
  analysis: PersonalityAnalysis;
}

export function CareerPersonalityAnalysis({ analysis }: Props) {
  const [iconUrl, setIconUrl] = useState<string>('');
  const [iconError, setIconError] = useState(false);
  
  useEffect(() => {
    // Reset error state when iconId changes
    setIconError(false);
    
    if (analysis?.iconId) {
      // Try to load the icon with a direct path first
      const iconPath = `/static/icon/${analysis.iconId}.png`;
      
      // Create a new image to test if the icon exists
      const img = new Image();
      img.onload = () => {
        setIconUrl(iconPath);
      };
      img.onerror = () => {
        // If direct path fails, try the API endpoint
        fetch(`/api/survey/icon/${analysis.iconId}`)
          .then(response => {
            if (!response.ok) {
              throw new Error('Failed to load icon');
            }
            return response.blob();
          })
          .then(blob => {
            const url = URL.createObjectURL(blob);
            setIconUrl(url);
          })
          .catch(error => {
            console.error('Error loading icon:', error);
            setIconError(true);
            // Use a fallback icon
            setIconUrl('/static/icon/default.png');
          });
      };
      img.src = iconPath;
    }
    
    // Cleanup
    return () => {
      if (iconUrl && iconUrl.startsWith('blob:')) {
        URL.revokeObjectURL(iconUrl);
      }
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
              {iconError ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <p className="text-gray-500 mb-2">Icon not available</p>
                    <div className="w-32 h-32 bg-gray-200 rounded-full mx-auto flex items-center justify-center">
                      <span className="text-4xl">🧑</span>
                    </div>
                  </div>
                </div>
              ) : iconUrl ? (
                <div className="relative w-full h-full">
                  <img
                    src={iconUrl}
                    alt="Character Icon"
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      console.error('Image failed to load, using fallback');
                      setIconError(true);
                      const target = e.target as HTMLImageElement;
                      target.src = '/static/icon/default.png';
                    }}
                  />
                </div>
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p>Loading character icon...</p>
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
