import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import type { IndustryRecommendation } from '../../types/survey';

interface Props {
  industries?: IndustryRecommendation[];
}

interface Education {
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
  const [schoolLogos, setSchoolLogos] = useState<{ [key: string]: string }>({});
  const [logoErrors, setLogoErrors] = useState<{ [key: string]: boolean }>({});

  useEffect(() => {
    if (industries.length > 0) {
      setSelectedIndustryId(industries[0].id);
    }
  }, [industries]);

  const parseEducation = (educationString: string): Education => {
    if (!educationString) return { program: '', jupasCode: '', school: '', score: '' };
    const parts = educationString.split('//').map(part => part.trim());
    return {
      program: parts[0] || '',
      jupasCode: parts[1] || '',
      school: parts[2] || '',
      score: parts[3] || ''
    };
  };

  const loadSchoolLogo = async (school: string) => {
    if (!school || schoolLogos[school] || logoErrors[school]) return;

    try {
      // Try direct path first
      const directPath = `/static/school_icon/${school.toLowerCase().replace(/\s+/g, '-')}.png`;
      
      // Test if the image exists
      const img = new Image();
      img.onload = () => {
        setSchoolLogos(prev => ({ ...prev, [school]: directPath }));
      };
      img.onerror = async () => {
        // If direct path fails, try API
        try {
          const response = await fetch(`/api/survey/school-icon/${school}`);
          if (!response.ok) {
            throw new Error('Failed to load school logo');
          }
          
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          setSchoolLogos(prev => ({ ...prev, [school]: url }));
        } catch (error) {
          console.error('Error loading school logo:', error);
          setLogoErrors(prev => ({ ...prev, [school]: true }));
          setSchoolLogos(prev => ({ ...prev, [school]: '/static/school_icon/default.png' }));
        }
      };
      img.src = directPath;
    } catch (error) {
      console.error('Error loading school logo:', error);
      setLogoErrors(prev => ({ ...prev, [school]: true }));
      setSchoolLogos(prev => ({ ...prev, [school]: '/static/school_icon/default.png' }));
    }
  };

  useEffect(() => {
    const selectedIndustry = industries.find(i => i.id === selectedIndustryId);
    if (selectedIndustry?.education) {
      const { school } = parseEducation(selectedIndustry.education);
      if (school) loadSchoolLogo(school);
    }

    return () => {
      // Cleanup URLs on unmount
      Object.values(schoolLogos).forEach(url => {
        if (url.startsWith('blob:')) {
          URL.revokeObjectURL(url);
        }
      });
    };
  }, [selectedIndustryId, industries]);

  if (industries.length === 0) {
    return (
      <div className="text-center p-8">
        <p>No industry recommendations available.</p>
      </div>
    );
  }

  const selectedIndustry = industries.find(i => i.id === selectedIndustryId) || industries[0];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3 mb-6">
        {industries.map((industry) => (
          <button
            key={industry.id}
            className={`px-4 py-2 rounded-full transition-colors ${
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
              <h3 className="text-xl font-semibold mb-4">Insight</h3>
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

          {selectedIndustry.education && (
            <Card className="bg-white text-black p-6">
              <CardContent>
                <h3 className="text-xl font-semibold mb-4">JUPAS Information</h3>
                <div className="grid md:grid-cols-2 gap-6 items-center">
                  <div className="space-y-3">
                    {(() => {
                      const edu = parseEducation(selectedIndustry.education);
                      return (
                        <div className="space-y-2">
                          <p className="text-lg">
                            <strong>Program:</strong> {edu.program}
                          </p>
                          {edu.jupasCode && (
                            <p className="text-lg">
                              <strong>JUPAS Code:</strong> {edu.jupasCode}
                            </p>
                          )}
                          {edu.school && (
                            <p className="text-lg">
                              <strong>School:</strong> {edu.school}
                            </p>
                          )}
                          {edu.score && (
                            <p className="text-lg">
                              <strong>Average Score:</strong> {edu.score}
                            </p>
                          )}
                        </div>
                      );
                    })()}
                  </div>

                  <div className="flex items-center justify-center h-full">
                    {(() => {
                      const { school } = parseEducation(selectedIndustry.education);
                      const logoUrl = schoolLogos[school];
                      const hasError = logoErrors[school];
                      
                      if (school && hasError) {
                        return (
                          <div className="text-center">
                            <p className="text-gray-500 mb-2">{school}</p>
                            <div className="w-32 h-32 bg-gray-200 rounded-lg mx-auto flex items-center justify-center">
                              <span className="text-4xl">🏫</span>
                            </div>
                          </div>
                        );
                      } else if (school && logoUrl) {
                        return (
                          <div className={`relative ${getSchoolLogoStyles(school)}`}>
                            <img 
                              src={logoUrl}
                              alt={`${school} Logo`}
                              className="w-full h-full object-contain"
                              onError={(e) => {
                                console.error(`School logo failed to load: ${school}`);
                                setLogoErrors(prev => ({ ...prev, [school]: true }));
                                const target = e.target as HTMLImageElement;
                                target.src = '/static/school_icon/default.png';
                              }}
                            />
                          </div>
                        );
                      }
                      return null;
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
