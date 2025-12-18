import z from "zod";

export const WorkspaceDtoSchema = z.object({
    id: z.string(),
    name: z.string(),
    icon: z.string().nullable().nullable(),
    description: z.string().nullable().nullable(),
})

export interface CompletableText {
    id?: string;
    title: string;
    isCompleted: boolean;
    tabLevel: number;
    originalTabLevel?: number;
}

export interface InitiativeDto {
    id: string;
    identifier: string;
    user_id: string;
    title: string;
    description: string;
    created_at: string;
    updated_at: string;
    status: string;
    type: string | null;
    tasks: Partial<TaskDto>[];
    has_pending_job: boolean | null;
    workspace?: WorkspaceDto;
    field_definitions?: Partial<FieldDefinitionDto>[];
    properties?: Record<string, any>;  // mapping of field_definition.id to value
    blocked_by_id?: string | null; // Foreign key ID
    blocked_by?: Partial<InitiativeDto>; // The initiative it's blocked by
    blocking?: Partial<InitiativeDto>[]; // Initiatives it blocks
    groups?: Partial<GroupDto>[]; // Groups it belongs to
    orderings?: OrderingDto[]; // Direct ordering relationships
}

export interface TaskDto {
    id: string;
    identifier: string;
    user_id: string;
    initiative_id: string;
    title: string;
    description: string;
    created_at: string;
    updated_at: string;
    status: string;
    type: string | null;
    checklist: Partial<ChecklistItemDto>[];
    has_pending_job: boolean | null;
    workspace: WorkspaceDto;
    field_definitions?: Partial<FieldDefinitionDto>[];
    properties?: Record<string, any>; // mapping of field_definition.id to value
    orderings?: OrderingDto[]; // Direct ordering relationships
}

export interface OrderingDto {
    id: string;
    contextType: ContextType;
    contextId: string | null;
    entityType: EntityType;
    initiativeId?: string | null;
    taskId?: string | null;
    position: string;
}


export interface ChecklistItemDto {
    id: string;
    title: string;
    order: number;
    task_id: string;
    is_complete: boolean;
}

export interface WorkspaceDto {
    id: string,
    name: string,
    description: string | null;
    icon: string | null;
}

export enum TaskStatus {
    TO_DO = 'TO_DO',
    IN_PROGRESS = 'IN_PROGRESS',
    BLOCKED = 'BLOCKED',
    DONE = 'DONE',
    ARCHIVED = 'ARCHIVED',
}

export enum InitiativeStatus {
    TO_DO = 'TO_DO',
    IN_PROGRESS = 'IN_PROGRESS',
    BLOCKED = 'BLOCKED',
    DONE = 'DONE',
    ARCHIVED = 'ARCHIVED',
    BACKLOG = 'BACKLOG',
}

export enum ContextType {
    GROUP = 'GROUP',
    STATUS_LIST = 'STATUS_LIST',
}


export const statusDisplay = (type: string): string => {
    if (type === '') {
        return '';
    }
    // capitalize the first letter and remove underscores
    return type.charAt(0).toUpperCase() + type.slice(1).toLowerCase().replace(/_/g, ' ');
}

export interface ChecklistPayload {
    id?: string;
    title: string;
    is_complete: boolean;
    order: number;
}

export interface TaskPayload {
    id?: string;
    title: string;
    status: string;
    checklist: ChecklistPayload[];
}

export interface InitiativePayload {
    id?: string;
    title: string;
    status: string;
    tasks: TaskPayload[];
}

export const ChecklistItemSchema = z.object({
    // Define the checklist item schema
    id: z.string(),
    title: z.string(),
    order: z.number(),
    task_id: z.string(),
    is_complete: z.boolean(),
});

// --- Field Definition Types ---

export enum EntityType {
    INITIATIVE = "INITIATIVE",
    TASK = "TASK",
}

export enum FieldType {
    TEXT = "TEXT",
    NUMBER = "NUMBER",
    SELECT = "SELECT",
    MULTI_SELECT = "MULTI_SELECT",
    STATUS = "STATUS",
    DATE = "DATE",
    CHECKBOX = "CHECKBOX",
    URL = "URL",
    EMAIL = "EMAIL",
    PHONE = "PHONE",
}

export const FieldDefinitionDtoSchema = z.object({
    id: z.string().uuid(),
    workspace_id: z.string().uuid(),
    entity_type: z.nativeEnum(EntityType),
    key: z.string(),
    name: z.string(),
    field_type: z.nativeEnum(FieldType),
    is_core: z.boolean(),
    column_name: z.string().nullable(),
    config: z.record(z.any()),
    created_at: z.string().datetime(),
    updated_at: z.string().datetime(),
    initiative_id: z.string().uuid().nullable().optional(),
    task_id: z.string().uuid().nullable().optional(),
});

