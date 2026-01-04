/**
 * Main canvas component for visualizing strategic entities using React Flow.
 * Renders Pillars → Outcomes → Themes → Initiatives as connected nodes.
 * Read-only with pan/zoom navigation enabled.
 */

import { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  NodeTypes,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  StrategyFlowCanvasProps,
  EntityType,
  PillarNodeData,
  OutcomeNodeData,
  ThemeNodeData,
  InitiativeNodeData,
} from './types';
import { EDGE_STYLE } from './nodes/nodeStyles';
import { computeInitiativeGridLayout } from './utils/initiativeGridLayout';
import VisionNode from './nodes/VisionNode';
import PillarNode from './nodes/PillarNode';
import OutcomeNode from './nodes/OutcomeNode';
import ThemeNode from './nodes/ThemeNode';
import InitiativeNode from './nodes/InitiativeNode';

/**
 * Custom node types registry for React Flow.
 */
const nodeTypes: NodeTypes = {
  vision: VisionNode,
  pillar: PillarNode,
  outcome: OutcomeNode,
  theme: ThemeNode,
  initiative: InitiativeNode,
};

/**
 * Default edge options for consistent styling.
 */
const defaultEdgeOptions = {
  type: 'smoothstep',
  style: EDGE_STYLE,
  animated: false,
};

/**
 * Build React Flow nodes and edges from strategic entities.
 * @param props - Strategic entity data
 * @returns Object containing nodes and edges arrays with dagre-computed positions
 */
function buildFlowData(props: StrategyFlowCanvasProps): {
  nodes: Node[];
  edges: Edge[];
} {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Create vision node as root (if provided)
  if (props.vision) {
    nodes.push({
      id: 'vision',
      type: 'vision',
      position: { x: 0, y: 0 },
      data: { ...props.vision },
    });
  }

  // Create pillar nodes
  props.pillars.forEach((pillar) => {
    nodes.push({
      id: pillar.identifier,
      type: 'pillar',
      position: { x: 0, y: 0 },
      data: { ...pillar },
    });

    // Create edge from vision to pillar (if vision exists)
    if (props.vision) {
      edges.push({
        id: `vision-${pillar.identifier}`,
        source: 'vision',
        target: pillar.identifier,
      });
    }
  });

  // Create outcome nodes and edges from pillars
  props.outcomes.forEach((outcome) => {
    nodes.push({
      id: outcome.identifier,
      type: 'outcome',
      position: { x: 0, y: 0 },
      data: { ...outcome },
    });

    // Create edges from each linked pillar to this outcome
    outcome.pillar_identifiers.forEach((pillarId) => {
      edges.push({
        id: `${pillarId}-${outcome.identifier}`,
        source: pillarId,
        target: outcome.identifier,
      });
    });
  });

  // Create theme nodes and edges from outcomes
  props.themes.forEach((theme) => {
    nodes.push({
      id: theme.identifier,
      type: 'theme',
      position: { x: 0, y: 0 },
      data: { ...theme },
    });

    // Create edges from each linked outcome to this theme
    theme.outcome_identifiers.forEach((outcomeId) => {
      edges.push({
        id: `${outcomeId}-${theme.identifier}`,
        source: outcomeId,
        target: theme.identifier,
      });
    });
  });

  // Create initiative nodes and edges from themes
  props.initiatives.forEach((initiative) => {
    nodes.push({
      id: initiative.identifier,
      type: 'initiative',
      position: { x: 0, y: 0 },
      data: { ...initiative },
    });

    // Create edge from linked theme to this initiative
    if (initiative.theme_identifier) {
      edges.push({
        id: `${initiative.theme_identifier}-${initiative.identifier}`,
        source: initiative.theme_identifier,
        target: initiative.identifier,
      });
    }
  });

  // Compute positions using initiative grid layout
  // Uses dagre for upper tiers, grid layout for initiatives
  return computeInitiativeGridLayout(nodes, edges);
}

/**
 * Strategy Flow Canvas component.
 * Renders strategic entities as an interactive, read-only graph visualization.
 *
 * @param props - Strategic entity data and optional click handler
 * @returns React Flow canvas with custom nodes and edges
 */
const StrategyFlowCanvas: React.FC<StrategyFlowCanvasProps> = (props) => {
  const { vision, pillars, outcomes, themes, initiatives, onNodeClick } = props;

  // Memoize flow data to avoid recalculation on every render
  const { nodes, edges } = useMemo(
    () => buildFlowData({ vision, pillars, outcomes, themes, initiatives }),
    [vision, pillars, outcomes, themes, initiatives]
  );

  // Handle node click events
  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      if (onNodeClick) {
        onNodeClick(node.id, node.type as EntityType);
      }
    },
    [onNodeClick]
  );

  // Empty state
  if (
    !vision &&
    pillars.length === 0 &&
    outcomes.length === 0 &&
    themes.length === 0 &&
    initiatives.length === 0
  ) {
    return (
      <div className="flex items-center justify-center h-full bg-background text-muted-foreground">
        <div className="text-center">
          <p className="text-lg font-medium">No strategic entities to display</p>
          <p className="text-sm mt-2">
            Add pillars, outcomes, themes, or initiatives to see them here.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        onNodeClick={handleNodeClick}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={true}
        panOnDrag={true}
        zoomOnScroll={true}
        zoomOnPinch={true}
        fitView
        fitViewOptions={{
          padding: 0.2,
          minZoom: 0.5,
          maxZoom: 1.5,
        }}
        minZoom={0.25}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          className="!bg-background"
        />
        <Controls
          showZoom={true}
          showFitView={true}
          showInteractive={false}
          className="!bg-card !border-border !shadow-md"
        />
        <MiniMap
          nodeStrokeWidth={3}
          pannable={true}
          zoomable={true}
          className="!bg-card !border-border"
          maskColor="hsl(var(--background) / 0.7)"
          style={{
            width: 150,
            height: 100,
          }}
        />
      </ReactFlow>
    </div>
  );
};

export default StrategyFlowCanvas;
