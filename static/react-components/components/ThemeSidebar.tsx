import React from 'react';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useThemePrioritization } from '#hooks/useThemePrioritization';
import { useUserPreferences } from '#hooks/useUserPreferences';

/**
 * Sidebar component for filtering initiatives by roadmap themes
 *
 * This component fetches and displays themes using the Roadmap Intelligence Context.
 * Themes are automatically separated into:
 * - Prioritized: Themes currently being actively worked on
 * - Unprioritized: Themes in the backlog
 *
 * Users can click on themes to filter the initiatives shown in the main view.
 * Multiple themes can be selected using Cmd/Ctrl + Click.
 */
const ThemeSidebar: React.FC = () => {
  const { currentWorkspace } = useWorkspaces();
  const {
    prioritizedThemes,
    unprioritizedThemes,
    isLoading,
    prioritizedError,
    unprioritizedError,
  } = useThemePrioritization(currentWorkspace?.id || '');

  const { preferences, updateSelectedThemes } = useUserPreferences();
  const selectedThemeIds = preferences.selectedThemeIds;

  const error = prioritizedError || unprioritizedError;

  /**
   * Handle theme click for filtering initiatives
   * Supports multi-select with Cmd/Ctrl key
   */
  const handleThemeClick = (themeId: string, event: React.MouseEvent) => {
    if (event.metaKey || event.ctrlKey) {
      // Multi-select mode
      if (selectedThemeIds.includes(themeId)) {
        // Deselect if already selected
        const newSelection = selectedThemeIds.filter(id => id !== themeId);
        // Don't allow empty selection - default to all-prioritized-themes
        updateSelectedThemes(newSelection.length > 0 ? newSelection : ['all-prioritized-themes']);
      } else {
        // Add to selection, removing special values if present
        const filteredSelection = selectedThemeIds.filter(
          id => id !== 'all-prioritized-themes' && id !== 'unthemed'
        );
        updateSelectedThemes([...filteredSelection, themeId]);
      }
    } else {
      // Single select mode
      if (selectedThemeIds.length === 1 && selectedThemeIds[0] === themeId) {
        // Clicking the same theme again - reset to all-prioritized-themes
        updateSelectedThemes(['all-prioritized-themes']);
      } else {
        updateSelectedThemes([themeId]);
      }
    }
  };

  /**
   * Handle special option clicks
   */
  const handleSpecialOptionClick = (optionId: string, event: React.MouseEvent) => {
    if (event.metaKey || event.ctrlKey) {
      // Multi-select with special option not allowed - just select the option
      updateSelectedThemes([optionId]);
    } else {
      // Toggle special option
      if (selectedThemeIds.length === 1 && selectedThemeIds[0] === optionId) {
        // Already selected - do nothing (special options can't be deselected via click)
        return;
      }
      updateSelectedThemes([optionId]);
    }
  };

  /**
   * Check if a theme is selected
   */
  const isThemeSelected = (themeId: string) => {
    // Check for exact match
    if (selectedThemeIds.includes(themeId)) {
      return true;
    }
    // Check if 'all-prioritized-themes' is selected and this is a prioritized theme
    if (selectedThemeIds.includes('all-prioritized-themes')) {
      return prioritizedThemes.some(theme => theme.id === themeId);
    }
    return false;
  };

  /**
   * Check if special option is selected
   */
  const isSpecialOptionSelected = (optionId: string) => {
    return selectedThemeIds.includes(optionId);
  };

  // Don't render if no workspace is selected
  if (!currentWorkspace) {
    return null;
  }

  // Error state
  if (error) {
    return (
      <div className="w-60 flex-shrink-0 border-r border-border bg-card">
        <div className="flex flex-col h-full items-center justify-center p-4">
          <p className="text-sm text-destructive text-center">
            Failed to load themes
          </p>
        </div>
      </div>
    );
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="w-60 flex-shrink-0 border-r border-border bg-card">
        <div className="flex flex-col h-full items-center justify-center p-4">
          <p className="text-sm text-muted-foreground">Loading themes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-60 flex-shrink-0 border-r border-border bg-card">
      <div className="flex flex-col h-full">
        {/* Prioritized Themes Section */}
        {(prioritizedThemes.length > 0 || unprioritizedThemes.length > 0) && (
          <div className="px-4 py-3">
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">
              Prioritized Themes
            </h3>
            <div className="space-y-1">
              {/* "All Prioritized" special option */}
              <div
                onClick={(e) => handleSpecialOptionClick('all-prioritized-themes', e)}
                className={`px-3 py-2 rounded-md cursor-pointer transition-all text-sm ${
                  isSpecialOptionSelected('all-prioritized-themes')
                    ? 'bg-primary/20 text-primary font-medium'
                    : 'hover:bg-accent text-foreground'
                }`}
              >
                All Prioritized
              </div>

              {/* Individual prioritized themes */}
              {prioritizedThemes.map((theme) => (
                <div
                  key={theme.id}
                  onClick={(e) => handleThemeClick(theme.id, e)}
                  className={`px-3 py-2 rounded-md cursor-pointer transition-all text-sm ${
                    isThemeSelected(theme.id)
                      ? 'bg-primary/20 text-primary font-medium'
                      : 'hover:bg-accent text-foreground'
                  }`}
                >
                  {theme.name}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Divider between prioritized and unprioritized */}
        {(prioritizedThemes.length > 0 || unprioritizedThemes.length > 0) && (
          <div className="border-t border-border" />
        )}

        {/* Unprioritized Themes Section */}
        {(prioritizedThemes.length > 0 || unprioritizedThemes.length > 0) && (
          <div className="px-4 py-3">
            <h3 className="text-sm font-semibold text-muted-foreground mb-2">
              Unprioritized
            </h3>
            <div className="space-y-1">
              {/* "Unthemed" special option */}
              <div
                onClick={(e) => handleSpecialOptionClick('unthemed', e)}
                className={`px-3 py-2 rounded-md cursor-pointer transition-all text-sm opacity-70 ${
                  isSpecialOptionSelected('unthemed')
                    ? 'bg-primary/20 text-primary font-medium'
                    : 'hover:bg-accent text-foreground'
                }`}
              >
                Unthemed Initiatives
              </div>

              {/* Individual unprioritized themes */}
              {unprioritizedThemes.map((theme) => (
                <div
                  key={theme.id}
                  onClick={(e) => handleThemeClick(theme.id, e)}
                  className={`px-3 py-2 rounded-md cursor-pointer transition-all text-sm opacity-70 ${
                    isThemeSelected(theme.id)
                      ? 'bg-primary/20 text-primary font-medium opacity-100'
                      : 'hover:bg-accent text-foreground'
                  }`}
                >
                  {theme.name}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty state */}
        {prioritizedThemes.length === 0 && unprioritizedThemes.length === 0 && (
          <div className="flex flex-col h-full items-center justify-center p-4">
            <p className="text-sm text-muted-foreground text-center">
              No themes yet
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ThemeSidebar;
