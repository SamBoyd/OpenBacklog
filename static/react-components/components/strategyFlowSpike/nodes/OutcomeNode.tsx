/**
 * Custom React Flow node for product outcomes.
 * Displays outcome identifier, name, and description with Target icon.
 * Has target handle on left (from pillars) and source handle on right (to themes).
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Target } from 'lucide-react';
import { OutcomeNodeData } from '../types';
import { NODE_COLORS, LAYOUT } from './nodeStyles';

interface OutcomeNodeProps {
  data: OutcomeNodeData;
}

/**
 * Custom node component for product outcomes.
 * @param props - React Flow node props with outcome data
 * @returns Styled outcome node with target and source handles
 */
const OutcomeNode = memo(({ data }: OutcomeNodeProps) => {
  const colors = NODE_COLORS.outcome;

  return (
    <div
      className={`${colors.background} ${colors.border} border rounded-lg p-3`}
      style={{ width: LAYOUT.NODE_WIDTH }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-success !w-2 !h-2 !border-0"
      />
      <div className="flex items-start gap-2">
        <div className={`p-1.5 rounded ${colors.identifierBg} flex-shrink-0`}>
          <Target className={`w-4 h-4 ${colors.iconColor}`} />
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
        className="!bg-success !w-2 !h-2 !border-0"
      />
    </div>
  );
});

OutcomeNode.displayName = 'OutcomeNode';

export default OutcomeNode;
