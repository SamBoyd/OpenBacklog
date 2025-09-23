import React, { useState, useRef, useEffect, useCallback } from 'react';
import { GroupDto, GroupType } from '#types';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups';
import { useUserPreferences } from '#hooks/useUserPreferences';
import SelectGroups from './SelectGroups';
import CreateGroupModal from './CreateGroupModal';
import { Button, NoBorderButton } from '#components/reusable/Button';
import { Plus, PlusCircle, ChevronLeft, ChevronRight } from 'lucide-react';

const defaultGroupAll: GroupDto = {
    id: 'all-pseudo-group',
    name: 'All',
    user_id: '',
    workspace_id: '',
    description: null,
    group_type: GroupType.SMART,
    group_metadata: null,
    query_criteria: null,
    parent_group_id: null
};

const SelectedGroupBadge = ({ id, name, onClick }: { id: string, name: string, onClick: () => void }) => {
    return (
        <span className="group inline-flex items-center max-w-[120px] min-w-0 flex-shrink-0 h-3 gap-x-0.5 rounded-md bg-muted/15 px-2 py-1 text-xs font-medium text-foreground cursor-default hover:bg-muted/20">
            <span className="overflow-hidden text-ellipsis whitespace-nowrap max-w-full">
                {name}
            </span>
            <button type="button" className="relative ml-2 -mr-1 h-3 size-3.5 flex-shrink-0 rounded-sm text-muted-foreground hover:text-foreground" onClick={onClick}>
                <span className="sr-only">Remove</span>
                <svg viewBox="0 0 14 14" stroke="currentColor" strokeWidth={2}>
                    <path d="M4 4l6 6m0-6l-6 6" />
                </svg>
                <span className="absolute -inset-1" />
            </button>
        </span>
    )
}

// ScrollButton component for horizontal scrolling
interface ScrollButtonProps {
    direction: 'left' | 'right';
    containerRef: React.RefObject<HTMLDivElement>;
    showCondition: boolean;
}

