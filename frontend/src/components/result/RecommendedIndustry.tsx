import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import type { IndustryRecommendation } from '../../types/survey';

interface Props {
  industries?: IndustryRecommendation[];
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

  const parseEducation = (educationString: string) => {
    if (!educationString) return { program: '', jupasCode: '', school: '', score: '' };
    const parts = educationString.split('//').map(part => part.trim());
    return {
      program: parts[0] || '',
      jupasCode: parts[1] || '',
      school: parts[2] || '',
      score: parts[3] || ''
    };
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex flex-wrap gap-4 mb-8">
        {industries.map((industry) => (
          <button
            key={industry.id}
            onClick={() => setSelectedIndustryId(industry.id)}
            className={`px-6 py-3 rounded-full transition-colors ${
              selectedIndustryId === industry.id
                ? 'bg-[#3B82F6] text-white'
                : 'bg-white/10 hover:bg-white/20'
            }`}
          >
            {industry.name}
          </button>
        ))}
      </div>

      {selectedIndustry && (
        <div className="space-y-6">
          <Card className="bg-white text-black p-6">
            <CardContent>
              <h3 className="text-xl font-semibold mb-4">Overview</h3>
              <p>{selectedIndustry.overview}</p>
            </CardContent>
          </Card>

          <Card className="bg-white text-black p-6">
            <CardContent>
              <h3 className="text-xl font-semibold mb-4">Trending</h3>
              <p>{selectedIndustry.trending}</p>
            </CardContent>
          </Card>

          <Card className="bg-white text-black p-6">
            <CardContent>
              <h3 className="text-xl font-semibold mb-4">Industry Insight</h3>
              <p>{selectedIndustry.insight}</p>
            </CardContent>
          </Card>

          <Card className="bg-white text-black p-6">
            <CardContent>
              <h3 className="text-xl font-semibold mb-4">Career Path</h3>
              <div className="space-y-4">
                {selectedIndustry.examplePaths.map((path, index) => (
                  <div key={index} className="border-l-4 border-blue-500 pl-4">
                    <p>{path}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {selectedIndustry && (selectedIndustry.education || selectedIndustry.jupasInfo) && (
            <Card className="bg-white text-black p-6">
              <CardContent>
                <h3 className="text-xl font-semibold mb-4">JUPAS Information</h3>
                <div className="grid md:grid-cols-2 gap-6 items-center">
                  <div className="space-y-3">
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
                    <div className={`relative ${getSchoolLogoStyles(school)}`}>
                      <img 
                        src={`${config.API_URL}/survey/school-icon/${school}`} // Use the API_URL from config
                        alt={`${school} Logo`}
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          console.error('Failed to load school logo:', school);
                          e.currentTarget.src = '/static/school_icon/default.png'; // Fallback image
                        }}
                      />
                    </div>
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