export interface FieldDefinitionDto {
    id: string;
    workspace_id: string;
    entity_type: EntityType;
    key: string;
    name: string;
    field_type: FieldType;
    is_core: boolean;
    column_name: string | null;
    config: Record<string, any>;
    created_at: string;
    updated_at: string;
    initiative_id?: string | null;
    task_id?: string | null;
}

export type CreateFieldDefinitionDto = Omit<FieldDefinitionDto, 'id' | 'workspace_id' | 'is_core' | 'column_name' | 'created_at' | 'updated_at'>


export const OrderingDtoSchema = z.object({
    id: z.string(),
    user_id: z.string(),
    workspace_id: z.string(),
    context_type: z.nativeEnum(ContextType),
    context_id: z.string().nullable(),
    entity_type: z.nativeEnum(EntityType),
    initiative_id: z.string().nullable(),
    task_id: z.string().nullable(),
    position: z.string(),
});

export const TaskSchema = z.object({
    // Define the task schema
    id: z.string(),
    identifier: z.string(),
    user_id: z.string(),
    initiative_id: z.string(),
    title: z.string(),
    description: z.string(),
    created_at: z.string(),
    updated_at: z.string(),
    status: z.enum([
        "TO_DO",
        "IN_PROGRESS",
        "BLOCKED",
        "DONE",
        "ARCHIVED"
    ]),
    type: z.string().nullable(),
    has_pending_job: z.boolean().nullable(),
    checklist: z.array(ChecklistItemSchema),
    workspace: WorkspaceDtoSchema.optional(),
    field_definitions: z.array(FieldDefinitionDtoSchema.partial()).optional(),
    properties: z.record(z.any()).optional(),
    orderings: z.array(OrderingDtoSchema).optional(),
});

export const InitiativeDtoSchema: z.ZodType<any> = z.lazy(() =>
    z.object({
        id: z.string(),
        identifier: z.string(),
        user_id: z.string(),
        title: z.string(),
        description: z.string(),
        created_at: z.string(),
        updated_at: z.string(),
        status: z.string(),
        type: z.string().nullable(),
        has_pending_job: z.boolean(),
        tasks: z.array(TaskSchema),
        field_definitions: z.array(FieldDefinitionDtoSchema.partial()).optional(),
        properties: z.record(z.any()).optional(),
        blocked_by_id: z.string().nullable().optional(), // Foreign key ID
        blocked_by: InitiativeDtoSchema.optional(), // The initiative it's blocked by (recursive partial)
        blocking: z.array(InitiativeDtoSchema).optional(), // Initiatives it blocks (recursive partial)
        groups: z.array(GroupDtoSchema).optional(), // Groups it belongs to
        orderings: z.array(OrderingDtoSchema).optional(), // Direct ordering relationships
        workspace: WorkspaceDtoSchema.optional(),
    })
);

export interface formatCompletableTextToJSONReturnType {
    initiatives: InitiativePayload[];
    initiativesToDelete: string[];
    tasksToDelete: string[];
    checklistItemsToDelete: string[];
}

export interface TasksInitiativeId {
    id: string;
}

export const TasksInitiativeIdSchema = z.object({
    id: z.string(),
});


export interface LocalStorageItems {
    filterTasksToInitiative: string | null;
}

export interface ContextDocumentDto {
    id?: string;
    title: string;
    content: string;
    created_at: string;
    updated_at: string;
}

export interface StrategicInitiativeDto {
    id: string;
    initiative_id: string;
    workspace_id: string;
    pillar_id: string | null;
    theme_id: string | null;
    description: string | null;
    narrative_intent: string | null;
    created_at: string;
    updated_at: string;
    initiative?: Partial<InitiativeDto>; // Join data for display
    pillar?: any; // Embedded pillar from PostgREST join (ThemeDto)
    theme?: any; // Embedded theme from PostgREST join (ThemeDto)
    heroes?: HeroDto[]; // Embedded heroes from strategic_initiative_heroes junction table
    villains?: VillainDto[]; // Embedded villains from strategic_initiative_villains junction table
    conflicts?: ConflictDto[]; // Embedded conflicts from strategic_initiative_conflicts junction table
}

export const ContextDocumentDtoSchema = z.object({
    id: z.string(),
    title: z.string(),
    content: z.string(),
    created_at: z.string(),
    updated_at: z.string(),
});

export enum GroupType {
    EXPLICIT = "EXPLICIT",
    SMART = "SMART",
}

export interface GroupDto {
    id: string;
    user_id: string;
    workspace_id: string;
    name: string;
    description: string | null;
    group_type: GroupType;
    group_metadata: Record<string, any> | null; // TODO: This should be a zod object
    query_criteria: Record<string, any> | null; // TODO: This should be a zod object
    parent_group_id: string | null;
    children?: GroupDto[]; // Optional recursive relationship
    initiatives?: Partial<InitiativeDto>[]; // Optional relationship
}