const ScrollButton: React.FC<ScrollButtonProps> = ({ direction, containerRef, showCondition }) => {
    const handleScroll = () => {
        if (!containerRef.current) return;

        const scrollAmount = 150; // Adjust scroll amount as needed
        const currentScroll = containerRef.current.scrollLeft;
        const newScroll = direction === 'left'
            ? currentScroll - scrollAmount
            : currentScroll + scrollAmount;

        containerRef.current.scrollTo({
            left: newScroll,
            behavior: 'smooth'
        });
    };

    if (!showCondition) return null;

    return (
        <div
            className={`absolute z-10 ${direction === 'left' ? 'left-0' : 'right-0'} bg-gradient-to-${direction === 'left' ? 'r' : 'l'} from-background to-transparent`}
        >
            <NoBorderButton
                onClick={handleScroll}
                className="h-full text-foreground hover:text-foreground"
                aria-label={`Scroll ${direction}`}
            >
                {direction === 'left' ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
            </NoBorderButton>
        </div>
    );
};

const GroupsSelectionHeader = () => {
    const { allGroupsInWorkspace, loading, error, findGroupsByIds } = useInitiativeGroups();
    
    const { preferences, updateSelectedGroups: updateSelectedGroupsInPrefs } = useUserPreferences();

    const scrollContainerRef = useRef<HTMLDivElement>(null);

    const [canScrollLeft, setCanScrollLeft] = useState(false);
    const [canScrollRight, setCanScrollRight] = useState(false);

    // Find the groups that match the saved IDs
    const getSelectedGroups = React.useCallback((ids: string[]): GroupDto[] => {
        const groups = findGroupsByIds(ids);
        if (ids.includes(defaultGroupAll.id)) {
            return [defaultGroupAll, ...groups];
        }

        if (groups.length === 0) {
            return [defaultGroupAll];
        }

        return groups;
    }, [allGroupsInWorkspace]);

    // Initialize with saved groups or default
    const [selectedGroups, setSelectedGroups] = useState<GroupDto[]>([defaultGroupAll]);
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const allGroups = [defaultGroupAll, ...allGroupsInWorkspace];

    const handleAddRemoveClick = () => {
        setIsDropdownOpen(prev => !prev);
    };

    const handleCreateNewClick = () => {
        setIsCreateModalOpen(true);
    };

    const handleCloseCreateModal = () => {
        setIsCreateModalOpen(false);
    };

    const setSelectedGroupsFromPreferences = (selectedGroupIds: string[]) => {
        const loadedGroups = getSelectedGroups(selectedGroupIds);
        setSelectedGroups(loadedGroups);
    }

    useEffect(() => {
        if (loading) return;

        if (preferences.selectedGroupIds && selectedGroups && preferences.selectedGroupIds.length !== selectedGroups.length) {
            setSelectedGroupsFromPreferences(preferences.selectedGroupIds);
        }
    }, [preferences.selectedGroupIds, loading]);

    // Check if scroll buttons should be shown
    const checkScroll = useCallback(() => {
        if (!scrollContainerRef.current) return;

        const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current;

        // Only show left button if we're scrolled away from the start
        setCanScrollLeft(scrollLeft > 0);

        // Only show right button if there's more content to scroll to
        setCanScrollRight(scrollLeft + clientWidth < scrollWidth - 10); // 10px buffer
    }, [preferences.selectedGroupIds]);

    // Add scroll event listener to update button visibility
    useEffect(() => {
        const scrollContainer = scrollContainerRef.current;
        if (scrollContainer) {
            scrollContainer.addEventListener('scroll', checkScroll);
            // Check on initial render
            checkScroll();

            // Also check when window resizes or content changes
            window.addEventListener('resize', checkScroll);
        }

        return () => {
            if (scrollContainer) {
                scrollContainer.removeEventListener('scroll', checkScroll);
            }
            window.removeEventListener('resize', checkScroll);
        };
    }, [checkScroll]);

    // Check scroll buttons when selected groups change
    useEffect(() => {
        checkScroll();
    }, [selectedGroups, checkScroll]);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(event.target as Node)
            ) {
                setIsDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const handleGroupsChange = (newSelectedGroups: GroupDto[]) => {
        setSelectedGroups(newSelectedGroups);
        updateSelectedGroupsInPrefs(newSelectedGroups.map(group => group.id));
    }

    const handleRemoveGroup = useCallback((id: string) => {
        setSelectedGroups(prev => prev.filter(group => group.id !== id));
        updateSelectedGroupsInPrefs(selectedGroups.filter(group => group.id !== id).map(group => group.id));
    }, [selectedGroups, updateSelectedGroupsInPrefs]);

    const handleGroupCreated = useCallback((group: GroupDto) => {
        setSelectedGroups(prev => [...prev, group]);
        updateSelectedGroupsInPrefs([...selectedGroups.map(group => group.id), group.id]);
    }, [selectedGroups, updateSelectedGroupsInPrefs]);

    if (loading) return <div className="p-4 text-sm text-gray-500">Loading groups...</div>;
    if (error) return <div className="p-4 text-sm text-red-500">Error loading groups: {error}</div>;


    return (
        <>
            <div
                className="relative flex items-center justify-between px-4 border-b border-x border-border bg-background text-foreground rounded-b-md "
            >
                {/* Selected Groups List with Scroll Navigation */}
                <div className="flex items-center flex-grow mr-4 relative" style={{ maxWidth: 'calc(100% - 40px)', overflow: 'hidden' }}>
                    {/* Left scroll button - only shown when scrolled */}
                    <ScrollButton
                        direction="left"
                        containerRef={scrollContainerRef}
                        showCondition={canScrollLeft}
                    />
                    { canScrollLeft && (
                        <div className="absolute top-0 left-0 bottom-0 w-10 pointer-events-none bg-gradient-to-r from-background via-background to-transparent"> </div>
                    )}


                    <div
                        id="selected-groups-list"
                        ref={scrollContainerRef}
                        className="relative flex items-center space-x-2 w-full overflow-x-auto scrollbar-hide scroll-smooth"
                        style={{ flexShrink: 1, flexGrow: 0, width: '100%', minWidth: 0 }}
                    >
                        {selectedGroups.map((item, index) => (
                            <SelectedGroupBadge key={index} id={item.id} name={item.name} onClick={() => handleRemoveGroup(item.id)} />
                        ))}

                        {selectedGroups.length === 0 && (
                            <span className="text-muted-foreground">No groups selected</span>
                        )}

                        {/* Add/Remove Group Button */}
                        <NoBorderButton
                            useRef={buttonRef}
                            onClick={handleAddRemoveClick}
                            className="text-muted flex-shrink-0"
                        >
                            <PlusCircle size={14} />
                        </NoBorderButton>


                        {/* overlay gradient */}
                    </div>
                    
                    <div className="absolute top-0 right-0 bottom-0 w-10 pointer-events-none bg-gradient-to-l from-background via-background to-transparent"> </div>

                    {/* Right scroll button - only shown when more content is available */}
                    <ScrollButton
                        direction="right"
                        containerRef={scrollContainerRef}
                        showCondition={canScrollRight}
                    />

                </div>


                {/* Create New Group Button */}
                <div className="flex items-center flex-shrink-0 space-x-2">
                    <NoBorderButton
                        onClick={handleCreateNewClick}
                    >
                        <Plus size={16} />
                    </NoBorderButton>
                </div>

                <CreateGroupModal
                    isOpen={isCreateModalOpen}
                    onClose={handleCloseCreateModal}
                    onGroupCreated={handleGroupCreated}
                />
            </div>

            {isDropdownOpen && (
                <>
                    <div
                        ref={dropdownRef}
                        className="absolute mt-2 w-72 bg-background border border-border rounded-md shadow-lg z-10 p-4 text-foreground"
                    >
                        <SelectGroups
                            allGroups={allGroups}
                            selectedGroups={selectedGroups}
                            onGroupsChange={handleGroupsChange}
                            idPrefix="header-group-select"
                        />
                    </div>
                </>
            )}
        </>
    );
};

export default GroupsSelectionHeader;
