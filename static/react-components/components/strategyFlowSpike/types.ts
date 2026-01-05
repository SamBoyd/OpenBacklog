/**
 * Type definitions for the Strategy Flow Canvas spike.
 * Defines entity types, node data interfaces, and component props.
 */

/**
 * The strategic entity types displayed on the canvas.
 */
export type EntityType = 'vision' | 'pillar' | 'outcome' | 'theme' | 'initiative';

/**
 * Initiative status values for status badge display.
 */
export type InitiativeStatus = 'BACKLOG' | 'TO_DO' | 'IN_PROGRESS';

/**
 * Data for a product vision node.
 */
export interface VisionNodeData {
  name: string;
  description: string;
}

/**
 * Data for a strategic pillar node.
 */
export interface PillarNodeData {
  identifier: string;
  name: string;
  description: string;
}

/**
 * Data for a product outcome node.
 */
export interface OutcomeNodeData {
  identifier: string;
  name: string;
  description: string;
  pillar_identifiers: string[];
}

/**
 * Data for a roadmap theme node.
 */
export interface ThemeNodeData {
  identifier: string;
  name: string;
  description: string;
  outcome_identifiers: string[];
}

/**
 * Data for a strategic initiative node.
 */
export interface InitiativeNodeData {
  identifier: string;
  title: string;
  description: string;
  status: InitiativeStatus;
  theme_identifier: string | null;
  onNavigate: () => void;
}

/**
 * Props for the StrategyFlowCanvas component.
 */
export interface StrategyFlowCanvasProps {
  vision?: VisionNodeData;
  pillars: PillarNodeData[];
  outcomes: OutcomeNodeData[];
  themes: ThemeNodeData[];
  initiatives: InitiativeNodeData[];
  onNodeClick?: (id: string, type: EntityType) => void;
}

/**
 * Union type for all node data types.
 */
export type StrategyNodeData =
  | VisionNodeData
  | PillarNodeData
  | OutcomeNodeData
  | ThemeNodeData
  | InitiativeNodeData;
