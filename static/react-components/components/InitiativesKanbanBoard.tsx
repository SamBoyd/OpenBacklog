import React, { useEffect } from 'react';
import { useNavigate } from 'react-router';
import { LexoRank } from 'lexorank';

import { useInitiativesContext } from '#contexts/InitiativesContext';
import { InitiativeDto, InitiativeStatus, TaskStatus } from '#types';
import KanbanBoardView from './reusable/KanbanBoardView';

import { OrderedEntity } from '#hooks/useOrderings';
import { computeOrderingIds } from '#utils/dragDropUtils';


interface InitiativesKanbanBoardProps {
    reloadCounter?: number;
    selectedStatuses?: InitiativeStatus[];
    data?: OrderedEntity<InitiativeDto>[] | null;
}

const InitiativesKanbanBoard: React.FC<InitiativesKanbanBoardProps> = ({
    reloadCounter,
    selectedStatuses = Object.values(InitiativeStatus),
    data: dataProp,
}) => {
    const contextData = useInitiativesContext();
    const navigate = useNavigate();

    // Use prop data if provided, otherwise use context data
    const initiativesData = dataProp ?? contextData.initiativesData;
    const shouldShowSkeleton = dataProp !== undefined ? false : contextData.shouldShowSkeleton;
    const error = dataProp !== undefined ? null : contextData.error;

    // Always use context for mutations
    const { updateInitiative, reloadInitiatives, reorderInitiative, moveInitiativeToStatus } = contextData;

    useEffect(() => {
        reloadInitiatives();
    }, [reloadCounter]);

    /**
     * When an item is dragged, compare its status before and after.
     * If different, trigger an update.
     */
    const handleItemDrag = async (initiative: OrderedEntity<InitiativeDto>, dropIndex: number) => {
        if (!initiativesData) {
            return;
        }
        const oldInitiative = initiativesData.find(i => i.id === initiative.id);

        if (!oldInitiative) {
            console.error('Could not find original initiative:', initiative);
            return;
        }

        // Check if the initiative moved position
        const orderedByStatus = initiativesData?.filter(i => i.status === initiative.status);
        const newIndex = dropIndex;
        const oldIndex = orderedByStatus.findIndex(i => i.id === initiative.id)
        const sourceStatus = oldInitiative.status as InitiativeStatus
        const destinationStatus = initiative.status as InitiativeStatus


        if (newIndex === oldIndex && destinationStatus === sourceStatus) {
            return;
        }

        const { beforeId, afterId } = computeOrderingIds(orderedByStatus, oldInitiative.id, newIndex);

        if (sourceStatus !== destinationStatus) {
            moveInitiativeToStatus(initiative.id, destinationStatus, afterId, beforeId);
        } else {
            reorderInitiative(initiative.id, afterId, beforeId);
        }
    };

    /**
     * Navigate to initiative detail when a card is clicked.
     */
    const handleCardClick = (initiative: InitiativeDto) => {
        navigate(`/workspace/initiatives/${initiative.id}`);
    };

    const hasBlockedInitiatives = initiativesData?.some(i => i.status === TaskStatus.BLOCKED);

    return (
        <KanbanBoardView<InitiativeDto>
            data={initiativesData || undefined}
            loading={shouldShowSkeleton}
            error={error ? new Error(error) : null}
            onCardClick={handleCardClick}
            onItemDrag={handleItemDrag}
            type="initiative"
            showBlocked={hasBlockedInitiatives}
            filterToStatus={selectedStatuses}
        />
    );
};

export default InitiativesKanbanBoard;
