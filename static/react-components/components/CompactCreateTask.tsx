import React from 'react';

import { EntityType, TaskStatus } from '#types';
import CompactCreateView from './CompactCreateView';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions';
import { useTasksContext } from '#contexts/TasksContext';

type CompactCreateTaskProps = {
    initiativeId?: string;
    disabled?: boolean;
    onTaskCreated?: () => void;
    focus?: boolean;
    startExpanded?: boolean;
};

// Renamed component to reflect it's the container/controller
const CompactCreateTask = ({ initiativeId, disabled, onTaskCreated, focus, startExpanded = false }: CompactCreateTaskProps) => {
    const { createTask } = useTasksContext();
    const { fieldDefinitions, loading: fieldDefinitionsLoading, error: fieldDefinitionsError } = useFieldDefinitions({});

    const [isExpanded, setIsExpanded] = React.useState(startExpanded);
    const [title, setTitle] = React.useState('');
    const [status, setStatus] = React.useState(TaskStatus.TO_DO);
    const [error, setError] = React.useState<string | null>(null);
    const [type, setType] = React.useState<string | null>(null);
    const [isCreating, setIsCreating] = React.useState(false);

    const titleRef = React.useRef<HTMLTextAreaElement>(null);

    const typeFieldDefinition = 
        (!fieldDefinitionsLoading && !fieldDefinitionsError)
        ? fieldDefinitions?.find(field => field.key === 'type' && field.entity_type === EntityType.TASK)
        : undefined

    const statusFieldDefinition = 
        (!fieldDefinitionsLoading && !fieldDefinitionsError)
        ? fieldDefinitions?.find(field => field.key === 'status' && field.entity_type === EntityType.TASK)
        : undefined

    React.useEffect(() => {
        if (!focus) return;
        handleOpen();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [focus]); 

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

    const handleTitleChange = (value: string) => setTitle(value);
    const handleStatusChange = (value: string) => setStatus(value as TaskStatus);

    const handleSubmit = async (event?: React.FormEvent | React.KeyboardEvent) => {
        event?.preventDefault();

        const trimmedTitle = title.trim();
        if (!trimmedTitle) {
            setTitle(''); // Clear title if only spaces were entered
            setError('Title is required');
            titleRef.current?.focus();
            return;
        }

        setIsCreating(true);
        setError(null); // Clear previous errors

        try {
            await createTask({
                title: trimmedTitle,
                status,
                initiative_id: initiativeId,
                description: '',
                type,
            });

            setTitle('');
            setStatus(TaskStatus.TO_DO);

            if (onTaskCreated) {
                onTaskCreated();
            }

            titleRef.current?.focus();
        } catch (err: any) {
            console.error("Error creating task:", err);
            setError(err.message || 'An unknown error occurred');
        } finally {
            setIsCreating(false);
        }
    };

    // Clear error after 5s
    React.useEffect(() => {
        if (!error) return;
        const timeout = setTimeout(() => setError(null), 5000);
        return () => clearTimeout(timeout);
    }, [error]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === 'Enter') {
            handleSubmit(e);
        }
        
        // Close on Escape
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
            disabled={disabled}
            titleRef={titleRef}
            onOpen={handleOpen}
            onClose={handleClose}
            onTitleChange={handleTitleChange}
            onStatusChange={handleStatusChange}
            onSubmit={handleSubmit}
            onKeyDown={handleKeyDown}
            statusFieldDefinition={statusFieldDefinition}
            typeFieldDefinition={typeFieldDefinition}
            type={type}
            setType={setType}
        />
    );
};

export default CompactCreateTask;
