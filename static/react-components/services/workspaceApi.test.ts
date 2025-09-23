import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as workspaceApi from './workspaceApi';
import { getAllWorkspaces, postWorkspace } from '#api/workspaces';
import { createDefaultFieldDefinitions } from '#hooks/useFieldDefinitions';
import { WorkspaceDto } from '#types';

// Mock the api module
vi.mock('#api/workspaces', () => ({
    getAllWorkspaces: vi.fn(),
    postWorkspace: vi.fn(),
    workspaceFromData: vi.fn((data) => data),
}));

// Mock the useFieldDefinitions hook
vi.mock('#hooks/useFieldDefinitions', () => ({
    createDefaultFieldDefinitions: vi.fn(),
}));

// We'll mock specific functions individually in each test as needed

describe('workspaceApi', () => {
    // Mock document.cookie
    let originalCookie: PropertyDescriptor | undefined;

    beforeEach(() => {
        // Save original document.cookie property descriptor
        originalCookie = Object.getOwnPropertyDescriptor(document, 'cookie');

        // Mock document.cookie
        let cookies: string = '';
        Object.defineProperty(document, 'cookie', {
            get: () => cookies,
            set: (value: string) => {
                cookies = `${cookies}${cookies ? '; ' : ''}${value}`;
            },
            configurable: true
        });
    });

    afterEach(() => {
        // Restore original document.cookie
        if (originalCookie) {
            Object.defineProperty(document, 'cookie', originalCookie);
        }

        // Clear all mocks
        vi.clearAllMocks();
        vi.restoreAllMocks();
    });

    describe('createWorkspace', () => {
        it('should create a workspace via API and return it', async () => {
            // Arrange
            const newWorkspace: workspaceApi.WorkspaceCreationPayload = {
                name: 'New Workspace',
                icon: 'new-icon',
                description: 'Test description'
            };
            const createdWorkspace: WorkspaceDto = {
                id: '3',
                name: 'New Workspace',
                icon: 'new-icon',
                description: 'Test description',
            };

            // Mock API call
            vi.mocked(postWorkspace).mockResolvedValue(createdWorkspace);

            // Act
            const result = await workspaceApi.createWorkspace(newWorkspace);

            // Assert
            expect(postWorkspace).toHaveBeenCalledTimes(1);
            expect(postWorkspace).toHaveBeenCalledWith({
                name: 'New Workspace',
                icon: 'new-icon',
                description: 'Test description',
            });
            expect(result).toEqual(createdWorkspace);
        });

        it('should create a workspace with null values', async () => {
            // Arrange
            const newWorkspace: workspaceApi.WorkspaceCreationPayload = {
                name: 'Minimal Workspace',
                icon: null,
                description: null
            };
            const createdWorkspace: WorkspaceDto = {
                id: '4',
                name: 'Minimal Workspace',
                icon: null,
                description: null,
            };

            // Mock API call
            vi.mocked(postWorkspace).mockResolvedValue(createdWorkspace);

            // Act
            const result = await workspaceApi.createWorkspace(newWorkspace);

            // Assert
            expect(postWorkspace).toHaveBeenCalledWith(newWorkspace);
            expect(result).toEqual(createdWorkspace);
        });

        it('should handle API errors when creating a workspace', async () => {
            // Arrange
            const newWorkspace: workspaceApi.WorkspaceCreationPayload = {
                name: 'New Workspace',
                icon: 'new-icon',
                description: null
            };
            const errorMessage = 'API error';

            // Mock dependencies
            const setCurrentWorkspaceSpy = vi.spyOn(workspaceApi, 'setCurrentWorkspace');
            vi.mocked(postWorkspace).mockRejectedValue(new Error(errorMessage));
            vi.mocked(createDefaultFieldDefinitions);

            // Act & Assert
            await expect(workspaceApi.createWorkspace(newWorkspace)).rejects.toThrow(`Failed to create workspace: ${errorMessage}`);
            expect(postWorkspace).toHaveBeenCalledTimes(1);
            expect(postWorkspace).toHaveBeenCalledWith(newWorkspace);
            expect(setCurrentWorkspaceSpy).not.toHaveBeenCalled();
            expect(createDefaultFieldDefinitions).not.toHaveBeenCalled();
        });

        it('should verify that createDefaultFieldDefinitions is called during workspace creation', async () => {
            // Arrange
            const newWorkspace: workspaceApi.WorkspaceCreationPayload = {
                name: 'Field Test Workspace',
                icon: 'field-icon',
                description: null
            };
            const createdWorkspace: WorkspaceDto = {
                id: '5',
                name: 'Field Test Workspace',
                icon: 'field-icon',
                description: null,
            };

            // Mock dependencies
            vi.mocked(postWorkspace).mockResolvedValue(createdWorkspace);
            vi.mocked(createDefaultFieldDefinitions).mockResolvedValue(undefined);

            // Act
            const result = await workspaceApi.createWorkspace(newWorkspace);

            // Assert - verify the side effect is called
            expect(postWorkspace).toHaveBeenCalledTimes(1);
            expect(createDefaultFieldDefinitions).toHaveBeenCalledTimes(1);
            expect(result).toEqual(createdWorkspace);
        });
    });

    describe('setCurrentWorkspace', () => {
        it('should set a cookie with the workspace', async () => {
            // Arrange
            const workspace = {
                id: '123',
                name: 'Test Workspace',
                icon: 'test-icon',
                description: null
            };

            // Act
            await workspaceApi.setCurrentWorkspace(workspace);

            // Assert
            expect(document.cookie).toContain(`current_workspace=${JSON.stringify(workspace)}`);
            expect(document.cookie).toContain('SameSite=Lax');
            expect(document.cookie).toContain('path=/');
            expect(document.cookie).toContain('expires=');
        });

        it('should handle errors when setting the cookie', async () => {
            // Arrange
            const workspace = {
                id: '123',
                name: 'Test Workspace',
                icon: 'test-icon',
                description: null
            };

            // Mock document.cookie to throw an error
            Object.defineProperty(document, 'cookie', {
                set: () => {
                    throw new Error('Cookie error');
                },
                get: () => '',
                configurable: true
            });

            // Act & Assert
            await expect(workspaceApi.setCurrentWorkspace(workspace)).rejects.toThrow('Failed to set current workspace: Cookie error');
        });
    });

    describe('getCurrentWorkspaceFromCookie', () => {
        it('should return the workspace from cookie when valid', () => {
            // Arrange
            const workspace: WorkspaceDto = {
                id: '123',
                name: 'Test Workspace',
                icon: 'test-icon',
                description: 'Test description'
            };
            document.cookie = `current_workspace=${JSON.stringify(workspace)}`;

            // Act
            const result = workspaceApi.getCurrentWorkspaceFromCookie();

            // Assert
            expect(result).toEqual(workspace);
        });

        it('should return null when no cookie exists', () => {
            // Arrange - ensure no cookie is set
            document.cookie = '';

            // Act
            const result = workspaceApi.getCurrentWorkspaceFromCookie();

            // Assert
            expect(result).toBeNull();
        });

        it('should return null when cookie contains invalid JSON', () => {
            // Arrange
            document.cookie = 'current_workspace=invalid-json';

            // Act
            const result = workspaceApi.getCurrentWorkspaceFromCookie();

            // Assert
            expect(result).toBeNull();
        });

        it('should return the correct workspace when multiple cookies exist', () => {
            // Arrange
            const workspace: WorkspaceDto = {
                id: '456',
                name: 'Multi Cookie Workspace',
                icon: 'multi-icon',
                description: null
            };
            document.cookie = 'other_cookie=value';
            document.cookie = `current_workspace=${JSON.stringify(workspace)}`;
            document.cookie = 'another_cookie=another_value';

            // Act
            const result = workspaceApi.getCurrentWorkspaceFromCookie();

            // Assert
            expect(result).toEqual(workspace);
        });

        it('should handle cookie with spaces around the name and value', () => {
            // Arrange
            const workspace: WorkspaceDto = {
                id: '789',
                name: 'Spaced Workspace',
                icon: null,
                description: 'With spaces'
            };
            document.cookie = ` current_workspace = ${JSON.stringify(workspace)} `;

            // Act
            const result = workspaceApi.getCurrentWorkspaceFromCookie();

            // Assert
            expect(result).toEqual(workspace);
        });

        it('should return null when current_workspace cookie is empty', () => {
            // Arrange
            document.cookie = 'current_workspace=';

            // Act
            const result = workspaceApi.getCurrentWorkspaceFromCookie();

            // Assert
            expect(result).toBeNull();
        });
    });

    describe('fetchCurrentWorkspace', () => {
        it('should return the workspace from the cookie if it exists', async () => {
            // Arrange
            const cookieWorkspace: WorkspaceDto = {
                id: '2', name: 'Workspace 2', icon: 'icon2',
                description: null
            };

            // Set up cookie to return the workspace
            document.cookie = `current_workspace=${JSON.stringify(cookieWorkspace)}`;

            // Act
            const result = await workspaceApi.fetchCurrentWorkspace();

            // Assert
            expect(getAllWorkspaces).not.toHaveBeenCalled(); // Should not call API if cookie exists
            expect(result).toEqual(cookieWorkspace);
        });

        it('should return the first workspace if no cookie exists', async () => {
            // Arrange
            const workspaces: WorkspaceDto[] = [
                {
                    id: '1', name: 'Workspace 1', icon: 'icon1',
                    description: null
                },
                {
                    id: '2', name: 'Workspace 2', icon: 'icon2',
                    description: null
                }
            ];

            // Ensure no cookie exists
            document.cookie = '';
            vi.mocked(getAllWorkspaces).mockResolvedValue(workspaces);

            // Act
            const result = await workspaceApi.fetchCurrentWorkspace();

            // Assert
            expect(getAllWorkspaces).toHaveBeenCalledTimes(1);
            expect(result).toEqual(workspaces[0]);
            // Verify cookie is set after fetching first workspace
            expect(document.cookie).toContain(`current_workspace=${JSON.stringify(workspaces[0])}`);
        });

        it('should return the first workspace if the workspace in the cookie has no id', async () => {
            // Arrange
            const workspaces: WorkspaceDto[] = [
                {
                    id: '1', name: 'Workspace 1', icon: 'icon1',
                    description: null
                },
                {
                    id: '2', name: 'Workspace 2', icon: 'icon2',
                    description: null
                }
            ];

            const invalidCookieWorkspace = { id: '', name: 'Invalid', icon: null, description: null } as WorkspaceDto;

            // Set up invalid cookie
            document.cookie = `current_workspace=${JSON.stringify(invalidCookieWorkspace)}`;
            vi.mocked(getAllWorkspaces).mockResolvedValue(workspaces);

            // Act
            const result = await workspaceApi.fetchCurrentWorkspace();

            // Assert
            expect(getAllWorkspaces).toHaveBeenCalledTimes(1);
            expect(result).toEqual(workspaces[0]);
            // Verify cookie is updated with valid first workspace
            expect(document.cookie).toContain(`current_workspace=${JSON.stringify(workspaces[0])}`);
        });

        it('should throw an error if no workspaces are available', async () => {
            // Arrange
            document.cookie = ''; // No cookie exists
            vi.mocked(getAllWorkspaces).mockResolvedValue([]);

            // Act & Assert
            await expect(workspaceApi.fetchCurrentWorkspace()).rejects.toThrow('No workspaces available');
            expect(getAllWorkspaces).toHaveBeenCalledTimes(1);
        });

        it('should handle API errors', async () => {
            // Arrange
            const errorMessage = 'API error';
            document.cookie = ''; // No cookie exists
            vi.mocked(getAllWorkspaces).mockRejectedValue(new Error(`Failed to fetch workspaces: ${errorMessage}`));

            // Act & Assert
            await expect(workspaceApi.fetchCurrentWorkspace()).rejects.toThrow(`Failed to fetch current workspace: Failed to fetch workspaces: ${errorMessage}`);
            expect(getAllWorkspaces).toHaveBeenCalledTimes(1);
        });
    });
});