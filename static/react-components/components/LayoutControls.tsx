import React from 'react';
import { PanelLeft, Columns, Maximize, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { ChatLayoutMode, Theme, useUserPreferences } from '#hooks/useUserPreferences';

interface LayoutControlsProps {
  currentMode: ChatLayoutMode;
  onModeChange: (mode: ChatLayoutMode) => void;
}

/**
 * Layout control buttons for switching between different chat layout modes.
 * Provides three layout options: minimize chat, 50/50 split, and maximize chat.
 * @param {object} props - The component props
 * @param {ChatLayoutMode} props.currentMode - The currently active layout mode
 * @param {(mode: ChatLayoutMode) => void} props.onModeChange - Callback when layout mode changes
 * @returns {React.ReactElement} The layout controls component
 */
const LayoutControls: React.FC<LayoutControlsProps> = ({ currentMode, onModeChange }) => {
  const { preferences } = useUserPreferences();

  const buttonBaseClasses = `
    rounded p-1 
    hover:text-sidebar-foreground/50 hover:bg-sidebar-foreground/5
    transition-colors flex items-center justify-center
    ${currentMode === 'minimized' && preferences.theme == 'light' ? 'text-foreground/40' : 'text-sidebar-foreground/40'}
  `;

  const getButtonClasses = (mode: ChatLayoutMode) => {
    return currentMode === mode
      ? `${buttonBaseClasses} ${currentMode === 'minimized' && preferences.theme == 'light' ? 'text-foreground/60' : 'text-sidebar-foreground/80'}`
      : buttonBaseClasses;
  };

  return (
    <div className="flex items-center">
      {/* Maximize Chat - Hide right panel */}
      <button
        onClick={() => onModeChange('maximized')}
        className={getButtonClasses('maximized')}
        title="Maximize chat panel"
      >
        <PanelLeftOpen className="size-4" />
      </button>

      {/* 50/50 Split */}
      <button
        onClick={() => onModeChange('split')}
        className={getButtonClasses('split')}
        title="50/50 split layout"
      >
        <Columns className="size-4" />
      </button>

      {/* Minimize Chat - Hide left panel */}
      <button
        onClick={() => onModeChange('minimized')}
        className={getButtonClasses('minimized')}
        title="Minimize chat panel"
      >
        <PanelLeftClose className="size-4" />
      </button>
      
    </div>
  );
};

export default LayoutControls;