import React, { useRef, useState, useEffect } from 'react';

import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions';

import CompactCreateView from '#components/CompactCreateView';

import { EntityType, GroupDto, InitiativeDto, InitiativeStatus, GroupType, ContextType } from '#types';


interface CreateInitiativeFromGroupProps {
    group: GroupDto;
    onClose: () => void;
    onCreated?: () => void;
}

/**
 * A form component for creating initiatives directly from a group.
 * @param {CreateInitiativeFromGroupProps} props - The component props
 * @param {GroupDto} props.group - The group to associate the initiative with (explicit or smart)
 * @param {() => void} props.onClose - Function to call when the form is closed
 * @param {() => void} [props.onCreated] - Optional callback when an initiative is created
 * @returns {React.ReactElement} The CreateInitiativeFromGroup component
 */
const CreateInitiativeFromGroup: React.FC<CreateInitiativeFromGroupProps> = ({
    group,
    onClose,
    onCreated
}) => {
    const { createInitiative } = useInitiativesContext();
    const { fieldDefinitions, loading: fieldDefinitionsLoading } = useFieldDefinitions({});
    const { addInitiativeToExplicitGroup } = useInitiativeGroups();

    // Form state
    const [title, setTitle] = useState('');
    const [status, setStatus] = useState<InitiativeStatus>(InitiativeStatus.BACKLOG);
    const [type, setType] = useState<string | null>(null);
    const [formError, setFormError] = useState<string | null>(null);
    const [isCreating, setIsCreating] = useState(false);

    const titleRef = useRef<HTMLTextAreaElement>(null);

    const typeFieldDefinition =
        (!fieldDefinitionsLoading)
            ? fieldDefinitions?.find(field => field.key === 'type' && field.entity_type === EntityType.INITIATIVE)
            : undefined;
    
    const statusFieldDefinition =
        (!fieldDefinitionsLoading)
            ? fieldDefinitions?.find(field => field.key === 'status' && field.entity_type === EntityType.INITIATIVE)
            : undefined;

    // Focus the title input when mounted
    useEffect(() => {
        setTimeout(() => {
            titleRef.current?.focus();
        }, 0);
    }, []);

    // Apply smart group criteria to the new initiative
    const applySmartGroupCriteria = (initiative: Partial<InitiativeDto>) => {
        if (!group.query_criteria || group.group_type !== GroupType.SMART) return initiative;

        const enhancedInitiative: Partial<InitiativeDto> = {
            ...initiative,
            properties: initiative.properties || {}
        };



        // Apply each criterion from the smart group's query_criteria
        Object.entries(group.query_criteria).forEach(([key, value]) => {
            if (key === 'status') {
                // Override user's selected status
                enhancedInitiative.status = value as InitiativeStatus;
                return;
            }

            if (key === 'type') {
                // Override user's selected type
                enhancedInitiative.type = value as string;
                return;
            }

            //   Find the field definition for the key
            const fieldDefinition = fieldDefinitions?.find(field => field.key === key && field.entity_type === EntityType.INITIATIVE);
            if (fieldDefinition) {
                // Apply the criterion to the initiative
                enhancedInitiative.properties ? [fieldDefinition.id] = value : null;
            } else {
                console.error(`Field definition not found for key: ${key}`);
            }
        });

        return enhancedInitiative;
    };

    const handleCreateInitiative = async () => {
        const trimmedTitle = title.trim();

        if (!trimmedTitle) {
            setTitle('');
            setFormError('Title is required');
            setTimeout(() => {
                setFormError(null);
            }, 5000);
            titleRef.current?.focus();
            return;
        }

        setIsCreating(true);

        // Create base initiative
        let newInitiative: Partial<InitiativeDto> = {
            title: trimmedTitle,
            status,
            description: '',
            type: type || undefined,
        };

        try {
            // Handle differently based on group type
            if (group.group_type === GroupType.EXPLICIT) {
                // For explicit groups, create the initiative then add it to the group
                // Ordering will be handled by addInitiativeToExplicitGroup
                const initiative = await createInitiative(newInitiative);
                await addInitiativeToExplicitGroup(initiative, group);
            } else if (group.group_type === GroupType.SMART) {
                // For smart groups, apply the query criteria then create the initiative
                newInitiative = applySmartGroupCriteria(newInitiative);
                await createInitiative(newInitiative);
            }

            setFormError(null);
            if (onCreated) {
                onCreated();
            }
            onClose();
        } catch (err: any) {
            setFormError(err?.message || 'Something went wrong');
        } finally {
            setIsCreating(false);
        }
    };

    return (
        <CompactCreateView
            isExpanded={true}
            title={title}
            status={status}
            error={formError}
            isCreating={isCreating}
            disabled={false}
            titleRef={titleRef}
            onOpen={() => {}}
            onClose={onClose}
            onTitleChange={setTitle}
            onStatusChange={(status) => setStatus(status as InitiativeStatus)}
            onSubmit={handleCreateInitiative}
            onKeyDown={() => {}}
            typeFieldDefinition={typeFieldDefinition}
            statusFieldDefinition={statusFieldDefinition}
            type={type}
            setType={setType}
        />
    );
};

export default CreateInitiativeFromGroup;
