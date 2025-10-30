import { WorkspaceDto, WorkspaceDtoSchema } from '#types';
import { getPostgrestClient, withApiCall } from './api-utils';

export function workspaceFromData(data: any): WorkspaceDto {
    return {
        id: data.id,
        name: data.name,
        icon: data.icon,
        description: data.description,
    };
}

export function workspaceToPayloadJSON(data: Partial<WorkspaceDto>): any {
    return {
        id: data.id,
        name: data.name,
        icon: data.icon,
        description: data.description,
    };
}

export async function getAllWorkspaces(): Promise<WorkspaceDto[]> {
    return withApiCall(async () => {
        const response = await getPostgrestClient()
            .from('workspace')
            .select('*');

        if (response.error) {
            console.error('Error loading workspaces', response.error);
            throw new Error('Error loading workspaces');
        }

        const parsedData = WorkspaceDtoSchema.array().safeParse(response.data);
        if (!parsedData.success) {
            console.error(
                'Error loading workspaces - data format',
                parsedData.error,
            );
            throw new Error('Error loading workspaces');
        }

        return parsedData.data.map(workspace => workspaceFromData(workspace));
    });
}

export async function postWorkspace(workspace: Partial<WorkspaceDto>): Promise<WorkspaceDto> {
    return withApiCall(async () => {
        const jsonPayload = workspaceToPayloadJSON(workspace);

        try {
            // Use FastAPI endpoint instead of PostgREST
            // This ensures the SQLAlchemy event listener creates required dependencies
            const response = await fetch('/api/workspaces', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: jsonPayload.name,
                    description: jsonPayload.description,
                    icon: jsonPayload.icon,
                }),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
                console.error('Error creating workspace', errorData);
                throw new Error(errorData.detail || 'Failed to create workspace');
            }

            const data = await response.json();

            // Validate response data
            const parsedData = WorkspaceDtoSchema.safeParse(data);
            if (!parsedData.success) {
                console.error('Error parsing workspace response', parsedData.error);
                throw new Error('Invalid workspace data returned');
            }

            return workspaceFromData(parsedData.data);
        } catch (error) {
            console.error('Failed to create workspace', error);
            throw error;
        }
    });
}
