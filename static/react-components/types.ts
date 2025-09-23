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

export enum LENS {
    NONE = 'NONE',
    INITIATIVE = 'INITIATIVE',
    TASK = 'TASK',
    INITIATIVES = 'INITIATIVES',
    TASKS = 'TASKS',
}

export enum AgentMode {
    DISCUSS = 'DISCUSS',
    EDIT = 'EDIT',
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

// --- AI Improvement Job Related Types ---

/**
 * Enum representing the action proposed by the LLM for an entity.
 */
export enum ManagedEntityAction {
    CREATE = "CREATE",
    UPDATE = "UPDATE",
    DELETE = "DELETE",
}

/**
 * Model for AI improvement errors.
 */
export interface AIImprovementError {
    type: "initiative" | "task";
    entity_id: string;
    status: "error";
    error_message: string;
    error_type?: string | null;
}

/**
 * Zod schema for AIImprovementError.
 */
export const AIImprovementErrorSchema = z.object({
    type: z.enum(["initiative", "task"]),
    entity_id: z.string(),
    status: z.literal("FAILED"),
    error_message: z.string(),
    error_type: z.string().nullable().optional(),
});


/**
 * Model representing a single proposed action on a task.
 */
export interface CreateTaskModel {
    action: ManagedEntityAction.CREATE;
    title: string; // Required for CREATE.
    description: string; // Required for CREATE.
    checklist: Record<string, any>[]; // Proposed checklist for the new task.
    initiative_identifier?: string | null; // Identifier of the parent initiative, if applicable.
}

export interface UpdateTaskModel {
    action: ManagedEntityAction.UPDATE;
    identifier: string; // Unique identifier for the existing task to update.
    title: string | null; // Updated title of the task.
    description: string | null; // Updated description of the task.
    checklist: Record<string, any>[]; // Updated checklist for the task.
}

export interface DeleteTaskModel {
    action: ManagedEntityAction.DELETE;
    identifier: string; // Unique identifier for the task to delete.
}

export type ManagedTaskModel = CreateTaskModel | UpdateTaskModel | DeleteTaskModel;

/**
 * Zod schema for ManagedTaskModel.
 */
export const CreateTaskModelSchema = z.object({
    action: z.literal(ManagedEntityAction.CREATE),
    title: z.string(),
    description: z.string(),
    checklist: z.array(z.record(z.any())).nullable().optional(),
    initiative_identifier: z.string().nullable().optional(),
});

export const UpdateTaskModelSchema = z.object({
    action: z.literal(ManagedEntityAction.UPDATE),
    identifier: z.string(),
    title: z.string().nullable().optional(),
    description: z.string().nullable().optional(),
    checklist: z.array(z.record(z.any())).nullable().optional(),
});

export const DeleteTaskModelSchema = z.object({
    action: z.literal(ManagedEntityAction.DELETE),
    identifier: z.string(),
});

export const ManagedTaskModelSchema = z.discriminatedUnion("action", [
    CreateTaskModelSchema,
    UpdateTaskModelSchema,
    DeleteTaskModelSchema,
]);


/**
 * Pydantic model defining the *standard* structure of the LLM response
 * for any task-related operation.
 */
export interface TaskLLMResponse {
    message: string;
    managed_tasks: ManagedTaskModel[]; // List of proposed actions (CREATE, UPDATE, DELETE) for tasks.
}

/**
 * Zod schema for TaskLLMResponse.
 */
export const TaskLLMResponseSchema = z.object({
    message: z.string(),
    managed_tasks: z.array(ManagedTaskModelSchema),
});


/**
 * Model representing a single proposed action on an initiative.
 */
export interface CreateInitiativeModel {
    action: ManagedEntityAction.CREATE;
    title: string; // Required for CREATE.
    description: string; // Required for CREATE.
    type?: string | null; // Type of the new initiative.
    workspace_identifier: string | null; // Identifier of the workspace for the new initiative.
    tasks?: ManagedTaskModel[]; // List of tasks associated with the new initiative.
}

export interface UpdateInitiativeModel {
    action: ManagedEntityAction.UPDATE;
    identifier: string; // Unique identifier for the existing initiative.
    title?: string | null; // Updated title of the initiative.
    description?: string | null; // Updated description of the initiative.
    type?: string | null; // Updated type of the initiative.
    status?: string | null; // Updated status of the initiative

