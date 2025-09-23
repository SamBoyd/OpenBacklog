import React from 'react';

import { FieldDefinitionDto, InitiativeStatus, TaskStatus, statusDisplay } from '#types';

import TaggingInput from './reusable/TaggingInput';
import { Button, CompactButton, PrimaryButton, SecondaryButton } from './reusable/Button';
import Card from './reusable/Card';
import { CompactSelectBox, SelectBox } from './reusable/Selectbox';
import { Input } from './reusable/Input';
import ResizingTextInput from './reusable/ResizingTextInput';

/* === ICON COMPONENTS === */
// NOTE: These could be moved to a shared location if used elsewhere
const PlusIcon = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth="1.5"
        stroke="currentColor"
        className="size-6"
    >
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
    </svg>
);

const CloseIcon = () => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        strokeWidth="1.5"
        stroke="currentColor"
        className="size-4"
    >
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
    </svg>
);

/* === TYPES === */
type CompactCreateTaskViewProps = {
    isExpanded: boolean;
    title: string;
    status: TaskStatus | InitiativeStatus;
    error: string | null;
    isCreating: boolean;
    disabled?: boolean;
    titleRef: React.RefObject<HTMLTextAreaElement>;
    typeFieldDefinition?: FieldDefinitionDto;
    statusFieldDefinition?: FieldDefinitionDto;
    type: string | null;

    onOpen: () => void;
    onClose: () => void;
    onTitleChange: (value: string) => void;
    onStatusChange: (value: string) => void;
    setType: (type: string | null) => void;
    onSubmit: (event?: React.FormEvent | React.KeyboardEvent) => void;
    onKeyDown: (event: React.KeyboardEvent<HTMLTextAreaElement>) => void;
};

/* === COMPONENT === */
const CompactCreateView = ({
    isExpanded,
    title,
    status,
    error,
    isCreating,
    disabled,
    titleRef,
    typeFieldDefinition,
    statusFieldDefinition,
    type,
    setType,
    onOpen,
    onClose,
    onTitleChange,
    onStatusChange,
    onSubmit,
    onKeyDown,
}: CompactCreateTaskViewProps) => {
    const transitionWrapperClasses = 'transition-all duration-300';

    return (
        <div className={transitionWrapperClasses} data-testid="compact-create-task">
            {/* --- Collapsed view (the "Create" button) --- */}
            <div
                className={
                    isExpanded
                        ? 'mb-8 max-h-0 opacity-0 pointer-events-none ' + transitionWrapperClasses
                        : `
                            mb-8 flex flex-row gap-3 w-full justify-center max-h-40 pointer-events-auto
                            ${transitionWrapperClasses}
                        `
                }
            >
                <SecondaryButton
                    onClick={onOpen}
                    disabled={disabled}
                    dataTestId="open-button"
                    className="w-full"
                >
                    <PlusIcon />
                </SecondaryButton>
            </div>

            {/* --- Expanded view (the form) --- */}
            <div
                className={
                    isExpanded
                        ? ` mx-2 pt-2 pb-1 px-2 w-full text-foreground
                            rounded border border-primary/40 focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-transparent focus:bg-background/80
                            bg-muted/5
                            overflow-visible flex flex-col gap-1 max-h-[1000px]
                            ${transitionWrapperClasses}
                        `
                        : 'max-h-0 opacity-0 pointer-events-none ' + transitionWrapperClasses
                }
                data-testid="expanded-form"
            >
                {/* --- Title + Close Button Row --- */}
                <div className="flex flex-row gap-3 w-full items-start">
                    <div className="flex-grow">
                        <div className="flex flex-col w-full pl-2">
                            <textarea
                                id="title"
                                ref={titleRef}
                                data-testid="title-input"
                                className={
                                    `text-foreground  w-full resize-none sm:text-sm/6 bg-transparent focus:outline-none focus:ring-0`
                                }
                                rows={2}
                                style={{ overflow: 'hidden' }}
                                value={title}
                                placeholder="Initiative title"
                                onInput={(e) => {
                                    const target = e.currentTarget;
                                    target.style.height = 'auto';
                                    target.style.height = (target.scrollHeight + 10) + 'px';
                                }}
                                onChange={e => {
                                    const newValue = e.target.value;
                                    // Apply 200 character limit
                                    if (newValue.length <= 200) {
                                        onTitleChange(newValue);
                                    }
                                }}
                                maxLength={200}
                                onKeyDown={onKeyDown}
                            />
                            {error && (
                                <div className="text-xs text-red-500 w-full">
                                    {error}
                                </div>
                            )}
                            <div className={`self-end text-xs mt-1 ${
                                title.length > 160 ? 'text-orange-500' : 
                                title.length >= 200 ? 'text-red-500' : 
                                'text-muted-foreground'
                            }`}>
                                {title.length}/200
                            </div>
                        </div>
                    </div>

                    <CompactButton
                        dataTestId="close-button"
                        onClick={onClose}
                    >
                        <CloseIcon />
                    </CompactButton>
                </div>

                {/* --- Button Row (Tag, Status, Create) --- */}
                <div className="flex flex-row justify-between">
                    <div className="flex flex-row w-full gap-3">
                        {/* Status dropdown */}
                        {statusFieldDefinition && (
                            <CompactSelectBox
                                id="status"
                                name="status"
                                value={status}
                                onChange={onStatusChange}
                                dataTestId="status-select"
                                options={statusFieldDefinition.config.options.map((option: string) => ({
                                    value: option,
                                    label: statusDisplay(option),
                                }))}
                            />
                        )}

                        {typeFieldDefinition && (
                            <CompactSelectBox
                                dataTestId="type-select"
                                id="type"
                                name="type"
                                placeholder="Select type"
                                value={type || ''}
                                onChange={value => setType(value as string)}
                                options={typeFieldDefinition.config.options.map((option: string) => ({
                                    value: option,
                                    label: statusDisplay(option),
                                }))}
                            />
                        )}
                    </div>

                    {/* Submit button */}
                    <CompactButton
                        onClick={onSubmit}
                        className="border border-border"
                        dataTestId="create-button"
                        disabled={isCreating}
                    >
                        {isCreating ? 'Creating...' : 'Create'}
                    </CompactButton>
                </div>
            </div>
        </div>
    );
};

export default CompactCreateView;
