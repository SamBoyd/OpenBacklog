// Set REST_URL environment variable for tests before any imports
process.env.POSTGREST_URL = 'http://localhost:3000';

import { expect, test, vi } from 'vitest';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

import {
    postInitiative,
    getAllInitiatives,
    deleteInitiative,
    getInitiativeById,
    createInitiative,
    moveInitiative,
    moveInitiativeToStatus,
    addInitiativeToGroup,
    removeInitiativeFromGroup
} from './initiatives';

import {
    ContextType,
    EntityType,
    WorkspaceDto,
} from '#types';

// Mock the fetchCurrentWorkspace function
vi.mock('#services/workspaceApi', () => ({
    fetchCurrentWorkspace: async () => ({
        id: 'workspace-123',
        name: 'Test Workspace',
        icon: 'folder',
    }),
    getCurrentWorkspaceIdFromCookie: () => 'workspace-123',
    getCurrentWorkspaceFromCookie: () => ({
        id: 'workspace-123',
        name: 'Test Workspace',
        icon: 'folder',
    }),
}));

// Mock JWT functions
vi.mock('#api/jwt', () => ({
    loadAndValidateJWT: vi.fn().mockReturnValue('mock-jwt-token'),
    checkJwtAndRenew: vi.fn().mockResolvedValue(undefined),
    renewJWT: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('#api/tasks', () => ({
    taskFromData: vi.fn().mockImplementation(item => item),
    createTask: vi.fn().mockImplementation(item => item),
    postTask: vi.fn().mockImplementation(item => item),
}));

const jwtBuilder = require('jwt-builder');

const testWorkspace: WorkspaceDto = {
    id: '1',
    name: 'Personal',
    description: null,
    icon: null
};

const testIntiativeData = [
    {
        type: 'FEATURE',
        id: 'e339ea65-171d-4572-be87-81d47efe086c',
        identifier: 'I-001',
        user_id: '0378cbd0-7aa6-4ee3-bbf0-5239dbdd1b22',
        title: 'Test Initiative',
        description: 'This is a test initiative',
        created_at: '2025-01-27T13:57:24.692117',
        updated_at: '2025-01-27T13:57:24.692117',
        status: 'IN_PROGRESS',
        has_pending_job: true,
        tasks: [
            {
                id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
                type: 'CODING',
                title: 'Test Task',
                status: 'IN_PROGRESS',
                user_id: '0378cbd0-7aa6-4ee3-bbf0-5239dbdd1b22',
                created_at: '2025-01-27T13:57:24.692172',
                identifier: 'TM-001',
                updated_at: '2025-01-27T13:57:24.692173',
                description: 'This is a test task',
                initiative_id: 'e339ea65-171d-4572-be87-81d47efe086c',
                has_pending_job: false,
                checklist: [
                    {
                        id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde',
                        order: 0,
                        title: 'This is a checklist item',
                        task_id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
                        is_complete: false,
                    },
                ],
                orderings: [
                    {
                        id: 'ordering-task-456',
                        user_id: '0378cbd0-7aa6-4ee3-bbf0-5239dbdd1b22',
                        workspace_id: '1',
                        context_type: ContextType.STATUS_LIST,
                        context_id: null,
                        entity_type: EntityType.TASK,
                        task_id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
                        initiative_id: null,
                        position: 'bb',
                    },
                ],
            },
        ],
        orderings: [
            {
                id: 'ordering-initiative-123',
                user_id: '0378cbd0-7aa6-4ee3-bbf0-5239dbdd1b22',
                workspace_id: '1',
                context_type: ContextType.STATUS_LIST,
                context_id: null,
                entity_type: EntityType.INITIATIVE,
                task_id: null,
                initiative_id: 'e339ea65-171d-4572-be87-81d47efe086c',
                position: 'aa',
            },
        ] as any,
        workspace: testWorkspace
    },
];

export const restHandlers = [
    http.get('http://localhost:3000/initiative', () => {
        const queryParams = new URLSearchParams(window.location.search);
        const workspaceId = queryParams.get('workspace_id');
        expect(workspaceId).toBe('workspace-123');

        return HttpResponse.json(testIntiativeData);
    }),
    http.post('http://localhost:3000/initiative', () => {
        const queryParams = new URLSearchParams(window.location.search);
        const workspaceId = queryParams.get('workspace_id');
        expect(workspaceId).toBe('workspace-123');

        return HttpResponse.json({ id: 'e339ea65-171d-4572-be87-81d47efe086c' });
    }),
    http.patch('http://localhost:3000/initiative', async ({ request }) => {
        const body = await request.json() as any;
        return HttpResponse.json([{ 
            id: body.id || 'e339ea65-171d-4572-be87-81d47efe086c',
            ...body 
        }]);
    }),
    http.patch('http://localhost:3000/task', async ({ request }) => {
        const body = await request.json() as any;
        return HttpResponse.json([{
            id: body.id || '3ea33233-0c90-41fc-9d26-185a7de67b51',
            ...body
        }]);
    }),
    http.put('http://localhost:3000/task', async ({ request }) => {
        const body = await request.json() as any;
        return HttpResponse.json([{
            id: body.id || '3ea33233-0c90-41fc-9d26-185a7de67b51',
            ...body
        }]);
    }),
];

// Suppress console.error output during tests
const originalConsoleError = console.error;
const server = setupServer(...restHandlers);

const jwtWithExpiry = (expiry: number) => {
    return jwtBuilder({
        algorithm: 'HS256',
        secret: 'super-secret',
        nbf: true,
        exp: (new Date()).getTime() + expiry,
        iss: 'https://example.com',
        userId: '539e4cba-4893-428a-bafd-1110f023514f',
        headers: {
            kid: '2016-11-17'
        }
    });
}


// Start server before all tests
beforeAll(() => {
    server.listen({ onUnhandledRequest: 'error' });
    console.error = vi.fn();

    document.cookie = `auth0_jwt=${jwtWithExpiry(10)}; expires=${new Date(Date.now() + 3600 * 1000).toUTCString()}; path=/;`;
    document.cookie = `refresh_token=refresh_token; expires=${new Date(Date.now() + 3600 * 1000).toUTCString()}; path=/;`;
});

// Close server after all tests
afterAll(() => {
    server.close();
    console.error = originalConsoleError;
});

// Reset handlers after each test for test isolation
afterEach(() => server.resetHandlers());

// Mock the fetchCurrentWorkspace function
vi.mock('#services/workspaceApi', () => ({
    fetchCurrentWorkspace: async () => ({
        id: 'workspace-123',
        name: 'Test Workspace',
        icon: 'folder',
    }),
    getCurrentWorkspaceFromCookie: () => ({
        id: 'workspace-123',
        name: 'Test Workspace',
        icon: 'folder',
    }),
    getCurrentWorkspaceIdFromCookie: () => 'workspace-123',
}));

// Mock JWT functions
vi.mock('#api/jwt', () => ({
    loadAndValidateJWT: vi.fn().mockReturnValue('mock-jwt-token'),
    checkJwtAndRenew: vi.fn().mockResolvedValue(undefined),
    renewJWT: vi.fn().mockResolvedValue(undefined),
}));

// Mock api-utils to override PostgrestClient initialization
vi.mock('#api/api-utils', async () => {
    const actual = await vi.importActual('#api/api-utils') as any;
    return {
        ...actual,
        REST_URL: 'http://localhost:3000',
        getPostgrestClient: () => {
            const { PostgrestClient } = require('@supabase/postgrest-js');
            return new PostgrestClient('http://localhost:3000', {
                headers: {
                    'Prefer': 'resolution=merge-duplicates',
                    Authorization: 'Bearer mock-jwt-token',
                    schema: 'dev',
                },
            });
        },
    };
});


describe('getAllInitiatives', () => {
    test('getAllInitiatives', async () => {
        // Mock API response that returns data with 'task' field (as API actually does)
        const apiResponse = testIntiativeData.map(init => ({
            ...init,
            task: init.tasks,
            orderings: init.orderings
        }));

        server.use(
            http.get('http://localhost:3000/initiative', ({ request }) => {
                const url = new URL(request.url)
                const workspaceId = url.searchParams.get('workspace_id');
                expect(workspaceId).toBe('eq.workspace-123');
                return HttpResponse.json(apiResponse);
            }),
        );

        const response = await getAllInitiatives();

        // First, verify orderings transformation separately
        expect(response[0].orderings).toBeDefined();
        expect(response[0].orderings).toHaveLength(1);
        if (response[0].orderings) {
            expect(response[0].orderings[0].contextType).toBe('STATUS_LIST'); // Transformed from context_type
            expect(response[0].orderings[0].entityType).toBe('INITIATIVE'); // Transformed from entity_type
            expect(response[0].orderings[0].initiativeId).toBe('e339ea65-171d-4572-be87-81d47efe086c'); // Transformed from entity_id
        }

        // Remove orderings from expectedData for the main matching test
        const expectedDataWithoutOrderings = testIntiativeData.map(init => {
            const { workspace, orderings, ...rest } = init;
            return {
                ...rest,
                tasks: rest.tasks?.map(task => {
                    const { orderings: taskOrderings, ...taskRest } = task;
                    return taskRest;
                })
            };
        });
        expect(response).toMatchObject(expectedDataWithoutOrderings);
    });

    test('throws error if response is not 200', async () => {
        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.text('error', { status: 500 });
            }),
        );

        await expect(getAllInitiatives()).rejects.toThrowError(
            'Error loading initiatives',
        );
    });

    test('throws error if response is not JSON', async () => {
        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.text('Internal Server Error');
            }),
        );

        await expect(getAllInitiatives()).rejects.toThrowError(
            'Error loading initiatives',
        );
    });

    test('throws error if response is not an array', async () => {
        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.json({ message: 'Internal Server Error' });
            }),
        );

        await expect(getAllInitiatives()).rejects.toThrowError(
            'response.data.map is not a function',
        );
    });

    test('throws error if response is not an array of InitiativeDto', async () => {
        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.json([{ message: 'Internal Server Error' }]);
            }),
        );

        await expect(getAllInitiatives()).rejects.toThrowError(
            'Error loading initiatives',
        );
    });

    test('validates TaskStatus enum', async () => {
        const slightlyInvalidData = [
            {
                ...testIntiativeData[0],
                task: [ // API returns 'task' field
                    {
                        ...testIntiativeData[0].tasks[0],
                        status: 'INVALID',
                    },
                ],
                tasks: undefined, // tasks field undefined in API response
            },
        ];

        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.json(slightlyInvalidData);
            }),
        );

        await expect(getAllInitiatives()).rejects.toThrowError(
            'Error loading initiatives',
        );
    });

    test('should rename task field to tasks and preserve task data', async () => {
        // Mock API response with 'task' field instead of 'tasks'
        const apiResponseWithTaskField = [
            {
                ...testIntiativeData[0],
                task: [  // API returns 'task' field
                    {
                        id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
                        type: 'CODING',
                        title: 'Test Task',
                        status: 'IN_PROGRESS',
                        user_id: '0378cbd0-7aa6-4ee3-bbf0-5239dbdd1b22',
                        created_at: '2025-01-27T13:57:24.692172',
                        identifier: 'TM-001',
                        updated_at: '2025-01-27T13:57:24.692173',
                        description: 'This is a test task',
                        initiative_id: 'e339ea65-171d-4572-be87-81d47efe086c',
                        has_pending_job: false,
                        checklist: [
                            {
                                id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde',
                                order: 0,
                                title: 'This is a checklist item',
                                task_id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
                                is_complete: false,
                            },
                        ],
                    },
                ],
                tasks: undefined  // tasks field should be undefined initially
            }
        ];

        server.use(
            http.get('http://localhost:3000/initiative', ({ request }) => {
                const url = new URL(request.url);
                const workspaceId = url.searchParams.get('workspace_id');
                expect(workspaceId).toBe('eq.workspace-123');
                return HttpResponse.json(apiResponseWithTaskField);
            }),
        );

        const response = await getAllInitiatives();

        // Verify that the task data is preserved in the tasks field
        expect(response).toHaveLength(1);
        expect(response[0].tasks).toBeDefined();
        expect(response[0].tasks).toHaveLength(1);
        expect(response[0].tasks[0].id).toBe('3ea33233-0c90-41fc-9d26-185a7de67b51');
        expect(response[0].tasks[0].title).toBe('Test Task');

        // Verify that original task field is removed (not exposed in final response)
        expect(response[0]).not.toHaveProperty('task');
    });

    test('should handle empty task field correctly', async () => {
        // Mock API response with empty task field
        const apiResponseWithEmptyTask = [
            {
                ...testIntiativeData[0],
                task: [],  // Empty array
                tasks: undefined
            }
        ];

        server.use(
            http.get('http://localhost:3000/initiative', ({ request }) => {
                const url = new URL(request.url);
                const workspaceId = url.searchParams.get('workspace_id');
                expect(workspaceId).toBe('eq.workspace-123');
                return HttpResponse.json(apiResponseWithEmptyTask);
            }),
        );

        const response = await getAllInitiatives();

        // Verify that empty task array is properly handled  
        expect(response).toHaveLength(1);
        expect(response[0].tasks).toBeDefined();
        expect(response[0].tasks).toHaveLength(0);
        expect(response[0]).not.toHaveProperty('task');
    });

    test('should handle null task field correctly', async () => {
        // Mock API response with null task field
        const apiResponseWithNullTask = [
            {
                ...testIntiativeData[0],
                task: null,  // Null value
                tasks: undefined
            }
        ];

        server.use(
            http.get('http://localhost:3000/initiative', ({ request }) => {
                const url = new URL(request.url);
                const workspaceId = url.searchParams.get('workspace_id');
                expect(workspaceId).toBe('eq.workspace-123');
                return HttpResponse.json(apiResponseWithNullTask);
            }),
        );

        const response = await getAllInitiatives();

        // Verify that null task field is converted to empty array
        expect(response).toHaveLength(1);
        expect(response[0].tasks).toBeDefined();
        expect(response[0].tasks).toHaveLength(0);
        expect(response[0]).not.toHaveProperty('task');
    });
})

