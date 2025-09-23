import React, { useEffect, useState } from 'react';
import { DragDropContext, Droppable, Draggable, DropResult } from '@hello-pangea/dnd';
import { Ellipsis, Plus } from 'lucide-react';

import { OrderedEntity, useOrderings } from '#hooks/useOrderings';

import { Button } from '#components/reusable/Button';
import CreateInitiativeFromGroup from '#components/groups/CreateInitiativeFromGroup';
import EditExplicitGroup from '#components/groups/EditExplicitGroup';

import { GroupDto, InitiativeDto, GroupType, InitiativeStatus, EntityType, ContextType } from '#types';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { computeOrderingIds } from '#utils/dragDropUtils';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups';


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
                <span className="text-sm/6 text-muted">{initiative.identifier}</span>
                <span className="ml-4 text-sm/6 text-foreground">{initiative.title}</span>
            </div>
        </div>
    );
};

type ExplicitGroupProps = {
    group: GroupDto;
    onInitiativeClick: (initiative: InitiativeDto) => void;
    selectedStatuses: InitiativeStatus[];
};

/**
 * Renders an explicit group, displaying its name, description, and associated initiatives.
 * Supports drag-and-drop reordering of initiatives.
 * @param {ExplicitGroupProps} props - The component props.
 * @param {GroupDto} props.group - The explicit group data.
 * @param {(initiative: InitiativeDto) => void} props.onInitiativeClick - Callback function when an initiative is clicked.
 * @param {InitiativeStatus[]} props.selectedStatuses - The statuses of initiatives to display.
 * @returns {React.ReactElement} The ExplicitGroup component.
 */
const ExplicitGroup: React.FC<ExplicitGroupProps> = ({ selectedStatuses, group, onInitiativeClick }) => {
    const { moveInitiativeInGroup } = useInitiativesContext();
    const { refetchGroups } = useInitiativeGroups();
    const [isEditing, setIsEditing] = useState(false);
    const [isCreating, setIsCreating] = useState(false);


    const { orderedEntities } = useOrderings<InitiativeDto>({
        contextType: ContextType.GROUP,
        contextId: group.id,
        entityType: EntityType.INITIATIVE,
        entitiesToOrder: group.initiatives as InitiativeDto[],
        orderDirection: 'asc'
    })

    useEffect(() => {
        console.log('[ExplicitGroup] orderedEntities', orderedEntities)
    })

    if (group.group_type !== GroupType.EXPLICIT) {
        console.warn('ExplicitGroup component received a non-explicit group:', group);
        return <p className="text-red-500">Error: Invalid group type for ExplicitGroup.</p>;
    }

    const handleDragEnd = (result: DropResult) => {
        if (!result.destination || !orderedEntities) return;

        const sourceIdx = result.source.index;
        const initiative = orderedEntities[sourceIdx]

        if (!initiative || !initiative.id || orderedEntities.length == 1) {
            return
        }

        const newIndex = result.destination.index;

        if (sourceIdx === newIndex) return;

        // Filter out initiatives without IDs and cast to ensure type compatibility
        const validInitiatives = (orderedEntities || []).filter(
            (init): init is OrderedEntity<InitiativeDto> => init.id !== undefined
        );
        const { beforeId, afterId } = computeOrderingIds(validInitiatives, initiative.id, newIndex);

        moveInitiativeInGroup(initiative.id as string, group.id, afterId, beforeId)
            .then(() => {
                refetchGroups()
            })
    };

    return (
        <div className="relative text-foreground p-4 bg-transparent">
            {/* Group header */}
            <div className="flex flex-row justify-between items-center mb-3">
                <div className="flex flex-row gap-2 items-baseline">
                    <h2 className="font-bold text-lg">{group.name}</h2>
                    {group.initiatives && group.initiatives.length > 0 && <p className="text-sm text-muted-foreground">({group.initiatives.length})</p>}
                    {group.description && <p className="text-sm text-muted-foreground">{group.description}</p>}
                </div>

                <div className="flex flex-row gap-2">
                    <Button
                        onClick={() => setIsCreating(!isCreating)}
                        className="p-1.5"
                        dataTestId="create-initiative-button"
                    >
                        <Plus size={16} />
                        <span className="sr-only">Add initiative to {group.name}</span>
                    </Button>
                    <Button onClick={() => setIsEditing(!isEditing)} className="p-1.5">
                        <Ellipsis size={16} />
                        <span className="sr-only">Edit group {group.name}</span>
                    </Button>
                    {isEditing && (
                        <EditExplicitGroup
                            groupToEdit={group}
                            onClose={() => setIsEditing(false)}
                            onGroupUpdated={() => {
                                setIsEditing(false);
                            }}
                            onGroupDeleted={() => {
                                setIsEditing(false);
                            }}
                        />
                    )}
                </div>
            </div>

            {/* Group initiatives */}
            <DragDropContext onDragEnd={handleDragEnd}>
                <Droppable droppableId="initiatives-list">
                    {(provided) => (
                        <div
                            className="flex flex-col min-h-[2rem]"
                            ref={provided.innerRef}
                            {...provided.droppableProps}
                        >
                            {orderedEntities.length > 0 ? (
                                orderedEntities.map((initiative, idx) => (
                                    <Draggable key={initiative.id} draggableId={initiative.id.toString()} index={idx}>
                                        {(draggableProvided, snapshot) => (
                                            <div
                                                ref={draggableProvided.innerRef}
                                                {...draggableProvided.draggableProps}
                                                {...draggableProvided.dragHandleProps}
                                                className={snapshot.isDragging ? 'opacity-70' : ''}
                                            >
                                                <ListItem
                                                    initiative={initiative}
                                                    onClick={() => onInitiativeClick(initiative)}
                                                />
                                            </div>
                                        )}
                                    </Draggable>
                                ))
                            ) : (
                                <p className="text-sm text-muted-foreground">No initiatives in this group.</p>
                            )}
                            {provided.placeholder}
                        </div>
                    )}
                </Droppable>
            </DragDropContext>

            {/* Initiative creation form */}
            {isCreating && (
                <div className="mt-4 border-t border-border pt-4">
                    <CreateInitiativeFromGroup
                        group={group}
                        onClose={() => setIsCreating(false)}
                        onCreated={() => setIsCreating(false)}
                    />
                </div>
            )}
        </div>
    );
};

export default ExplicitGroup;


