import React from 'react';

export type SkeletonType = 'text' | 'image' | 'paragraph';

interface SkeletonProps {
  type: SkeletonType;
  width?: string;
  height?: string;
  className?: string;
  animated?: boolean;
}

/**
 * A customizable skeleton loading component with support for different content types.
 * @param {object} props - The component props
 * @param {SkeletonType} props.type - The skeleton type: 'text', 'image', or 'paragraph'
 * @param {string} [props.width] - Custom width (overrides type defaults)
 * @param {string} [props.height] - Custom height (overrides type defaults)
 * @param {string} [props.className] - Additional CSS classes
 * @param {boolean} [props.animated=true] - Whether to animate with pulse effect
 * @returns {React.ReactElement} The skeleton component
 */
export const Skeleton: React.FC<SkeletonProps> = ({
  type,
  width,
  height,
  className = '',
  animated = true,
}) => {
  const getTypeClasses = () => {
    const pulseClass = animated ? ' animate-pulse' : '';
    switch (type) {
      case 'text':
        return `my-1 h-4 bg-muted/20 rounded-full${pulseClass}`;
      case 'image':
        return `my-1 bg-muted/20 rounded-full${pulseClass} aspect-square`;
      case 'paragraph':
        return '';
      default:
        return `my-1 h-4 bg-muted/20 rounded-full${pulseClass}`;
    }
  };

  const getDefaultDimensions = () => {
    switch (type) {
      case 'text':
        return { width: width || 'w-full', height: height || '' };
      case 'image':
        return { width: width || 'w-12', height: height || 'h-12' };
      case 'paragraph':
        return { width: '', height: '' };
      default:
        return { width: width || 'w-full', height: height || '' };
    }
  };

  if (type === 'paragraph') {
    const pulseClass = animated ? ' animate-pulse' : '';
    return (
      <div className={`my-1 space-y-2 ${className}`} role="status" aria-label="Loading...">
        <div className={`h-4 bg-muted/20 rounded-full${pulseClass} w-3/4`}></div>
        <div className={`h-4 bg-muted/20 rounded-full${pulseClass} w-full`}></div>
        <div className={`h-4 bg-muted/20 rounded-full${pulseClass} w-5/6`}></div>
        <div className={`h-4 bg-muted/20 rounded-full${pulseClass} w-4/5`}></div>
        <div className={`h-4 bg-muted/20 rounded-full${pulseClass} w-full`}></div>
        <span className="sr-only">Loading...</span>
      </div>
    );
  }

  const dimensions = getDefaultDimensions();
  const typeClasses = getTypeClasses();

  return (
    <div
      className={`${typeClasses} ${dimensions.width} ${dimensions.height} ${className}`}
      role="status"
      aria-label="Loading..."
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
};