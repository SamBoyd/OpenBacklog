import React from 'react';
import { Tooltip } from 'react-tooltip'
import { ArrowRightIcon } from 'lucide-react';

import { Skeleton } from '#components/reusable/Skeleton';

import StatusGroupedListView from '#components/reusable/StatusGroupedListView';

import { InitiativeDto, InitiativeStatus, TaskStatus } from '#types';

import '../styles/tooltip.css';
import { OrderedEntity } from '#hooks/useOrderings';

type ListItemProps = {
    initiative: InitiativeDto;
    onClick: () => void;
    moveToStatus: ((status: InitiativeStatus) => (event: React.MouseEvent<HTMLDivElement>) => void) | undefined;
};

const ListItem = ({ initiative, onClick, moveToStatus }: ListItemProps) => {
    return (
        <div
            data-testid={`list-item-${initiative.id}`}
            key={initiative.id}
            className=""
            onClick={onClick}
        >
            <div className="group/line flex flex-row justify-between flex-grow pl-3 rounded hover:bg-muted-foreground/5 cursor-pointer items-start">
                <div className="flex flex-row justify-start items-start">
                    <span className="text-sm text-muted flex-shrink-0">{initiative.identifier}</span>
                    <span className="ml-4 text-sm text-foreground flex-grow">{initiative.title}</span>
                </div>

                {initiative.status === InitiativeStatus.BACKLOG && (
                    <div className="w-14 flex-grow-0 flex flex-row justify-end items-start">
                        <div
                            id="move-to-todo-button"
                            className={`
                            group/button
                            flex flex-row justify-end items-start
                            hover:!bg-muted/10
                            rounded-md p-1 space-x-1
                            transition-all duration-200 ease-in-out
                            w-5 hover:!w-8
                        `}
                            data-tooltip-id={`move-to-todo-button-${initiative.id}`}
                            data-tooltip-content="⇄ To do"
                            data-tooltip-place="bottom-end"
                            data-tooltip-delay-show={600}
                            onClick={moveToStatus ? moveToStatus(InitiativeStatus.TO_DO) : undefined}
                        >
                            <ArrowRightIcon className="w-4 h-4 text-transparent group-hover/line:text-muted-foreground/50 group-hover/button:!text-foreground" />
                        </div>
                    </div>
                )}
            </div>

            <Tooltip
                id={`move-to-todo-button-${initiative.id}`}
                className="custom-tooltip"
            />
        </div>
    );
};

const LoadingListItem = () => (
    <div
        data-testid="loading-list-item"
        className=""
    >
        <div className="flex flex-row justify-start items-start flex-grow space-x-4 px-3 rounded hover:bg-muted-foreground/5 cursor-pointer opacity-40">
            <Skeleton type="text" width="w-8" height="h-5" />
            <Skeleton type="text" width="w-64" height="h-5" />
        </div>
    </div>
);

interface InitiativesListProps {
    initiatives: OrderedEntity<InitiativeDto>[] | null | undefined;
    loading: boolean;
    error: string | null;
    selectedStatuses: InitiativeStatus[];
    onInitiativeClick: (initiativeId: string) => void;
    onOrderChange: (updatedEntity: OrderedEntity<InitiativeDto>, afterId: string | null, beforeId: string | null) => void;
    onStatusChange: (updatedEntity: OrderedEntity<InitiativeDto>, newStatus: InitiativeStatus | TaskStatus,  afterId: string | null, beforeId: string | null) => void;
    moveToStatus?: (initiativeId: string) => (status: InitiativeStatus) => (event: React.MouseEvent<HTMLDivElement>) => void;
}

/**
 * Container component for displaying a list of initiatives grouped by status.
 * @param {InitiativesListProps} props - The component props
 * @returns {React.ReactElement} The rendered initiative list view
 */
export default function InitiativesListView({
    initiatives,
    loading,
    error,
    selectedStatuses,
    onInitiativeClick,
    onOrderChange,
    moveToStatus,
    onStatusChange,
}: InitiativesListProps) {
    const renderInitiative = (initiative: InitiativeDto, onItemClick: (id: string) => void) => (
        <ListItem
            key={initiative.id}
            initiative={initiative}
            onClick={() => onItemClick(initiative.id)}
            moveToStatus={moveToStatus ? moveToStatus(initiative.id) : undefined}
        />
    );

    const renderLoadingInitiative = () => <LoadingListItem key={Math.random()} />;

    return (
        <StatusGroupedListView<InitiativeDto>
            items={initiatives}
            loading={loading}
            error={error}
            emptyStateMessage="You currently don't have any Initiatives. Create some below."
            showEmptyState={true}
            renderItem={renderInitiative}
            renderLoadingItem={renderLoadingInitiative}
            onItemClick={onInitiativeClick}
            selectedStatuses={selectedStatuses}
            dataTestId="initiative-list-nav"
            onOrderChange={onOrderChange}
            onStatusChange={onStatusChange}
        />
    );
}
