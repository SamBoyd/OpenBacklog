import React from 'react';

interface ResponsiveLayoutProps {
    children: React.ReactNode;
}

/**
 * ResponsiveLayout renders the main content area in a single-column layout.
 */
export const ResponsiveLayout: React.FC<ResponsiveLayoutProps> = ({ children }) => {
    return <div className="w-full h-full">{children}</div>;
}