/**
 * Custom React Flow node for strategic initiatives.
 * Displays initiative identifier, title, and status badge with Zap icon.
 * Compact card design for grid layout with vertical chaining.
 * Has target handle on top (from theme or previous initiative) and
 * source handle on bottom (to next initiative in chain).
 */

import { memo, useState, useCallback } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Zap, ArrowRight } from 'lucide-react';
import { InitiativeNodeData } from '../types';
import { NODE_COLORS, STATUS_STYLES } from './nodeStyles';

/**
 * Width constants for initiative cards.
 * Compact width for default grid layout, expanded width for detail view.
 */
const COMPACT_WIDTH = 200;
const EXPANDED_WIDTH = 280;

interface InitiativeNodeProps {
  data: InitiativeNodeData;
}

/**
 * Custom node component for strategic initiatives.
 * Clickable card that expands to show full title and description.
 * @param props - React Flow node props with initiative data
 * @returns Styled initiative node with top/bottom handles, expandable on click
 */
const InitiativeNode = memo(({ data }: InitiativeNodeProps) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const colors = NODE_COLORS.initiative;
  const statusStyle = STATUS_STYLES[data.status] || STATUS_STYLES.BACKLOG;

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setIsExpanded((prev) => !prev);
  }, []);

  const handleNavigate = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (data.onNavigate) {
        data.onNavigate();
      }
    },
    [data.onNavigate]
  );

  return (
    <div
      onClick={handleClick}
      className={`${colors.background} ${colors.border} border rounded-lg p-2 cursor-pointer transition-all duration-200 ease-in-out hover:shadow-md`}
      style={{ width: isExpanded ? EXPANDED_WIDTH : COMPACT_WIDTH }}
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
          <h3
            className={`text-xs font-medium text-foreground ${!isExpanded && 'truncate'}`}
          >
            {data.title}
          </h3>
          {isExpanded && data.description && (
            <p className="text-[10px] text-muted-foreground mt-1.5 line-clamp-3">
              {data.description}
            </p>
          )}
          {isExpanded && (
            <button
              onClick={handleNavigate}
              className="mt-2 flex items-center gap-1 text-[10px] text-primary hover:text-primary/80 font-medium transition-colors"
            >
              View details
              <ArrowRight className="w-3 h-3" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
});

InitiativeNode.displayName = 'InitiativeNode';

export default InitiativeNode;