export const GroupDtoSchema: z.ZodType<GroupDto> = z.lazy(() => z.object({
    id: z.string().uuid(),
    user_id: z.string().uuid(),
    workspace_id: z.string().uuid(),
    name: z.string(),
    description: z.string().nullable(),
    group_type: z.nativeEnum(GroupType),
    group_metadata: z.record(z.any()).nullable(),
    query_criteria: z.record(z.any()).nullable(),
    parent_group_id: z.string().uuid().nullable(),
    children: z.array(GroupDtoSchema).optional(), // Recursive definition
    initiatives: z.array(InitiativeDtoSchema)
}));

export interface InitiativeGroupDto {
    initiative_id: string;
    group_id: string;
}

export const InitiativeGroupDtoSchema = z.object({
    initiative_id: z.string().uuid(),
    group_id: z.string().uuid(),
    initiative: z.array(InitiativeDtoSchema)
});

// --- Narrative Layer Types ---

/**
 * Hero (user persona) data transfer object.
 */
export interface HeroDto {
    id: string;
    identifier: string;
    workspace_id: string;
    name: string;
    description: string | null;
    is_primary: boolean;
    created_at: string;
    updated_at: string;
}

export const HeroDtoSchema = z.object({
    id: z.string().uuid(),
    identifier: z.string(),
    workspace_id: z.string().uuid(),
    name: z.string().min(1).max(100),
    description: z.string().min(1).max(2000).nullable(),
    is_primary: z.boolean(),
    created_at: z.string(),
    updated_at: z.string(),
});

/**
 * Villain type enumeration for categorizing obstacles.
 */
export enum VillainType {
    EXTERNAL = 'EXTERNAL',
    INTERNAL = 'INTERNAL',
    TECHNICAL = 'TECHNICAL',
    WORKFLOW = 'WORKFLOW',
    OTHER = 'OTHER',
}

/**
 * Villain (problem/obstacle) data transfer object.
 */
export interface VillainDto {
    id: string;
    identifier: string;
    user_id: string;
    workspace_id: string;
    name: string;
    villain_type: VillainType;
    description: string;
    severity: number; // 1-5
    is_defeated: boolean;
    created_at: string;
    updated_at: string;
}

export const VillainDtoSchema = z.object({
    id: z.string().uuid(),
    identifier: z.string(),
    user_id: z.string().uuid(),
    workspace_id: z.string().uuid(),
    name: z.string().min(1).max(100),
    villain_type: z.nativeEnum(VillainType),
    description: z.string().min(1).max(2000),
    severity: z.number().int().min(1).max(5),
    is_defeated: z.boolean(),
    created_at: z.string(),
    updated_at: z.string(),
});

/**
 * Roadmap theme (story arc) data transfer object.
 */
export interface RoadmapThemeDto {
    id: string;
    identifier: string;
    workspace_id: string;
    title: string;
    description: string | null;
    created_at: string;
    updated_at: string;
}

export const RoadmapThemeDtoSchema = z.object({
    id: z.string().uuid(),
    identifier: z.string(),
    workspace_id: z.string().uuid(),
    name: z.string().min(1).max(200),
    description: z.string().min(1).max(2000).nullable(),
    created_at: z.string(),
    updated_at: z.string(),
});

/**
 * Conflict status enumeration.
 */
export enum ConflictStatus {
    OPEN = 'OPEN',
    ESCALATING = 'ESCALATING',
    RESOLVING = 'RESOLVING',
    RESOLVED = 'RESOLVED',
}

/**
 * Conflict data transfer object representing a hero vs villain tension.
 */
export interface ConflictDto {
    id: string;
    identifier: string;
    workspace_id: string;
    hero_id: string;
    villain_id: string;
    description: string;
    status: ConflictStatus;
    story_arc_id: string | null;
    resolved_at: string | null;
    created_at: string;
    updated_at: string;
    resolved_by_initiative_id?: string | null;
    hero?: HeroDto;
    villain?: VillainDto;
    story_arc?: RoadmapThemeDto;
    resolved_by_initiative?: Partial<InitiativeDto>;
}

export const ConflictDtoSchema = z.object({
    id: z.string().uuid(),
    identifier: z.string(),
    workspace_id: z.string().uuid(),
    hero_id: z.string().uuid(),
    villain_id: z.string().uuid(),
    description: z.string().min(1).max(2000),
    status: z.nativeEnum(ConflictStatus),
    story_arc_id: z.string().uuid().nullable(),
    resolved_at: z.string().nullable(),
    resolved_by_initiative_id: z.string().uuid().nullable().optional(),
    created_at: z.string(),
    updated_at: z.string(),
    hero: HeroDtoSchema.optional(),
    villain: VillainDtoSchema.optional(),
    story_arc: RoadmapThemeDtoSchema.nullable().optional(),
    resolved_by_initiative: InitiativeDtoSchema.nullable().optional(),
});

