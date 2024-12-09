import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import type { IndustryRecommendation } from '../../types/survey';
import { config } from '../../config';

interface Props {
  industries?: IndustryRecommendation[];
}

interface EducationInfo {
  program: string;
  jupasCode: string;
  school: string;
  score: string;
}

const getSchoolLogoStyles = (school: string) => {
  const schoolStyles: { [key: string]: string } = {
    'HKUST': 'w-64 h-64',
    'HKU': 'w-48 h-48',
    'CUHK': 'w-48 h-48',
    'HKBU': 'w-56 h-56',
    'PolyU': 'w-52 h-52',
    'CityU': 'w-48 h-48',
  };
  return schoolStyles[school] || 'w-48 h-48';
};

export function RecommendedIndustry({ industries = [] }: Props) {
  const [selectedIndustryId, setSelectedIndustryId] = useState<string>('');

  useEffect(() => {
    if (industries && industries.length > 0) {
      setSelectedIndustryId(industries[0].id);
    }
  }, [industries]);

  if (!industries || industries.length === 0) {
    return (
      <div className="text-center p-8">
        <p>No industry recommendations available.</p>
      </div>
    );
  }

  const selectedIndustry = industries.find(i => i.id === selectedIndustryId);

  const parseEducation = (educationString: string): EducationInfo => {
    try {
      const parts = educationString.split('|').map(part => part.trim());
      return {
        program: parts[0] || '',
        jupasCode: parts[1] || '',
        school: parts[2] || '',
        score: parts[3] || ''
      };
    } catch (error) {
      console.error('Error parsing education string:', error);
      return {
        program: '',
        jupasCode: '',
        school: '',
        score: ''
      };
    }
  };

  if (!selectedIndustry) return null;

  return (
    <div className="space-y-6">
      <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-blue-500 scrollbar-track-blue-100">
        {industries.map((industry) => (
          <button
            key={industry.id}
            className={`px-6 py-3 rounded-full whitespace-nowrap transition-colors ${
              selectedIndustryId === industry.id
                ? 'bg-[#3B82F6] text-white'
                : 'bg-white/10 hover:bg-white/20'
            }`}
            onClick={() => setSelectedIndustryId(industry.id)}
          >
            {industry.name}
          </button>
        ))}
      </div>

      {selectedIndustry && (
        <div className="space-y-6">
          <Card className="bg-white text-black p-6">
            <CardContent>
              <h3 className="text-xl font-bold text-[#1B2541] mb-4">Overview</h3>
              <p>{selectedIndustry.overview}</p>
            </CardContent>
          </Card>

          <Card className="bg-white text-black p-6">
            <CardContent>
              <h3 className="text-xl font-bold text-[#1B2541] mb-4">Trending</h3>
              <p>{selectedIndustry.trending}</p>
            </CardContent>
          </Card>

          <Card className="bg-white text-black p-6">
            <CardContent>
              <h3 className="text-xl font-bold text-[#1B2541] mb-4">Insight</h3>
              <p>{selectedIndustry.insight}</p>
            </CardContent>
          </Card>

          <Card className="bg-white text-black p-6">
            <CardContent>
              <h3 className="text-xl font-bold text-[#1B2541] mb-4">Example Career Paths</h3>
              <ul className="list-disc pl-5 space-y-2">
                {selectedIndustry.examplePaths.map((path, index) => (
                  <li key={index}>{path}</li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {selectedIndustry.education && (
            <Card className="bg-white text-black p-6">
              <CardContent>
                <h3 className="text-xl font-bold text-[#1B2541] mb-4">Education Path</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <div className="space-y-2">
                    {(() => {
                      const edu = parseEducation(selectedIndustry.education || '');
                      return (
                        <div className="space-y-2">
                          <p className="text-lg">
                            <strong>Program:</strong> {edu.program}
                          </p>
                          <p className="text-lg">
                            <strong>JUPAS Code:</strong> {edu.jupasCode}
                          </p>
                          <p className="text-lg">
                            <strong>School:</strong> {edu.school}
                          </p>
                          <p className="text-lg">
                            <strong>Average Score:</strong> {edu.score}
                          </p>
                        </div>
                      );
                    })()}
                  </div>

                  <div className="flex items-center justify-center h-full">
                    {(() => {
                      const edu = parseEducation(selectedIndustry.education || '');
                      return (
                        <div className={`relative ${getSchoolLogoStyles(edu.school)}`}>
                          <img 
                            src={`${config.API_URL}/survey/school-icon/${edu.school}`}
                            alt={`${edu.school} Logo`}
                            className="w-full h-full object-contain"
                            onError={(e) => {
                              console.error('Failed to load school logo:', edu.school);
                              e.currentTarget.src = '/fallback-school-icon.png';
                            }}
                          />
                        </div>
                      );
                    })()}
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
