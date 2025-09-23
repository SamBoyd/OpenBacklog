import { OrderingDto } from "#types";

export function orderingsToPayloadJSON(data: Partial<OrderingDto> & { task_id?: string; initiative_id?: string }): any {
    return {
        id: data.id,
        context_type: data.contextType,
        context_id: data.contextId,
        entity_type: data.entityType,
        position: data.position,
        task_id: data.task_id,
        initiative_id: data.initiative_id,
    };
}

export function orderingsFromData(data: any): OrderingDto[] {
    return data.map((ordering: any) => {
        return {
            ...ordering,
            contextType: ordering.context_type,
            contextId: ordering.context_id,
            context_id: undefined,
            entityType: ordering.entity_type,
            entity_type: undefined,
            initiativeId: ordering.initiative_id,
            initiative_id: undefined,
            taskId: ordering.task_id,
            task_id: undefined,
            position: ordering.position,
        };
    });
}
