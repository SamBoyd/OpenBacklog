import React from 'react';
import { useParams, useNavigate } from 'react-router';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useRoadmapThemeDetail } from '#hooks/useRoadmapThemeDetail';
import RoadmapThemeDetailLayout from './RoadmapThemeDetailLayout';

/**
 * RoadmapThemeDetail is the top-level page component for the roadmap theme detail view.
 * It handles routing, workspace context, data fetching, and navigation.
 *
 * Route: /workspace/story-bible/theme/:themeId
 *
 * This component:
 * 1. Extracts themeId from route params
 * 2. Gets workspace ID from context
 * 3. Fetches roadmap theme data via useRoadmapThemeDetail hook
 * 4. Handles loading, error, and no-data states
 * 5. Wires up navigation handlers
 * 6. Renders RoadmapThemeDetailLayout with fetched data
 *
 * @returns {React.ReactElement} The roadmap theme detail page
 */
const RoadmapThemeDetail = () => {
    const { themeId } = useParams();
    const navigate = useNavigate();
    const { currentWorkspace } = useWorkspaces();

    // Get workspace ID from context
    const workspaceId = currentWorkspace?.id || '';

    // Fetch roadmap theme detail data
    const {
        arc,
        hero,
        villains,
        themes,
        beats,
        conflicts,
        outcomes,
        pillars,
        visionText,
        metrics,
        isLoading,
        error,
    } = useRoadmapThemeDetail(workspaceId, themeId || '');

    // Show error state if workspace is not available
    if (!workspaceId && !isLoading) {
        return (
            <div className="min-h-screen bg-background">
                <div className="flex items-center justify-center min-h-screen p-6">
                    <div className="max-w-md w-full border border-destructive/50 rounded-lg p-8 bg-destructive/5">
                        <h2 className="text-xl font-bold text-destructive mb-3">
                            No Workspace Selected
                        </h2>
                        <p className="text-sm text-muted-foreground mb-4">
                            Please select a workspace to view roadmap themes.
                        </p>
                        <button
                            onClick={() => navigate('/workspace')}
                            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                        >
                            Go to Workspace
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Show error state if themeId is missing
    if (!themeId && !isLoading) {
        return (
            <div className="min-h-screen bg-background">
                <div className="flex items-center justify-center min-h-screen p-6">
                    <div className="max-w-md w-full border border-destructive/50 rounded-lg p-8 bg-destructive/5">
                        <h2 className="text-xl font-bold text-destructive mb-3">
                            Invalid Roadmap theme
                        </h2>
                        <p className="text-sm text-muted-foreground mb-4">
                            No roadmap theme ID was provided. Please select a valid roadmap theme.
                        </p>
                        <button
                            onClick={() => navigate('/workspace/story-bible')}
                            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                        >
                            Go to Story Bible
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Callback handlers
    const handleViewOutcome = (outcomeId: string) => {
        navigate(`/workspace/outcomes/${outcomeId}`);
    };

    const handleViewHero = (heroId: string) => {
        navigate(`/workspace/story-bible?tab=heroes`);
    };

    const handleViewVillain = (villainId: string) => {
        navigate(`/workspace/story-bible?tab=villains`);
    };

    // Render the layout with all data and handlers
    // Note: arc can be null during loading, but layout handles this with its own loading state
    return (
        <RoadmapThemeDetailLayout
            arc={arc!}
            hero={hero}
            villains={villains}
            themes={themes}
            beats={beats}
            conflicts={conflicts}
            outcomes={outcomes}
            pillars={pillars}
            visionText={visionText}
            metrics={metrics}
            isLoading={isLoading}
            error={error}
            onViewOutcome={handleViewOutcome}
            onViewHero={handleViewHero}
            onViewVillain={handleViewVillain}
        />
    );
};

export default RoadmapThemeDetail;
