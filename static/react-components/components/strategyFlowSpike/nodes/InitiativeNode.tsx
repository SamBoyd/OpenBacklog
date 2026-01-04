/**
 * Custom React Flow node for strategic initiatives.
 * Displays initiative identifier, title, description, and status badge with Zap icon.
 * Has target handle on left only (from themes) - initiatives are leaf nodes.
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Zap } from 'lucide-react';
import { InitiativeNodeData } from '../types';
import { NODE_COLORS, LAYOUT, STATUS_STYLES } from './nodeStyles';

interface InitiativeNodeProps {
  data: InitiativeNodeData;
}

/**
 * Custom node component for strategic initiatives.
 * @param props - React Flow node props with initiative data
 * @returns Styled initiative node with target handle and status badge
 */
const InitiativeNode = memo(({ data }: InitiativeNodeProps) => {
  const colors = NODE_COLORS.initiative;
  const statusStyle = STATUS_STYLES[data.status] || STATUS_STYLES.BACKLOG;

  return (
    <div
      className={`${colors.background} ${colors.border} border rounded-lg p-3`}
      style={{ width: LAYOUT.NODE_WIDTH }}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!bg-muted-foreground !w-2 !h-2 !border-0"
      />
      <div className="flex items-start gap-2">
        <div className={`p-1.5 rounded ${colors.identifierBg} flex-shrink-0`}>
          <Zap className={`w-4 h-4 ${colors.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-xs font-mono px-1.5 py-0.5 rounded ${colors.identifierBg} ${colors.iconColor}`}
            >
              {data.identifier}
            </span>
            <span
              className={`text-xs px-1.5 py-0.5 rounded ${statusStyle.background} ${statusStyle.text}`}
            >
              {(data.status|| '').replace('_', ' ')}
            </span>
          </div>
          <h3 className="text-sm font-medium text-foreground truncate">
            {data.title}
          </h3>
          <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
            {data.description}
          </p>
        </div>
      </div>
    </div>
  );
});

InitiativeNode.displayName = 'InitiativeNode';

export default InitiativeNode;
