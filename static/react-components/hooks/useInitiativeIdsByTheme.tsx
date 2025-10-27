import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRoadmapWithInitiatives } from '#hooks/useRoadmapWithInitiatives';
import { getAllInitiatives } from '#api/initiatives';

/**
 * Derives initiative IDs to display based on selected theme IDs
 * Handles special values: 'all-prioritized-themes', 'unthemed'
 *
 * This hook encapsulates the business logic for converting theme selections
 * into a list of initiative IDs that should be displayed.
 *
 * @param {string} workspaceId - The workspace ID
 * @param {string[]} selectedThemeIds - Array of selected theme IDs (may include special values)
 * @returns {string[]} Array of initiative IDs to display
 */
export function useInitiativeIdsByTheme(
  workspaceId: string,
  selectedThemeIds: string[]
): string[] {
  // Use existing hook to get strategic initiatives grouped by theme
  const { prioritizedThemes, unprioritizedThemes, isLoading: isLoadingThemes } =
    useRoadmapWithInitiatives(workspaceId);

  // Query all initiatives only if we need to detect unthemed initiatives
  const needsAllInitiatives = selectedThemeIds.includes('unthemed');
  const { data: allInitiatives } = useQuery({
    queryKey: ['initiatives', {}],
    queryFn: () => getAllInitiatives(),
    enabled: !!workspaceId && needsAllInitiatives && !isLoadingThemes,
  });

  return useMemo(() => {
    // If themes are still loading, return empty array to avoid showing wrong data
    if (isLoadingThemes) {
      return [];
    }

    let initiativeIds: string[] = [];

    // Handle 'all-prioritized-themes' special value
    if (selectedThemeIds.includes('all-prioritized-themes')) {
      initiativeIds = prioritizedThemes.flatMap(
        theme => theme.strategicInitiatives.map(si => si.initiative_id)
      );
    } else {
      // Handle specific theme IDs (excluding special values)
      const regularThemeIds = selectedThemeIds.filter(
        id => id !== 'all-prioritized-themes' && id !== 'unthemed'
      );

      if (regularThemeIds.length > 0) {
        const allThemes = [...prioritizedThemes, ...unprioritizedThemes];
        const relevantThemes = allThemes.filter(t => regularThemeIds.includes(t.id));
        initiativeIds = relevantThemes.flatMap(
          theme => theme.strategicInitiatives.map(si => si.initiative_id)
        );
      }
    }

    // Handle 'unthemed' special value
    if (selectedThemeIds.includes('unthemed') && allInitiatives) {
      // Get all initiative IDs that are assigned to any theme
      const themedInitiativeIds = [...prioritizedThemes, ...unprioritizedThemes]
        .flatMap(theme => theme.strategicInitiatives.map(si => si.initiative_id));

      // Find initiatives that are NOT in any theme
      const unthemedIds = allInitiatives
        .map(initiative => initiative.id)
        .filter(id => !themedInitiativeIds.includes(id));

      initiativeIds = [...initiativeIds, ...unthemedIds];
    }

    // Remove duplicates and return
    return [...new Set(initiativeIds)];
  }, [selectedThemeIds, prioritizedThemes, unprioritizedThemes, allInitiatives, isLoadingThemes]);
}
