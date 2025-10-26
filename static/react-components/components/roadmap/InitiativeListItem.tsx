import React from 'react';
import { StrategicInitiativeDto } from '#types';

export interface InitiativeListItemProps {
  strategicInitiative: StrategicInitiativeDto;
}

/**
 * Read-only display component for a strategic initiative in a list
 * Shows initiative identifier and title for context
 * @param {InitiativeListItemProps} props - Component props
 * @returns {React.ReactElement} The initiative list item
 */
const InitiativeListItem: React.FC<InitiativeListItemProps> = ({ strategicInitiative }) => {
  const initiative = strategicInitiative.initiative;

  if (!initiative) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 py-1 px-2 rounded hover:bg-muted/50 transition-colors">
      <span className="text-xs font-mono text-muted-foreground">
        {initiative.identifier}
      </span>
      <span className="text-sm text-foreground truncate">
        {initiative.title}
      </span>
    </div>
  );
};

export default InitiativeListItem;
