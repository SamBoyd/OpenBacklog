import React from 'react';
import { Plus, CopyIcon, Trash } from 'lucide-react';
import { BaseFieldSettingsProps } from '#components/entityField/types';
import OptionsList from '#components/entityField/OptionsList';
import { SettingsSection, SettingsRow, Toggle } from '#components/entityField/ui/index';
import { EntityType } from '#types';

/**
 * Component for status field settings
 */
const StatusFieldSettings: React.FC<BaseFieldSettingsProps> = ({ entityType, settings, onUpdate }) => {
    const handleCycleSortType = () => {
        // Cycle through sort types
        const currentSortType = settings.sortType || 'manual';
        const nextSortType = currentSortType === 'manual'
            ? 'alphabetical'
            : currentSortType === 'alphabetical' ? 'reverse' : 'manual';
        onUpdate({ sortType: nextSortType });
    };

    const handleAddOption = (option: string) => {
        const updatedOptions = [...(settings.statusOptions || []), option];
        onUpdate({ statusOptions: updatedOptions });
    };

    const handleEditOption = (index: number, newValue: string) => {
        const updatedOptions = [...(settings.statusOptions || [])];
        updatedOptions[index] = newValue;
        onUpdate({ statusOptions: updatedOptions });
    };

    const handleDeleteOption = (index: number) => {
        const updatedOptions = (settings.statusOptions || []).filter((_, i) => i !== index);
        onUpdate({ statusOptions: updatedOptions });
    };

    function handleToggleAIAutofill(isEnabled: boolean): void {
        onUpdate({ aiAutofill: isEnabled });
    }

    function handleToggleAddToAllInitiatives(isEnabled: boolean): void {
        onUpdate({ addToAllInitiatives: isEnabled });
    }

    function handleToggleAddToAllTasks(isEnabled: boolean): void {
        onUpdate({ addToAllTasks: isEnabled });
    }

    return (
        <div className="flex flex-col gap-4 mt-4">
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
            {/* Sort type */}
            <SettingsRow
                label="Sort"
                value={settings.sortType || 'Manual'}
                onClick={handleCycleSortType}
                className="py-2"
            />

            {/* Options section */}
            <SettingsSection
                title="Status Options"
                className="border-t border-border pt-2"
            >
                <div className="flex justify-end mb-2">
                    <button className="text-primary">
                        <Plus size={18} />
                    </button>
                </div>

                <OptionsList
                    options={settings.statusOptions || []}
                    onAddOption={handleAddOption}
                    onEditOption={handleEditOption}
                    onDeleteOption={handleDeleteOption}
                    optionBgColor="bg-green-100"
                    optionTextColor="text-green-800"
                    placeholder="Add new status"
                    emptyMessage="No status options added yet"
                />
            </SettingsSection>
        </div>
    );
};

export default StatusFieldSettings; 