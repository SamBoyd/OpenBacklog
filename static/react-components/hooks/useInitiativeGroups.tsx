import React, { createContext, useContext, useMemo, ReactNode, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    GroupDto,
    InitiativeDto,
    InitiativeGroupDto,
    GroupType,
    FieldDefinitionDto,
    FieldType,
} from '#types';
import {
    getGroups,
    postGroup,
    deleteGroup as apiDeleteGroup,
    getGroupById as apiGetGroupById,
} from '#api/groups';

import {
    addInitiativeToGroup as apiAddInitiativeToGroup,
    removeInitiativeFromGroup as apiRemoveInitiativeFromGroup
} from '#api/initiatives';

// --- Context Definition ---

export interface UseInitiativeGroupsReturn {
    allGroupsInWorkspace: GroupDto[]; // All groups in the workspace with ordered initiatives
    loading: boolean;
    error: string | null;

    deleteGroup: (group: GroupDto) => Promise<void>;
    updateGroup: (group: GroupDto) => Promise<GroupDto>;

    refetchGroups: () => Promise<any>;

    createNewExplicitGroup: (
        groupDetails: Pick<GroupDto, 'name' | 'description'>,
        initiativesToLink?: InitiativeDto[]
    ) => Promise<GroupDto>;
    addInitiativeToExplicitGroup: (
        initiative: InitiativeDto,
        group: GroupDto | GroupDto
    ) => Promise<GroupDto>;
    removeInitiativeFromExplicitGroup: (
        initiative: InitiativeDto,
        group: GroupDto | GroupDto
    ) => Promise<GroupDto>;

    createNewSmartGroup: (group: GroupDto | GroupDto) => Promise<GroupDto>;
    updateSmartGroup: (group: GroupDto | GroupDto) => Promise<GroupDto>;

    findGroupsByIds: (ids: string[]) => GroupDto[];
}

interface InitiativeGroupsContextType extends UseInitiativeGroupsReturn {}

const InitiativeGroupsContext = createContext<InitiativeGroupsContextType | undefined>(undefined);

// --- Provider Component ---

export interface InitiativeGroupsProviderProps {
    children: ReactNode;
}

