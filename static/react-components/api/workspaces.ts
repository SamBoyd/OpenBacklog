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
        let response: Partial<WorkspaceDto>[];

        try {
            const res = await getPostgrestClient()
                .from('workspace')
                .upsert(jsonPayload)
                .select();

            if (res.error) {
                console.error('Error posting workspace', res);
                throw new Error(res.error.message);
            }

            response = res.data as Partial<WorkspaceDto>[];
        } catch (error) {
            throw new Error('Failed to create workspace');
        }

        // Check that we have a response and that it's not an empty array
        if (!response || response.length === 0) {
            throw new Error('No workspace created');
        }

        return workspaceFromData(response[0]);
    });
}
