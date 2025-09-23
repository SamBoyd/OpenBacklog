import React, { useState } from 'react';
import { CreateFieldDefinitionDto, FieldDefinitionDto } from '#types';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    getFieldDefinitionsForInitiative,
    getFieldDefinitionsForTask,
    postFieldDefinition,
    deleteFieldDefinition as apiDeleteFieldDefinition,
    getFieldDefinitionsForWorkspace
} from '#api/fieldDefinitions';
import { initiativeStatusFieldDefinition, initiativeTypeFieldDefinition, taskStatusFieldDefinition, taskTypeFieldDefinition } from '#constants/coreFieldDefinitions';

export interface UseFieldDefinitionsProps {
    initiativeId?: string;
    taskId?: string;
}

export interface UseFieldDefinitionsReturn {
    fieldDefinitions: FieldDefinitionDto[];
    loading: boolean;
    error: string | null;
    createFieldDefinition: (fieldDefinition: CreateFieldDefinitionDto) => Promise<FieldDefinitionDto>;
    updateFieldDefinition: (fieldDefinition: FieldDefinitionDto) => Promise<FieldDefinitionDto>;
    deleteFieldDefinition: (fieldDefinitionId: string) => Promise<void>;
    invalidateQuery: () => void;
}

export const useFieldDefinitions = (props: UseFieldDefinitionsProps): UseFieldDefinitionsReturn => {
    const { initiativeId, taskId } = props;
    const queryClient = useQueryClient();

    // Determine query keys based on the provided props
    let queryKey: string[] = ['fieldDefinitions'];
    if (initiativeId) {
        queryKey.push('initiative', initiativeId);
    } else if (taskId) {
        queryKey.push('task', taskId);
    }

    // Data fetching query
    const { data, isLoading, error } = useQuery({
        queryKey,
        queryFn: async (): Promise<FieldDefinitionDto[]> => {
            if (initiativeId) {
                return getFieldDefinitionsForInitiative(initiativeId);
            } else if (taskId) {
                return getFieldDefinitionsForTask(taskId);
            }
            return getFieldDefinitionsForWorkspace();
        },
        enabled: true,
    });

    // Create/Update field definition mutation
    const { mutateAsync: mutateFieldDefinition } = useMutation({
        mutationFn: postFieldDefinition,
        onSuccess: (newFieldDefinition) => {
            // Update the query cache with the new data
            queryClient.setQueryData(queryKey, (oldData: FieldDefinitionDto[] = []) => {
                // Find and replace if exists, otherwise add
                const exists = oldData.some(item => item.id === newFieldDefinition.id);
                if (exists) {
                    return oldData.map(item =>
                        item.id === newFieldDefinition.id ? newFieldDefinition : item
                    );
                }
                return [...oldData, newFieldDefinition];
            });
            // Also invalidate to ensure consistency
            queryClient.invalidateQueries({ queryKey });
        },
    });

    // Delete field definition mutation
    const { mutateAsync: mutateDeleteFieldDefinition } = useMutation({
        mutationFn: apiDeleteFieldDefinition,
        onSuccess: () => {
            // Invalidate relevant queries to refresh data
            queryClient.invalidateQueries({ queryKey });
        },
    });

    // invalidate the query when the component is mounted
    const invalidateQuery = () => {
        queryClient.invalidateQueries({ queryKey });
    }

    return {
        fieldDefinitions: data || [],
        loading: isLoading,
        error: error ? (error as Error).message : null,
        createFieldDefinition: mutateFieldDefinition,
        updateFieldDefinition: mutateFieldDefinition,
        deleteFieldDefinition: mutateDeleteFieldDefinition,
        invalidateQuery,
    };
}


const defaultFieldDefinitions: Partial<FieldDefinitionDto>[] = [
    initiativeStatusFieldDefinition,
    initiativeTypeFieldDefinition,
    taskStatusFieldDefinition,
    taskTypeFieldDefinition
]

export const createDefaultFieldDefinitions = async () => {
    Promise.all(defaultFieldDefinitions.map(async (fieldDefinition) => {
        await postFieldDefinition(fieldDefinition);
    }));
}