describe("postInitiative", () => {
    it('posts an initiative and receives the id of the new row back', async () => {

        let sentJson: any;

        server.use(
            http.patch(
                'http://localhost:3000/initiative',
                async ({ request }) => {
                    sentJson = await request.json();
                    return HttpResponse.json([{ id: 'e339ea65-171d-4572-be87-81d47efe086c' }]);
                }),
        );

        const response = await postInitiative({
            ...testIntiativeData[0],
            tasks: []
        });
        expect(response).toEqual({
            id: 'e339ea65-171d-4572-be87-81d47efe086c',
        });

        expect(sentJson).toMatchObject(
            {
                type: 'FEATURE',
                id: 'e339ea65-171d-4572-be87-81d47efe086c',
                identifier: 'I-001',
                user_id: '0378cbd0-7aa6-4ee3-bbf0-5239dbdd1b22',
                title: 'Test Initiative',
                description: 'This is a test initiative',
                created_at: '2025-01-27T13:57:24.692117',
                updated_at: '2025-01-27T13:57:24.692117',
                status: 'IN_PROGRESS',
                workspace_id: 'workspace-123',
            }
        )
    });

    it('should be able to post an Initiative without an id', async () => {
        let sentJson: any;

        server.use(
            http.patch(
                'http://localhost:3000/initiative',
                async ({ request }) => {
                    sentJson = await request.json();
                    return HttpResponse.json([{ id: 'e339ea65-171d-4572-be87-81d47efe086c' }]);
                }),
        );

        const response = await postInitiative({
            type: 'FEATURE',
            identifier: 'I-001',
            user_id: '0378cbd0-7aa6-4ee3-bbf0-5239dbdd1b22',
            title: 'Test Initiative',
            description: 'This is a test initiative',
            created_at: '2025-01-27T13:57:24.692117',
            updated_at: '2025-01-27T13:57:24.692117',
            status: 'IN_PROGRESS',
        });

        expect(response).toEqual({
            id: 'e339ea65-171d-4572-be87-81d47efe086c',
        });

    });

    it('should update the api with the tasks if it has any', async () => {
        server.use(
            http.patch(
                'http://localhost:3000/initiative',
                async ({ request }) => {
                    return HttpResponse.json([{ id: 'e339ea65-171d-4572-be87-81d47efe086c' }]);
                }),
        );

        const { postTask } = await import('#api/tasks');
        const postTaskSpy = vi.mocked(postTask);

        const response = await postInitiative({
            ...testIntiativeData[0],
            tasks: [{
                ...testIntiativeData[0].tasks[0],
                checklist: [],
                orderings: testIntiativeData[0].tasks[0].orderings?.map(o => ({
                    ...o,
                    contextType: o.context_type,
                    contextId: o.context_id,
                    entityType: o.entity_type,
                    taskId: o.task_id,
                    initiativeId: o.initiative_id,
                })),
            }],
        });

        expect(postTaskSpy).toHaveBeenCalledWith(
            expect.objectContaining({
                id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
                type: 'CODING',
                title: 'Test Task',
                status: 'IN_PROGRESS',
                user_id: '0378cbd0-7aa6-4ee3-bbf0-5239dbdd1b22',
                created_at: '2025-01-27T13:57:24.692172',
                identifier: 'TM-001',
                updated_at: '2025-01-27T13:57:24.692173',
                description: 'This is a test task',
                initiative_id: 'e339ea65-171d-4572-be87-81d47efe086c',
            })
        )
    });
})

