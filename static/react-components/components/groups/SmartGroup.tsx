import React, { useState } from 'react';
import { GroupDto, InitiativeDto, GroupType, FieldDefinitionDto, EntityType, InitiativeStatus } from '#types';
import { Button } from '#components/reusable/Button';
import { Ellipsis, Plus } from 'lucide-react';
import CreateInitiativeFromGroup from './CreateInitiativeFromGroup';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import EditSmartGroup from '#components/groups/EditSmartGroup';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions';
import { applySmartGroupCriteria, useInitiativeGroups } from '#hooks/useInitiativeGroups';

// ListItem component - consider moving to a shared location if used elsewhere
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

type SmartGroupProps = {
    group: GroupDto;
    onInitiativeClick: (initiative: InitiativeDto) => void;
    selectedStatuses: InitiativeStatus[];
};

/**
 * Renders a smart group, displaying its name, description, and dynamically filtered initiatives.
 * Initiatives are filtered based on the group's query_criteria.
 * @param {SmartGroupProps} props - The component props.
 * @param {GroupDto} props.group - The smart group data.
 * @param {(initiative: InitiativeDto) => void} props.onInitiativeClick - Callback function when an initiative is clicked.
 * @param {InitiativeStatus[]} props.selectedStatuses - The statuses of initiatives to display.
 * @returns {React.ReactElement} The SmartGroup component.
 */
const SmartGroup: React.FC<SmartGroupProps> = ({ group, onInitiativeClick, selectedStatuses }) => {
    const { initiativesData: allInitiatives, shouldShowSkeleton: initiativesLoading, error: initiativesError } = useInitiativesContext();
    const [isEditing, setIsEditing] = useState(false);
    const [isCreating, setIsCreating] = useState(false);
    // Fetch all field definitions for the workspace
    const { fieldDefinitions: workspaceFieldDefinitions, loading: fieldDefsLoading, error: fieldDefsError } =
        useFieldDefinitions({});


    // Filter the initiatives based on the group's query_criteria
    const filteredInitiatives = React.useMemo(() => {
        if (initiativesLoading || fieldDefsLoading  || group == null) {
            return []; // Or a loading state indicator
        }

        if (!group) {
            console.error('SmartGroup component received a group that is not in the workspace:', group);
            return [];
        }

        if (initiativesError || fieldDefsError) {
            console.error("Error loading data for smart group:", initiativesError, fieldDefsError);
            return []; // Or an error state indicator
        }
        if (!allInitiatives || !workspaceFieldDefinitions) {
            return [];
        }
        // Filter field definitions for initiatives before applying criteria
        const initiativeFieldDefinitions = workspaceFieldDefinitions.filter(
            fd => fd.entity_type === EntityType.INITIATIVE
        )

        const filteredInitiatives = allInitiatives.filter(initiative => selectedStatuses.includes(initiative.status as InitiativeStatus));

        return applySmartGroupCriteria(filteredInitiatives, group.query_criteria, initiativeFieldDefinitions);
    }, [allInitiatives, group, workspaceFieldDefinitions, initiativesLoading, fieldDefsLoading, initiativesError, fieldDefsError]);



    let errorOrLoadingMessage = null;

    if (initiativesLoading || fieldDefsLoading) {
        errorOrLoadingMessage = <p className="text-sm text-muted-foreground">Loading...</p>;
    }

    if (initiativesError || fieldDefsError) {
        errorOrLoadingMessage = <p className="text-red-500">Error: {initiativesError}</p>;
    }


    if (group && group.group_type !== GroupType.SMART) {
        console.error('SmartGroup component received a non-smart group:', group);
        errorOrLoadingMessage = <p className="text-red-500">Error: Invalid group type for SmartGroup.</p>;
    }

    if (!group) {
        return <p className="text-red-500">Error: Group not found in workspace.</p>;
    }

    const toggleEdit = () => {
        setIsEditing(!isEditing);
    };

    return (
        <div className="relative text-foreground p-4 bg-transparent">
            {/* Group header */}
            <div className="flex flex-row justify-between items-center mb-3">
                <div className="flex flex-row gap-2 items-baseline">
                    <h2 className="font-bold text-lg">{group.name}</h2>
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
                    
                    {/* Use className as per Button.tsx capabilities */}
                    <Button onClick={() => toggleEdit()} className="p-1.5">
                        <Ellipsis size={16} />
                        <span className="sr-only">Edit group {group.name}</span>
                    </Button>

                    {isEditing && (
                        <EditSmartGroup
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

            {errorOrLoadingMessage}

            {!errorOrLoadingMessage && (
                <>
                    {/* Filtered initiatives */}
                    {filteredInitiatives.length > 0 ? (
                        <div className="flex flex-col gap-2">
                            {filteredInitiatives.map(initiative => (
                                <ListItem
                                    key={initiative.id}
                                    initiative={initiative}
                                    onClick={() => onInitiativeClick(initiative)}
                                />
                            ))}
                        </div>
                    ) : (
                        <p className="text-sm text-muted-foreground">No initiatives match the criteria for this smart group.</p>
                    )}
                </>
            )}
            
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

export default SmartGroup;


