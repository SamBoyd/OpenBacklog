import React, { useEffect, useState } from 'react';
import { GrDocumentText } from 'react-icons/gr';
import { Skeleton } from './reusable/Skeleton';
import ResizingTextInput from './reusable/ResizingTextInput';
import FileSuggestionTextInput from './reusable/FileSuggestionTextInput';

/**
 * EntityDescriptionEditor component for editing entity descriptions
 * @param {object} props - The component props
 * @param {string} props.description - The current description text
 * @param {(value: string) => void} props.onChange - Function called when description changes
 * @param {boolean} [props.loading=false] - Whether the component is in loading state
 * @param {string} [props.testId='description-section'] - Test ID for the component
 * @returns {React.ReactElement} The EntityDescriptionEditor component
 */
type EntityDescriptionEditorProps = {
    description: string;
    onChange: (value: string) => void;
    loading?: boolean;
    testId?: string;
    disabled?: boolean;
    className?: string;
    filepathSuggestionsEnabled?: boolean;
};

const EntityDescriptionEditor: React.FC<EntityDescriptionEditorProps> = ({
    description,
    onChange,
    loading = false,
    testId = 'description-section',
    disabled = false,
    className = '',
    filepathSuggestionsEnabled = false,
}) => {
    const [localDescription, setLocalDescription] = useState(description);

    useEffect(() => {
        setLocalDescription(description);
    }, [description]);

    const handleChange = (value: string) => {
        setLocalDescription(value);
    };

    const handleBlur = () => {
        onChange(localDescription);
    };

    return (
        <div className={`mt-2 text-foreground`} data-testid={testId}>
            <div className="flex flex-row justify-between">
                <div className="flex flex-row gap-2 min-w-[13rem] items-baseline font-light">
                    <GrDocumentText />
                    <span className="ml-2.5">Description</span>
                </div>
            </div>

            {loading && (
                <Skeleton type="paragraph" className="h-[500px] w-full" />
            )}

            <div className="w-full relative">
                {!loading && filepathSuggestionsEnabled && (
                    <FileSuggestionTextInput
                        id="description-area"
                        value={localDescription}
                        onChange={handleChange}
                        onBlur={handleBlur}
                    />
                )}

                {!loading && !filepathSuggestionsEnabled && (
                    <ResizingTextInput
                        id="description-area"
                        value={localDescription}
                        onChange={handleChange}
                        onBlur={handleBlur}
                    />
                )}

            </div>
        </div>
    );
};

export default EntityDescriptionEditor;
