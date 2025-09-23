import React from 'react';
import { SelectBox } from '#components/reusable/Selectbox';
import { BaseFieldSettingsProps } from '#components/entityField/types';
import { Toggle } from '../ui';
import { EntityType } from '#types';

/**
 * Component for number field settings
 */
const NumberFieldSettings: React.FC<BaseFieldSettingsProps> = ({ entityType, settings, onUpdate }) => {
    const formatOptions = [
        { value: 'plain', label: 'Plain' },
        { value: 'comma', label: 'With commas' },
        { value: 'percent', label: 'Percent' },
        { value: 'currency', label: 'Currency' }
    ];

    const decimalOptions = [
        { value: '0', label: '0' },
        { value: '1', label: '1' },
        { value: '2', label: '2' },
        { value: '3', label: '3' },
        { value: '4', label: '4' }
    ];

    const displayOptions = [
        { value: 'number', label: 'Number' },
        { value: 'bar', label: 'Bar' },
        { value: 'ring', label: 'Ring' }
    ];

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
            <div className="flex items-center justify-between ">
                <label className="block text-sm font-medium mb-1">Format</label>
                <SelectBox
                    options={formatOptions}
                    value={settings.numberFormat}
                    onChange={(value) => onUpdate({ numberFormat: value as any })}
                />
            </div>

            <div className="flex items-center justify-between ">
                <label className="block text-sm font-medium mb-1">Decimal places</label>
                <SelectBox
                    options={decimalOptions}
                    value={settings.decimalPlaces?.toString()}
                    onChange={(value) => onUpdate({ decimalPlaces: parseInt(value) })}
                />
            </div>

            <div className="flex items-center justify-between ">
                <label className="block text-sm font-medium mb-1">Display as</label>
                <SelectBox
                    options={displayOptions}
                    value={settings.displayAs}
                    onChange={(value) => onUpdate({ displayAs: value as any })}
                />
            </div>
        </div>
    );
};

export default NumberFieldSettings; 