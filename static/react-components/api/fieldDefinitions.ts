import {
    FieldDefinitionDto,
    FieldDefinitionDtoSchema,
    EntityType,
} from '#types';
import { fetchCurrentWorkspace } from '#services/workspaceApi';
import { getPostgrestClient, withApiCall } from './api-utils';

export function fieldDefinitionFromData(data: any): FieldDefinitionDto {
    const response: Partial<FieldDefinitionDto> = {
        id: data.id,
        workspace_id: data.workspace_id,
        entity_type: data.entity_type,
        key: data.key,
        name: data.name,
        field_type: data.field_type,
        is_core: data.is_core,
        column_name: data.column_name,
        config: data.config,
        created_at: data.created_at,
        updated_at: data.updated_at,
        initiative_id: data.initiative_id,
        task_id: data.task_id,
    };

    return response as FieldDefinitionDto;
}

export function fieldDefinitionToPayloadJSON(data: Partial<FieldDefinitionDto>): any {
    return {
        id: data.id,
        workspace_id: data.workspace_id,
        entity_type: data.entity_type,
        key: data.key,
        name: data.name,
        field_type: data.field_type,
        is_core: data.is_core,
        column_name: data.column_name,
        config: data.config,
        initiative_id: data.initiative_id,
        task_id: data.task_id,
    };
}

export async function getFieldDefinitionById(id: string): Promise<FieldDefinitionDto> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        return await getPostgrestClient()
            .from('field_definition')
            .select('*')
            .eq('workspace_id', currentWorkspace.id)
            .eq('id', id)
            .maybeSingle()
            .then((response) => {
                if (response.error) {
                    console.error(
                        'Error loading field definition',
                        response.error,
                    );
                    throw new Error('Error loading field definition');
                }

                if (!response.data) {
                    throw new Error('Field definition not found');
                }

                const parsedData = FieldDefinitionDtoSchema.safeParse(
                    response.data,
                );
                if (!parsedData.success) {
                    console.error(
                        'Error loading field definition - data format',
                        parsedData.error,
                    );
                    throw new Error(
                        `Error loading field definition: Invalid format: ${parsedData.error}`,
                    );
                }

                return fieldDefinitionFromData(parsedData.data);
            });
    });
}

export async function postFieldDefinition(
    fieldDefinition: Partial<FieldDefinitionDto>,
): Promise<FieldDefinitionDto> {
    const currentWorkspace = await fetchCurrentWorkspace();

    const jsonPayload = {
        ...fieldDefinitionToPayloadJSON(fieldDefinition),
        workspace_id: currentWorkspace.id,
    };

    return withApiCall(async () => {
        const response = await getPostgrestClient()
            .from('field_definition')
            .upsert(jsonPayload)
            .select()
            .single();

        if (response.error) {
            console.error('Error posting field definition', response.error);
            throw new Error(response.error.message);
        }

        if (!response.data) {
            throw new Error('No field definition created or updated');
        }

        return fieldDefinitionFromData(response.data);
    });
}

export async function deleteFieldDefinition(id: string): Promise<void> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        const { error } = await getPostgrestClient()
            .from('field_definition')
            .delete()
            .eq('id', id)
            .eq('workspace_id', currentWorkspace.id);

        if (error) {
            console.error('Error deleting field definition', error);
            throw new Error(error.message);
        }
    });
}

export async function getFieldDefinitionsForWorkspace(): Promise<FieldDefinitionDto[]> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        const response = await getPostgrestClient()
            .from('field_definition')
            .select('*')
            .eq('workspace_id', currentWorkspace.id);

        if (response.error) {
            console.error('Error loading field definitions for workspace', response.error);
            throw new Error('Error loading field definitions for workspace');
        }

        return response.data.map((data) => fieldDefinitionFromData(data));
    })
}

export async function getFieldDefinitionsForInitiative(initiativeId: string): Promise<FieldDefinitionDto[]> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        const response = await getPostgrestClient()
            .from('field_definition')
            .select('*')
            .eq('workspace_id', currentWorkspace.id)
            .eq('entity_type', EntityType.INITIATIVE)
            .or(`initiative_id.eq.${initiativeId},initiative_id.is.null`)
            .then((response) => {
                if (response.error) {
                    console.error(
                        'Error loading field definitions for initiative',
                        response.error,
                    );
                    throw new Error('Error loading field definitions for initiative');
                }

                if (!response.data) {
                    return [];
                }

                return response.data.map((data) => fieldDefinitionFromData(data));
            });

        return response;
    });
}

export async function getFieldDefinitionsForTask(taskId: string): Promise<FieldDefinitionDto[]> {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        const response = await getPostgrestClient()
            .from('field_definition')
            .select('*')
            .eq('workspace_id', currentWorkspace.id)
            .eq('entity_type', EntityType.TASK)
            .or(`task_id.eq.${taskId},task_id.is.null`)
            .then((response) => {
                if (response.error) {
                    console.error(
                        'Error loading field definitions for task',
                        response.error,
                    );
                    throw new Error('Error loading field definitions for task');
                }

                if (!response.data) {
                    return [];
                }

                return response.data.map((data) => fieldDefinitionFromData(data));
            });

        return response;
    });
}