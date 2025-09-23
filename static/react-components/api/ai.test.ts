import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { requestAiImprovement, AiImprovementRequest, AiApiError } from './ai';
import { InitiativeDto, LENS, WorkspaceDto } from '#types';
import { ZodError } from 'zod';

const jwtBuilder = require('jwt-builder');


// Set up MSW server
export const restHandlers = []
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
const originalConsoleError = console.error;
afterAll(() => {
    server.close();
    console.error = originalConsoleError;
});

const testWorkspace: WorkspaceDto = {
    id: '1',
    name: 'Personal',
    description: null,
    icon: null
};


const testInitiativeDto: InitiativeDto = {
    id: 'init-123',
    title: 'Test Initiative',
    description: 'A test initiative',
    identifier: 'I-001',
    user_id: '2',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    status: 'IN_PROGRESS',
    tasks: [],
    type: null,
    has_pending_job: null,
    workspace: testWorkspace,
};

describe.skip('AI API', () => {
    // Set up MSW before tests
    beforeAll(() => server.listen());

    // Reset handlers between tests
    afterEach(() => server.resetHandlers());

    // Clean up after tests are done
    afterAll(() => server.close());

    describe.skip('requestAiImprovement', () => {
        it('should make a POST request to the correct endpoint with correct data', async () => {
            // Set up the MSW handler for this test
            server.use(
                http.post('/api/ai-improvement', async ({ request }) => {
                    const body = await request.json();

                    // Verify request body
                    expect(body).toEqual({
                        initiative_id: 'init-123',
                        task_id: undefined,
                        input_data: testInitiativeDto
                    });

                    return HttpResponse.json({
                        job_id: '123abc',
                        status: 'pending'
                    },
                        { status: 200 }
                    );
                })
            );

            const params: AiImprovementRequest = {
                initiativeId: 'init-123',
                inputData: [testInitiativeDto],
                lens: LENS.INITIATIVE,
                threadId: 'thread1'
            };

            const result = await requestAiImprovement(params);

            // Check response is correct
            expect(result).toEqual({
                job_id: '123abc',
                status: 'pending'
            });
        });

        it('should throw an error if neither initiativeId nor taskId is provided', async () => {
            const params: AiImprovementRequest = {
                inputData: [testInitiativeDto],
                lens: LENS.INITIATIVE,
                threadId: 'thread1'
            };

            await expect(requestAiImprovement(params)).rejects.toThrow(
                'Either initiativeId or taskId must be provided'
            );
        });

        it('should handle HTTP error responses', async () => {
            // Mock error response with MSW
            server.use(
                http.post('/api/ai-improvement', ({ request }) => {
                    return HttpResponse.text(
                        'Bad Request',
                        { status: 400 }
                    );
                })
            );

            const params = {
                taskId: 'task-123',
                inputData: [testInitiativeDto],
                lens: LENS.INITIATIVE,
                threadId: 'thread1'
            };

            await expect(requestAiImprovement(params)).rejects.toThrow(AiApiError);
            await expect(requestAiImprovement(params)).rejects.toThrow(
                'Failed to request AI improvement: Bad Request'
            );
        });

        it('should validate response format using Zod schema', async () => {
            // Mock invalid response format with MSW
            server.use(
                http.post('/api/ai-improvement', ({ request }) => {
                    return HttpResponse.json(
                        {
                            invalid_field: 'some value'
                            // missing required job_id and status
                        },
                        { status: 200 }
                    );
                })
            );

            const params: AiImprovementRequest = {
                taskId: 'task-123',
                inputData: [testInitiativeDto],
                lens: LENS.INITIATIVE,
                threadId: 'thread1'
            };

            await expect(requestAiImprovement(params)).rejects.toThrow(ZodError);
        });

        it('should work with taskId instead of initiativeId', async () => {
            // Set up MSW handler for this test
            server.use(
                http.post('/api/ai-improvement', async ({ request }) => {
                    const body = await request.json();

                    // Verify request uses taskId
                    expect(body).toEqual({
                        initiative_id: undefined,
                        task_id: 'task-456',
                        input_data: testInitiativeDto
                    });

                    return HttpResponse.json(
                        {
                            job_id: '456def',
                            status: 'processing'
                        },
                        { status: 200 }
                    );
                })
            );

            const params: AiImprovementRequest = {
                taskId: 'task-456',
                inputData: [testInitiativeDto],
                lens: LENS.INITIATIVE,
                threadId: 'thread1'
            };

            const result = await requestAiImprovement(params);

            expect(result).toEqual({
                job_id: '456def',
                status: 'processing'
            });
        });
    });

    describe.skip('getAiImprovements', () => {
        it('should make a GET request to the correct endpoint with correct data', async () => {
            // TODO - write tests for getAiImprovements
            expect(true).toBe(false);
        });
    });

    describe.skip('deleteAiImprovementJob', () => {
        it('should delete', async () => {
            // TODO - write tests for deleteAiImprovementJob
            expect(true).toBe(false);
        });
    });
});
