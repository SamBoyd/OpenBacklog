import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
    FieldDefinitionDto,
    FieldDefinitionDtoSchema,
    EntityType,
    FieldType,
    WorkspaceDto,
} from '#types';
import { fetchCurrentWorkspace } from '#services/workspaceApi';
import { getPostgrestClient, withApiCall } from './api-utils';
import {
    fieldDefinitionFromData,
    fieldDefinitionToPayloadJSON,
    getFieldDefinitionById,
    postFieldDefinition,
    deleteFieldDefinition,
    getFieldDefinitionsForInitiative,
    getFieldDefinitionsForTask,
} from './fieldDefinitions';

// --- Mock Dependencies ---
vi.mock('#services/workspaceApi');
vi.mock('./api-utils', async (importOriginal) => {
    const actual: any = await importOriginal();
    return {
        // Mock withApiCall to simply execute the passed function
        withApiCall: vi.fn().mockImplementation(async (fn) => fn()), // Return promise directly
        getPostgrestClient: vi.fn(),
    };
});

// Mock Postgrest client methods globally
const mockSelect = vi.fn();
const mockEq = vi.fn();
const mockMaybeSingle = vi.fn();
const mockUpsert = vi.fn();
const mockSingle = vi.fn();
const mockDelete = vi.fn();
const mockThen = vi.fn(); // For promise resolution in specific chains like getById
const mockClientThen = vi.fn(); // For promise resolution of the client itself (e.g., delete)
// Dedicated mock for the delete builder's then method
const mockDeleteBuilderThen = vi.fn();
const mockDeleteBuilder = { then: mockDeleteBuilderThen };

const mockPostgrestClient = {
    from: vi.fn().mockReturnThis(),
    select: mockSelect.mockReturnThis(),
    eq: mockEq.mockReturnThis(),
    maybeSingle: mockMaybeSingle, // Terminal method returning object with .then
    upsert: mockUpsert.mockReturnThis(),
    single: mockSingle, // Terminal method returning object with .then
    delete: mockDelete.mockReturnThis(), // Returns this
    // Mock the `then` used implicitly/explicitly in query chains like getById
    then: mockThen,
    // Add a then method to make the client itself thenable for cases like the delete chain
    // where the builder is awaited directly.
    // We need to simulate the builder being thenable.
    // Let's make the *builder* returned by eq/delete thenable.
};

// --- Sample Data ---
const mockWorkspace: WorkspaceDto = {
    id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
    name: 'Test Workspace',
    icon: 'test-icon',
    description: 'A test workspace for field definitions',
};

const mockFieldDef1CreatedAt = new Date('2024-01-01T10:00:00.000Z').toISOString();
const mockFieldDef1UpdatedAt = new Date('2024-01-01T11:00:00.000Z').toISOString();

const mockFieldDef1: FieldDefinitionDto = {
    id: "cd441dc5-1bf8-423f-9f88-f47e1c747584",
    workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
    entity_type: EntityType.INITIATIVE,
    key: 'custom_field_1',
    name: 'Custom Field 1',
    field_type: FieldType.TEXT,
    is_core: false,
    column_name: 'custom_field_1',
    config: {},
    created_at: mockFieldDef1CreatedAt,
    updated_at: mockFieldDef1UpdatedAt,
    initiative_id: null,
    task_id: null,
};

// Raw data equivalent for mockFieldDef1, mimicking database response
const mockRawFieldDef1 = {
    id: 'cd441dc5-1bf8-423f-9f88-f47e1c747584',
    workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
    entity_type: 'INITIATIVE',
    key: 'custom_field_1',
    name: 'Custom Field 1',
    field_type: 'TEXT',
    is_core: false,
    column_name: 'custom_field_1',
    config: {},
    created_at: mockFieldDef1CreatedAt,
    updated_at: mockFieldDef1UpdatedAt,
    initiative_id: null,
    task_id: null,
};

