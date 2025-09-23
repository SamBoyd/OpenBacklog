import React from 'react';
import { useNavigate } from 'react-router';

import { useInitiativesContext } from '#contexts/InitiativesContext';
import { ContextType, EntityType, InitiativeDto, TaskStatus } from '#types';

import StatusGroupedListView from './reusable/StatusGroupedListView';
import { Skeleton } from './reusable/Skeleton';
import { OrderedEntity } from '#hooks/useOrderings';

type ListItemProps = {
    initiative: InitiativeDto;
    onClick: () => void;
};

const ListItem = ({ initiative, onClick }: ListItemProps) => {
    return (
        <div
            data-testid={`list-item-${initiative.id}`}
            key={initiative.id}
            className=""
            onClick={onClick}
        >
            <div className="flex-grow px-3 rounded hover:bg-muted-foreground/5 cursor-pointer">
                <span className="text-sm/6">{initiative.identifier}</span>
                <span className="ml-4 text-sm/6 text-foreground">{initiative.title}</span>
            </div>
        </div>
    );
};

const LoadingListItem = () => (
    <div
        data-testid="loading-list-item"
        className=""
    >
        <div className="flex flex-row justify-start items-start flex-grow space-x-4 px-3 rounded hover:bg-muted-foreground/5 cursor-pointer opacity-40">
            <Skeleton type="text" className="w-[30px]" />
            <Skeleton type="text" className="w-[200px]" />
        </div>
    </div>
);

interface InitiativesListProps {
    initiatives: InitiativeDto[] | null | undefined;
    loading: boolean;
    error: string | null;
    selectedStatuses: TaskStatus[];
    onInitiativeClick: (initiativeId: string) => void;
    onOrderChange: (initiatives: InitiativeDto[]) => void;
}

interface InitiativesListViewProps {
    selectedStatuses?: TaskStatus[];
}

export default function InitiativesList({ selectedStatuses = Object.values(TaskStatus) }: InitiativesListViewProps) {
    const { initiativesData, shouldShowSkeleton, isQueryFetching, error, reorderInitiative } = useInitiativesContext();
    const navigate = useNavigate();

    const loading = shouldShowSkeleton || isQueryFetching;

    // Navigate to initiative detail when clicked.
    const handleCardClick = (initiativeId: string) => {
        if (loading || error) return;
        const initiative = initiativesData?.find((i: any) => i.id === initiativeId);
        if (!initiative) return;

        navigate(`/workspace/initiatives/${initiativeId}`);
    };

    const handleOrderChange = async (updatedEntity: OrderedEntity<InitiativeDto>, afterId: string | null, beforeId: string | null) => {
        await reorderInitiative(updatedEntity.id,  afterId, beforeId);
    }

    const renderInitiative = (initiative: InitiativeDto, onItemClick: (id: string) => void) => (
        <ListItem
            key={initiative.id}
            initiative={initiative}
            onClick={() => onItemClick(initiative.id)}
        />
    );

    const renderLoadingInitiative = () => <LoadingListItem key={Math.random()} />;

    return (
        <StatusGroupedListView
            items={initiativesData}
            loading={shouldShowSkeleton}
            error={error}
            emptyStateMessage="You currently don't have any Initiatives. Create some below."
            showEmptyState={true}
            renderItem={renderInitiative}
            renderLoadingItem={renderLoadingInitiative}
            onItemClick={handleCardClick}
            selectedStatuses={selectedStatuses}
            dataTestId="initiative-list-nav"
            onOrderChange={handleOrderChange}
        />
    );
}
