import { describe, it, expect, vi, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { workspaceFromData, workspaceToPayloadJSON, getAllWorkspaces, postWorkspace } from './workspaces';
import { WorkspaceDto } from '#types';

const jwtBuilder = require('jwt-builder');

const mockWorkspace: WorkspaceDto = {
    id: '123',
    name: 'Test Workspace',
    description: 'Test Workspace Description',
    icon: 'folder',
};

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

// Setup MSW server
const server = setupServer(
    // Default handlers will be overridden in individual tests
    http.get('http://localhost:3000/workspace', () => {
        return HttpResponse.json([]);
    }),
    http.post('http://localhost:3000/workspace', () => {
        return HttpResponse.json([]);
    })
);

// Suppress console.error output during tests
const originalConsoleError = console.error;

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

describe.skip('workspace API functions', () => {
    describe.skip('workspaceFromData', () => {
        it('should convert raw data to WorkspaceDto', () => {
            const rawData = {
                id: '123',
                name: 'Test Workspace',
                icon: 'folder',
                description: 'Test Workspace Description',
                extraField: 'should be ignored'
            };

            const result = workspaceFromData(rawData);

            expect(result).toEqual({
                id: '123',
                name: 'Test Workspace',
                icon: 'folder',
                description: 'Test Workspace Description',
            });
        });
    });

    describe.skip('workspaceToPayloadJSON', () => {
        it('should convert WorkspaceDto to JSON payload', () => {
            const result = workspaceToPayloadJSON(mockWorkspace);

            expect(result).toEqual({
                id: '123',
                name: 'Test Workspace',
                icon: 'folder',
                description: 'Test Workspace Description',
            });
        });

        it('should handle partial workspace data', () => {
            const partialWorkspace: Partial<WorkspaceDto> = {
                name: 'Test Workspace'
            };

            const result = workspaceToPayloadJSON(partialWorkspace);

            expect(result).toEqual({
                id: undefined,
                name: 'Test Workspace',
                icon: undefined,
                description: undefined,
            });
        });
    });

    describe.skip('getAllWorkspaces', () => {
        it('should return parsed workspaces on successful API call', async () => {
            // Setup handler for this specific test
            server.use(
                http.get('http://localhost:3000/workspace', () => {
                    return HttpResponse.json([mockWorkspace]);
                })
            );

            const result = await getAllWorkspaces();

            expect(result).toEqual([mockWorkspace]);
        });

        it('should throw an error when API call fails', async () => {
            server.use(
                http.get('http://localhost:3000/workspace', () => {
                    return HttpResponse.text('Server error', { status: 500 });
                })
            );

            await expect(getAllWorkspaces()).rejects.toThrow('Error loading workspaces');
        });

        it('should throw an error when schema validation fails', async () => {
            server.use(
                http.get('http://localhost:3000/workspace', () => {
                    return HttpResponse.json([{ invalid: 'data' }]);
                })
            );

            await expect(getAllWorkspaces()).rejects.toThrow('Error loading workspaces');
        });
    });

    describe.skip('postWorkspace', () => {
        it('should successfully post a workspace and return the created workspace', async () => {
            let sentJson: any;

            server.use(
                http.post('http://localhost:3000/workspace', async ({ request }) => {
                    sentJson = await request.json();
                    return HttpResponse.json([mockWorkspace]);
                })
            );

            const result = await postWorkspace(mockWorkspace);
            expect(result).toEqual(mockWorkspace);
            expect(sentJson).toEqual({
                id: '123',
                name: 'Test Workspace',
                description: 'Test Workspace Description',
                icon: 'folder'
            });
        });

        it('should throw an error when API call fails', async () => {
            server.use(
                http.post('http://localhost:3000/workspace', () => {
                    return HttpResponse.json({
                        error: { message: 'Failed to create workspace' }
                    }, { status: 400 });
                })
            );

            await expect(postWorkspace(mockWorkspace)).rejects.toThrow('Failed to create workspace');
        });

        it('should throw an error when no workspace is returned', async () => {
            server.use(
                http.post('http://localhost:3000/workspace', () => {
                    return HttpResponse.json([]);
                })
            );

            await expect(postWorkspace(mockWorkspace)).rejects.toThrow('No workspace created');
        });
    });
});
