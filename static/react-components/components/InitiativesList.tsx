import React from 'react';
import { useNavigate } from 'react-router';

import { useInitiativesContext } from '#contexts/InitiativesContext';
import { InitiativeDto, InitiativeStatus, TaskStatus } from '#types';
import { OrderedEntity } from '#hooks/useOrderings';

import InitiativesListView from './InitiativesListView';

interface InitiativesListViewProps {
    selectedStatuses?: InitiativeStatus[];
    moveToStatus?: (initiativeId: string) => (status: InitiativeStatus) => (event: React.MouseEvent<HTMLDivElement>) => void;
}

export default function InitiativesList({ selectedStatuses = Object.values(InitiativeStatus), moveToStatus }: InitiativesListViewProps) {
    const { initiativesData, shouldShowSkeleton, isQueryFetching, error, reorderInitiative, moveInitiativeToStatus } = useInitiativesContext();
    const navigate = useNavigate();

    const loading = shouldShowSkeleton || isQueryFetching;

    const handleCardClick = (initiativeId: string) => {
        if (loading || error) return;
        const initiative = initiativesData?.find(i => i.id === initiativeId);
        if (!initiative) return;

        navigate(`/workspace/initiatives/${initiativeId}`);
    };

    const handleOrderChange = async (updatedEntity: OrderedEntity<InitiativeDto>, afterId: string | null, beforeId: string | null) => {
        await reorderInitiative(updatedEntity.id, afterId, beforeId);
    }

    const handleStatusChange = async (updatedEntity: OrderedEntity<InitiativeDto>, newStatus: InitiativeStatus | TaskStatus, afterId: string | null, beforeId: string | null) => {
        await moveInitiativeToStatus(updatedEntity.id, newStatus as InitiativeStatus, afterId, beforeId);
    };

    return (
        <InitiativesListView
            initiatives={initiativesData}
            loading={shouldShowSkeleton}
            error={error}
            selectedStatuses={selectedStatuses}
            onInitiativeClick={handleCardClick}
            onOrderChange={handleOrderChange}
            onStatusChange={handleStatusChange}
            moveToStatus={moveToStatus}
        />
    );
}
