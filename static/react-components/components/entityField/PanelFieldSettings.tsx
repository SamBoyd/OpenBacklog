import React, { useRef, useState } from 'react';
import { ArrowLeft, X, Info, Loader2, Trash } from 'lucide-react';
import { Input } from '../reusable/Input';
import { Button } from '../reusable/Button';
import { FieldType, FieldDefinitionDto } from '#types';

interface PanelFieldSettingsProps {
    title: string;
    fieldName: string;
    onNameChange: (name: string) => void;
    onBack: () => void;
    onClose: () => void;
    onSubmit: () => void;
    onDelete?: () => void;
    children?: React.ReactNode;
    hasSettings?: boolean;
    submitButtonText?: string;
    submitButtonDisabled?: boolean;
    isLoading?: boolean;
}

/**
 * Component for inputting a field name
 */
const PanelFieldSettings: React.FC<PanelFieldSettingsProps> = ({
    title,
    fieldName,
    onNameChange,
    onBack,
    onClose,
    onSubmit,
    onDelete,
    children,
    hasSettings = true,
    submitButtonText = "Add field",
    submitButtonDisabled = false,
    isLoading = false,
}) => {
    const [nameError, setNameError] = useState<string | null>(null);
    const inputRef = useRef<HTMLInputElement>(null);


    /**
     * Validates the field name input
     */
    const validateName = (): boolean => {
        if (!fieldName.trim()) {
            setNameError("Field name is required");
            if (inputRef.current) {
                inputRef.current.focus();
            }
            return false;
        }

        if (fieldName.trim().length < 2) {
            setNameError("Field name must be at least 2 characters");
            if (inputRef.current) {
                inputRef.current.focus();
            }
            return false;
        }

        // name must be alphanumeric and whitespace only
        if (!/^[a-zA-Z0-9\s]+$/.test(fieldName)) {
            setNameError("Field name must be alphanumeric and whitespace only");
            if (inputRef.current) {
                inputRef.current.focus();
            }
            return false;
        }

        setNameError(null);
        return true;
    };

    /**
     * Handles name change and performs real-time validation
     */
    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        onNameChange(value);

        if (nameError && value.trim()) {
            setNameError(null);
        }
    };

    /**
     * Handles submit button click with validation
     */
    const handleSubmit = () => {
        if (validateName()) {
            onSubmit();
        }
    };

    return (
        <div className="flex-grow p-4 bg-background text-foreground rounded-lg shadow-lg w-72">
            <div className="flex justify-between items-center mb-4 pb-2 border-b border-border">
                <div className="flex flex-row gap-2 items-center">
                    <button
                        onClick={onBack}
                        className="hover:bg-muted/5 rounded"
                    >
                        <ArrowLeft size={16} />
                    </button>
                    <h3 className="font-medium">{title}</h3>
                </div>

                <button onClick={onClose} className="p-2 rounded hover:bg-muted/5">
                    <X size={14} />
                </button>
            </div>

            <div className="flex flex-col gap-4">
                <div className="flex items-center">
                    <Input
                        ref={inputRef}
                        type="text"
                        value={fieldName}
                        onChange={handleChange}
                        placeholder="Field name"
                        autoFocus
                        className={`${nameError ? "border-red-500 focus:ring-red-500" : ""} flex-grow`}
                    />
                    <button className="ml-2 text-muted-foreground">
                        <Info size={16} />
                    </button>
                </div>
                {nameError && (
                    <p className="text-red-500 text-xs mt-1">{nameError}</p>
                )}

                {hasSettings && children && (
                    <>
                        <hr className="text-border" />
                        {children}
                    </>
                )}

                {onDelete && (
                    <div className="flex justify-between gap-4 mt-2">
                        <Button
                            onClick={onDelete}
                        >
                            <Trash size={16} /> Delete
                        </Button>
                        <Button
                            onClick={handleSubmit}
                            disabled={submitButtonDisabled || isLoading}
                        >
                            {isLoading ? (
                                <span className="flex items-center gap-2">
                                    <Loader2 size={16} className="animate-spin" />
                                    Saving...
                                </span>
                            ) : (
                                submitButtonText
                            )}
                        </Button>
                    </div>
                )}

                {!onDelete && (
                    <div className="flex justify-end gap-4 mt-2">
                        <Button
                            onClick={handleSubmit}
                            disabled={submitButtonDisabled || isLoading}
                        >
                            {isLoading ? (
                                <span className="flex items-center gap-2">
                                    <Loader2 size={16} className="animate-spin" />
                                    Saving...
                                </span>
                            ) : (
                                submitButtonText
                            )}
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PanelFieldSettings; 