import React from 'react';
import { Plus, CopyIcon, Trash, ArrowUpDown } from 'lucide-react';
import { BaseFieldSettingsProps } from '#components/entityField/types';
import OptionsList from '#components/entityField/OptionsList';
import { SettingsSection, SettingsRow, Toggle, BadgeLabel } from '#components/entityField/ui/index';
import { EntityType } from '#types';

/**
 * Component for select/multi-select field settings
 */
const SelectFieldSettings: React.FC<BaseFieldSettingsProps> = ({ entityType, settings, onUpdate }) => {
    // Determine if we're dealing with a Select or Multi-Select
    const isMultiSelect = settings.isMultiSelect;

    const handleCycleSortType = () => {
        // Cycle through sort types
        const currentSortType = settings.sortType || 'manual';
        const nextSortType = currentSortType === 'manual'
            ? 'alphabetical'
            : currentSortType === 'alphabetical' ? 'reverse' : 'manual';
        onUpdate({ sortType: nextSortType });
    };

    const handleToggleMultiSelect = () => {
        onUpdate({ isMultiSelect: !isMultiSelect });
    };

    const handleToggleAIAutofill = () => {
        onUpdate({ aiAutofill: !settings.aiAutofill });
    };

    const handleAddOption = (option: string) => {
        const updatedOptions = [...(settings.options || []), option];
        onUpdate({ options: updatedOptions });
    };

    const handleEditOption = (index: number, newValue: string) => {
        const updatedOptions = [...(settings.options || [])];
        updatedOptions[index] = newValue;
        onUpdate({ options: updatedOptions });
    };

    const handleDeleteOption = (index: number) => {
        const updatedOptions = (settings.options || []).filter((_, i) => i !== index);
        onUpdate({ options: updatedOptions });
    };

    function handleToggleAddToAllInitiatives(isEnabled: boolean): void {
        onUpdate({ addToAllInitiatives: isEnabled });
    }

    function handleToggleAddToAllTasks(isEnabled: boolean): void {
        onUpdate({ addToAllTasks: isEnabled });
    }

    return (
        <div className="flex flex-col gap-4">
            {/* Type selector */}
            <SettingsRow
                label="Type"
                value={isMultiSelect ? 'Multi-select' : 'Single select'}
                onClick={handleToggleMultiSelect}
                className="py-2"
            />

            {/* Sort type */}
            <SettingsRow
                label="Sort"
                value={settings.sortType || 'Manual'}
                onClick={handleCycleSortType}
                className="py-2"
            />

            {/* AI Autofill */}
            <div className="flex items-center justify-between py-2 border-t border-b border-border">
                <div className="flex items-center gap-2">
                    <span>AI autofill</span>
                </div>
                <Toggle
                    isEnabled={!!settings.aiAutofill}
                    onChange={handleToggleAIAutofill}
                />
            </div>

            {/* Add to all initiatives */}
            <div className="flex items-center justify-between py-2 border-t border-b border-border">
                <div className="flex items-center gap-2">
                    <span>Add to all {entityType === EntityType.INITIATIVE ? 'initiatives' : 'tasks'}</span>
                </div>
                {entityType === EntityType.INITIATIVE && (
                    <Toggle
                        isEnabled={!!settings.addToAllInitiatives}
                        onChange={handleToggleAddToAllInitiatives}
                    />
                ) || (
                    <Toggle
                        isEnabled={!!settings.addToAllTasks}
                        onChange={handleToggleAddToAllTasks}
                    />
                )}
            </div>

            {/* Options section */}
            <SettingsSection
                title="Options"
                className="relative"
            >
                <OptionsList
                    options={settings.options || []}
                    onAddOption={handleAddOption}
                    onEditOption={handleEditOption}
                    onDeleteOption={handleDeleteOption}
                    optionBgColor="bg-blue-100"
                    optionTextColor="text-blue-800"
                    placeholder="Add new option"
                    emptyMessage="No options added yet"
                />
            </SettingsSection>
        </div>
    );
};

export default SelectFieldSettings; 