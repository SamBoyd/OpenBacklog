import { expect, test, vi } from 'vitest';
import { afterAll, afterEach, beforeAll } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';

import {
    ContextType,
    EntityType,
    InitiativeDto,
    TaskDto,
    WorkspaceDto,
} from '#types';

import { getAllTasks, getTaskById, deleteTask, postTask, createTask, moveTask, moveTaskToStatus } from './tasks';

const jwtBuilder = require('jwt-builder');

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

// Mock checklistItems module - keeping original functions but ensuring checklistItemFromData works
vi.mock('./checklistItems', async () => {
    const actual = await vi.importActual('./checklistItems') as any;
    return {
        ...actual,
        checklistItemFromData: vi.fn().mockImplementation(item => item)
    };
});

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


const testWorkspace: WorkspaceDto = {
    id: 'workspace-123',
    name: 'Test Workspace',
    icon: 'folder',
    description: 'This is a test workspace',
};

const testIntiativeData: InitiativeDto[] = [
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
                        id: 'ordering-task-123',
                        user_id: '0378cbd0-7aa6-4ee3-bbf0-5239dbdd1b22',
                        workspace_id: 'workspace-123',
                        context_type: ContextType.STATUS_LIST,
                        context_id: 'e339ea65-171d-4572-be87-81d47efe086c',
                        entity_type: EntityType.TASK,
                        task_id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
                        initative_id: null,
                        position: 'aa',
                    },
                ] as any,
            },
        ],
        has_pending_job: null,
        workspace: testWorkspace
    },
];

