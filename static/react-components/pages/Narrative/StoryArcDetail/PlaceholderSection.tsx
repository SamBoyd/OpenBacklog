import React from 'react';
import { PlaceholderSectionProps } from '#types/storyArc';

/**
 * PlaceholderSection displays an empty state for sections with no data.
 * Used for Foreshadowing, Turning Points, Related Lore sections.
 * @param {PlaceholderSectionProps} props - Component props
 * @returns {React.ReactElement} The PlaceholderSection component
 */
const PlaceholderSection: React.FC<PlaceholderSectionProps> = ({
    title,
    emptyMessage,
    actionButton,
}) => {
    return (
        <div className="border border-border rounded-lg p-8 bg-muted/20">
            <div className="flex flex-col items-center justify-center gap-4 text-center">
                <h3 className="text-base font-semibold text-foreground">
                    {title}
                </h3>
                <p className="text-sm text-muted-foreground max-w-md">
                    {emptyMessage}
                </p>
                {actionButton && (
                    <button
                        onClick={actionButton.onClick}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                    >
                        {actionButton.label}
                    </button>
                )}
            </div>
        </div>
    );
};

export default PlaceholderSection;
