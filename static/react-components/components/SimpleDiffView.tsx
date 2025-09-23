import React from 'react';

/**
 * Props for the SimpleDiffView component
 */
interface SimpleDiffViewProps {
    titleChanged: boolean;
    descriptionChanged: boolean;
    originalTitle: string | null | undefined;
    changedTitle: string | null | undefined;
    originalDescription: string | null | undefined;
    changedDescription: string | null | undefined;
}

/**
 * A component that displays a simple side-by-side diff when structured diffs cannot be generated
 * @param {SimpleDiffViewProps} props - The component props
 * @returns {React.ReactElement} The simple diff view component
 */
export const SimpleDiffView: React.FC<SimpleDiffViewProps> = ({
    titleChanged,
    descriptionChanged,
    originalTitle,
    changedTitle,
    originalDescription,
    changedDescription
}) => {
    return (
        <div className="initiative-diff-container">
            {titleChanged && (
                <div className="mb-4">
                    <h3 className="text-lg font-medium mb-2">Title Changes</h3>
                    <div className="p-3 bg-gray-50 border rounded">
                        <div className="mb-2">
                            <span className="font-medium">Original: </span>
                            <span className="text-red-500">{originalTitle || '(empty)'}</span>
                        </div>
                        <div>
                            <span className="font-medium">Changed: </span>
                            <span className="text-green-500">{changedTitle || '(empty)'}</span>
                        </div>
                    </div>
                </div>
            )}

            {descriptionChanged && (
                <div>
                    <h3 className="text-lg font-medium mb-2">Description Changes</h3>
                    <div className="p-3 bg-gray-50 border rounded">
                        <div className="mb-3">
                            <div className="font-medium mb-1">Original:</div>
                            <pre className="whitespace-pre-wrap text-red-500 bg-gray-100 p-2 rounded">
                                {originalDescription || '(empty)'}
                            </pre>
                        </div>
                        <div>
                            <div className="font-medium mb-1">Changed:</div>
                            <pre className="whitespace-pre-wrap text-green-500 bg-gray-100 p-2 rounded">
                                {changedDescription || '(empty)'}
                            </pre>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
