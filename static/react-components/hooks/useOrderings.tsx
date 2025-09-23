import { z } from "zod";
import { LexoRank } from "lexorank";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo } from "react";

import { ContextType, EntityType, OrderingDto } from "#types";


export type OrderedEntity<T> = T & { position: string; orderingId: string };

export interface useOrderingsReturn<T> {
    orderedEntities: OrderedEntity<T>[];
    isError: boolean;
}

export interface useOrderingsProps<T extends { id: string; orderings?: OrderingDto[] }> {
    contextType: ContextType;
    entityType: EntityType;
    contextId: string | null;
    entitiesToOrder: T[];
    orderDirection: 'asc' | 'desc';
}

export const useOrderings = <T extends { id: string; orderings?: OrderingDto[] }>({
    contextType,
    contextId,
    entityType,
    entitiesToOrder,
    orderDirection = 'asc',
}: useOrderingsProps<T>): useOrderingsReturn<T> => {

    // Extract orderings from embedded data in entities, preserving entity context
    const allOrderings = useMemo(() =>
        entitiesToOrder.flatMap(entity =>
            (entity.orderings || []).map(ordering => ({
                ...ordering,
                // Ensure the ordering knows which entity it belongs to
                parentEntityId: entity.id
            }))
        ),
        [entitiesToOrder]
    );

    // Filter orderings that match our current context
    const contextOrderings = useMemo(() =>
        allOrderings.filter(ordering =>
            ordering.contextType == contextType &&
            ordering.entityType == entityType &&
            ordering.contextId == contextId
        ),
        [allOrderings, contextType, entityType, contextId]
    );

    useEffect(() => {
        if (contextId === null) {
            console.log('[useOrderings] no contextType')
            return;
        }
        console.log('[useOrderings] contextType', contextType)
        console.log('[useOrderings] contextId', contextId)
        console.log('[useOrderings] entityType', entityType)
        console.log('[useOrderings] allOrderings', allOrderings)
        console.log('[useOrderings] contextOrderings', contextOrderings)
    }, [
        contextOrderings
    ]);

    // Create ordered entities from embedded orderings data
    const orderedEntities = useMemo<OrderedEntity<T>[]>(() => {
        if (entitiesToOrder.length === 0) {
            return [];
        }

        // If no orderings exist for this context, we'll need to create them
        if (contextOrderings.length === 0) {
            // Return entities in their natural order for now
            return entitiesToOrder.map(entity => ({
                ...entity,
                position: '',
                orderingId: ''
            }));
        }

        // Sort orderings by position
        const sortedOrderings = [...contextOrderings].sort((a, b) => {
            if (orderDirection === 'asc') {
                return LexoRank.parse(a.position).compareTo(LexoRank.parse(b.position));
            } else {
                return LexoRank.parse(b.position).compareTo(LexoRank.parse(a.position));
            }
        });

        // Map orderings to entities using the preserved parent context
        return sortedOrderings.map((ordering) => {
            // First try to find entity using the preserved parent context
            let entity = entitiesToOrder.find((e) => e.id === (ordering as any).parentEntityId);

            // Fallback to original logic if parentEntityId is not available
            if (!entity) {
                entity = entitiesToOrder.find((e) => e.id === ordering.initiativeId || e.id === ordering.taskId);
            }

            return { ...entity, position: ordering.position, orderingId: ordering.id };
        }).filter(entity => entity.id) as OrderedEntity<T>[];
    }, [entitiesToOrder, contextOrderings, orderDirection]);

    const isError = false;   // No API errors to handle

    return {
        orderedEntities,
        isError,
    };
}
