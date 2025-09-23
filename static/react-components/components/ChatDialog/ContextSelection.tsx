import React, { useMemo, useState, useRef, useEffect } from 'react';
import { Tooltip } from 'react-tooltip';
import { Check, X } from 'lucide-react';

import { CompactInput, Input } from '#components/reusable/Input';
import { useInitiativesContext } from '#contexts/InitiativesContext';
import { useTasksContext } from '#contexts/TasksContext';
import { CompactButton } from '#components/reusable/Button';

import { useActiveEntity } from '#hooks/useActiveEntity';

import { InitiativeDto, TaskDto } from '#types';

interface ContextSelectionProps {
    isOpen?: boolean;
    disabled: boolean;
    onOpenChange?: (isOpen: boolean) => void;
    currentContext: (InitiativeDto | TaskDto)[];
    onContextChange: (context: (InitiativeDto | TaskDto)[]) => void;
}

type SearchEntity = {
    id: string;
    title: string;
    description: string;
    identifier: string;
    type: 'initiative' | 'task';
};

const ContextSelection: React.FC<ContextSelectionProps> = ({
    isOpen,
    disabled,
    onOpenChange,
    currentContext,
    onContextChange
}) => {
    const { initiativesData } = useInitiativesContext();
    const { tasks } = useTasksContext();
    const { recentInitiatives: recentInitiativeIds } = useActiveEntity();

    const [selectedIndex, setSelectedIndex] = useState(0);
    const [searchQuery, setSearchQuery] = useState('');
    const [internalIsOpen, setInternalIsOpen] = useState(false);

    const inputRef = useRef<HTMLInputElement>(null);
    const listRef = useRef<HTMLDivElement>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    const isDropdownOpen = isOpen !== undefined ? isOpen : internalIsOpen;

    const lastAddedEntity = useRef<InitiativeDto | TaskDto | null>(null);

    const recentInitiatives = useMemo(() =>
        initiativesData?.filter(
            initiative => recentInitiativeIds.includes(initiative.id)
        ), [initiativesData, recentInitiativeIds]);

    const setIsDropdownOpen = (value: boolean) => {
        if (onOpenChange) {
            onOpenChange(value);
        } else {
            setInternalIsOpen(value);
        }
    };

    const initiativeSearchIndex = useMemo(() => initiativesData?.map(initiative => ({
        id: initiative.id,
        title: initiative.title,
        description: initiative.description,
        identifier: initiative.identifier,
        type: 'initiative' as const,
    })), [initiativesData]);

    const taskSearchIndex = useMemo(() => tasks?.map(task => ({
        id: task.id,
        title: task.title,
        description: task.description,
        identifier: task.identifier,
        type: 'task' as const,
    })), [tasks]);

    const filteredInitiatives = useMemo(() =>
        initiativeSearchIndex?.filter(initiative =>
            initiative.title.toLowerCase().includes(searchQuery.toLowerCase())
        ).slice(0, 5) || [],
        [initiativeSearchIndex, searchQuery]);

    const filteredTasks = useMemo(() =>
        taskSearchIndex?.filter(task =>
            task.title.toLowerCase().includes(searchQuery.toLowerCase())
        ).slice(0, 5) || [],
        [taskSearchIndex, searchQuery]);

    const filteredRecentInitiatives = useMemo(() => {
        if (searchQuery !== '' || !recentInitiatives) return [];
        return recentInitiatives.filter(initiative =>
            !filteredInitiatives.some(f => f.id === initiative.id) &&
            !filteredTasks.some(t => t.id === initiative.id)
        );
    }, [recentInitiatives, filteredInitiatives, filteredTasks, searchQuery]);

    const allResults = useMemo(() => {
        const recentAsSearchEntities = (filteredRecentInitiatives || []).map(initiative => ({
            id: initiative.id,
            title: initiative.title,
            description: initiative.description,
            identifier: initiative.identifier,
            type: 'initiative' as const,
        }));
        const combined = [...recentAsSearchEntities, ...filteredInitiatives, ...filteredTasks];
        return combined.filter((item, index, arr) =>
            arr.findIndex(other => other.id === item.id) === index
        );
    }, [filteredRecentInitiatives, filteredInitiatives, filteredTasks]);

    useEffect(() => {
        if (isDropdownOpen) {
            setTimeout(() => {
                inputRef.current?.focus();
            }, 0);
        }
    }, [isDropdownOpen]);

    useEffect(() => {
        setSelectedIndex(0);
    }, [searchQuery]);

    // Scroll selected item into view
    useEffect(() => {
        if (!listRef.current) return;

        const selectedElement = listRef.current.children[selectedIndex + 1]; // +1 for header
        if (selectedElement && 'scrollIntoView' in selectedElement) {
            selectedElement.scrollIntoView({ block: 'nearest' });
        }
    }, [selectedIndex]);

    // Add click outside handler
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                containerRef.current &&
                !containerRef.current.contains(event.target as Node)
            ) {
                setIsDropdownOpen(false);
                setSearchQuery('');
            }
        };

        if (isDropdownOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [containerRef, isDropdownOpen, setIsDropdownOpen]);

    const handleEntitySelect = (entity: SearchEntity) => {
        const fullEntity = entity.type === 'initiative'
            ? initiativesData?.find(i => i.id === entity.id)
            : tasks?.find(t => t.id === entity.id);

        if (fullEntity) {
            const isAlreadyInContext = currentContext.some(e => e.id === entity.id);

            if (isAlreadyInContext) {
                onContextChange(currentContext.filter(e => e.id !== entity.id));
                lastAddedEntity.current = null;
            } else {
                onContextChange([...currentContext, fullEntity]);
                lastAddedEntity.current = fullEntity;
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (!isDropdownOpen || allResults.length === 0) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                setSelectedIndex(prev =>
                    prev < allResults.length - 1 ? prev + 1 : 0
                );
                break;
            case 'ArrowUp':
                e.preventDefault();
                setSelectedIndex(prev =>
                    prev > 0 ? prev - 1 : allResults.length - 1
                );
                break;
            case 'Tab':
                e.preventDefault();
                setSelectedIndex(prev =>
                    prev < allResults.length - 1 ? prev + 1 : 0
                );
                break;
            case 'Enter':
                e.preventDefault();
                if (allResults[selectedIndex]) {
                    handleEntitySelect(allResults[selectedIndex]);
                }
                break;
            case 'Escape':
                e.preventDefault();
                setIsDropdownOpen(false);
                setSearchQuery('');
                break;
        }
    };

    return (
        <div id="context-selector" className="mx-2 text-sidebar-foreground relative" ref={containerRef}>
            <div className="" >
                <div className="flex items-end">
                    {isDropdownOpen && (
                        <CompactButton
                            className="my-1 bg-primary/30 text-white hover:bg-primary/30"
                            onClick={() => {
                                setIsDropdownOpen(!isDropdownOpen);
                            }}
                            data-tooltip-id="add-to-context-button"
                            data-tooltip-place="bottom"
                            data-tooltip-delay-show={200}
                            active={isDropdownOpen ? "true" : "false"}
                        >
                            @
                        </CompactButton>
                    ) || (
                            <CompactButton
                                className="text-sidebar-foreground my-1 hover:bg-primary/30 hover:text-white"
                                onClick={() => {
                                    setIsDropdownOpen(!isDropdownOpen);
                                    setSearchQuery('');
                                }}
                                disabled={disabled}
                                data-tooltip-id="add-to-context-button"
                                data-tooltip-place="bottom"
                                data-tooltip-delay-show={200}
                                active={isDropdownOpen ? "true" : "false"}
                            >
                                @
                            </CompactButton>
                        )}

                    {/* Context list */}
                    <div className="my-1 flex flex-col justify-start overflow-clip w-[calc(100%-1rem)]">
                        {!isDropdownOpen && currentContext.map((entity, index) => (
                            <div
                                key={index}
                                className="group w-fit max-w-[100%] cursor-pointer bg-muted/5 py-0.5 rounded-sm flex flex-row pr-4 mt-0.5 justify-start items-center group relative"
                                onClick={() => onContextChange(currentContext.filter(e => e.id !== entity.id))}
                            >
                                <button
                                    className="w-0 group-hover:w-auto mx-0 group-hover:mx-1 overflow-hidden transition-all duration-200 ease-in-out p-0.5 group-hover:bg-accent/25 group-hover:text-accent-foreground rounded transform -translate-x-2 group-hover:translate-x-0 opacity-0 group-hover:opacity-100"
                                >
                                    <X className="h-3 w-3 text-muted-foreground group-hover:text-accent-foreground transition-colors duration-200 shrink-0" />
                                </button>

                                <div className="text-sm text-muted-foreground truncate transition-all duration-200 ease-in-out text-xs">
                                    <span className="text-muted-foreground/50">{entity.identifier}</span> {entity.title}
                                </div>
                            </div>
                        ))}

                        {isDropdownOpen && lastAddedEntity.current && (
                            <div
                                className="group w-fit max-w-[100%] cursor-pointer bg-muted/5 py-0.5 rounded-sm flex flex-row pr-4 mt-0.5 justify-start items-center group relative"
                                onClick={() => {
                                    onContextChange(currentContext.filter(e => e.id !== lastAddedEntity.current?.id));
                                    lastAddedEntity.current = null;
                                }}
                            >
                                <button
                                    className="w-0 group-hover:w-auto mx-0 group-hover:mx-1 overflow-hidden transition-all duration-200 ease-in-out p-0.5 group-hover:bg-accent/25 group-hover:text-accent-foreground rounded transform -translate-x-2 group-hover:translate-x-0 opacity-0 group-hover:opacity-100"
                                >
                                    <X className="h-3 w-3 text-muted-foreground group-hover:text-accent-foreground transition-colors duration-200 shrink-0" />
                                </button>

                                <div className="text-sm text-muted-foreground truncate transition-all duration-200 ease-in-out text-xs">
                                    <span className="text-muted-foreground/50">{lastAddedEntity.current.identifier}</span> {lastAddedEntity.current.title}
                                </div>
                            </div>
                        )}
                    </div>

                    <Tooltip
                        id="add-to-context-button"
                        className="custom-tooltip"
                    >
                        <div className='flex flex-row items-baseline gap-1'>
                            <span className='text-xs text-muted-foreground'>Add to context</span>
                            <span className='text-[9px] text-muted-foreground/50'>Ctrl+Shift+P</span>
                        </div>
                    </Tooltip>
                </div>
            </div>

            {isDropdownOpen && (
                <div
                    id="context-selector-list"
                    ref={listRef}
                    className="absolute bottom-[100%] bg-sidebar border border-border rounded-md shadow-lg z-50 max-h-[300px] overflow-y-auto w-full"
                >
                    <input
                        ref={inputRef}
                        placeholder="Search for tasks and initiatives..."
                        value={searchQuery}
                        onChange={e => {
                            setSearchQuery(e.target.value);
                            setIsDropdownOpen(true);
                        }}
                        onKeyDown={handleKeyDown}
                        className={`
                            z-10 bg-sidebar w-full text-muted-foreground text-xs
                            block rounded-t-md px-2 py-0.5 text-sm selected:bg-background/80
                            border border-border focus:outline-none focus:ring-0 focus:ring-primary/50
                        `}
                    />

                    <>
                        {filteredRecentInitiatives?.length > 0
                            && filteredRecentInitiatives.map((initiative, index) => {
                                const isSelected = index === selectedIndex;
                                const isInContext = currentContext.some(e => e.id === initiative.id);

                                return (
                                    <div
                                        key={initiative.id}
                                        className={`
                                            px-4 py-1 cursor-pointer text-sm flex items-center gap-2 relative z-50
                                            ${isSelected ? 'bg-primary/15' : 'hover:bg-primary/15'}
                                        `}
                                        onClick={(event) => {
                                            event.stopPropagation();

                                            handleEntitySelect({
                                                id: initiative.id,
                                                title: initiative.title,
                                                description: initiative.description,
                                                identifier: initiative.identifier,
                                                type: 'initiative'
                                            })
                                        }}
                                    >
                                        <span className="text-muted-foreground/50 text-xs">{initiative.identifier}</span>
                                        <span className="flex-1 text-xs truncate">{initiative.title}</span>
                                        {isInContext && (
                                            <Check className="absolute right-2 h-4 w-4 text-primary shrink-0" />
                                        )}
                                    </div>
                                )
                            })}
                    </>

                    <>
                        {filteredInitiatives.map((initiative, index) => {
                            const isSelected = (filteredRecentInitiatives?.length || 0) + index === selectedIndex;
                            const isInContext = currentContext.some(e => e.id === initiative.id);
                            return (
                                <div
                                    key={initiative.id}
                                    className={`
                                        px-4 py-1 cursor-pointer text-sm flex items-center gap-2 
                                        ${isSelected ? 'bg-primary/15' : 'hover:bg-primary/15'}
                                    `}
                                    onClick={(event) => {
                                        event.stopPropagation();
                                        handleEntitySelect(initiative)
                                    }}
                                >
                                    <span className="text-muted-foreground/50 text-xs">{initiative.identifier}</span>
                                    <span className="flex-1 text-xs truncate">{initiative.title}</span>
                                    {isInContext && (
                                        <Check className="h-4 w-4 text-primary shrink-0" />
                                    )}
                                </div>
                            );
                        })}

                        {filteredTasks.map((task, index) => {
                            const isSelected = (filteredRecentInitiatives?.length || 0) + filteredInitiatives.length + index === selectedIndex;
                            const isInContext = currentContext.some(e => e.id === task.id);
                            return (
                                <div
                                    key={task.id}
                                    className={`
                                        px-4 py-1 cursor-pointer truncate text-sm flex items-center
                                        gap-2 relative z-50
                                        ${isSelected ? 'bg-primary/15' : 'hover:bg-primary/15'}
                                    `}
                                    onClick={(event) => {
                                        event.stopPropagation();

                                        handleEntitySelect(task)
                                    }}
                                >
                                    <span className="text-muted-foreground/50 text-xs">{task.identifier}</span>
                                    <span className="flex-1 text-xs">{task.title}</span>
                                    {isInContext && (
                                        <Check className="h-4 w-4 text-primary shrink-0" />
                                    )}
                                </div>
                            );
                        })}
                    </>
                </div>
            )}
        </div >

    );
};

export default ContextSelection;

