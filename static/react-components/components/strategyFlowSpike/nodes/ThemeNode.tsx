/**
 * Custom React Flow node for roadmap themes.
 * Displays theme identifier, name, and description with BookOpen icon.
 * Has target handle on left (from outcomes) and source handle on right (to initiatives).
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { BookOpen } from 'lucide-react';
import { ThemeNodeData } from '../types';
import { NODE_COLORS, LAYOUT } from './nodeStyles';

interface ThemeNodeProps {
  data: ThemeNodeData;
}

/**
 * Custom node component for roadmap themes.
 * @param props - React Flow node props with theme data
 * @returns Styled theme node with target and source handles
 */
const ThemeNode = memo(({ data }: ThemeNodeProps) => {
  const colors = NODE_COLORS.theme;

  return (
    <div
      className={`${colors.background} ${colors.border} border rounded-lg p-3`}
      style={{ width: LAYOUT.NODE_WIDTH }}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!bg-accent !w-2 !h-2 !border-0"
      />
      <div className="flex items-start gap-2">
        <div className={`p-1.5 rounded ${colors.identifierBg} flex-shrink-0`}>
          <BookOpen className={`w-4 h-4 ${colors.iconColor}`} />
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
        position={Position.Right}
        className="!bg-accent !w-2 !h-2 !border-0"
      />
    </div>
  );
});

ThemeNode.displayName = 'ThemeNode';

export default ThemeNode;