export const restHandlers = [
    http.get('http://localhost:3000/initiative', () => {
        return HttpResponse.json(testIntiativeData);
    }),
    http.post('http://localhost:3000/initiative', () => {
        return HttpResponse.json({ id: 'e339ea65-171d-4572-be87-81d47efe086c' });
    }),
    // Handler for postTask's update call (Postgrest uses PATCH for updates)
    http.patch('http://localhost:3000/task', async ({ request }) => {
        const body = await request.json() as any;
        return HttpResponse.json([{ 
            id: body.id || '3ea33233-0c90-41fc-9d26-185a7de67b51',
            ...body 
        }]);
    }),
    // Handler for checklist item creation
    http.post('http://localhost:3000/checklist', async ({ request }) => {
        const body = await request.json() as any;
        return HttpResponse.json([{ 
            id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde',
            ...body
        }]);
    }),
    // Handler for checklist item deletion
    http.delete('http://localhost:3000/checklist', ({ request }) => {
        return HttpResponse.json({ success: true });
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


describe('getTaskById', () => {
    const sampleTask = {
        id: 'task-123',
        identifier: 'TM-123',
        user_id: 'user-123',
        initiative_id: 'init-123',
        title: 'Test Task',
        description: 'Description of test task',
        created_at: '2025-01-27T13:57:24.692Z',
        updated_at: '2025-01-27T13:57:24.692Z',
        status: 'IN_PROGRESS',
        type: 'CODING',
        has_pending_job: false,
        workspace: {
            id: 'workspace-123',
            name: 'Test Workspace',
            icon: 'folder',
            description: 'Test workspace description',
        },
        checklist: [
            {
                id: 'check-123',
                title: 'Checklist Item',
                order: 0,
                task_id: 'task-123',
                is_complete: false,
            },
        ],
        orderings: [
            {
                id: 'ordering-123',
                user_id: 'user-123',
                workspace_id: 'workspace-123',
                context_type: ContextType.STATUS_LIST,
                context_id: 'init-123',
                entity_type: EntityType.TASK,
                task_id: 'task-123',
                initiative_id: null,
                position: 'aa',
            },
        ],
    };

    test('returns task data for valid task id', async () => {
        server.use(
            http.get('http://localhost:3000/task', ({ request }) => {
                const url = new URL(request.url)
                const workspaceId = url.searchParams.get('workspace_id');
                expect(workspaceId).toBe('eq.workspace-123');

                return HttpResponse.json([sampleTask]);
            })
        );

        const result = await getTaskById('task-123');

        expect(result.id).toBe(sampleTask.id);
        expect(result.title).toBe(sampleTask.title);
        expect(result.checklist[0].id).toBe(sampleTask.checklist[0].id);

        // Verify that orderings data is properly transformed from snake_case to camelCase
        expect(result.orderings).toBeDefined();
        expect(result.orderings).toHaveLength(1);
        if (result.orderings) {
            expect(result.orderings[0].id).toBe('ordering-123');
            expect(result.orderings[0].contextType).toBe('STATUS_LIST'); // Transformed from context_type
            expect(result.orderings[0].contextId).toBe('init-123'); // Transformed from context_id
            expect(result.orderings[0].entityType).toBe('TASK'); // Transformed from entity_type
            expect(result.orderings[0].taskId).toBe('task-123'); // Transformed from entity_id
            expect(result.orderings[0].position).toBe('aa');
        }
    });

    test('throws error if no task found', async () => {
        server.use(
            http.get('http://localhost:3000/task', () => {
                return HttpResponse.json([]);
            })
        );

        await expect(getTaskById('nonexistent')).rejects.toThrowError('Task not found');
    });

    test('throws error if multiple tasks found', async () => {
        server.use(
            http.get('http://localhost:3000/task', () => {
                return HttpResponse.json([sampleTask, sampleTask]);
            })
        );

        await expect(getTaskById('task-123')).rejects.toThrowError('Error loading task');
    });

    test('throws error if task data fails validation', async () => {
        // Simulate invalid data (e.g. missing required property "id")
        const invalidTask = { ...sampleTask, id: undefined };
        server.use(
            http.get('http://localhost:3000/task', () => {
                return HttpResponse.json([invalidTask]);
            })
        );

        await expect(getTaskById('task-123')).rejects.toThrowError('Error loading task');
    });
});

describe('getAllTasks', () => {
    const sampleTask = {
        id: 'task-123',
        identifier: 'TM-123',
        user_id: 'user-123',
        initiative_id: 'init-123',
        title: 'Test Task',
        description: 'Description of test task',
        order: 1,
        created_at: '2025-01-27T13:57:24.692Z',
        updated_at: '2025-01-27T13:57:24.692Z',
        status: 'IN_PROGRESS',
        type: 'CODING',
        has_pending_job: false,
        workspace: {
            id: 'workspace-123',
            name: 'Test Workspace',
            icon: 'folder',
            description: 'Test workspace description',
        },
        checklist: [
            {
                id: 'check-123',
                title: 'Checklist Item',
                order: 0,
                task_id: 'task-123',
                is_complete: false,
            },
        ],
        orderings: [
            {
                id: 'ordering-123',
                user_id: 'user-123',
                workspace_id: 'workspace-123',
                context_type: ContextType.STATUS_LIST,
                context_id: 'init-123',
                entity_type: EntityType.TASK,
                task_id: 'task-123',
                initiative_id: null,
                position: 'aa',
            },
        ] as any,
    };

    test('returns an array of tasks for a valid response', async () => {
        server.use(
            http.get('http://localhost:3000/task', ({ request }) => {
                const url = new URL(request.url)
                const workspaceId = url.searchParams.get('workspace_id');
                expect(workspaceId).toBe('eq.workspace-123');

                return HttpResponse.json([sampleTask]);
            })
        );

        const tasks = await getAllTasks();
        expect(Array.isArray(tasks)).toBe(true);
        expect(tasks[0].id).toBe(sampleTask.id);
    });

    test('throws error if response has an error status', async () => {
        server.use(
            http.get('http://localhost:3000/task', () => {
                return HttpResponse.text('error', { status: 500 });
            })
        );

        await expect(getAllTasks()).rejects.toThrowError('Error loading tasks');
    });

    test('throws error if tasks array fails validation', async () => {
        // Simulate invalid task data by sending an object instead of expected fields
        const invalidTask = { ...sampleTask, id: undefined };
        server.use(
            http.get('http://localhost:3000/task', () => {
                return HttpResponse.json([invalidTask]);
            })
        );

        await expect(getAllTasks()).rejects.toThrowError('Error loading tasks');
    });
})

describe('postTask', () => {
    it('posts a task and receives the id of the new row back', async () => {
        let sentJson: any;

        server.use(
            http.patch(
                'http://localhost:3000/task',
                async ({ request }) => {
                    sentJson = await request.json();
                    return HttpResponse.json([{ id: '3ea33233-0c90-41fc-9d26-185a7de67b51' }]);
                }),
        );

        const response = await postTask({
            ...testIntiativeData[0].tasks[0],
            checklist: [],
        });
        expect(response).toEqual({
            id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
            type: undefined,
            title: undefined,
            status: undefined,
            user_id: undefined,
            created_at: undefined,
            identifier: undefined,
            updated_at: undefined,
            description: undefined,
            initiative_id: undefined,
            has_pending_job: undefined,
            checklist: undefined,
            workspace: undefined,
            orderings: undefined,
        });

        expect(sentJson).toMatchObject(
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
                workspace_id: 'workspace-123',
            }
        )
    });

    it('should be able to post a Task without an id', async () => {
        let sentJson: any;

        server.use(
            http.patch(
                'http://localhost:3000/task',
                async ({ request }) => {
                    sentJson = await request.json();
                    return HttpResponse.json([{ id: '3ea33233-0c90-41fc-9d26-185a7de67b51' }]);
                }),
        );

        const response: TaskDto = await postTask({
            type: 'CODING',
            title: 'Test Task',
            status: 'IN_PROGRESS',
            user_id: '0378cbd0-7aa6-4ee3-bbf0-5239dbdd1b22',
            created_at: '2025-01-27T13:57:24.692172',
            identifier: 'TM-001',
            updated_at: '2025-01-27T13:57:24.692173',
            description: 'This is a test task',
            initiative_id: 'e339ea65-171d-4572-be87-81d47efe086c',
        });

        expect(response).toEqual({
            id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
            type: undefined,
            title: undefined,
            status: undefined,
            user_id: undefined,
            created_at: undefined,
            identifier: undefined,
            updated_at: undefined,
            description: undefined,
            initiative_id: undefined,
            has_pending_job: undefined,
            checklist: undefined,
            workspace: undefined,
            orderings: undefined,
        });

    });

    it('should update the api with the checklist items if it has any', async () => {
        server.use(
            http.patch(
                'http://localhost:3000/task',
                async ({ request }) => {
                    return HttpResponse.json([{ id: '3ea33233-0c90-41fc-9d26-185a7de67b51' }]);
                }),
        );

        let sentChecklistItemJson: any;
        server.use(
            http.post(
                'http://localhost:3000/checklist',
                async ({ request }) => {
                    sentChecklistItemJson = await request.json();
                    return HttpResponse.json([{ id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde' }]);
                }),
        )

        const response = await postTask({
            ...testIntiativeData[0].tasks[0]
        });

        expect(sentChecklistItemJson).toMatchObject(
            {
                id: '14b96e1f-2f0a-4dff-968e-bb60a8ca9fde',
                order: 0,
                title: 'This is a checklist item',
                task_id: '3ea33233-0c90-41fc-9d26-185a7de67b51',
                is_complete: false,
            }
        )
    });
})

describe('deleteTask', () => {
    test('deletes the task successfully using FastAPI', async () => {
        server.use(
            http.delete('/api/tasks/456', () => {
                return HttpResponse.json({ message: 'Task deleted successfully' }, { status: 200 });
            })
        );

        await expect(deleteTask('456')).resolves.toBeUndefined();
    });

    test('handles error response from FastAPI', async () => {
        server.use(
            http.delete('/api/tasks/456', () => {
                return HttpResponse.json(
                    { detail: 'Task not found' },
                    { status: 404 }
                );
            })
        );

        await expect(deleteTask('456')).rejects.toThrowError('Task not found');
    });

    test('handles network errors', async () => {
        server.use(
            http.delete('/api/tasks/456', () => {
                return HttpResponse.json(
                    { detail: 'Internal server error' },
                    { status: 500 }
                );
            })
        );

        await expect(deleteTask('456')).rejects.toThrowError('Internal server error');
    });
})

describe('createTask', () => {
    test('creates a task using FastAPI endpoint', async () => {
        let sentJson: any;

        server.use(
            http.post('/api/tasks', async ({ request }) => {
                sentJson = await request.json();
                return HttpResponse.json({
                    id: 'new-task-123',
                    identifier: 'TM-123',
                    user_id: 'user-123',
                    initiative_id: 'init-123',
                    title: 'Test Task',
                    description: 'Test description',
                    status: 'TO_DO',
                    type: 'CODING',
                    workspace_id: 'workspace-123',
                    checklist: [
                        {
                            id: 'check-123',
                            title: 'Test checklist item',
                            is_complete: false,
                            order: 0,
                            task_id: 'new-task-123',
                            user_id: 'user-123'
                        }
                    ]
                });
            })
        );

        const taskData = {
            title: 'Test Task',
            description: 'Test description',
            status: 'TO_DO',
            type: 'CODING',
            initiative_id: 'init-123',
            checklist: [
                {
                    title: 'Test checklist item',
                    is_complete: false,
                    order: 0
                }
            ]
        };

        const response = await createTask(taskData);

        expect(sentJson).toMatchObject({
            title: 'Test Task',
            status: 'TO_DO',
            type: 'CODING',
            description: 'Test description',
            workspace_id: 'workspace-123',
            initiative_id: 'init-123',
            checklist: [
                {
                    title: 'Test checklist item',
                    is_complete: false,
                    order: 0
                }
            ]
        });

        expect(response.id).toBe('new-task-123');
        expect(response.title).toBe('Test Task');
        expect(response.status).toBe('TO_DO');
    });

    test('handles error response from FastAPI', async () => {
        server.use(
            http.post('/api/tasks', () => {
                return HttpResponse.json(
                    { detail: 'Validation error' },
                    { status: 400 }
                );
            })
        );

        await expect(createTask({ title: 'Test Task' })).rejects.toThrowError('Validation error');
    });

    test('includes workspace_id in request payload', async () => {
        let sentJson: any;

        server.use(
            http.post('/api/tasks', async ({ request }) => {
                sentJson = await request.json();
                return HttpResponse.json({
                    id: 'new-task-123',
                    identifier: 'TM-123',
                    title: 'Test Task',
                    status: 'TO_DO',
                    workspace_id: 'workspace-123'
                });
            })
        );

        await createTask({ title: 'Test Task', initiative_id: 'init-123' });

        expect(sentJson.workspace_id).toBe('workspace-123');
    });
})

describe('moveTask', () => {
    test('moves a task using FastAPI endpoint', async () => {
        let sentJson: any;

        server.use(
            http.put('/api/tasks/task-123/move', async ({ request }) => {
                sentJson = await request.json();
                return HttpResponse.json({
                    id: 'task-123',
                    identifier: 'TM-123',
                    user_id: 'user-123',
                    initiative_id: 'init-123',
                    title: 'Moved Task',
                    description: 'Test description',
                    status: 'TO_DO',
                    type: 'CODING',
                    workspace_id: 'workspace-123'
                });
            })
        );

        const response = await moveTask('task-123', 'after-task-456', null);

        expect(sentJson).toMatchObject({
            after_id: 'after-task-456',
            before_id: null
        });

        expect(response.id).toBe('task-123');
        expect(response.title).toBe('Moved Task');
    });

    test('moves task with before_id parameter', async () => {
        let sentJson: any;

        server.use(
            http.put('/api/tasks/task-123/move', async ({ request }) => {
                sentJson = await request.json();
                return HttpResponse.json({
                    id: 'task-123',
                    identifier: 'TM-123',
                    title: 'Moved Task',
                    status: 'TO_DO'
                });
            })
        );

        await moveTask('task-123', null, 'before-task-789');

        expect(sentJson).toMatchObject({
            after_id: null,
            before_id: 'before-task-789'
        });
    });

    test('handles error response from moveTask API', async () => {
        server.use(
            http.put('/api/tasks/task-123/move', () => {
                return HttpResponse.json(
                    { detail: 'Task not found' },
                    { status: 404 }
                );
            })
        );

        await expect(moveTask('task-123', null, null)).rejects.toThrowError('Task not found');
    });
})

describe('moveTaskToStatus', () => {
    test('moves a task to new status using FastAPI endpoint', async () => {
        let sentJson: any;

        server.use(
            http.put('/api/tasks/task-123/status', async ({ request }) => {
                sentJson = await request.json();
                return HttpResponse.json({
                    id: 'task-123',
                    identifier: 'TM-123',
                    user_id: 'user-123',
                    initiative_id: 'init-123',
                    title: 'Status Changed Task',
                    description: 'Test description',
                    status: 'IN_PROGRESS',
                    type: 'CODING',
                    workspace_id: 'workspace-123'
                });
            })
        );

        const response = await moveTaskToStatus('task-123', 'IN_PROGRESS', 'after-task-456', null);

        expect(sentJson).toMatchObject({
            new_status: 'IN_PROGRESS',
            after_id: 'after-task-456',
            before_id: null
        });

        expect(response.id).toBe('task-123');
        expect(response.status).toBe('IN_PROGRESS');
        expect(response.title).toBe('Status Changed Task');
    });

    test('moves task to status with positioning parameters', async () => {
        let sentJson: any;

        server.use(
            http.put('/api/tasks/task-123/status', async ({ request }) => {
                sentJson = await request.json();
                return HttpResponse.json({
                    id: 'task-123',
                    identifier: 'TM-123',
                    title: 'Status Changed Task',
                    status: 'DONE'
                });
            })
        );

        await moveTaskToStatus('task-123', 'DONE', null, 'before-task-789');

        expect(sentJson).toMatchObject({
            new_status: 'DONE',
            after_id: null,
            before_id: 'before-task-789'
        });
    });

    test('moves task to status without positioning', async () => {
        let sentJson: any;

        server.use(
            http.put('/api/tasks/task-123/status', async ({ request }) => {
                sentJson = await request.json();
                return HttpResponse.json({
                    id: 'task-123',
                    status: 'DONE'
                });
            })
        );

        await moveTaskToStatus('task-123', 'DONE', null, null);

        expect(sentJson).toMatchObject({
            new_status: 'DONE',
            after_id: null,
            before_id: null
        });
    });

    test('handles error response from moveTaskToStatus API', async () => {
        server.use(
            http.put('/api/tasks/task-123/status', () => {
                return HttpResponse.json(
                    { detail: 'Invalid status transition' },
                    { status: 400 }
                );
            })
        );

        await expect(moveTaskToStatus('task-123', 'INVALID_STATUS', null, null)).rejects.toThrowError('Invalid status transition');
    });
})