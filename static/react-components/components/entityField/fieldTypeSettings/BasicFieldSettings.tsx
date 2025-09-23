import React from 'react';
import { SettingsSection, SettingsRow, Toggle } from '#components/entityField/ui/index';
import { BaseFieldSettingsProps } from '../types';
import { EntityType } from '#types';

const BasicFieldSettings: React.FC<BaseFieldSettingsProps> = ({ entityType, settings, onUpdate }) => {

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
        </div>
    );
};

export default BasicFieldSettings;