import React, { useEffect, useState } from 'react';
import ResizableTwoColumns from '#components/resizableTwoColumns';
import ResizableTwoRows from '#components/resizableTwoRows';
import { useIsDeviceMobile } from '#hooks/isDeviceMobile';
import { ChatLayoutMode, useUserPreferences } from '#hooks/useUserPreferences';

interface ResponsiveLayoutProps {
    leftColumnComponent: React.ReactNode;
    rightColumnComponent: React.ReactNode;
}

/**
 * ResponsiveLayout switches between a two-column and two-row resizable layout based on screen size.
 * On mobile screens, it stacks rightColumnComponent above leftColumnComponent in a vertical layout.
 * On desktop, it uses a horizontal two-column layout with optional layout mode control.
 */
export const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({ leftColumnComponent, rightColumnComponent, }) => {
    const isMobile = useIsDeviceMobile();
    const { preferences, updateChatLayoutMode } = useUserPreferences();

    if (isMobile) {
        return <ResizableTwoRows
            leftColumnComponent={leftColumnComponent}
            rightColumnComponent={rightColumnComponent}
        />;
    }

    return <ResizableTwoColumns
        leftColumnComponent={leftColumnComponent}
        rightColumnComponent={rightColumnComponent}
        layoutMode={preferences.chatLayoutMode}
        onLayoutModeChange={updateChatLayoutMode}
    />;
}