export const InitiativeGroupsProvider: React.FC<InitiativeGroupsProviderProps> = ({ 
    children, 
}) => {
    const queryClient = useQueryClient();

    const groupsQueryKey = ['groups', {}];
    const { data: allGroupsData, isLoading: allGroupsLoading, error: allGroupsError, refetch: refetchGroups } = useQuery<GroupDto[], Error>({
        queryKey: groupsQueryKey,
        queryFn: () => getGroups(),
        staleTime: 1000 * 60 * 5, // 5 minutes,
    });

    useEffect(() => {
        console.log('[useInitiativesGroups] allGroupsError', allGroupsError)
    }, [allGroupsError])

    useEffect(() => {
        console.log('[useInitiativesGroups] allGroupsInWorkflow', allGroupsData)
    }, [allGroupsData])

    // Mutations
    const postGroupMutation = useMutation<GroupDto, Error, { groupPayload: Partial<GroupDto>} >({
        mutationFn: ({ groupPayload }) => postGroup(groupPayload),
        onSuccess: (newOrUpdatedGroup) => {
            // Update the main groups list cache
            queryClient.setQueryData<GroupDto[]>(groupsQueryKey, (oldData) => {
                if (!oldData) return [newOrUpdatedGroup];
                const existingIndex = oldData.findIndex(group => group.id === newOrUpdatedGroup.id);
                if (existingIndex >= 0) {
                    // Update existing group
                    return oldData.map((group, index) => 
                        index === existingIndex ? newOrUpdatedGroup : group
                    );
                } else {
                    // Add new group
                    return [...oldData, newOrUpdatedGroup];
                }
            });
            
            // Update the individual group cache
            queryClient.setQueryData<GroupDto>(['groups', { groupId: newOrUpdatedGroup.id }], newOrUpdatedGroup);
        },
    });

    const deleteGroupMutation = useMutation<void, Error, GroupDto>({
        mutationFn: async (groupToDelete) => {
            await apiDeleteGroup(groupToDelete.id);
        },
        onSuccess: (_, groupDeleted) => { // first argument is void, second is the variable passed to mutateAsync
            // Remove the deleted group from the main groups list cache
            queryClient.setQueryData<GroupDto[]>(groupsQueryKey, (oldData) => {
                if (!oldData) return oldData;
                return oldData.filter(group => group.id !== groupDeleted.id);
            });
            
            // Remove the individual group cache
            queryClient.removeQueries({ queryKey: ['groups', { groupId: groupDeleted.id }] });
        },
    });

    const addInitiativeToGroupMutation = useMutation<
        GroupDto,
        Error,
        { initiative: InitiativeDto; group: GroupDto; afterId: string | null, beforeId: string | null}
    >({
        mutationFn: async ({ initiative, group, afterId, beforeId }) => {
            await apiAddInitiativeToGroup(initiative.id, group.id, afterId, beforeId);
            return apiGetGroupById(group.id); // Refetch the group to get updated initiative list
        },
        onSuccess: (updatedGroup, variables) => { // variables: { initiative, group, position? }
            // Update the main groups list cache with the updated group
            queryClient.setQueryData<GroupDto[]>(groupsQueryKey, (oldData) => {
                if (!oldData) return [updatedGroup];
                return oldData.map(group => 
                    group.id === updatedGroup.id ? updatedGroup : group
                );
            });
            
            // Update the individual group cache
            queryClient.setQueryData<GroupDto>(['groups', { groupId: updatedGroup.id }], updatedGroup);
        },
    });

    const removeInitiativeFromGroupMutation = useMutation<
        GroupDto,
        Error,
        { initiative: InitiativeDto; group: GroupDto }
    >({
        mutationFn: async ({ initiative, group }) => {
            await apiRemoveInitiativeFromGroup(initiative.id, group.id);

            return apiGetGroupById(group.id); // Refetch the group
        },
        onSuccess: (updatedGroup, variables) => { // variables: { initiative, group }
            // Update the main groups list cache with the updated group
            queryClient.setQueryData<GroupDto[]>(groupsQueryKey, (oldData) => {
                if (!oldData) return [updatedGroup];
                return oldData.map(group => 
                    group.id === updatedGroup.id ? updatedGroup : group
                );
            });
            
            // Update the individual group cache
            queryClient.setQueryData<GroupDto>(['groups', { groupId: updatedGroup.id }], updatedGroup);
        },
    });

    const createExplicitGroupWithInitiativesMutation = useMutation<
        GroupDto,
        Error,
        { groupDetails: Pick<GroupDto, 'name' | 'description'>; initiativesToLink?: InitiativeDto[] }
    >({
        mutationFn: async ({ groupDetails, initiativesToLink }) => {
            // First create the group
            const newGroup = await postGroupMutation.mutateAsync({
                groupPayload: {
                    ...groupDetails,
                    group_type: GroupType.EXPLICIT,
                }
            });
            
            // If there are initiatives to link, add them to the group
            if (initiativesToLink && initiativesToLink.length > 0) {
                await Promise.all(
                    initiativesToLink.map(initiative => 
                        apiAddInitiativeToGroup(initiative.id, newGroup.id, null, null)
                    )
                );
                // Return the group with linked initiatives
                return apiGetGroupById(newGroup.id);
            }
            
            return newGroup;
        },
        onSuccess: (newGroupWithInitiatives) => {
            // Update the main groups list cache
            queryClient.setQueryData<GroupDto[]>(groupsQueryKey, (oldData) => {
                if (!oldData) return [newGroupWithInitiatives];
                const existingIndex = oldData.findIndex(group => group.id === newGroupWithInitiatives.id);
                if (existingIndex >= 0) {
                    // Update existing group (shouldn't happen for create, but safety check)
                    return oldData.map((group, index) => 
                        index === existingIndex ? newGroupWithInitiatives : group
                    );
                } else {
                    // Add new group
                    return [...oldData, newGroupWithInitiatives];
                }
            });
            
            // Update the individual group cache
            queryClient.setQueryData<GroupDto>(['groups', { groupId: newGroupWithInitiatives.id }], newGroupWithInitiatives);
        },
    });

    const mutations = [
        postGroupMutation,
        deleteGroupMutation,
        addInitiativeToGroupMutation,
        removeInitiativeFromGroupMutation,
        createExplicitGroupWithInitiativesMutation,
    ];
    const isLoadingMutations = mutations.some(m => m.isPending);
    const mutationError = mutations.find(m => m.error)?.error;

    const contextValue = useMemo(() => ({
        allGroupsInWorkspace: allGroupsData || [],
        loading: allGroupsLoading || isLoadingMutations,
        error: mutationError?.message || null,
        deleteGroup: (group: GroupDto) => deleteGroupMutation.mutateAsync(group),
        updateGroup: async (group: GroupDto) => await postGroupMutation.mutateAsync({
            groupPayload: group,
        }),
        refetchGroups,

        createNewExplicitGroup: async (groupDetails: Pick<GroupDto, 'name' | 'description'>, initiativesToLink?: InitiativeDto[]) => {
            return await createExplicitGroupWithInitiativesMutation.mutateAsync({ groupDetails, initiativesToLink });
        },
        addInitiativeToExplicitGroup: async (initiative: InitiativeDto, group: GroupDto) => {
            return addInitiativeToGroupMutation.mutateAsync({ initiative, group, afterId: null, beforeId: null});
        },
        removeInitiativeFromExplicitGroup: async (initiative: InitiativeDto, group: GroupDto) => {
            return await removeInitiativeFromGroupMutation.mutateAsync({ initiative, group });
        },

        createNewSmartGroup: async (group: GroupDto) => {
            return await postGroupMutation.mutateAsync({
                groupPayload: { ...group, group_type: GroupType.SMART },
            });
        },

        updateSmartGroup: async (group: GroupDto) => {
            return await postGroupMutation.mutateAsync({
                groupPayload: { ...group, group_type: GroupType.SMART },
            });
        },

        findGroupsByIds: (ids: string[]) => {
            return allGroupsData?.filter(group => ids.includes(group.id)) ?? [];
        }
    }), [
        allGroupsData,
        allGroupsLoading,
        isLoadingMutations,
        refetchGroups,
        mutationError?.message,
        deleteGroupMutation,
        postGroupMutation,
        addInitiativeToGroupMutation,
        removeInitiativeFromGroupMutation,
        createExplicitGroupWithInitiativesMutation
    ]);

    return (
        <InitiativeGroupsContext.Provider value={contextValue}>
            {children}
        </InitiativeGroupsContext.Provider>
    );
};

