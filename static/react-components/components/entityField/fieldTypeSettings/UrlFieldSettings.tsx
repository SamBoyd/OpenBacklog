import React from 'react';
import { SelectBox } from '#components/reusable/Selectbox';
import { BaseFieldSettingsProps } from '#components/entityField/types';
import { Toggle } from '../ui';
import { EntityType } from '#types';

/**
 * Component for URL field settings
 */
const UrlFieldSettings: React.FC<BaseFieldSettingsProps> = ({ entityType, settings, onUpdate }) => {
    const showFullUrlOptions = [
        { value: 'true', label: 'Yes' },
        { value: 'false', label: 'No' }
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
                <label className="block text-sm font-medium mb-1">Show full URL</label>
                <SelectBox
                    options={showFullUrlOptions}
                    value={settings.showFullUrl ? "true" : "false"}
                    onChange={(value) => onUpdate({ showFullUrl: value === "true" })}
                />
            </div>
        </div>
    );
};

export default UrlFieldSettings; 