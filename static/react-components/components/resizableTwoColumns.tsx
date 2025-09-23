import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import '../../react-components/styles/output.css'; // Keep Tailwind styles
import AppBackground from './AppBackground';
import { ChatLayoutMode } from '#hooks/useUserPreferences';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import LayoutControls from './LayoutControls';

interface ResizableTwoColumnsProps {
    leftColumnComponent: React.ReactNode;
    rightColumnComponent: React.ReactNode;
    leftColumnMinWidth?: number; // Note: react-resizable-panels uses percentages primarily
    leftColumnMaxWidth?: number; // Note: react-resizable-panels uses percentages primarily
    leftColumnHidden?: boolean;
    layoutMode: ChatLayoutMode;
    onLayoutModeChange: (mode: ChatLayoutMode) => void;
}

// Helper to estimate percentage, adjust as needed for your layout context
const pixelsToPercentage = (pixels: number, containerWidth = 1200): number => {
    return Math.max(0, Math.min(100, (pixels / containerWidth) * 100));
};

const ResizableTwoColumns: React.FC<ResizableTwoColumnsProps> = ({
    leftColumnComponent,
    rightColumnComponent,
    leftColumnMinWidth = 208,
    leftColumnMaxWidth = 800, // Max width constraint might be harder to enforce strictly with percentages
    leftColumnHidden = false,
    layoutMode = 'normal',
    onLayoutModeChange,
}) => {
    const panelGroupRef = useRef<any>(null); // Ref for potential imperative control
    const [isHoverActive, setIsHoverActive] = useState(false);

    const minSizePercentage = pixelsToPercentage(leftColumnMinWidth);

    // Calculate panel sizes based on layout mode
    const getPanelSizes = () => {
        switch (layoutMode) {
            case 'minimized':
                return { left: 0, right: 100 };
            case 'split':
                return { left: 50, right: 50 };
            case 'maximized':
                return { left: 100, right: 0 };
            case 'normal':
            default:
                return { left: leftColumnHidden ? 0 : 30, right: leftColumnHidden ? 100 : 70 };
        }
    };

    const { left: leftSize, right: rightSize } = getPanelSizes();

    // Effect to handle layout mode changes
    useEffect(() => {
        const group = panelGroupRef.current;
        if (group && group.setLayout) {
            // Set layout programmatically when mode changes
            group.setLayout([leftSize, rightSize]);
        }
    }, [layoutMode, leftSize, rightSize]);

    // Handler for returning to normal layout from minimized/maximized states
    const handleReturnToNormal = useCallback(() => {
        if (onLayoutModeChange) {
            onLayoutModeChange('normal');
            setIsHoverActive(false);
        }
    }, [onLayoutModeChange]);


    return (
        <div className="overflow-clip bg-sidebar h-full relative">
            <div className="absolute top-2 left-2 z-50">
                <LayoutControls
                    currentMode={layoutMode}
                    onModeChange={onLayoutModeChange}
                />
            </div>
            <PanelGroup direction="horizontal" ref={panelGroupRef}>
                <Panel
                    id="left-panel"
                    order={1}
                    collapsible={true}
                    defaultSize={leftSize}
                    minSize={leftSize === 0 ? 0 : minSizePercentage}
                    className="flex-shrink-0 bg-sidebar"
                >
                    {/* Render content only if not collapsed */}
                    {leftColumnComponent}
                </Panel>

                {/* Only show resize handle in normal and split modes */}
                {layoutMode === 'normal' || layoutMode === 'split' ? (
                    <PanelResizeHandle
                        onDragging={() => onLayoutModeChange('normal')}
                        className="w-2 bg-transparent hover:bg-neutral-400/5 cursor-col-resize transition-colors duration-200 ease-in-out flex items-center justify-center"
                    >
                        <div className="w-[1px] h-4 bg-neutral-400 dark:bg-neutral-700"></div>
                    </PanelResizeHandle>
                ) : null}

                <Panel
                    id="right-panel"
                    order={2}
                    collapsible={true}
                    defaultSize={rightSize}
                    minSize={rightSize === 0 ? 0 : 10}
                    className={`
                        ${rightSize > 0 ? 'rounded-lg mr-4 mb-5 h-[calc(100vh-4rem)]' : ''} 
                    `}
                >
                    <AppBackground>
                        <div className="w-full h-full overflow-y-auto">
                            <div className="max-w-4xl mx-auto h-[calc(100vh-4rem)] flex flex-col">

                                {rightColumnComponent}
                            </div>
                        </div>
                    </AppBackground>
                </Panel>
            </PanelGroup>

            {/* Left hover zone for minimized mode */}
            {layoutMode === 'minimized' && (
                <div
                    className="absolute left-0 top-0 bottom-0 w-2 z-50 cursor-pointer"
                    onMouseEnter={() => setIsHoverActive(true)}
                    onMouseLeave={() => setIsHoverActive(false)}
                    onClick={handleReturnToNormal}
                    title="Click to restore normal layout"
                >
                    {/* Hover indicator */}
                    <div className="flex items-center justify-center h-full">
                        <div className="h-8 bg-primary/25 rounded-r-md hover:bg-primary/30 transition-colors flex items-center text-muted">
                            <ChevronRight size={18} />
                        </div>
                    </div>
                </div>
            )}

            {/* Right hover zone for maximized mode */}
            {layoutMode === 'maximized' && (
                <div
                    className="absolute right-0 top-0 bottom-0 z-50 cursor-pointer"
                    onMouseEnter={() => setIsHoverActive(true)}
                    onMouseLeave={() => setIsHoverActive(false)}
                    onClick={handleReturnToNormal}
                    title="Click to restore normal layout"
                >
                    {/* Hover indicator */}
                    <div className="flex items-center justify-center h-full">
                        <div className="h-8 bg-primary/15 rounded-l-md hover:bg-primary/30 transition-colors flex items-center text-muted">
                            <ChevronLeft size={18} />
                        </div>
                    </div>
                </div>
            )}

            {/* Temporary hover panel overlay for minimized mode */}
            {layoutMode === 'minimized' && isHoverActive && (
                <div className="absolute left-0 top-0 w-80 h-full bg-sidebar border-r border-border z-40 shadow-xl transition-all duration-300 ease-in-out">
                    {leftColumnComponent}
                </div>
            )}

            {/* Temporary hover panel overlay for maximized mode */}
            {layoutMode === 'maximized' && isHoverActive && (
                <div className="absolute right-0 top-0 w-80 h-full border-l border-border z-40 shadow-xl transition-all duration-300 ease-in-out rounded-lg mb-5">
                    <AppBackground>
                        <div className="w-full h-full overflow-y-auto">
                            <div className="max-w-4xl mx-auto h-[calc(100vh-4rem)] flex flex-col">
                                {rightColumnComponent}
                            </div>
                        </div>
                    </AppBackground>
                </div>
            )}
        </div>
    )
}

export default ResizableTwoColumns;