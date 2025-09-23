import React, { FormEvent } from 'react';
import { ContextType, EntityType, InitiativeDto, InitiativeStatus, } from '#types';

import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions';

import CompactCreateView from '#components/CompactCreateView';

interface CompactCreateInitiativeProps {
    onCreate?: () => void;
    focus?: boolean;
    startExpanded?: boolean;
    defaultInitiativeStatus?: InitiativeStatus;
    orderingContext?: {
        contextType?: ContextType;
        contextId?: string | null;
        entityType?: EntityType;
    };
}

const CompactCreateInitiative = ({ focus, startExpanded = false, defaultInitiativeStatus = InitiativeStatus.TO_DO, orderingContext }: CompactCreateInitiativeProps) => {
    const { createInitiative } = useInitiativesContext();
    const { fieldDefinitions, loading: fieldDefinitionsLoading, error: fieldDefinitionsError } = useFieldDefinitions({});

    const [isExpanded, setIsExpanded] = React.useState(startExpanded);
    const [title, setTitle] = React.useState('');
    const [status, setStatus] = React.useState<InitiativeStatus>(defaultInitiativeStatus);
    const [type, setType] = React.useState<string | null>(null);
    const [error, setError] = React.useState<string | null>(null);
    const [isCreating, setIsCreating] = React.useState(false);

    const titleRef = React.useRef<HTMLTextAreaElement>(null);

    const typeFieldDefinition =
        (!fieldDefinitionsLoading && !fieldDefinitionsError)
            ? fieldDefinitions?.find(field => field.key === 'type' && field.entity_type === EntityType.INITIATIVE)
            : undefined

    const statusFieldDefinition =
        (!fieldDefinitionsLoading && !fieldDefinitionsError)
            ? fieldDefinitions?.find(field => field.key === 'status' && field.entity_type === EntityType.INITIATIVE)
            : undefined

    React.useEffect(() => {
        if (!focus) return;
        handleOpen();
    }, [focus]);

    React.useEffect(() => {
        if (!startExpanded) return;
        handleOpen();
    }, []);

    React.useEffect(() => {
        if (!error) return;
        const timeout = setTimeout(() => setError(null), 5000);
        return () => clearTimeout(timeout);
    }, [error]);

    const handleOpen = () => {
        setIsExpanded(true);
        setTimeout(() => {
            titleRef.current?.focus();
        }, 0);
    };

    const handleClose = () => {
        setIsExpanded(false);
        setError(null);
    };

    const handleSubmit = async (event?: FormEvent | MouseEvent) => {
        event?.preventDefault();
        const trimmedTitle = title.trim();
        if (!trimmedTitle) {
            setTitle('');
            setError('Title is required');
            setTimeout(() => {
                setError(null);
            }, 5000);
            titleRef.current?.focus();
            return;
        }
        setIsCreating(true);
        const newInitiative: Partial<InitiativeDto> = {
            title: trimmedTitle,
            status,
            description: '',
            type: type || undefined,
        };
        const initiative = await createInitiative(
            newInitiative,
            {
                contextType: orderingContext?.contextType ?? ContextType.STATUS_LIST,
                contextId: orderingContext?.contextId ?? null,
                entityType: orderingContext?.entityType ?? EntityType.INITIATIVE
            }
        ).then((res) => {
            setError(null);
            return res;
        }).catch((err: any) => {
            setError(err?.message || 'Something went wrong');
        });
        if (!initiative) {
            throw new Error('Failed to create initiative');
        }
        setTitle('');
        setStatus(defaultInitiativeStatus);
        setIsCreating(false);
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter') {
            handleSubmit(e);
        }

        if (e.key === 'Escape') {
            handleClose();
        }
    };

    return (
        <CompactCreateView
            isExpanded={isExpanded}
            title={title}
            status={status}
            error={error}
            isCreating={isCreating}
            disabled={false}
            titleRef={titleRef}
            onOpen={handleOpen}
            onClose={handleClose}
            onTitleChange={setTitle}
            onStatusChange={(status) => setStatus(status as InitiativeStatus)}
            onSubmit={handleSubmit}
            onKeyDown={handleKeyDown}
            typeFieldDefinition={typeFieldDefinition}
            statusFieldDefinition={statusFieldDefinition}
            type={type}
            setType={setType}
        />
    );
};

export default CompactCreateInitiative;
