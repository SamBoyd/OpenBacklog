import React from 'react';

interface BadgeLabelProps {
    label: string;
    variant?: 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info';
    size?: 'sm' | 'md';
    className?: string;
}

/**
 * A reusable badge component for displaying labels
 */
const BadgeLabel: React.FC<BadgeLabelProps> = ({
    label,
    variant = 'default',
    size = 'sm',
    className = ''
}) => {
    const variantClasses = {
        default: 'bg-gray-100 text-gray-800',
        primary: 'bg-primary-100 text-primary-800',
        success: 'bg-green-100 text-green-800',
        warning: 'bg-yellow-100 text-yellow-800',
        danger: 'bg-red-100 text-red-800',
        info: 'bg-blue-100 text-blue-800'
    };

    const sizeClasses = {
        sm: 'text-xs px-1.5 py-0.5',
        md: 'text-sm px-2 py-0.5'
    };

    return (
        <span
            className={`
                ${variantClasses[variant]} 
                ${sizeClasses[size]} 
                rounded 
                ${className}
            `}
        >
            {label}
        </span>
    );
};

export default BadgeLabel; 