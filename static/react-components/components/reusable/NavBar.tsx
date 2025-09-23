import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router';
import NavBarView from './NavBarView';
import { useUserPreferences } from '#hooks/useUserPreferences';

export interface NavBarProps {
    enableNavigation?: boolean
}
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
            backlogPath={'/workspace/backlog'}
            initiativesPath={'/workspace/initiatives'}
            tasksPath={'/workspace/tasks'}
            billingPath={'/workspace/billing'}
            supportPath={'/support'}
            accountPath={'/account'}
        />
    );
};

export default NavBar;