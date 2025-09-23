import React from 'react';

interface ToggleProps {
    isEnabled: boolean;
    onChange: (isEnabled: boolean) => void;
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

/**
 * A reusable toggle switch component
 */
const Toggle: React.FC<ToggleProps> = ({
    isEnabled,
    onChange,
    size = 'md',
    className = ''
}) => {
    const sizeClasses = {
        sm: 'w-8 h-4',
        md: 'w-11 h-6',
        lg: 'w-14 h-7'
    };

    const thumbSizeClasses = {
        sm: 'w-3 h-3',
        md: 'w-4 h-4',
        lg: 'w-5 h-5'
    };

    return (
        <div
            onClick={() => onChange(!isEnabled)}
            className={`
                ${sizeClasses[size]} rounded-full flex items-center p-1 
                cursor-pointer transition-colors 
                ${isEnabled ? 'bg-primary justify-end' : 'bg-gray-300 justify-start'}
                ${className}
            `}
            role="switch"
            aria-checked={isEnabled}
        >
            <div className={`${thumbSizeClasses[size]} rounded-full bg-white`}></div>
        </div>
    );
};

export default Toggle; 