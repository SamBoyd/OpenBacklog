import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router';
import NavBarView from './NavBarView';
import { useUserPreferences } from '#hooks/useUserPreferences';

export interface NavBarProps {
    enableNavigation?: boolean
}

const docsSiteUrl = process.env.DOCS_SITE_URL || ''

const NavBar = ({ enableNavigation = true }: NavBarProps) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { toggleTheme, preferences } = useUserPreferences();
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const handleNavigate = (path: string) => {
        navigate(path);
        setIsMenuOpen(false); // Close menu on navigation
    };

    const handleToggleMenu = () => {
        setIsMenuOpen(!isMenuOpen);
    };

    return (
        <NavBarView
            enableNavigation={enableNavigation}
            isMenuOpen={isMenuOpen}
            currentPath={location.pathname}
            onToggleMenu={handleToggleMenu}
            onNavigate={handleNavigate}
            currentTheme={preferences.theme}
            toggleTheme={toggleTheme}
            dashboardPath={'/workspace'}
            initiativesPath={'/workspace/initiatives'}
            supportPath={`${docsSiteUrl}/support`}
            accountPath={'/account'}
            roadmapPath={'/workspace/roadmap'}
            storyBiblePath={'/workspace/story-bible'}
        />
    );
};

export default NavBar;