const mockFieldDef2: FieldDefinitionDto = {
    id: 'cd441dc5-1bf8-423f-9f88-f47e1c747585',
    workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
    entity_type: EntityType.TASK,
    key: 'custom_field_2',
    name: 'Custom Field 2',
    field_type: FieldType.NUMBER,
    is_core: false,
    column_name: 'custom_field_2',
    config: { precision: 2 },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    initiative_id: null,
    task_id: null,
};
const mockRawData = {
    id: 'cd441dc5-1bf8-423f-9f88-f47e1c747584',
    workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
    entity_type: 'INITIATIVE',
    key: 'raw_field',
    name: 'Raw Field',
    field_type: 'TEXT',
    is_core: false,
    column_name: 'raw_field',
    config: { foo: 'bar' },
    created_at: '2023-01-01T00:00:00.000Z',
    updated_at: '2023-01-01T00:00:00.000Z',
    initiative_id: null,
    task_id: null,
    extra_prop: 'ignored',
};

describe.skip('fieldDefinitions API', () => {
    beforeEach(() => {
        // Reset mocks before each test
        vi.clearAllMocks();

        // Setup default mock implementations
        vi.mocked(fetchCurrentWorkspace).mockResolvedValue(mockWorkspace);
        vi.mocked(getPostgrestClient).mockReturnValue(mockPostgrestClient as any);

        // Reset Postgrest method mocks to return `this` or specific mock function
        mockPostgrestClient.from.mockClear().mockReturnThis();
        mockSelect.mockClear().mockReturnThis();
        mockEq.mockClear().mockReturnThis();
        mockUpsert.mockClear().mockReturnThis();
        mockDelete.mockClear().mockReturnThis();

        // Reset terminal method mocks returning promises/values
        mockMaybeSingle.mockClear();
        mockSingle.mockClear();
        mockThen.mockClear(); // For chains ending in .then()
        mockClientThen.mockClear(); // For chains ending implicitly (await builder)
        mockDeleteBuilderThen.mockClear(); // Clear the delete builder then mock

        // Default behavior for eq to return the client mock for chaining,
        // EXCEPT for the delete tests where specific behavior is needed.
        mockEq.mockReturnThis();
        // Default behavior for delete to return the client mock for chaining
        mockDelete.mockReturnThis();

        // Make the client mock itself thenable for implicit awaits on non-delete chains if needed
        // Example: If another function awaits the client directly, uncomment the line below.
        // (mockPostgrestClient as any).then = mockClientThen;

    });

    // --- Sync Function Tests ---

    describe.skip('fieldDefinitionFromData', () => {
        it('should correctly map raw data to FieldDefinitionDto', () => {
            const result = fieldDefinitionFromData(mockRawData);
            expect(result).toEqual({
                id: 'cd441dc5-1bf8-423f-9f88-f47e1c747584',
                workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
                entity_type: 'INITIATIVE',
                key: 'raw_field',
                name: 'Raw Field',
                field_type: 'TEXT',
                is_core: false,
                column_name: 'raw_field',
                config: { foo: 'bar' },
                created_at: '2023-01-01T00:00:00.000Z',
                updated_at: '2023-01-01T00:00:00.000Z',
                initiative_id: null,
                task_id: null,
            });
        });

        it('should handle missing optional fields', () => {
            const minimalRawData = {
                id: 'fd-min',
                workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
                entity_type: 'TASK',
                key: 'min_field',
                name: 'Min Field',
                field_type: 'DATE',
                is_core: true,
                column_name: 'min_field',
            };
            const result = fieldDefinitionFromData(minimalRawData);
            expect(result).toEqual({
                id: 'fd-min',
                workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
                entity_type: 'TASK',
                key: 'min_field',
                name: 'Min Field',
                field_type: 'DATE',
                is_core: true,
                column_name: 'min_field',
                config: undefined,
                created_at: undefined,
                updated_at: undefined,
                initiative_id: undefined,
                task_id: undefined,
            });
        });
    });

    describe.skip('fieldDefinitionToPayloadJSON', () => {
        it('should correctly map FieldDefinitionDto to JSON payload', () => {
            const result = fieldDefinitionToPayloadJSON(mockFieldDef1);
            // Excludes created_at, updated_at
            expect(result).toEqual({
                id: "cd441dc5-1bf8-423f-9f88-f47e1c747584",
                workspace_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
                entity_type: EntityType.INITIATIVE,
                key: 'custom_field_1',
                name: 'Custom Field 1',
                field_type: FieldType.TEXT,
                is_core: false,
                column_name: 'custom_field_1',
                config: {},
                initiative_id: null,
                task_id: null,
            });
        });

        it('should handle partial FieldDefinitionDto', () => {
            const partialData: Partial<FieldDefinitionDto> = {
                key: 'new_field',
                name: 'New Field',
                field_type: FieldType.CHECKBOX,
                entity_type: EntityType.TASK,
            };
            const result = fieldDefinitionToPayloadJSON(partialData);
            expect(result).toEqual({
                id: undefined,
                workspace_id: undefined,
                entity_type: EntityType.TASK,
                key: 'new_field',
                name: 'New Field',
                field_type: FieldType.CHECKBOX,
                is_core: undefined,
                column_name: undefined,
                config: undefined,
                initiative_id: undefined,
                task_id: undefined,
            });
        });
    });

    // --- Async Function Tests ---

    describe.skip('getFieldDefinitionById', () => {
        beforeEach(() => {
            // Mock the promise resolution via .then() for getFieldDefinitionById
            // maybeSingle returns an object that has a .then method
            mockMaybeSingle.mockReturnValue({ then: mockThen });
        });

        it('should fetch a field definition by ID', async () => {
            // Mock successful response within the .then() callback
            // IMPORTANT: Provide the RAW data format here for safeParse
            mockThen.mockImplementationOnce(async (callback) => callback({ data: mockRawFieldDef1, error: null }));

            const result = await getFieldDefinitionById("cd441dc5-1bf8-423f-9f88-f47e1c747584");

            expect(fetchCurrentWorkspace).toHaveBeenCalledTimes(1);
            expect(getPostgrestClient).toHaveBeenCalledTimes(1);
            expect(mockPostgrestClient.from).toHaveBeenCalledWith('field_definition');
            expect(mockSelect).toHaveBeenCalledWith('*');
            expect(mockEq).toHaveBeenCalledWith('workspace_id', mockWorkspace.id);
            expect(mockEq).toHaveBeenCalledWith('id', "cd441dc5-1bf8-423f-9f88-f47e1c747584");
            expect(mockMaybeSingle).toHaveBeenCalledTimes(1);
            expect(mockThen).toHaveBeenCalledTimes(1);
            // The final result should match the processed DTO
            expect(result).toEqual(mockFieldDef1);
        });

        it('should throw an error if field definition is not found', async () => {
            mockThen.mockImplementationOnce(async (callback) => callback({ data: null, error: null }));

            await expect(getFieldDefinitionById('fd-not-found')).rejects.toThrow('Field definition not found');

            expect(mockEq).toHaveBeenCalledWith('id', 'fd-not-found');
            expect(mockMaybeSingle).toHaveBeenCalledTimes(1);
            expect(mockThen).toHaveBeenCalledTimes(1);
        });


        it('should throw an error if API call fails', async () => {
            const apiError = { message: 'Network error' };
            mockThen.mockImplementationOnce(async (callback) => callback({ data: null, error: apiError }));

            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
            await expect(getFieldDefinitionById("cd441dc5-1bf8-423f-9f88-f47e1c747584")).rejects.toThrow('Error loading field definition');
            expect(consoleSpy).toHaveBeenCalledWith('Error loading field definition', apiError);
            consoleSpy.mockRestore();
        });


        it('should throw an error if data validation fails', async () => {
            const invalidRawData = { ...mockRawFieldDef1, name: null }; // name is required
            mockThen.mockImplementationOnce(async (callback) => callback({ data: invalidRawData, error: null }));

            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
            await expect(getFieldDefinitionById("cd441dc5-1bf8-423f-9f88-f47e1c747584")).rejects.toThrow('Error loading field definition: Invalid format');
            expect(consoleSpy).toHaveBeenCalledWith(
                'Error loading field definition - data format',
                expect.any(Object) // ZodError
            );
            consoleSpy.mockRestore();
        });
    });


    describe.skip('postFieldDefinition', () => {
        const newFieldDefPayload: Partial<FieldDefinitionDto> = {
            entity_type: EntityType.TASK,
            key: 'new_task_field',
            name: 'New Task Field',
            field_type: FieldType.NUMBER,
        };
        // Raw data returned by the API after creation
        const createdRawFieldDef = {
            ...fieldDefinitionToPayloadJSON(newFieldDefPayload),
            id: 'fd-new',
            workspace_id: mockWorkspace.id,
            is_core: false,
            column_name: 'new_task_field',
            config: {},
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        };
        // Processed DTO expected as the final result
        const expectedCreatedFieldDef = fieldDefinitionFromData(createdRawFieldDef);

        beforeEach(() => {
            // Mock the terminal .single() method for postFieldDefinition
            // It returns an object with .then
            mockSingle.mockReturnValue({ then: mockThen });
            // Default successful upsert returns the raw created data
            mockThen.mockImplementation(async (callback) => callback({ data: createdRawFieldDef, error: null }));
        });

        it('should create a new field definition', async () => {
            const result = await postFieldDefinition(newFieldDefPayload);

            expect(fetchCurrentWorkspace).toHaveBeenCalledTimes(1);
            expect(getPostgrestClient).toHaveBeenCalledTimes(1);
            expect(mockPostgrestClient.from).toHaveBeenCalledWith('field_definition');
            expect(mockUpsert).toHaveBeenCalledWith({
                ...fieldDefinitionToPayloadJSON(newFieldDefPayload),
                workspace_id: mockWorkspace.id,
            });
            expect(mockSelect).toHaveBeenCalledTimes(1);
            expect(mockSingle).toHaveBeenCalledTimes(1);
            expect(mockThen).toHaveBeenCalledTimes(1); // From single()
            expect(result).toEqual(expectedCreatedFieldDef); // Compare with processed DTO
        });

        it('should update an existing field definition', async () => {
            const updatePayload: Partial<FieldDefinitionDto> = {
                id: "cd441dc5-1bf8-423f-9f88-f47e1c747584",
                name: 'Updated Name',
            };
            const updatedRawResponseData = {
                ...mockRawFieldDef1, // Start with raw data
                name: 'Updated Name', // Apply update
                updated_at: new Date().toISOString(), // Update timestamp
            };
            const expectedUpdatedFieldDef = fieldDefinitionFromData(updatedRawResponseData);

            // Override the mock response for this specific test case
            mockThen.mockReset().mockImplementationOnce(async (callback) => callback({ data: updatedRawResponseData, error: null }));

            const result = await postFieldDefinition(updatePayload);

            expect(mockUpsert).toHaveBeenCalledWith({
                ...fieldDefinitionToPayloadJSON(updatePayload),
                workspace_id: mockWorkspace.id,
            });
            expect(mockSingle).toHaveBeenCalledTimes(1);
            expect(mockThen).toHaveBeenCalledTimes(1);
            expect(result).toEqual(expectedUpdatedFieldDef);
        });

        it('should throw an error if API call fails', async () => {
            const apiError = { message: 'Insert failed', code: '23505' };
            // Mock the .then() call from .single() to return an error
            mockThen.mockReset().mockImplementationOnce(async (callback) => callback({ data: null, error: apiError }));

            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
            await expect(postFieldDefinition(newFieldDefPayload)).rejects.toThrow(apiError.message);
            expect(consoleSpy).toHaveBeenCalledWith('Error posting field definition', apiError);
            consoleSpy.mockRestore();
        });


        it('should throw an error if no data is returned after upsert', async () => {
            // Mock the .then() call from .single() to return no data and no error
            mockThen.mockReset().mockImplementationOnce(async (callback) => callback({ data: null, error: null }));

            await expect(postFieldDefinition(newFieldDefPayload)).rejects.toThrow('No field definition created or updated');
        });
    });

    describe.skip('deleteFieldDefinition', () => {
        beforeEach(() => {
            vi.clearAllMocks();
            vi.mocked(fetchCurrentWorkspace).mockResolvedValue(mockWorkspace);
        });

        it('should delete a field definition by ID', async () => {
            // Create a mock for the entire PostgrestClient.from().delete().eq().eq() chain
            const mockDeleteSuccess = Promise.resolve({ error: null });
            const mockDeleteChain = {
                from: vi.fn().mockReturnValue({
                    delete: vi.fn().mockReturnValue({
                        eq: vi.fn().mockImplementation((field, value) => {
                            // First eq call (id)
                            expect(field).toBe('id');
                            expect(value).toBe("cd441dc5-1bf8-423f-9f88-f47e1c747584");
                            return {
                                eq: vi.fn().mockImplementation((field, value) => {
                                    // Second eq call (workspace_id)
                                    expect(field).toBe('workspace_id');
                                    expect(value).toBe(mockWorkspace.id);
                                    return mockDeleteSuccess;
                                })
                            };
                        })
                    })
                })
            };

            // Override the getPostgrestClient mock for this specific test
            vi.mocked(getPostgrestClient).mockReturnValue(mockDeleteChain as any);

            await expect(deleteFieldDefinition("cd441dc5-1bf8-423f-9f88-f47e1c747584")).resolves.toBeUndefined();

            expect(fetchCurrentWorkspace).toHaveBeenCalledTimes(1);
            expect(getPostgrestClient).toHaveBeenCalledTimes(1);
            expect(mockDeleteChain.from).toHaveBeenCalledWith('field_definition');
        });

        it('should throw an error if API call fails', async () => {
            const apiError = { message: 'Delete failed' };
            // Create a mock for the entire PostgrestClient.from().delete().eq().eq() chain
            const mockDeleteError = Promise.resolve({ error: apiError });
            const mockDeleteChain = {
                from: vi.fn().mockReturnValue({
                    delete: vi.fn().mockReturnValue({
                        eq: vi.fn().mockImplementation((field, value) => {
                            // First eq call (id)
                            return {
                                eq: vi.fn().mockReturnValue(mockDeleteError)
                            };
                        })
                    })
                })
            };

            // Override the getPostgrestClient mock for this specific test
            vi.mocked(getPostgrestClient).mockReturnValue(mockDeleteChain as any);

            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
            await expect(deleteFieldDefinition("cd441dc5-1bf8-423f-9f88-f47e1c747584")).rejects.toThrow(apiError.message);
            expect(consoleSpy).toHaveBeenCalledWith('Error deleting field definition', apiError);
            consoleSpy.mockRestore();
        });
    });

    describe.skip('getFieldDefinitionsForInitiative', () => {
        const initiativeId = '59a6ea4b-7494-4daf-819a-1884bd4eab6c';
        const mockInitiativeFieldDefs = [
            {
                ...mockRawFieldDef1,
                entity_type: 'INITIATIVE',
                initiative_id: initiativeId
            },
            {
                ...mockRawFieldDef1,
                id: 'fd-global-initiative',
                key: 'global_initiative_field',
                name: 'Global Initiative Field',
                entity_type: 'INITIATIVE',
                initiative_id: null
            }
        ];

        beforeEach(() => {
            // Mock for the or() method chain
            const mockOr = vi.fn();
            // Mock for the then() method on the or() result
            mockThen.mockReset();

            // Setup mocks for the chain
            mockPostgrestClient.from.mockReturnThis();
            mockSelect.mockReturnThis();
            mockEq.mockReturnThis();
            mockOr.mockReturnValue({ then: mockThen });

            // Add or method to the chain
            (mockPostgrestClient as any).or = mockOr;
        });

        it('should fetch field definitions for an initiative', async () => {
            mockThen.mockImplementationOnce(async (callback) => callback({
                data: mockInitiativeFieldDefs,
                error: null
            }));

            const result = await getFieldDefinitionsForInitiative(initiativeId);

            expect(fetchCurrentWorkspace).toHaveBeenCalledTimes(1);
            expect(getPostgrestClient).toHaveBeenCalledTimes(1);
            expect(mockPostgrestClient.from).toHaveBeenCalledWith('field_definition');
            expect(mockSelect).toHaveBeenCalledWith('*');
            expect(mockEq).toHaveBeenCalledWith('workspace_id', mockWorkspace.id);
            expect(mockEq).toHaveBeenCalledWith('entity_type', EntityType.INITIATIVE);
            expect((mockPostgrestClient as any).or).toHaveBeenCalledWith(`initiative_id.eq.${initiativeId},initiative_id.is.null`);
            expect(mockThen).toHaveBeenCalledTimes(1);

            // Should have 2 field definitions
            expect(result).toHaveLength(2);
            // First one should have the initiative_id
            expect(result[0].initiative_id).toBe(initiativeId);
            // Second one should be the global field (null initiative_id)
            expect(result[1].initiative_id).toBeNull();
        });

        it('should return an empty array if no field definitions are found', async () => {
            mockThen.mockImplementationOnce(async (callback) => callback({
                data: [],
                error: null
            }));

            const result = await getFieldDefinitionsForInitiative(initiativeId);

            expect(result).toEqual([]);
        });

        it('should throw an error if API call fails', async () => {
            const apiError = { message: 'Network error' };
            mockThen.mockImplementationOnce(async (callback) => callback({
                data: null,
                error: apiError
            }));

            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
            await expect(getFieldDefinitionsForInitiative(initiativeId)).rejects.toThrow('Error loading field definitions for initiative');
            expect(consoleSpy).toHaveBeenCalledWith(
                'Error loading field definitions for initiative',
                apiError
            );
            consoleSpy.mockRestore();
        });
    });

    describe.skip('getFieldDefinitionsForTask', () => {
        const taskId = '1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p';
        const mockTaskFieldDefs = [
            {
                ...mockRawFieldDef1,
                id: 'fd-task-specific',
                key: 'task_specific_field',
                name: 'Task Specific Field',
                entity_type: 'TASK',
                field_type: 'DATE',
                task_id: taskId
            },
            {
                ...mockRawFieldDef1,
                id: 'fd-global-task',
                key: 'global_task_field',
                name: 'Global Task Field',
                entity_type: 'TASK',
                field_type: 'CHECKBOX',
                task_id: null
            }
        ];

        beforeEach(() => {
            // Mock for the or() method chain
            const mockOr = vi.fn();
            // Mock for the then() method on the or() result
            mockThen.mockReset();

            // Setup mocks for the chain
            mockPostgrestClient.from.mockReturnThis();
            mockSelect.mockReturnThis();
            mockEq.mockReturnThis();
            mockOr.mockReturnValue({ then: mockThen });

            // Add or method to the chain
            (mockPostgrestClient as any).or = mockOr;
        });

        it('should fetch field definitions for a task', async () => {
            mockThen.mockImplementationOnce(async (callback) => callback({
                data: mockTaskFieldDefs,
                error: null
            }));

            const result = await getFieldDefinitionsForTask(taskId);

            expect(fetchCurrentWorkspace).toHaveBeenCalledTimes(1);
            expect(getPostgrestClient).toHaveBeenCalledTimes(1);
            expect(mockPostgrestClient.from).toHaveBeenCalledWith('field_definition');
            expect(mockSelect).toHaveBeenCalledWith('*');
            expect(mockEq).toHaveBeenCalledWith('workspace_id', mockWorkspace.id);
            expect(mockEq).toHaveBeenCalledWith('entity_type', EntityType.TASK);
            expect((mockPostgrestClient as any).or).toHaveBeenCalledWith(`task_id.eq.${taskId},task_id.is.null`);
            expect(mockThen).toHaveBeenCalledTimes(1);

            // Should have 2 field definitions
            expect(result).toHaveLength(2);
            // First one should have the task_id
            expect(result[0].task_id).toBe(taskId);
            // First one should be a DATE field type
            expect(result[0].field_type).toBe('DATE');
            // Second one should be the global field (null task_id)
            expect(result[1].task_id).toBeNull();
            // Second one should be a CHECKBOX field type
            expect(result[1].field_type).toBe('CHECKBOX');
        });

        it('should return an empty array if no field definitions are found', async () => {
            mockThen.mockImplementationOnce(async (callback) => callback({
                data: [],
                error: null
            }));

            const result = await getFieldDefinitionsForTask(taskId);

            expect(result).toEqual([]);
        });

        it('should throw an error if API call fails', async () => {
            const apiError = { message: 'Network error' };
            mockThen.mockImplementationOnce(async (callback) => callback({
                data: null,
                error: apiError
            }));

            const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => { });
            await expect(getFieldDefinitionsForTask(taskId)).rejects.toThrow('Error loading field definitions for task');
            expect(consoleSpy).toHaveBeenCalledWith(
                'Error loading field definitions for task',
                apiError
            );
            consoleSpy.mockRestore();
        });
    });
});
