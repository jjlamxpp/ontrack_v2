interface ProgressBarProps {
    currentPage: number;
    totalPages: number;
  }
  
  export const ProgressBar = ({ currentPage, totalPages }: ProgressBarProps) => {
    const progress = (currentPage / totalPages) * 100;
    
    return (
      <div className="w-full bg-white/20 h-2 rounded-full overflow-hidden">
        <div 
          className="h-full rounded-full transition-all duration-300"
          style={{ 
            width: `${progress}%`,
            backgroundColor: '#3B82F6'
          }}
        />
      </div>
    );
  };