describe('createInitiative', () => {
    test('creates an initiative successfully using FastAPI endpoint', async () => {
        const mockResponse = {
            id: 'new-initiative-123',
            identifier: 'I-123',
            title: 'New Initiative',
            status: 'BACKLOG',
            type: 'FEATURE',
            user_id: 'user-123',
            workspace_id: 'workspace-123'
        };

        server.use(
            http.post('/api/initiatives', async ({ request }) => {
                const sentJson = await request.json();
                expect(sentJson).toMatchObject({
                    title: 'New Initiative',
                    status: 'BACKLOG',
                    type: 'FEATURE',
                    workspace_id: 'workspace-123'
                });
                return HttpResponse.json(mockResponse, { status: 200 });
            }),
        );

        const result = await createInitiative({
            title: 'New Initiative',
            status: 'BACKLOG',
            type: 'FEATURE'
        });

        expect(result).toMatchObject({
            id: 'new-initiative-123',
            title: 'New Initiative',
            status: 'BACKLOG',
            type: 'FEATURE'
        });
    });
});

describe('deleteInitiative', () => {
    test('deletes the initiative successfully', async () => {
        server.use(
            http.delete('/api/initiatives/123', () => {
                return HttpResponse.json({ message: 'Initiative deleted successfully' }, { status: 200 });
            }),
        );

        const result = await deleteInitiative('123');
    });
});

