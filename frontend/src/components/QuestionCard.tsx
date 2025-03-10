import { Button } from '@/components/ui/button';

interface QuestionCardProps {
  question: string;
  onAnswer: (answer: string) => void;
}

export const QuestionCard = ({ question, onAnswer }: QuestionCardProps) => {
  return (
    <div className="bg-white/10 rounded-lg p-6">
      <p className="text-lg mb-4">{question}</p>
      <div className="flex gap-4">
        <Button
          className="flex-1 bg-[#3B82F6] hover:bg-[#2563EB]"
          onClick={() => onAnswer('YES')}
        >
          YES
        </Button>
        <Button
          className="flex-1 bg-[#F87171] hover:bg-[#EF4444]"
          onClick={() => onAnswer('NO')}
        >
          NO
        </Button>
      </div>
    </div>
  );
};
