import { EntityType, FieldDefinitionDto, FieldType  } from "#types";

export const initiativeStatusFieldDefinition: Omit<FieldDefinitionDto, 'id' | 'workspace_id'> = {
    entity_type: EntityType.INITIATIVE,
    key: 'status',
    name: 'Status',
    field_type: FieldType.SELECT,
    is_core: true,
    column_name: 'status',
    config: {
        options: [
            'BACKLOG',
            'TO_DO',
            'IN_PROGRESS',
            'DONE',
            'BLOCKED',
            'ARCHIVED',
        ]
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
};

export const initiativeTypeFieldDefinition: Omit<FieldDefinitionDto, 'id' | 'workspace_id'> = {
    entity_type: EntityType.INITIATIVE,
    key: 'type',
    name: 'Type',
    field_type: FieldType.SELECT,
    is_core: true,
    column_name: 'type',
    config: {
        options: [
            'FEATURE',
            'BUGFIX',
            'CHORE',
            'RESEARCH',
            'CODING',
            'TESTING',
            'DOCUMENTATION',
            'DESIGN',
        ]
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
};

export const taskStatusFieldDefinition: Omit<FieldDefinitionDto, 'id' | 'workspace_id'> = {
    entity_type: EntityType.TASK,
    key: 'status',
    name: 'Status',
    field_type: FieldType.SELECT,
    is_core: true,
    column_name: 'status',
    config: {
        options: [
            'TO_DO',
            'IN_PROGRESS',
            'DONE',
            'BLOCKED',
            'ARCHIVED',
        ]
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
};

export const taskTypeFieldDefinition: Omit<FieldDefinitionDto, 'id' | 'workspace_id'> = {
    entity_type: EntityType.TASK,
    key: 'type',
    name: 'Type',
    field_type: FieldType.SELECT,
    is_core: true,
    column_name: 'type',
    config: {
        options: [
            'FEATURE',
            'BUGFIX',
            'CHORE',
            'RESEARCH',
            'CODING',
            'TESTING',
            'DOCUMENTATION',
            'DESIGN',
        ]
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
};