describe('getInitiativeById', () => {
    const sampleInitiative = {
        id: 'init-123',
        identifier: 'I-123',
        user_id: 'user-123',
        title: 'Test Initiative',
        description: 'Initiative description',
        order: 1,
        created_at: '2025-01-27T13:57:24.692Z',
        updated_at: '2025-01-27T13:57:24.692Z',
        status: 'IN_PROGRESS',
        type: 'FEATURE',
        has_pending_job: false,
        tasks: [
            {
                id: 'task-123',
                identifier: 'TM-123',
                user_id: 'user-123',
                initiative_id: 'init-123',
                title: 'Test Task',
                description: 'Task description',
                order: 1,
                created_at: '2025-01-27T13:57:24.692Z',
                updated_at: '2025-01-27T13:57:24.692Z',
                status: 'IN_PROGRESS',
                type: 'CODING',
                has_pending_job: false,
                checklist: [],
                orderings: [
                    {
                        id: 'ordering-task-789',
                        user_id: 'user-123',
                        workspace_id: 'workspace-123',
                        context_type: ContextType.STATUS_LIST,
                        context_id: 'init-123',
                        entity_type: EntityType.TASK,
                        task_id: 'task-123',
                        initiative_id: null,
                        position: 'cc',
                    },
                ] as any,
            },
        ],
        orderings: [
            {
                id: 'ordering-initiative-789',
                user_id: 'user-123',
                workspace_id: 'workspace-123',
                context_type: ContextType.STATUS_LIST,
                context_id: null,
                entity_type: EntityType.INITIATIVE,
                task_id: null,
                initiative_id: 'init-123',
                position: 'dd',
            },
        ] as any,
    };

    test('returns initiative data for valid id', async () => {
        // Mock API response with 'task' field (as API actually returns)
        const apiResponse = {
            ...sampleInitiative,
            task: sampleInitiative.tasks, // API returns 'task' field
            tasks: undefined, // tasks field undefined in API response
            orderings: sampleInitiative.orderings // API returns orderings embedded
        };

        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.json([apiResponse]);
            })
        );

        const result = await getInitiativeById('init-123');
        expect(result.id).toBe(sampleInitiative.id);
        expect(result.title).toBe(sampleInitiative.title);
        expect(result.tasks[0].id).toBe(sampleInitiative.tasks[0].id);

        // Verify that orderings data is properly transformed from snake_case to camelCase
        expect(result.orderings).toBeDefined();
        expect(result.orderings).toHaveLength(1);
        if (result.orderings) {
            expect(result.orderings[0].id).toBe('ordering-initiative-789');
            expect(result.orderings[0].contextType).toBe('STATUS_LIST'); // Transformed from context_type
            expect(result.orderings[0].contextId).toBe(null); // Transformed from context_id
            expect(result.orderings[0].entityType).toBe('INITIATIVE'); // Transformed from entity_type
            expect(result.orderings[0].initiativeId).toBe('init-123'); // Transformed from entity_id
            expect(result.orderings[0].position).toBe('dd');
        }
    });

    test('throws error if no initiative found', async () => {
        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.json([]);
            })
        );

        await expect(getInitiativeById('nonexistent')).rejects.toThrowError('Initiative not found');
    });

    test('throws error if initiative data fails validation', async () => {
        // Simulate invalid data removing required field "id"
        const invalidInitiative = { ...sampleInitiative, id: undefined };
        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.json([invalidInitiative]);
            })
        );

        await expect(getInitiativeById('init-123')).rejects.toThrowError('Error loading initiative');
    });

    test('should rename task field to tasks and preserve task data', async () => {
        // Mock API response with 'task' field instead of 'tasks'
        const apiResponseWithTaskField = {
            ...sampleInitiative,
            task: [  // API returns 'task' field
                {
                    id: 'task-123',
                    identifier: 'TM-123',
                    user_id: 'user-123',
                    initiative_id: 'init-123',
                    title: 'Test Task',
                    description: 'Task description',
                    order: 1,
                    created_at: '2025-01-27T13:57:24.692Z',
                    updated_at: '2025-01-27T13:57:24.692Z',
                    status: 'IN_PROGRESS',
                    type: 'CODING',
                    has_pending_job: false,
                    checklist: [],
                },
            ],
            tasks: undefined  // tasks field should be undefined initially
        };

        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.json([apiResponseWithTaskField]);
            })
        );

        const result = await getInitiativeById('init-123');

        // Verify that the task data is preserved in the tasks field
        expect(result.tasks).toBeDefined();
        expect(result.tasks).toHaveLength(1);
        expect(result.tasks[0].id).toBe('task-123');
        expect(result.tasks[0].title).toBe('Test Task');

        // Verify that original task field is removed (not exposed in final response)
        expect(result).not.toHaveProperty('task');
    });

    test('should handle empty task field correctly', async () => {
        // Mock API response with empty task field
        const apiResponseWithEmptyTask = {
            ...sampleInitiative,
            task: [],  // Empty array
            tasks: undefined
        };

        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.json([apiResponseWithEmptyTask]);
            })
        );

        const result = await getInitiativeById('init-123');

        // Verify that empty task array is properly handled  
        expect(result.tasks).toBeDefined();
        expect(result.tasks).toHaveLength(0);
        expect(result).not.toHaveProperty('task');
    });

    test('should handle null task field correctly', async () => {
        // Mock API response with null task field
        const apiResponseWithNullTask = {
            ...sampleInitiative,
            task: null,  // Null value
            tasks: undefined
        };

        server.use(
            http.get('http://localhost:3000/initiative', () => {
                return HttpResponse.json([apiResponseWithNullTask]);
            })
        );

        const result = await getInitiativeById('init-123');

        // Verify that null task field is converted to empty array
        expect(result.tasks).toBeDefined();
        expect(result.tasks).toHaveLength(0);
        expect(result).not.toHaveProperty('task');
    });
});

