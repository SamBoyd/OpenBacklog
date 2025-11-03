import React, { useRef, useState } from 'react';
import { Link } from 'react-router';
import { MdOutlineViewKanban, MdViewHeadline } from 'react-icons/md';

import StatusFilter from '#components/StatusFilter';
import ThemeFilter from '#components/ThemeFilter';
import { Button } from '#components/reusable/Button';
import Card from '#components/reusable/Card';
import { InitiativeStatus } from '#types';
import { ThemeDto } from '#api/productStrategy';
import WorkspaceSwitcher from './WorkspaceSwitcher';
import { useContainerWidth } from '#hooks/useContainerWidth';

interface InitiativesTopBarProps {
  showListView: boolean;
  showToggleView?: boolean;
  showFilterView?: boolean;
  selectedStatuses: InitiativeStatus[];
  availableStatuses: InitiativeStatus[];
  prioritizedThemes: ThemeDto[];
  unprioritizedThemes: ThemeDto[];
  selectedThemeIds: string[];
  onToggleView: () => void;
  onStatusToggle: (status: InitiativeStatus) => void;
  onThemeToggle: (themeId: string) => void;
  onCreateInitiative: () => void;
  withBottomBorder: boolean;
}

/**
 * Presentational component for the Initiatives page top bar
 * 
 * @param props The component properties
 * @returns A React component
 */
const InitiativesTopBar: React.FC<InitiativesTopBarProps> = ({
  showListView,
  showToggleView = true,
  showFilterView = true,
  selectedStatuses,
  availableStatuses,
  prioritizedThemes,
  unprioritizedThemes,
  selectedThemeIds,
  onToggleView,
  onStatusToggle,
  onThemeToggle,
  onCreateInitiative,
  withBottomBorder,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { isNarrow } = useContainerWidth(containerRef, 600);

  // Manage filter visibility state internally
  const [isStatusFilterOpen, setIsStatusFilterOpen] = useState(false);
  const [isThemeFilterOpen, setIsThemeFilterOpen] = useState(false);

  const handleStatusToggle = (status: string) => {
    onStatusToggle(status as InitiativeStatus);
  };

  const handleThemeToggle = (themeId: string) => {
    onThemeToggle(themeId);
  };

  return (
    <div ref={containerRef}>
      <Card 
        className={`
          relative border-t border-x border-border rounded-b-none flex gap-2 justify-between items-center p-4
          bg-background
          ${withBottomBorder ? 'border-b' : ''}
        `}
      >
      <WorkspaceSwitcher workspaceLimit={1} />

      <div className="flex items-center gap-x-2">
        {showToggleView && (
          <Button
            id="switch-task-view"
            data-testid="switch-task-view"
            onClick={onToggleView}
            title={showListView ? "Switch to Kanban View" : "Switch to List View"}
          >
            {!showListView ? (
              <MdOutlineViewKanban stroke='1' size='24' />
            ) : (
              <MdViewHeadline stroke='1' size='24' />
            )}
          </Button>
        )}

        {showFilterView && (
          <>
            {/* Theme Filter */}
            <div className="relative">
              <Button
                onClick={() => setIsThemeFilterOpen(!isThemeFilterOpen)}
                data-testid="theme-filter-button"
                aria-expanded={isThemeFilterOpen}
                aria-controls="theme-filter-popover"
                title="Filter by theme"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5"
                  stroke="currentColor" className="size-6">
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M9.568 3H5.25A2.25 2.25 0 0 0 3 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 0 0 5.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 0 0 9.568 3Z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6Z" />
                </svg> {!isNarrow && 'Theme'}
              </Button>
              {isThemeFilterOpen && (
                <div id="theme-filter-popover">
                  <ThemeFilter
                    prioritizedThemes={prioritizedThemes}
                    unprioritizedThemes={unprioritizedThemes}
                    selectedThemeIds={selectedThemeIds}
                    onThemeToggle={handleThemeToggle}
                    onClose={() => setIsThemeFilterOpen(false)}
                  />
                </div>
              )}
            </div>

            {/* Status Filter */}
            <div className="relative">
              <Button
                onClick={() => setIsStatusFilterOpen(!isStatusFilterOpen)}
                data-testid="status-filter-button"
                aria-expanded={isStatusFilterOpen}
                aria-controls="status-filter-popover"
                title="Filter by status"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5"
                  stroke="currentColor" className="size-6">
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 0 1-.659 1.591l-5.432 5.432a2.25 2.25 0 0 0-.659 1.591v2.927a2.25 2.25 0 0 1-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 0 0-.659-1.591L3.659 7.409A2.25 2.25 0 0 1 3 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0 1 12 3Z" />
                </svg> {!isNarrow && 'Status'}
              </Button>
              {isStatusFilterOpen && (
                <div id="status-filter-popover">
                  <StatusFilter
                    availableStatuses={availableStatuses}
                    selectedStatuses={selectedStatuses}
                    onStatusToggle={handleStatusToggle}
                    onClose={() => setIsStatusFilterOpen(false)}
                  />
                </div>
              )}
            </div>
          </>
        )}

        <Button
          onClick={onCreateInitiative}
          className="gap-x-1.5 px-2.5 py-1.5"
          title="Create initiative"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5"
            stroke="currentColor" className="size-6">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg> {!isNarrow && 'Create initiative'}
        </Button>
      </div>
    </Card>
    </div>
  );
};

export default InitiativesTopBar;
