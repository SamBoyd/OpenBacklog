import React from 'react';
import { Button, SecondaryButton } from './Button';

interface ChecklistOverlayProps {
    onManualEdit: () => void;
    documentationUrl?: string;
}

/**
 * Educational overlay component that appears over empty checklist sections
 * to inform users about Claude Code integration for automatic checklist management.
 * @param {object} props - The component props
 * @param {() => void} props.onManualEdit - Callback to bypass overlay and enable manual editing
 * @param {string} [props.documentationUrl] - Optional URL to Claude Code documentation
 * @returns {React.ReactElement} The overlay component
 */
const ChecklistOverlay: React.FC<ChecklistOverlayProps> = ({
    onManualEdit,
    documentationUrl
}) => {
    return (
        <div className="relative rounded-lg border border-border bg-background/50 p-6 mb-4 z-10">
            <div className="pt-8 text-center space-y-4 text-sm">
                {/* Header with icon and title */}
                {/* <div className="flex items-center justify-center space-x-2">
                    <span className="text-2xl" role="img" aria-label="Robot">🤖</span>
                    <h3 className="text-lg font-semibold text-foreground">
                        Smart Checklists with Claude Code
                    </h3>
                </div> */}
                
                {/* Primary message */}
                <p className="text-muted-foreground max-w-md mx-auto leading-relaxed">
                    Checklists are automatically generated and managed by Claude Code and updated via MCP tools. 
                    This ensures accurate, code-aware task tracking.
                </p>
                
                {/* Feature list */}
                <div className="text-left max-w-sm mx-auto space-y-2 py-4">
                    <div className="flex items-start space-x-2 text-sm text-muted-foreground">
                        <span className="text-primary mt-0.5">•</span>
                        <span>Analyze your codebase to create detailed implementation steps</span>
                    </div>
                    <div className="flex items-start space-x-2 text-sm text-muted-foreground">
                        <span className="text-primary mt-0.5">•</span>
                        <span>Use MCP to update checklist items as work progresses</span>
                    </div>
                    <div className="flex items-start space-x-2 text-sm text-muted-foreground">
                        <span className="text-primary mt-0.5">•</span>
                        <span>Track completion automatically</span>
                    </div>
                </div>
                
                {/* Action buttons */}
                <div className="flex items-center justify-center space-x-3 pt-2">
                    {documentationUrl && (
                        <SecondaryButton
                            onClick={() => window.open(documentationUrl, '_blank')}
                            className="text-xs"
                        >
                            Learn More
                        </SecondaryButton>
                    )}
                    <Button
                        onClick={onManualEdit}
                        className="text-xs"
                        dataTestId="manual-edit-button"
                    >
                        Edit Manually
                    </Button>
                </div>
                
                {/* Helper text */}
                <p className="text-xs text-muted-foreground/80 pt-2">
                    Need to create a checklist manually? Some tasks don't require Claude Code integration.
                </p>
            </div>
        </div>
    );
};

export default ChecklistOverlay;