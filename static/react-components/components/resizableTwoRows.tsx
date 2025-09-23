import React, { useRef } from 'react';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import '../../react-components/styles/output.css';
import AppBackground from './AppBackground';
import NavBar from './reusable/NavBar';
import MobileBlocker from './MobileBlocker';

interface ResizableTwoRowsProps {
    leftColumnComponent: React.ReactNode;
    rightColumnComponent: React.ReactNode;
    topRowMinHeight?: number;
    topRowMaxHeight?: number;
    topRowHidden?: boolean;
}

const pixelsToPercentage = (pixels: number, containerHeight = 800): number => {
    return Math.max(0, Math.min(100, (pixels / containerHeight) * 100));
};

/**
 * A resizable two-row layout for mobile screens, stacking rightColumnComponent above leftColumnComponent.
 */
const ResizableTwoRows: React.FC<ResizableTwoRowsProps> = ({
    leftColumnComponent,
    rightColumnComponent,
}) => {
    return (
        <div className="overflow-clip w-full h-screen flex flex-col">
            <AppBackground>
                <div
                    id="top-panel"
                    className="flex-grow overflow-y-auto minimal-scrollbar pb-52"
                >
                    <NavBar />
                    <MobileBlocker />

                    {rightColumnComponent}
                </div>
                <div
                    id="bottom-panel"
                    className="absolute bottom-0 left-0 right-0 bg-sidebar w-screen h-fit overflow-y-visible"
                >
                    {leftColumnComponent}
                </div>
            </AppBackground>
        </div>
    );
};

export default ResizableTwoRows; 