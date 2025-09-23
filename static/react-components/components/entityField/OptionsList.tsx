import React, { useRef, useState } from 'react';
import { Input } from '../reusable/Input';
import { OptionItem } from './ui';
import { Plus } from 'lucide-react';

interface OptionsListProps {
    options: string[];
    onAddOption: (option: string) => void;
    optionBgColor?: string;
    optionTextColor?: string;
    placeholder?: string;
    emptyMessage?: string;
    onEditOption?: (index: number, newValue: string) => void;
    onDeleteOption?: (index: number) => void;
}

/**
 * A reusable component for displaying and managing a list of options
 */
const OptionsList: React.FC<OptionsListProps> = ({
    options,
    onAddOption,
    optionBgColor = 'bg-blue-100',
    optionTextColor = 'text-blue-800',
    placeholder = 'Add new option',
    emptyMessage = 'No options added yet',
    onEditOption,
    onDeleteOption
}) => {
    const [newOption, setNewOption] = useState('');
    const newOptionInputRef = useRef<HTMLInputElement>(null);

    const handleAddOption = () => {
        if (newOption.trim()) {
            onAddOption(newOption.trim());
            setNewOption('');
        }
        newOptionInputRef.current?.focus();
    };

    return (
        <div>
            <div className="absolute top-0 right-0 flex justify-end mb-2">
                <button className="text-primary" onClick={handleAddOption}>
                    <Plus size={18} />
                </button>
            </div>

            {/* Option input */}
            <div className="mb-4">
                <Input
                    ref={newOptionInputRef}
                    type="text"
                    value={newOption}
                    onChange={(e) => setNewOption(e.target.value)}
                    placeholder={placeholder}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter' && newOption.trim()) {
                            handleAddOption();
                        }
                    }}
                />
            </div>

            {/* Options list */}
            <div className="space-y-1 max-h-48 overflow-y-auto">
                {options.map((option, index) => (
                    <OptionItem
                        key={index}
                        index={index}
                        option={option}
                        bgColor={optionBgColor}
                        textColor={optionTextColor}
                        onEdit={() => onEditOption && onEditOption(index, option)}
                        onDelete={() => onDeleteOption && onDeleteOption(index)}
                    />
                ))}
            </div>

            {options.length === 0 && (
                <div className="text-center text-muted-foreground text-sm py-2">
                    {emptyMessage}
                </div>
            )}
        </div>
    );
};

export default OptionsList; 