describe('moveInitiative', () => {
    test('moves an initiative successfully', async () => {
        const mockResponse = {
            id: 'initiative-123',
            identifier: 'I-123',
            title: 'Test Initiative',
            status: 'IN_PROGRESS',
            type: 'FEATURE',
            user_id: 'user-123',
            workspace_id: 'workspace-123'
        };

        server.use(
            http.put('/api/initiatives/initiative-123/move', async ({ request }) => {
                const sentJson = await request.json();
                expect(sentJson).toMatchObject({
                    after_id: 'other-initiative-456',
                    before_id: null
                });
                return HttpResponse.json(mockResponse, { status: 200 });
            }),
        );

        const result = await moveInitiative('initiative-123', 'other-initiative-456', null);

        expect(result).toMatchObject({
            id: 'initiative-123',
            title: 'Test Initiative',
            status: 'IN_PROGRESS'
        });
    });
});

describe('moveInitiativeToStatus', () => {
    test('moves an initiative to a different status successfully', async () => {
        const mockResponse = {
            id: 'initiative-123',
            identifier: 'I-123',
            title: 'Test Initiative',
            status: 'DONE',
            type: 'FEATURE',
            user_id: 'user-123',
            workspace_id: 'workspace-123'
        };

        server.use(
            http.put('/api/initiatives/initiative-123/status', async ({ request }) => {
                const sentJson = await request.json();
                expect(sentJson).toMatchObject({
                    new_status: 'DONE',
                    after_id: null,
                    before_id: null
                });
                return HttpResponse.json(mockResponse, { status: 200 });
            }),
        );

        const result = await moveInitiativeToStatus('initiative-123', 'DONE', null, null);

        expect(result).toMatchObject({
            id: 'initiative-123',
            title: 'Test Initiative',
            status: 'DONE'
        });
    });
});

