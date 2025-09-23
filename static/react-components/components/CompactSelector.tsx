import React, { useState, useRef, useEffect } from 'react';
import { NoBorderButton } from './reusable/Button';
import { LayoutGrid, Rows2, Rows3, Rows4 } from 'lucide-react';
import { useUserPreferences } from '../hooks/useUserPreferences';

/**
 * Represents the different levels of UI compactness
 */
export type CompactnessLevel = 'spacious' | 'normal' | 'compact';

/**
 * Props for the CompactSelector component
 */
interface CompactSelectorProps {
    /** Optional CSS class name for styling */
    className?: string;
}

/**
 * Configuration for each compactness option
 */
interface CompactnessOption {
    level: CompactnessLevel;
    label: string;
    description: string;
    size: number; // Size of the icon to represent density
}

/**
 * Available compactness options with their display information
 */
const compactnessOptions: CompactnessOption[] = [
    {
        level: 'spacious',
        label: 'Comfortable',
        description: 'More spacing and larger elements',
        size: 16
    },
    {
        level: 'normal',
        label: 'Normal',
        description: 'Balanced spacing and sizing',
        size: 16
    },
    {
        level: 'compact',
        label: 'Compact',
        description: 'Minimal spacing for dense layouts',
        size: 16
    }
];

/**
 * A selector component that allows users to choose between three levels of UI compactness.
 * Displays as a button that opens a dropdown menu with options.
 * 
 * @param props - The component props
 * @returns The CompactSelector component
 */
export const CompactSelector: React.FC<CompactSelectorProps> = ({
    className = ''
}) => {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const { preferences, updateCompactnessLevel } = useUserPreferences();

    /**
     * Gets the currently selected option
     */
    const selectedOption = compactnessOptions.find(option => option.level === preferences.compactnessLevel);

    // Update css class on body
    useEffect(() => {
        document.body.classList.remove('font-compact', 'font-spacious', 'font-normal');
        document.body.classList.add(`font-${preferences.compactnessLevel}`);
    }, [preferences.compactnessLevel]);

    /**
     * Handles clicking outside the dropdown to close it
     */
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    /**
     * Handles selecting an option from the dropdown
     */
    const handleOptionSelect = (level: CompactnessLevel): void => {
        updateCompactnessLevel(level);
        setIsOpen(false);
    };

    return (
        <div className={`relative ${className}`} ref={dropdownRef}>
            {/* Trigger Button */}
            <NoBorderButton
                onClick={() => setIsOpen(!isOpen)}
                className='text-sidebar-foreground/80 hover:text-sidebar-foreground rounded-md p-1.5'
                aria-label={`Select compactness level (currently ${selectedOption?.label})`}
                aria-expanded={isOpen}
                aria-haspopup="true"
            >
                {preferences.compactnessLevel === 'spacious' ? (
                    <Rows2 size={16} />
                ) : preferences.compactnessLevel === 'normal' ? (
                    <Rows3 size={16} />
                ) : (
                    <Rows4 size={16} />
                )}
            </NoBorderButton>

            {/* Dropdown Menu */}
            {isOpen && (
                <div
                    className="
                        absolute top-full right-0 mt-1 w-64
                        bg-background rounded-lg shadow-lg border border-border
                        text-foreground
                        py-1 z-50
                    "
                    role="menu"
                >
                    {compactnessOptions.map((option) => {
                        const isSelected = option.level === preferences.compactnessLevel;

                        return (
                            <button
                                key={option.level}
                                onClick={() => handleOptionSelect(option.level)}
                                className={`
                                    w-full flex items-center gap-3 px-3 py-2
                                    transition-colors duration-150
                                    ${isSelected
                                        ? 'bg-muted/15 text-foreground'
                                        : 'text-muted-foreground hover:bg-muted/15 hover:text-muted-foreground'
                                    }
                                `}
                                role="menuitem"
                                aria-current={isSelected}
                            >
                                {/* Icon */}
                                <LayoutGrid size={option.size} />

                                {/* Label and description */}
                                <div className="flex flex-col items-start text-left">
                                    <span className={`
                                        text-sm font-medium
                                    `}>
                                        {option.label}
                                    </span>
                                    <span className={`
                                        text-xs
                                    `}>
                                        {option.description}
                                    </span>
                                </div>
                            </button>
                        );
                    })}
                </div>
            )}
        </div>
    );
};
