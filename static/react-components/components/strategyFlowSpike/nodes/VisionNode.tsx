/**
 * Custom React Flow node for product vision.
 * Displays vision name and description with Star icon.
 * Has a source handle on the bottom for connecting to pillars.
 */

import { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import { Star } from 'lucide-react';
import { VisionNodeData } from '../types';
import { NODE_COLORS, LAYOUT } from './nodeStyles';

interface VisionNodeProps {
  data: VisionNodeData;
}

/**
 * Custom node component for product vision.
 * @param props - React Flow node props with vision data
 * @returns Styled vision node with source handle
 */
const VisionNode = memo(({ data }: VisionNodeProps) => {
  const colors = NODE_COLORS.vision;

  return (
    <div
      className={`${colors.background} ${colors.border} border-2 rounded-lg p-4`}
      style={{ width: (LAYOUT.NODE_WIDTH * 2) + 40, minHeight: LAYOUT.NODE_HEIGHT + 20 }}
    >
      <div className="flex items-start gap-3">
        <div className={`p-2 rounded-lg ${colors.identifierBg} flex-shrink-0`}>
          <Star className={`w-5 h-5 ${colors.iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-base font-semibold text-foreground mb-1">
            {data.name}
          </h2>
          <p className="text-sm text-muted-foreground line-clamp-3">
            {data.description}
          </p>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="!bg-secondary !w-2.5 !h-2.5 !border-0"
      />
    </div>
  );
});

VisionNode.displayName = 'VisionNode';

export default VisionNode;

