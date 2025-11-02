import React, { useEffect, useState } from 'react';
import { GrDocumentText } from 'react-icons/gr';
import { Skeleton } from './reusable/Skeleton';
import AutocompleteTextInput from './reusable/AutocompleteTextInput ';
import { Tooltip } from 'react-tooltip';
import ResizingTextInput from './reusable/ResizingTextInput';
import VoiceChat from './ChatDialog/VoiceChat';
import FileSuggestionTextInput from './reusable/FileSuggestionTextInput';
import { useBillingUsage } from '#hooks/useBillingUsage';
import { hasActiveSubscription } from '#constants/userAccountStatus';

/**
 * EntityDescriptionEditor component for editing entity descriptions with AI suggestions
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
    autocompleteEnabled?: boolean;
    filepathSuggestionsEnabled?: boolean;
};

const EntityDescriptionEditor: React.FC<EntityDescriptionEditorProps> = ({
    description,
    onChange,
    loading = false,
    testId = 'description-section',
    disabled = false,
    className = '',
    autocompleteEnabled = false,
    filepathSuggestionsEnabled = false,
}) => {
    const [localDescription, setLocalDescription] = useState(description);

    // Check subscription status
    const { userAccountDetails } = useBillingUsage();
    const hasSubscription = userAccountDetails ? hasActiveSubscription(userAccountDetails.status) : false;

    useEffect(() => {
        3
        setLocalDescription(description);
    }, [description]);

    const handleChange = (value: string) => {
        setLocalDescription(value);
    };

    const handleBlur = () => {
        onChange(localDescription);
    };

    const handleVoiceInput = (value: string) => {
        setLocalDescription(description + '\n' + value);
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
                {!loading && autocompleteEnabled && (
                    <AutocompleteTextInput
                        id="description-area"
                        value={localDescription}
                        onChange={handleChange}
                        testId="description-input"
                        disabled={disabled}
                        className={`min-h-[100px] ${className}`}
                        onBlur={handleBlur}
                    />
                )}

                {!loading && !autocompleteEnabled && filepathSuggestionsEnabled && (
                    <FileSuggestionTextInput
                        id="description-area"
                        value={localDescription}
                        onChange={handleChange}
                        onBlur={handleBlur}
                    />
                )}

                {!loading && !autocompleteEnabled && !filepathSuggestionsEnabled && (
                    <ResizingTextInput
                        id="description-area"
                        value={localDescription}
                        onChange={handleChange}
                        onBlur={handleBlur}
                    />
                )}

                <div className="absolute bottom-7 right-1">
                    <VoiceChat
                        disabled={disabled || loading}
                        onVoiceInput={handleVoiceInput}
                        shouldDisplayRewriteDialog={true}
                        existingDescription={localDescription}
                        hasActiveSubscription={hasSubscription}
                        data-tooltip-id="description-voice-input"
                        data-tooltip-place="bottom"
                        data-tooltip-delay-show={500}
                    />
                </div>
                {(!disabled || loading) && (
                    <Tooltip
                        id="description-voice-input"
                        className="custom-tooltip"
                    >
                        <div className='flex flex-col'>
                            <span className='text-xs text-muted-foreground'>Transcribe and rewrite</span>
                        </div>
                    </Tooltip>
                )}
            </div>
        </div>
    );
};

export default EntityDescriptionEditor;
