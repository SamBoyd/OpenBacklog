/**
 * Dagre layout utility for automatic tree positioning.
 * Computes hierarchical top-to-bottom layout for strategic entities.
 */

import dagre from '@dagrejs/dagre';
import { Node, Edge } from '@xyflow/react';
import { LAYOUT } from '../nodes/nodeStyles';

/**
 * Options for dagre layout configuration.
 */
interface DagreLayoutOptions {
  rankdir?: 'TB' | 'BT' | 'LR' | 'RL';
  nodesep?: number;
  ranksep?: number;
  ranker?: 'network-simplex' | 'tight-tree' | 'longest-path';
}

/**
 * Default layout options optimized for tree structures.
 */
const DEFAULT_OPTIONS: Required<DagreLayoutOptions> = {
  rankdir: 'TB',
  nodesep: 50,
  ranksep: 150,
  ranker: 'tight-tree',
};

/**
 * Compute node positions using dagre layout algorithm.
 * @param nodes - React Flow nodes with initial positions
 * @param edges - React Flow edges connecting nodes
 * @param options - Optional dagre layout configuration
 * @returns Nodes with computed x,y positions
 */
export function computeDagreLayout(
  nodes: Node[],
  edges: Edge[],
  options: DagreLayoutOptions = {}
): Node[] {
  const config = { ...DEFAULT_OPTIONS, ...options };

  // Create a new directed graph
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));

  // Set graph layout options
  g.setGraph({
    rankdir: config.rankdir,
    nodesep: config.nodesep,
    ranksep: config.ranksep,
    ranker: config.ranker,
  });

  // Add nodes to dagre graph with their dimensions
  nodes.forEach((node) => {
    // Use node width/height from LAYOUT constants
    // Vision nodes are slightly larger
    const width = node.type === 'vision' ? (LAYOUT.NODE_WIDTH * 2) + 40 : LAYOUT.NODE_WIDTH;
    const height = node.type === 'vision' ? LAYOUT.NODE_HEIGHT + 20 : LAYOUT.NODE_HEIGHT;

    g.setNode(node.id, {
      width,
      height,
    });
  });

  // Add edges to dagre graph
  edges.forEach((edge) => {
    g.setEdge(edge.source, edge.target);
  });

  // Run dagre layout algorithm
  dagre.layout(g);

  // Update node positions with computed coordinates
  return nodes.map((node) => {
    const dagreNode = g.node(node.id);
    return {
      ...node,
      position: {
        x: dagreNode.x - (dagreNode.width / 2),
        y: dagreNode.y - (dagreNode.height / 2),
      },
    };
  });
}

