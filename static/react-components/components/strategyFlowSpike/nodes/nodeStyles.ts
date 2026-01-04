/**
 * Shared styling constants and layout utilities for strategy flow nodes.
 * Uses Tailwind theme tokens for consistent theming.
 */

import { EntityType } from '../types';

/**
 * Color configuration for each entity type.
 * Uses Tailwind CSS classes for consistent theming.
 */
export const NODE_COLORS: Record<
  EntityType,
  {
    background: string;
    border: string;
    iconColor: string;
    identifierBg: string;
  }
> = {
  vision: {
    background: 'bg-secondary/90',
    border: 'border-secondary/50',
    iconColor: 'text-secondary-foreground',
    identifierBg: 'bg-secondary/30',
  },
  pillar: {
    background: 'bg-primary/10',
    border: 'border-primary/30',
    iconColor: 'text-primary',
    identifierBg: 'bg-primary/20',
  },
  outcome: {
    background: 'bg-success/10',
    border: 'border-success/30',
    iconColor: 'text-success',
    identifierBg: 'bg-success/20',
  },
  theme: {
    background: 'bg-accent/10',
    border: 'border-accent/30',
    iconColor: 'text-accent',
    identifierBg: 'bg-accent/20',
  },
  initiative: {
    background: 'bg-muted/10',
    border: 'border-border',
    iconColor: 'text-muted-foreground',
    identifierBg: 'bg-muted-foreground/20',
  },
};

/**
 * Layout constants for node positioning.
 */
export const LAYOUT = {
  NODE_WIDTH: 280,
  NODE_HEIGHT: 100,
  COLUMN_GAP: 350,
  ROW_GAP: 130,
  PADDING_LEFT: 50,
  PADDING_TOP: 50,
};


/**
 * Status badge styling for initiative nodes.
 */
export const STATUS_STYLES: Record<
  string,
  { background: string; text: string }
> = {
  BACKLOG: {
    background: 'bg-muted-foreground/20',
    text: 'text-muted-foreground',
  },
  TO_DO: {
    background: 'bg-muted-foreground/20',
    text: 'text-status-todo',
  },
  IN_PROGRESS: {
    background: 'bg-muted-foreground/20',
    text: 'text-status-in-progress',
  },
  DONE: {
    background: 'bg-muted-foreground/20',
    text: 'text-status-done',
  },
};

/**
 * Edge styling for React Flow edges.
 */
export const EDGE_STYLE = {
  stroke: 'hsl(var(--border))',
  strokeWidth: 1.5,
};
