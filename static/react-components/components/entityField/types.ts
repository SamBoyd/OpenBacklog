import { EntityType, FieldType } from "#types";

/**
 * Field settings for different field types
 */
export interface FieldSettings {
    // Number field settings
    numberFormat?: 'plain' | 'comma' | 'percent' | 'currency';
    decimalPlaces?: number;
    displayAs?: 'number' | 'bar' | 'ring';

    // Select field settings
    orderSort?: boolean;
    options?: string[];
    isMultiSelect?: boolean;
    sortType?: 'manual' | 'alphabetical' | 'reverse';
    aiAutofill?: boolean;

    // Status field settings
    statusOptions?: string[];

    // Date field settings
    dateFormat?: string;
    timeFormat?: string;

    // Person field settings
    limit?: number;
    defaultValue?: string;

    // URL field settings
    showFullUrl?: boolean;

    // Add to all initiatives
    addToAllInitiatives?: boolean;

    // Add to all tasks
    addToAllTasks?: boolean;
}

export interface BaseFieldSettingsProps {
    entityType: EntityType;
    settings: FieldSettings;
    onUpdate: (updatedSettings: Partial<FieldSettings>) => void;
}

export interface AddFieldResult {
    name: string;
    field_type: FieldType;
    entity_type: EntityType;
    settings?: FieldSettings;
} 