describe('addInitiativeToGroup', () => {
    test('adds an initiative to a group successfully', async () => {
        const mockResponse = {
            id: 'initiative-123',
            identifier: 'I-123',
            title: 'Test Initiative',
            status: 'IN_PROGRESS',
            type: 'FEATURE',
            user_id: 'user-123',
            workspace_id: 'workspace-123'
        };

        server.use(
            http.put('/api/initiatives/initiative-123/groups', async ({ request }) => {
                const sentJson = await request.json();
                expect(sentJson).toMatchObject({
                    group_id: 'group-456',
                    after_id: null,
                    before_id: null
                });
                return HttpResponse.json(mockResponse, { status: 200 });
            }),
        );

        const result = await addInitiativeToGroup('initiative-123', 'group-456', null, null);

        expect(result).toMatchObject({
            id: 'initiative-123',
            title: 'Test Initiative'
        });
    });
});

describe('removeInitiativeFromGroup', () => {
    test('removes an initiative from a group successfully', async () => {
        server.use(
            http.delete('/api/initiatives/initiative-123/groups/group-456', () => {
                return HttpResponse.json({ message: 'Initiative removed from group successfully' }, { status: 200 });
            }),
        );

        const result = await removeInitiativeFromGroup('initiative-123', 'group-456');

        expect(result).toEqual({ message: 'Initiative removed from group successfully' });
    });
});