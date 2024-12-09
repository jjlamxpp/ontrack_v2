interface NavigationButtonsProps {
    currentPage: number;
    onNext: () => void;
    onPrevious: () => void;
    onSubmit: () => void;
  }
  
  export const NavigationButtons = ({
    currentPage,
    onNext,
    onPrevious,
    onSubmit,
  }: NavigationButtonsProps) => {
    return (
      <div className="navigation-buttons">
        {currentPage > 1 && (
          <button onClick={onPrevious}>Previous</button>
        )}
        {currentPage < 4 ? (
          <button onClick={onNext}>Next</button>
        ) : (
          <button onClick={onSubmit}>Submit</button>
        )}
      </div>
    );
  };