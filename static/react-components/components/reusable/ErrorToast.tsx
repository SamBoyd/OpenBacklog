
import React, { useEffect, useState } from 'react';

interface ErrorToastProps {
  error: string | null;
}

const ErrorToast: React.FC<ErrorToastProps> = ({ error }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (error && error !== null && error !== "") {
      console.log('[ErrorToast] displaying error toast', JSON.stringify(error));
      setIsVisible(true);
      
      const timer = setTimeout(() => {
        setIsVisible(false);
      }, 3000);

      return () => clearTimeout(timer);
    }

    return () => {}
  }, [error]);

  if (!error || error === null || error === "") return null;

  return (
    <div 
      className={`fixed bottom-4 transform mb-4 z-[60] transition-all duration-300 ease-in-out ${
        isVisible 
          ? 'translate-y-0 opacity-100' 
          : 'translate-y-full opacity-0'
      }`}
      data-testid="error-toast"
    >
      <div className="bg-destructive text-destructive-foreground px-6 py-4 rounded-lg shadow-lg max-w-md">
        <div className="font-medium text-sm">{error}</div>
        <div className="text-xs mt-1 opacity-90">Oops, something went wrong. Try again.</div>
      </div>
    </div>
  );
};

export default ErrorToast;