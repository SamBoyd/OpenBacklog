import React from 'react';
import { useParams, useNavigate } from 'react-router';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useRoadmapThemeDetail } from '#hooks/useRoadmapThemeDetail';
import StoryArcDetailLayout from './StoryArcDetailLayout';

/**
 * StoryArcDetail is the top-level page component for the story arc detail view.
 * It handles routing, workspace context, data fetching, and navigation.
 *
 * Route: /workspace/story-bible/arc/:arcId
 *
 * This component:
 * 1. Extracts arcId from route params
 * 2. Gets workspace ID from context
 * 3. Fetches story arc data via useRoadmapThemeDetail hook
 * 4. Handles loading, error, and no-data states
 * 5. Wires up navigation handlers
 * 6. Renders StoryArcDetailLayout with fetched data
 *
 * @returns {React.ReactElement} The story arc detail page
 */
const StoryArcDetail = () => {
    const { arcId } = useParams();
    const navigate = useNavigate();
    const { currentWorkspace } = useWorkspaces();

    // Get workspace ID from context
    const workspaceId = currentWorkspace?.id || '';

    // Fetch story arc detail data
    const {
        arc,
        hero,
        villains,
        themes,
        beats,
        conflicts,
        metrics,
        isLoading,
        error,
    } = useRoadmapThemeDetail(workspaceId, arcId || '');

    /**
     * Navigate to a specific beat (initiative) detail page.
     * @param {string} initiativeId - The initiative ID to navigate to
     */
    const handleViewBeat = (initiativeId: string) => {
        navigate(`/workspace/initiatives/${initiativeId}`);
    };

    /**
     * Navigate to the roadmap page.
     * This is a placeholder for MVP - will be enhanced in future iterations.
     */
    const handleViewRoadmap = () => {
        navigate('/workspace/roadmap');
    };

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
                            Please select a workspace to view story arcs.
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

    // Show error state if arcId is missing
    if (!arcId && !isLoading) {
        return (
            <div className="min-h-screen bg-background">
                <div className="flex items-center justify-center min-h-screen p-6">
                    <div className="max-w-md w-full border border-destructive/50 rounded-lg p-8 bg-destructive/5">
                        <h2 className="text-xl font-bold text-destructive mb-3">
                            Invalid Story Arc
                        </h2>
                        <p className="text-sm text-muted-foreground mb-4">
                            No story arc ID was provided. Please select a valid story arc.
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

    // Render the layout with all data and handlers
    // Note: arc can be null during loading, but layout handles this with its own loading state
    return (
        <StoryArcDetailLayout
            arc={arc!}
            hero={hero}
            villains={villains}
            themes={themes}
            beats={beats}
            conflicts={conflicts}
            metrics={metrics}
            isLoading={isLoading}
            error={error}
            onViewBeat={handleViewBeat}
        />
    );
};

export default StoryArcDetail;
