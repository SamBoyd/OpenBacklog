import React from 'react';
import { InitiativeDto, statusDisplay } from '#types';

type SmartGroupPreviewProps = {
    filteredPreviewInitiatives: InitiativeDto[] | undefined;
    previewLoading: boolean;
    previewError: string | null;
    debouncedCriteria: Record<string, any>;
    keywords: string;
    previewInitiatives: InitiativeDto[] | undefined;
};

/**
 * Displays a preview of initiatives matching the smart group criteria.
 * It shows loading and error states, and the list of matching initiatives.
 */
const SmartGroupPreview: React.FC<SmartGroupPreviewProps> = ({
    filteredPreviewInitiatives,
    previewLoading,
    previewError,
    debouncedCriteria,
    keywords,
    previewInitiatives
}) => {
    return (
        <div className="mb-4 p-2 border border-border rounded-md">
            <h3 className="text-base font-semibold mb-2">Preview Matching Initiatives</h3>
            {previewLoading && <p className="text-xs">Loading preview...</p>}
            {previewError && <p className="text-red-500 text-xs">Error loading preview</p>}
            {!previewLoading && !previewError && (
                <>
                    {filteredPreviewInitiatives && filteredPreviewInitiatives.length > 0 ? (
                        <ul className="list-disc pl-4 space-y-0.5 max-h-32 overflow-y-auto bg-input p-2 rounded text-xs">
                            {filteredPreviewInitiatives.map((initiative: InitiativeDto) => (
                                <li key={initiative.id} className="w-full text-xs overflow-hidden">
                                    {initiative.title} ({initiative.identifier}) - Status: {statusDisplay(initiative.status)}
                                </li>
                            ))}
                        </ul>
                    ) : (
                        <p className="text-xs text-muted-foreground">
                            {Object.keys(debouncedCriteria).length > 0 || keywords.trim().length > 0
                                ? 'No initiatives match the current criteria/keywords.'
                                : (previewInitiatives && previewInitiatives.length > 0 ? 'Define criteria or enter keywords to filter the list.' : 'No initiatives available, or define criteria/keywords to see a preview.')
                            }
                        </p>
                    )}
                </>
            )}
        </div>
    );
};

export default SmartGroupPreview; 