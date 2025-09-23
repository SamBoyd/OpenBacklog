import { z } from 'zod';
import { getAllWorkspaces, postWorkspace } from '#api/workspaces';
import { WorkspaceDto, WorkspaceDtoSchema } from '#types';
import { createDefaultFieldDefinitions } from '#hooks/useFieldDefinitions';

/**
 * Schema for validating workspace objects from the API
 */
export const WorkspaceCreationPayloadSchema = z.object({
    id: z.string(),
    name: z.string(),
    icon: z.string().nullable()
});

/**
 * Type definition for a workspace
 */
export type WorkspaceCreationPayload = {
    name: string;
    icon: string | null;
    description: string | null;
}

/**
 * Schema for validating an array of workspaces from the API
 */
export const WorkspacesResponseSchema = z.array(WorkspaceDtoSchema);

/**
 * Cookie name for storing the current workspace ID
 */
const CURRENT_WORKSPACE_COOKIE = 'current_workspace';

/**
 * Creates a new workspace
 * @param {WorkspaceCreationPayload} workspace - The workspace to create
 * @returns {Promise<WorkspaceDto>} Promise resolving to the created workspace
 */
export const createWorkspace = async (workspace: WorkspaceCreationPayload): Promise<WorkspaceDto> => {
    try {
        const created_workspace = await postWorkspace(workspace);
        await setCurrentWorkspace(created_workspace)
        await createDefaultFieldDefinitions()
        return created_workspace
    } catch (error) {
        console.error('Failed to create workspace:', error);
        throw new Error(`Failed to create workspace: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
};

/**
 * Updates the current workspace selection by storing it in a cookie
 * @param {WorkspaceDto} workspace - The workspace to set as current
 * @returns {Promise<void>} Promise resolving when the operation is complete
 */
export const setCurrentWorkspace = async (workspace: WorkspaceDto): Promise<void> => {
    try {
        // Set cookie with 30 day expiration
        const expiryDate = new Date();
        expiryDate.setDate(expiryDate.getDate() + 30);
        document.cookie = `${CURRENT_WORKSPACE_COOKIE}=${JSON.stringify(workspace)}; expires=${expiryDate.toUTCString()}; path=/; SameSite=Lax`;
        return Promise.resolve();
    } catch (error) {
        console.error('Failed to set current workspace:', error);
        throw new Error(`Failed to set current workspace: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
};

/**
 * Gets the current workspace ID from cookies
 * @returns {string|null} The current workspace ID or null if not set
 */
export const getCurrentWorkspaceFromCookie = (): WorkspaceDto | null => {
    const cookies = document.cookie.split(';');
    for (const cookie of cookies) {
        const name = cookie.trim().split('=')[0].trim();
        if (name === CURRENT_WORKSPACE_COOKIE) {
            try {
                return JSON.parse(cookie.split('=')[1].trim()) as WorkspaceDto;
            } catch (error) {
                return null;
            }
        }
    }
    return null;
};

/**
 * Fetches the current workspace for the user
 * @returns {Promise<WorkspaceDto>} Promise resolving to current workspace
 */
export const fetchCurrentWorkspace = async (): Promise<WorkspaceDto> => {
    try {
        const cookieWorkspace = getCurrentWorkspaceFromCookie();

        if (cookieWorkspace && cookieWorkspace.id) {
            return cookieWorkspace;
        }

        const workspaces: WorkspaceDto[] = await getAllWorkspaces();

        if (!workspaces || workspaces.length === 0) {
            throw new Error('No workspaces available');
        }

        await setCurrentWorkspace(workspaces[0]);
        // Default to the first workspace if no cookie or workspace not found
        return workspaces[0];
    } catch (error) {
        console.error('Failed to fetch current workspace:', error);
        throw new Error(`Failed to fetch current workspace: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
};

