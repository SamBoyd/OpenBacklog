/**
 * Custom React Flow node for strategic initiatives.
 * Displays initiative identifier, title, and status badge with Zap icon.
 * Compact card design for grid layout with vertical chaining.
 * Has target handle on top (from theme or previous initiative) and
 * source handle on bottom (to next initiative in chain).
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Zap } from 'lucide-react';
import { InitiativeNodeData } from '../types';
import { NODE_COLORS, STATUS_STYLES } from './nodeStyles';

/**
 * Compact width for initiative cards in grid layout.
 */
const INITIATIVE_CARD_WIDTH = 200;

interface InitiativeNodeProps {
  data: InitiativeNodeData;
}

/**
 * Custom node component for strategic initiatives.
 * Compact design for vertical column layout under themes.
 * @param props - React Flow node props with initiative data
 * @returns Styled initiative node with top/bottom handles and status badge
 */
const InitiativeNode = memo(({ data }: InitiativeNodeProps) => {
  const colors = NODE_COLORS.initiative;
  const statusStyle = STATUS_STYLES[data.status] || STATUS_STYLES.BACKLOG;

  return (
    <div
      className={`${colors.background} ${colors.border} border rounded-lg p-2`}
      style={{ width: INITIATIVE_CARD_WIDTH }}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="!bg-muted-foreground !w-2 !h-2 !border-0"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-muted-foreground !w-2 !h-2 !border-0"
      />
      <div className="flex items-start gap-2">
        <div className={`p-1 rounded ${colors.identifierBg} flex-shrink-0`}>
          <Zap className={`w-3 h-3 ${colors.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span
              className={`text-[10px] font-mono px-1 py-0.5 rounded ${colors.identifierBg} ${colors.iconColor}`}
            >
              {data.identifier}
            </span>
            <span
              className={`text-[10px] px-1 py-0.5 rounded ${statusStyle.background} ${statusStyle.text}`}
            >
              {(data.status || '').replace('_', ' ')}
            </span>
          </div>
          <h3 className="text-xs font-medium text-foreground truncate">
            {data.title}
          </h3>
        </div>
      </div>
    </div>
  );
});

InitiativeNode.displayName = 'InitiativeNode';

export default InitiativeNode;
