import React from 'react';
import { useNavigate } from 'react-router';

import { RoadmapThemeDetailLayoutProps } from '#types/storyArc';
import HeaderSection from './HeaderSection';
import StorySection from './StorySection';
import BeatsSection from './BeatsSection';
import ConflictsStakesSection from './ConflictsStakesSection';
import PlaceholderSection from './PlaceholderSection';
import MetricsSection from './MetricsSection';
import StrategicContextSection from './StrategicContextSection';
import CharactersSection from './CharactersSection';

/**
 * RoadmapThemeDetailLayout orchestrates all section components into a responsive 2-column layout.
 * This component handles the overall page structure, loading states, error states, and
 * responsive behavior across desktop, tablet, and mobile devices.
 *
 * @param {RoadmapThemeDetailLayoutProps} props - Component props containing arc data and callbacks
 * @returns {React.ReactElement} The complete roadmap theme detail layout
 */
const RoadmapThemeDetailLayout: React.FC<RoadmapThemeDetailLayoutProps> = ({
    arc,
    hero,
    villains,
    beats,
    conflicts,
    outcomes,
    pillars,
    visionText,
    metrics,
    isLoading,
    error,
    onViewOutcome,
    onViewHero,
    onViewVillain,
}) => {
    const navigate = useNavigate();
    // Handle error state
    if (error && !isLoading) {
        return (
            <div className="min-h-screen bg-background">
                <div className="flex items-center justify-center min-h-screen p-6">
                    <div className="max-w-md w-full border border-destructive/50 rounded-lg p-8 bg-destructive/5">
                        <h2 className="text-xl font-bold text-destructive mb-3">
                            Failed to load roadmap theme
                        </h2>
                        <p className="text-sm text-muted-foreground mb-4">
                            {error || 'An unexpected error occurred. Please try again.'}
                        </p>
                        <button
                            onClick={() => window.location.reload()}
                            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                        >
                            Retry
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Handle no data state (arc not found)
    if (!arc && !isLoading) {
        return (
            <div className="min-h-screen bg-background">
                <div className="flex items-center justify-center min-h-screen p-6">
                    <div className="max-w-md w-full border border-border rounded-lg p-8 bg-card text-center">
                        <h2 className="text-xl font-bold text-foreground mb-3">
                            Roadmap Theme Not Found
                        </h2>
                        <p className="text-sm text-muted-foreground mb-4">
                            The requested roadmap theme could not be found. It may have been deleted or you may not have permission to view it.
                        </p>
                        <button
                            onClick={() => window.history.back()}
                            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium hover:opacity-90 transition-opacity"
                        >
                            Go Back
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Handle loading state - show skeleton loaders
    if (isLoading || !arc) {
        return (
            <div className="min-h-screen bg-background">
                {/* Loading header */}
                <div className="sticky top-0 z-50 bg-background border-b border-border">
                    <div className="px-6 py-4">
                        <div className="h-6 bg-muted rounded animate-pulse mb-4 w-1/3" />
                        <div className="h-8 bg-muted rounded animate-pulse mb-2 w-1/2" />
                        <div className="flex gap-2">
                            <div className="h-8 bg-muted rounded animate-pulse w-24" />
                            <div className="h-8 bg-muted rounded animate-pulse w-32" />
                            <div className="h-8 bg-muted rounded animate-pulse w-28" />
                        </div>
                    </div>
                </div>

                {/* Loading context bar */}
                <div className="border-b border-border bg-card">
                    <div className="px-6 py-4">
                        <div className="h-6 bg-muted rounded animate-pulse w-1/4" />
                    </div>
                </div>

                {/* Loading content */}
                <div className="p-6 md:p-8">
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                        <div className="lg:col-span-2 space-y-8">
                            <div className="h-64 bg-muted rounded-lg animate-pulse" />
                            <div className="h-96 bg-muted rounded-lg animate-pulse" />
                        </div>
                        <div className="lg:col-span-1 space-y-4">
                            <div className="h-48 bg-muted rounded-lg animate-pulse" />
                            <div className="h-48 bg-muted rounded-lg animate-pulse" />
                            <div className="h-48 bg-muted rounded-lg animate-pulse" />
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // No-op handlers for disabled actions (MVP)
    const handleEditMode = () => {
        console.log('Edit mode - coming soon');
    };

    const handleViewRoadmap = () => {
        // This will be wired up in the parent page component
        navigate('/workspace/roadmap');
    };

    const handleShare = () => {
        console.log('Share/Export - coming soon');
    };

    const handleLinkEntity = () => {
        console.log('Link Entity - coming soon');
    };

    const handleDelete = () => {
        console.log('Delete - coming soon');
    };

    const handleAddBeat = () => {
        console.log('Add Beat - coming soon');
    };

    const handleRegenerateStory = () => {
        console.log('Regenerate Story - coming soon');
    };

    const handleEditStory = () => {
        console.log('Edit Story - coming soon');
    };

    const handleEditLinks = () => {
        console.log('Edit Links - coming soon');
    };

    const handleAddConflict = () => {
        console.log('Add Conflict - coming soon');
    };

    const handleViewBeat = (initiativeId: string) => {
        navigate(`/workspace/initiatives/${initiativeId}`);
    };

    const handleHeroClick = (heroId: string) => {
        navigate(`/workspace/story-bible?tab=heroes`);
    };

    const handleVillainClick = (villainId: string) => {
        navigate(`/workspace/story-bible?tab=villains`);
    };

    const handleThemeClick = (themeId: string) => {
        navigate(`/workspace/story-bible/theme/${themeId}`);
    };

    return (
        <div className="min-h-screen bg-background flex flex-col gap-4">
            {/* Sticky Header */}
            <HeaderSection
                arcTitle={arc.name}
                arcSubtitle={arc.description?.substring(0, 100)}
                arcStatus="in_progress"
                onEditMode={handleEditMode}
                onViewRoadmap={handleViewRoadmap}
                onShare={handleShare}
                onLinkEntity={handleLinkEntity}
                onDelete={handleDelete}
            />

            {/* Strategic Context */}
            <StrategicContextSection
                visionText={visionText}
                outcomes={outcomes}
                pillars={pillars}
                progressPercent={metrics.progressPercent}
                onViewOutcome={onViewOutcome}
            />

            {/* Characters */}
            <CharactersSection
                hero={hero}
                villains={villains}
                onViewHero={onViewHero}
                onViewVillain={onViewVillain}
            />

            {/* Main Content Area */}
            <div className="">
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {/* Left Column (60%) - Main Content */}
                    <div className="lg:col-span-2 space-y-4">
                        {/* Story Section */}
                        <StorySection
                            storyText={arc.description || 'No story description available.'}
                            isLoading={false}
                            onRegenerateClick={handleRegenerateStory}
                            onEditClick={handleEditStory}
                        />

                        {/* Beats Section */}
                        <BeatsSection
                            beats={beats}
                            arcId={arc.id}
                            isLoading={false}
                            onViewBeat={handleViewBeat}
                            onAddBeat={handleAddBeat}
                        />
                    </div>

                    {/* Right Sidebar (40%) - Sticky on Desktop */}
                    <div className="lg:col-span-1 space-y-4 lg:sticky lg:top-[200px] lg:self-start">
                        {/* Conflicts and Stakes */}
                        <ConflictsStakesSection
                            conflicts={conflicts}
                            arcId={arc.id}
                            onAddConflict={handleAddConflict}
                        />

                        {/* Placeholder: Foreshadowing */}
                        <PlaceholderSection
                            title="Foreshadowing"
                            emptyMessage="No foreshadowing elements defined yet."
                        />

                        {/* Placeholder: Turning Points */}
                        <PlaceholderSection
                            title="Turning Points"
                            emptyMessage="No turning points defined yet."
                        />

                        {/* Placeholder: Related Lore */}
                        <PlaceholderSection
                            title="Related Lore"
                            emptyMessage="No related lore defined yet."
                        />

                        {/* Metrics Section */}
                        <MetricsSection
                            completionPercent={metrics.completionPercent}
                            scenesComplete={metrics.scenesComplete}
                            scenesTotal={metrics.scenesTotal}
                            beatsComplete={metrics.beatsComplete}
                            beatsInProgress={metrics.beatsInProgress}
                            beatsPlanned={metrics.beatsPlanned}
                            startDate={metrics.startDate}
                            lastActivityDate={metrics.lastActivityDate}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default RoadmapThemeDetailLayout;
