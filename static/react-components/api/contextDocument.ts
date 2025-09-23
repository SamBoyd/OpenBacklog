import { getPostgrestClient, withApiCall } from './api-utils';
import { ContextDocumentDto, ContextDocumentDtoSchema } from '#types';
import { fetchCurrentWorkspace } from '#services/workspaceApi';

export const getContextDocument = async (): Promise<ContextDocumentDto> => {
    const currentWorkspace = await fetchCurrentWorkspace();

    return withApiCall(async () => {
        const client = getPostgrestClient();
        const { data, error } = await client
            .from('context_document')
            .select('*')
            .eq('workspace_id', currentWorkspace.id)
            .single();

        if (error) {
            console.error('[getContextDocument] error', error);
            throw new Error(error.message);
        }

        return ContextDocumentDtoSchema.parse(data);
    });
}

export const updateContextDocument = async (contextDocument: ContextDocumentDto): Promise<ContextDocumentDto> => {
     // Get the current workspace
     const currentWorkspace = await fetchCurrentWorkspace();

     const jsonPayload = {
         ...contextDocument,
         workspace_id: currentWorkspace.id
     };

    return withApiCall(async () => {
        const client = getPostgrestClient();
        const { data, error } = await client
            .from('context_document')
            .upsert(jsonPayload)
            .select('*')
            .single();

        if (error) {
            console.error('[updateContextDocument] error', error);
            throw new Error(error.message);
        }

        return ContextDocumentDtoSchema.parse(data);
    });
}
