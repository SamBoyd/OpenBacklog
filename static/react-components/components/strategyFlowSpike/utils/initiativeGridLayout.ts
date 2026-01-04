/**
 * Grid layout utility for initiatives.
 * Arranges initiatives in vertical columns under each theme,
 * with edges connecting initiatives vertically within each column.
 */

import dagre from '@dagrejs/dagre';
import { Node, Edge } from '@xyflow/react';
import { LAYOUT } from '../nodes/nodeStyles';

/**
 * Configuration for the initiative grid layout.
 */
export interface InitiativeGridLayoutOptions {
  /** Maximum number of initiatives per column before wrapping to next column */
  maxPerColumn?: number;
  /** Horizontal gap between columns within a theme */
  columnGap?: number;
  /** Vertical gap between initiatives in a column */
  rowGap?: number;
  /** Node separation for dagre (upper tiers) */
  nodesep?: number;
  /** Rank separation for dagre (upper tiers) */
  ranksep?: number;
}

const DEFAULT_OPTIONS: Required<InitiativeGridLayoutOptions> = {
  maxPerColumn: 4,
  columnGap: 40,
  rowGap: 20,
  nodesep: 50,
  ranksep: 150,
};

/**
 * Initiative card dimensions (smaller than standard nodes).
 */
const INITIATIVE_WIDTH = 200;
const INITIATIVE_HEIGHT = 80;

/**
 * Compute layout with grid-based initiative positioning.
 * Uses dagre for upper tiers (vision → pillars → outcomes → themes)
 * and custom grid layout for initiatives under each theme.
 *
 * @param nodes - All React Flow nodes
 * @param edges - All React Flow edges (will be modified to add vertical chains)
 * @param options - Layout configuration
 * @returns Object with positioned nodes and updated edges
 */
export function computeInitiativeGridLayout(
  nodes: Node[],
  edges: Edge[],
  options: InitiativeGridLayoutOptions = {}
): { nodes: Node[]; edges: Edge[] } {
  const config = { ...DEFAULT_OPTIONS, ...options };

  // Separate initiative nodes from upper tier nodes
  const upperTierNodes = nodes.filter((n) => n.type !== 'initiative');
  const initiativeNodes = nodes.filter((n) => n.type === 'initiative');

  // Build map of theme -> initiatives
  const themeInitiativesMap = new Map<string, Node[]>();
  initiativeNodes.forEach((initiative) => {
    const themeId = initiative.data.theme_identifier as string | null;
    if (themeId) {
      const existing = themeInitiativesMap.get(themeId) || [];
      existing.push(initiative);
      themeInitiativesMap.set(themeId, existing);
    }
  });

  // Find edges that connect themes to initiatives (we'll replace these)
  const themeToInitiativeEdges = edges.filter((e) =>
    initiativeNodes.some((n) => n.id === e.target)
  );
  const upperTierEdges = edges.filter(
    (e) => !initiativeNodes.some((n) => n.id === e.target)
  );

  // Use dagre to layout upper tiers only
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({
    rankdir: 'TB',
    nodesep: config.nodesep,
    ranksep: config.ranksep,
    ranker: 'tight-tree',
  });

  upperTierNodes.forEach((node) => {
    const width = node.type === 'vision' ? LAYOUT.NODE_WIDTH * 2 + 40 : LAYOUT.NODE_WIDTH;
    const height = node.type === 'vision' ? LAYOUT.NODE_HEIGHT + 20 : LAYOUT.NODE_HEIGHT;
    g.setNode(node.id, { width, height });
  });

  upperTierEdges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  dagre.layout(g);

  // Position upper tier nodes
  const positionedUpperNodes = upperTierNodes.map((node) => {
    const dagreNode = g.node(node.id);
    return {
      ...node,
      position: {
        x: dagreNode.x - dagreNode.width / 2,
        y: dagreNode.y - dagreNode.height / 2,
      },
    };
  });

  // Now position initiatives in grids under each theme
  const positionedInitiatives: Node[] = [];
  const newEdges: Edge[] = [...upperTierEdges];

  // Find theme nodes to get their positions
  const themePositions = new Map<string, { x: number; y: number; width: number }>();
  positionedUpperNodes
    .filter((n) => n.type === 'theme')
    .forEach((theme) => {
      themePositions.set(theme.id, {
        x: theme.position.x,
        y: theme.position.y,
        width: LAYOUT.NODE_WIDTH,
      });
    });

  // Calculate the bottom Y of theme tier (for placing initiatives below)
  const themeBottomY = Math.max(
    ...positionedUpperNodes
      .filter((n) => n.type === 'theme')
      .map((n) => n.position.y + LAYOUT.NODE_HEIGHT)
  );

  // Position initiatives for each theme
  themeInitiativesMap.forEach((initiatives, themeId) => {
    const themePos = themePositions.get(themeId);
    if (!themePos) return;

    // Split initiatives into columns
    const numColumns = Math.ceil(initiatives.length / config.maxPerColumn);
    const columns: Node[][] = Array.from({ length: numColumns }, () => []);

    initiatives.forEach((initiative, index) => {
      const columnIndex = Math.floor(index / config.maxPerColumn);
      columns[columnIndex].push(initiative);
    });

    // Calculate total width of all columns for this theme
    const totalColumnsWidth =
      numColumns * INITIATIVE_WIDTH + (numColumns - 1) * config.columnGap;

    // Start X position (center columns under theme)
    const startX = themePos.x + themePos.width / 2 - totalColumnsWidth / 2;

    // Position each column
    columns.forEach((column, colIndex) => {
      const columnX = startX + colIndex * (INITIATIVE_WIDTH + config.columnGap);

      column.forEach((initiative, rowIndex) => {
        const y = themeBottomY + config.ranksep + rowIndex * (INITIATIVE_HEIGHT + config.rowGap);

        positionedInitiatives.push({
          ...initiative,
          position: { x: columnX, y },
        });

        // Create edges
        if (rowIndex === 0) {
          // First in column connects to theme
          newEdges.push({
            id: `${themeId}-${initiative.id}`,
            source: themeId,
            target: initiative.id,
          });
        } else {
          // Connect to previous initiative in column
          const prevInitiative = column[rowIndex - 1];
          newEdges.push({
            id: `${prevInitiative.id}-${initiative.id}`,
            source: prevInitiative.id,
            target: initiative.id,
          });
        }
      });
    });
  });

  // Handle initiatives without a theme (orphans)
  const orphanInitiatives = initiativeNodes.filter(
    (n) => !n.data.theme_identifier
  );
  // Position orphans at the far right
  if (orphanInitiatives.length > 0) {
    const maxX = Math.max(
      ...positionedUpperNodes.map((n) => n.position.x + LAYOUT.NODE_WIDTH),
      ...positionedInitiatives.map((n) => n.position.x + INITIATIVE_WIDTH)
    );

    orphanInitiatives.forEach((initiative, index) => {
      const rowIndex = index % config.maxPerColumn;
      const colIndex = Math.floor(index / config.maxPerColumn);

      positionedInitiatives.push({
        ...initiative,
        position: {
          x: maxX + 100 + colIndex * (INITIATIVE_WIDTH + config.columnGap),
          y: themeBottomY + config.ranksep + rowIndex * (INITIATIVE_HEIGHT + config.rowGap),
        },
      });
    });
  }

  return {
    nodes: [...positionedUpperNodes, ...positionedInitiatives],
    edges: newEdges,
  };
}