// --- Consumer Hook ---

export const useInitiativeGroups = (): UseInitiativeGroupsReturn => {
    const context = useContext(InitiativeGroupsContext);
    if (context === undefined) {
        throw new Error('useInitiativeGroups must be used within an InitiativeGroupsProvider');
    }
    return context;
};

/**
 * Filters a list of initiatives based on smart group query criteria and keywords.
 * @param {InitiativeDto[]} initiatives - The list of initiatives to filter.
 * @param {Record<string, any>} queryCriteria - The query criteria, where keys are field keys or _keywords.
 * @param {FieldDefinitionDto[]} fieldDefinitions - All available field definitions for the entity type.
 * @returns {InitiativeDto[]} The filtered list of initiatives.
 */
export const applySmartGroupCriteria = (
    initiatives: InitiativeDto[],
    queryCriteria: Record<string, any> | null | undefined,
    fieldDefinitions: FieldDefinitionDto[]
): InitiativeDto[] => {
    if (!initiatives || initiatives.length === 0) {
        return [];
    }

    if (!queryCriteria || Object.keys(queryCriteria).length === 0) {
        return initiatives;
    }

    const keywords = queryCriteria._keywords || '';
    const criteria = { ...queryCriteria };
    delete criteria._keywords;

    const lowerCaseKeywords: string[] = keywords.trim().toLowerCase().split(' ').filter((k: string) => k);

    // If criteria exist but no field definitions are loaded (e.g., during initial load or error),
    // treat as no matches, as criteria cannot be interpreted.
    // Similarly, if keywords are present but there are no initiatives to filter, it's an empty result.
    if ((fieldDefinitions.length === 0 && Object.keys(criteria).length > 0)) {
        return [];
    }

    if (lowerCaseKeywords.length > 0 && initiatives.length === 0 && Object.keys(criteria).length === 0) {
        return [];
    }


    return initiatives.filter(initiative => {
        // Keyword Search (Title and Description)
        let matchesKeywords = true;
        if (lowerCaseKeywords.length > 0) {
            const titleMatch = lowerCaseKeywords.every((kw: string) => initiative.title?.toLowerCase().includes(kw));
            const descriptionMatch = lowerCaseKeywords.every((kw: string) => initiative.description?.toLowerCase().includes(kw));
            matchesKeywords = titleMatch || descriptionMatch;
        }
        if (!matchesKeywords) return false;

        // Existing Criteria Search
        if (Object.keys(criteria).length === 0) return true; // No criteria to check, keyword match is enough

        return Object.entries(criteria).every(([fieldKey, criterionValue]) => {
            // If criterionValue is empty, it doesn't restrict this initiative for this field.
            if (criterionValue === undefined || criterionValue === null || criterionValue === '' || (Array.isArray(criterionValue) && criterionValue.length === 0)) {
                return true;
            }

            const fieldDef = fieldDefinitions.find(fd => fd.key === fieldKey);
            // If field definition not found for a criterion key, this criterion cannot be evaluated.
            // Treat as non-match if a value is expected by the criterion.
            if (!fieldDef) return false;

            let initiativeValue: any;

            // Standard, directly accessible InitiativeDto properties
            if (fieldKey === 'status') {
                initiativeValue = initiative.status;
            } else if (fieldKey === 'type') {
                initiativeValue = initiative.type;
            } else if (fieldKey === 'title') {
                initiativeValue = initiative.title;
            } else if (fieldKey === 'identifier') {
                initiativeValue = initiative.identifier;
            } else if (initiative.properties && fieldDef.id && initiative.properties.hasOwnProperty(fieldDef.id)) {
                // Custom fields accessed by fieldDef.id
                initiativeValue = initiative.properties[fieldDef.id];
            } else {
                // Field not found on initiative (neither standard known nor in custom_fields)
                // Since criterionValue is not empty, this is a non-match.
                return false;
            }

            // If initiative has no value for the field, but criterion expects one.
            if (initiativeValue === undefined || initiativeValue === null) {
                return false;
            }

            // Comparison logic
            switch (fieldDef.field_type) {
                case FieldType.MULTI_SELECT:
                    const filterValues = (Array.isArray(criterionValue) ? criterionValue : [criterionValue]).map(v => String(v).toLowerCase());
                    const actualValues = (Array.isArray(initiativeValue) ? initiativeValue : [initiativeValue]).map(v => String(v).toLowerCase());
                    return filterValues.some(fv => actualValues.includes(fv));
                case FieldType.CHECKBOX:
                    const critBool = typeof criterionValue === 'string' ? criterionValue.toLowerCase() === 'true' : Boolean(criterionValue);
                    const initBool = typeof initiativeValue === 'string' ? initiativeValue.toLowerCase() === 'true' : Boolean(initiativeValue);
                    return initBool === critBool;
                default: // Includes TEXT, SELECT, STATUS, DATE, URL, EMAIL, PHONE, NUMBER
                    return String(initiativeValue).toLowerCase().includes(String(criterionValue).toLowerCase());
            }
        });
    });
};
