import { useEffect, useState, RefObject } from 'react';

/**
 * Custom hook to track container width changes using ResizeObserver
 * Following patterns established in GroupsSelectionHeader and InitiativeFilter components
 * 
 * @param elementRef - React ref to the element to observe
 * @param breakpoint - Width threshold below which isNarrow becomes true (default: 600px)
 * @returns Object containing current width and responsive flags
 */
export const useContainerWidth = (
  elementRef: RefObject<HTMLElement>, 
  breakpoint: number = 600
) => {
  const [width, setWidth] = useState<number>(0);
  const [isNarrow, setIsNarrow] = useState<boolean>(false);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    // Initialize with current width
    const initialWidth = element.clientWidth;
    setWidth(initialWidth);
    setIsNarrow(initialWidth < breakpoint);

    // Create ResizeObserver to track width changes
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const newWidth = entry.contentRect.width;
        setWidth(newWidth);
        setIsNarrow(newWidth < breakpoint);
      }
    });

    // Start observing the element
    resizeObserver.observe(element);

    // Cleanup function
    return () => {
      resizeObserver.disconnect();
    };
  }, [breakpoint]); // Re-run if breakpoint changes

  return {
    width,
    isNarrow,
    isWide: !isNarrow,
  };
};

export default useContainerWidth;