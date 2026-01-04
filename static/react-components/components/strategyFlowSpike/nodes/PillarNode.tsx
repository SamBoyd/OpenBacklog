/**
 * Custom React Flow node for strategic pillars.
 * Displays pillar identifier, name, and description with Compass icon.
 * Has a source handle on the right for connecting to outcomes.
 */

import { memo, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Compass } from 'lucide-react';
import { PillarNodeData } from '../types';
import { NODE_COLORS, LAYOUT } from './nodeStyles';

interface PillarNodeProps {
  data: PillarNodeData;
}

/**
 * Custom node component for strategic pillars.
 * @param props - React Flow node props with pillar data
 * @returns Styled pillar node with source handle
 */
const PillarNode = memo(({ data }: PillarNodeProps) => {
  const colors = NODE_COLORS.pillar;

  return (
    <div
      className={`${colors.background} ${colors.border} border rounded-lg p-3`}
      style={{ width: LAYOUT.NODE_WIDTH }}
    >
      <div className="flex items-start gap-2">
        <div className={`p-1.5 rounded ${colors.identifierBg} flex-shrink-0`}>
          <Compass className={`w-4 h-4 ${colors.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-xs font-mono px-1.5 py-0.5 rounded ${colors.identifierBg} ${colors.iconColor}`}
            >
              {data.identifier}
            </span>
          </div>
          <h3 className="text-sm font-medium text-foreground truncate">
            {data.name}
          </h3>
          <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
            {data.description}
          </p>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-primary !w-2 !h-2 !border-0"
      />
    </div>
  );
});

PillarNode.displayName = 'PillarNode';

export default PillarNode;
