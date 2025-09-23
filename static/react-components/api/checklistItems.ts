import { ChecklistItemDto } from '#types';
import { getPostgrestClient, withApiCall } from './api-utils';

export function checklistItemFromData(data: any): ChecklistItemDto {
    return {
        id: data.id,
        title: data.title,
        order: data.order,
        task_id: data.task_id,
        is_complete: data.is_complete,
    };
}

export function checklistItemToPayloadJSON(data: Partial<ChecklistItemDto>): any {
    return {
        id: data.id,
        title: data.title,
        order: data.order,
        task_id: data.task_id,
        is_complete: data.is_complete,
    };
}

export async function postChecklistItem(checklistItem: Partial<ChecklistItemDto>): Promise<ChecklistItemDto> {
    const jsonPayload = checklistItemToPayloadJSON(checklistItem);

    return withApiCall(async () => {
        const response = await getPostgrestClient().from('checklist').upsert(jsonPayload).select().then(response => {
            if (response.error) {
                console.error('Error posting checklist item', response);
                throw new Error(response.error.message);
            }

            return response.data as Partial<ChecklistItemDto>[];
        });

        if (!response || response.length === 0) {
            throw new Error('No checklist item created');
        }

        return checklistItemFromData(response[0]);
    })
}

export async function deleteChecklistItem(checklistItemId: string): Promise<void> {
    return withApiCall(async () => {
        const { error } = await getPostgrestClient()
            .from('checklist')
            .delete()
            .eq('id', checklistItemId);

        if (error) {
            console.error('Error deleting checklist item', error);
            throw new Error('Error deleting checklist item');
        }
    })
}
