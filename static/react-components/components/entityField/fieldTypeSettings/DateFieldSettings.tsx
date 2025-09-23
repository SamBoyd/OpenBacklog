import React from 'react';
import { SelectBox } from '#components/reusable/Selectbox';
import { BaseFieldSettingsProps } from '#components/entityField/types';
import { Toggle } from '../ui';
import { EntityType } from '#types';

/**
 * Component for date field settings
 */
const DateFieldSettings: React.FC<BaseFieldSettingsProps> = ({ entityType, settings, onUpdate }) => {
    const dateFormatOptions = [
        { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY' },
        { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY' },
        { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD' }
    ];

    const timeFormatOptions = [
        { value: '12h', label: '12-hour (AM/PM)' },
        { value: '24h', label: '24-hour' },
        { value: 'none', label: 'No time' }
    ];

    function handleToggleAddToAllInitiatives(isEnabled: boolean): void {
        onUpdate({ addToAllInitiatives: isEnabled });
    }

    function handleToggleAddToAllTasks(isEnabled: boolean): void {
        onUpdate({ addToAllTasks: isEnabled });
    }

    return (
        <div className="flex flex-col gap-4 mt-4">
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

            <div>
                <label className="block text-sm font-medium mb-1">Date format</label>
                <SelectBox
                    options={dateFormatOptions}
                    value={settings.dateFormat}
                    onChange={(value) => onUpdate({ dateFormat: value })}
                />
            </div>

            <div>
                <label className="block text-sm font-medium mb-1">Time format</label>
                <SelectBox
                    options={timeFormatOptions}
                    value={settings.timeFormat}
                    onChange={(value) => onUpdate({ timeFormat: value })}
                />
            </div>
        </div>
    );
};

export default DateFieldSettings; 