    tasks?: ManagedTaskModel[] // Updated list of tasks associated with the initiative.
}

export interface DeleteInitiativeModel {
    action: ManagedEntityAction.DELETE;
    identifier: string; // Unique identifier for the initiative to delete.
}

export type ManagedInitiativeModel = CreateInitiativeModel | UpdateInitiativeModel | DeleteInitiativeModel;

/**
 * Zod schema for ManagedInitiativeModel.
 */
export const CreateInitiativeModelSchema = z.object({
    action: z.literal(ManagedEntityAction.CREATE),
    title: z.string(),
    description: z.string(),
    type: z.string().nullable().optional(),
    workspace_identifier: z.string().nullable().optional(),
    tasks: z.array(ManagedTaskModelSchema).nullable().optional(),
});

export const UpdateInitiativeModelSchema = z.object({
    action: z.literal(ManagedEntityAction.UPDATE),
    identifier: z.string(),
    title: z.string().nullable().optional(),
    description: z.string().nullable().optional(),
    type: z.string().nullable().optional(),
    status: z.nativeEnum(InitiativeStatus).nullable().optional(),
    tasks: z.array(ManagedTaskModelSchema).nullable().optional(),
});

export const DeleteInitiativeModelSchema = z.object({
    action: z.literal(ManagedEntityAction.DELETE),
    identifier: z.string(),
});

export const ManagedInitiativeModelSchema = z.discriminatedUnion("action", [
    CreateInitiativeModelSchema,
    UpdateInitiativeModelSchema,
    DeleteInitiativeModelSchema,
]);


/**
 * Pydantic model defining the standardized structure of the LLM response
 * for initiative batch operations.
 */
export interface InitiativeLLMResponse {
    message: string;
    managed_initiatives: ManagedInitiativeModel[]; // List of proposed actions (CREATE, UPDATE, DELETE) for initiatives.
}

/**
 * Zod schema for InitiativeLLMResponse.
 */
export const InitiativeLLMResponseSchema = z.object({
    message: z.string(),
    managed_initiatives: z.array(ManagedInitiativeModelSchema),
});

export interface DiscussResponseModel {
    message: string;
}

export const DiscussResponseModelSchema = z.object({
    message: z.string(),
});

export interface TasksInitiativeId {
    id: string;
}

export const TasksInitiativeIdSchema = z.object({
    id: z.string(),
});

export enum AiImprovementJobStatus {
    PENDING = 'PENDING',
    PROCESSING = 'PROCESSING',
    COMPLETED = 'COMPLETED',
    FAILED = "FAILED",
    CANCELED = "CANCELED",
}

/**
 * Schema for the ChatMessage interface used in AI Improvement Jobs
 */
export interface AiJobChatMessage {
    role: 'user' | 'assistant';
    content: string;
    suggested_changes?: ManagedTaskModel[] | ManagedInitiativeModel[] | null;
}

/**
 * Interface for the AI improvement job result
 */
export interface AiImprovementJobResult {
    id: string;
    lens: LENS;
    thread_id: string;
    status: AiImprovementJobStatus;
    mode: AgentMode;
    input_data: InitiativeDto[] | (TaskDto & TasksInitiativeId)[];
    result_data: InitiativeLLMResponse | TaskLLMResponse | DiscussResponseModel | AIImprovementError | null;
    messages: AiJobChatMessage[] | null;
    error_message: string | null;
    created_at: string;
    updated_at: string;
    user_id: string;
}

/**
 * Schema for the AiJobChatMessage interface
 */
export const AiJobChatMessageSchema = z.object({
    role: z.enum(['user', 'assistant']),
    content: z.string(),
});

/**
 * Schema for the AI improvement job result
 */
export const AiImprovementJobResultSchema = z.object({
    id: z.string(),
    lens: z.enum([LENS.INITIATIVE, LENS.TASK, LENS.INITIATIVES, LENS.TASKS]),
    status: z.nativeEnum(AiImprovementJobStatus),
    mode: z.nativeEnum(AgentMode),
    input_data: z.array(InitiativeDtoSchema).or(z.array(z.union([TaskSchema, z.object({ id: z.string() })]))),
    result_data: z.union([
        InitiativeLLMResponseSchema,
        TaskLLMResponseSchema,
        DiscussResponseModelSchema,
        AIImprovementErrorSchema,
    ]).nullable(),
    messages: z.array(AiJobChatMessageSchema).nullable(),
    error_message: z.string().nullable(),
    created_at: z.string(),
    updated_at: z.string(),
    user_id: z.string(),
});

export interface ChatMessage {
    id: string;
    text: string;
    sender: 'user' | 'assistant';
    timestamp: Date;
    entityId: string | null;
    entityTitle: string | null;
    entityIdentifier: string | null;
    entityType: 'initiative' | 'task' | null;
}

export interface LocalStorageItems {
    filterTasksToInitiative: string | null;
    chat_messages: ChatMessage[];
}

export interface ContextDocumentDto {
    id?: string;
    title: string;
    content: string;
    created_at: string;
    updated_at: string;
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

