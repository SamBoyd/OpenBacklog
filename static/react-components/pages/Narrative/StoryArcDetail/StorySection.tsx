import React from 'react';
import { StorySectionProps } from '#types/storyArc';

/**
 * StorySection displays the narrative description of the story arc.
 * Optimized for reading with proper typography and layout.
 * @param {StorySectionProps} props - Component props
 * @returns {React.ReactElement} The StorySection component
 */
const StorySection: React.FC<StorySectionProps> = ({
    storyText,
    isLoading = false,
    onRegenerateClick,
    onEditClick,
}) => {
    if (isLoading) {
        return (
            <div className="border border-border rounded-lg p-6 bg-background">
                <h2 className="text-lg font-semibold text-foreground mb-6">The Story</h2>
                <div className="text-center py-12 text-muted-foreground">
                    Loading story...
                </div>
            </div>
        );
    }

    return (
        <div className="border border-border rounded-lg p-6 bg-background">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold text-foreground">The Story</h2>
                <div className="flex gap-2">
                    <button
                        disabled
                        onClick={onRegenerateClick}
                        className="px-3 py-1.5 bg-secondary text-secondary-foreground rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Coming soon"
                    >
                        Regenerate
                    </button>
                    <button
                        disabled
                        onClick={onEditClick}
                        className="px-3 py-1.5 bg-primary text-primary-foreground rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        title="Coming soon"
                    >
                        Edit
                    </button>
                </div>
            </div>

            {storyText ? (
                <div
                    className="prose prose-sm max-w-none"
                    style={{
                        fontSize: '16px',
                        lineHeight: '1.7',
                        maxWidth: '75ch',
                        margin: '0 auto',
                    }}
                >
                    <p className="text-foreground whitespace-pre-wrap leading-relaxed">
                        {storyText}
                    </p>
                </div>
            ) : (
                <div className="border border-border rounded-lg text-center">
                    <p className="text-sm text-muted-foreground">
                        No story text available. The narrative description will appear here.
                    </p>
                </div>
            )}
        </div>
    );
};

export default StorySection;
