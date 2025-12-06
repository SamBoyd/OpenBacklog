import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';

import NarrativeSummaryCard from '#components/Narrative/NarrativeSummaryCard';
import NarrativeTabList, { NarrativeTabType } from '#components/Narrative/NarrativeTabList';
import NarrativeHeroCard from '#components/Narrative/NarrativeHeroCard';
import StrategicPillarCard from '#components/Narrative/StrategicPillarCard';
import RoadmapThemeCard from '#components/Narrative/RoadmapThemeCard';
import { useStrategicPillars } from '#hooks/useStrategicPillars';
import { useRoadmapThemes } from '#hooks/useRoadmapThemes';
import { useHeroes } from '#hooks/useHeroes';
import { useVillains } from '#hooks/useVillains';
import { useWorkspaces } from '#hooks/useWorkspaces';

/**
 * Props for StoryBiblePage component.
 */
export interface StoryBiblePageProps {
    /**
     * Product narrative summary
     */
    narrativeSummary?: string;
    /**
     * Narrative health percentage
     */
    healthPercentage?: number;
    /**
     * Callback when Edit is clicked
     */
    onEditNarrative?: () => void;
    /**
     * Callback when Regenerate is clicked
     */
    onRegenerateNarrative?: () => void;
}

/**
 * StoryBiblePage displays the complete narrative structure with tabs for different story elements.
 * Fetches all narrative data (heroes, villains, pillars, themes) via hooks.
 * @param {StoryBiblePageProps} props - Component props
 * @returns {React.ReactElement} The StoryBiblePage component
 */
const StoryBiblePage: React.FC<StoryBiblePageProps> = ({
    narrativeSummary = '',
    healthPercentage = 72,
    onEditNarrative,
    onRegenerateNarrative,
}) => {
    const [activeTab, setActiveTab] = useState<NarrativeTabType>('heroes');
    const [expandedHeroId, setExpandedHeroId] = useState<string | null>(null);
    const [expandedVillainId, setExpandedVillainId] = useState<string | null>(null);
    const [expandedPillarId, setExpandedPillarId] = useState<string | null>(null);
    const [expandedThemeId, setExpandedThemeId] = useState<string | null>(null);

    const { currentWorkspace } = useWorkspaces();
    const workspaceId = currentWorkspace?.id || '';

    const [searchParams ] = useSearchParams();

    useEffect(() => {
        if (searchParams.get('tab')) {
            if (searchParams.get('tab') === 'heroes') {
                setActiveTab('heroes');
            } else if (searchParams.get('tab') === 'villains') {
                setActiveTab('villains');
            } else if (searchParams.get('tab') === 'pillars') {
                setActiveTab('pillars');
            } else if (searchParams.get('tab') === 'themes') {
                setActiveTab('themes');
            } else if (searchParams.get('tab') === 'lore') {
                setActiveTab('lore');
            } else if (searchParams.get('tab') === 'continuity') {
                setActiveTab('continuity');
            } 
        }
    })

    // Fetch all narrative data
    const {
        heroes,
        isLoading: heroesLoading,
    } = useHeroes(workspaceId);

    const {
        villains,
        isLoading: villainsLoading,
    } = useVillains(workspaceId);

    const {
        pillars,
        isLoading: pillarsLoading,
    } = useStrategicPillars(workspaceId);

    const {
        themes,
        isLoading: themesLoading,
    } = useRoadmapThemes(workspaceId);

    const handleTabChange = (tab: NarrativeTabType) => {
        setActiveTab(tab);
    };

    const handleHeroToggle = (heroId: string, expanded: boolean) => {
        setExpandedHeroId(expanded ? heroId : null);
    };

    const handleVillainToggle = (villainId: string, expanded: boolean) => {
        setExpandedVillainId(expanded ? villainId : null);
    };

    const handlePillarToggle = (pillarId: string, expanded: boolean) => {
        setExpandedPillarId(expanded ? pillarId : null);
    };

    const handleThemeToggle = (themeId: string, expanded: boolean) => {
        setExpandedThemeId(expanded ? themeId : null);
    };

    return (
        <div className="flex flex-col gap-8 p-6 bg-background min-h-screen">
            {/* Narrative Summary Card */}
            <NarrativeSummaryCard
                summary={narrativeSummary}
                healthPercentage={healthPercentage}
                needsAttention={healthPercentage < 80}
                onEdit={onEditNarrative}
                onRegenerate={onRegenerateNarrative}
            />

            {/* Tabbed Content Section */}
            <div className="flex flex-col gap-6">
                {/* Tab List */}
                <NarrativeTabList
                    activeTab={activeTab}
                    onTabChange={handleTabChange}
                    heroCount={heroes.length}
                    villainCount={villains.length}
                    pillarCount={pillars.length}
                    themeCount={themes.length}
                    loreCount={0}
                    continuityCount={0}
                />

                {/* Tab Content */}
                <div>
                    {/* Heroes Tab */}
                    {activeTab === 'heroes' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-foreground">Heroes</h2>
                                <button className="px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
                                    + Add Hero
                                </button>
                            </div>
                            {heroesLoading ? (
                                <div className="text-center py-12 text-muted-foreground">Loading heroes...</div>
                            ) : heroes.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground">
                                    No heroes defined yet. Add one to get started.
                                </div>
                            ) : (
                                <div className="flex flex-col gap-4">
                                    {heroes.map((hero) => (
                                        <NarrativeHeroCard
                                            key={hero.id}
                                            hero={hero}
                                            arcCount={0}
                                            villainCount={0}
                                            isExpanded={expandedHeroId === hero.id}
                                            onToggleExpand={(expanded) => handleHeroToggle(hero.id, expanded)}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Villains Tab */}
                    {activeTab === 'villains' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-foreground">Villains</h2>
                                <button className="px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
                                    + Add Villain
                                </button>
                            </div>
                            {villainsLoading ? (
                                <div className="text-center py-12 text-muted-foreground">Loading villains...</div>
                            ) : villains.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground">
                                    No villains defined yet. Add one to get started.
                                </div>
                            ) : (
                                <div className="flex flex-col gap-4">
                                    {villains.map((villain) => (
                                        <div
                                            key={villain.id}
                                            className="border border-border p-6 rounded-lg hover:bg-accent/30 transition-colors"
                                        >
                                            <div className="flex items-start justify-between mb-2">
                                                <div>
                                                    <h3 className="text-base font-semibold text-foreground">{villain.name}</h3>
                                                    <p className="text-sm text-muted-foreground">{villain.villain_type}</p>
                                                </div>
                                                <button
                                                    onClick={() => handleVillainToggle(villain.id, expandedVillainId !== villain.id)}
                                                    className="p-2 rounded-lg text-muted-foreground hover:bg-accent/50 transition-colors"
                                                >
                                                    <span className={`text-lg transition-transform ${expandedVillainId === villain.id ? 'rotate-180' : ''}`}>
                                                        ▼
                                                    </span>
                                                </button>
                                            </div>
                                            <p className="text-sm text-muted-foreground line-clamp-2">{villain.description}</p>
                                            {expandedVillainId === villain.id && (
                                                <div className="mt-4 pt-4 border-t border-border">
                                                    <p className="text-sm text-foreground leading-relaxed">{villain.description}</p>
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Pillars Tab */}
                    {activeTab === 'pillars' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-foreground">Strategic Pillars</h2>
                                <button className="px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
                                    + Add Pillar
                                </button>
                            </div>
                            {pillarsLoading ? (
                                <div className="text-center py-12 text-muted-foreground">Loading pillars...</div>
                            ) : pillars.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground">
                                    No pillars defined yet. Add one to get started.
                                </div>
                            ) : (
                                <div className="flex flex-col gap-4">
                                    {pillars.map((pillar) => (
                                        <StrategicPillarCard
                                            key={pillar.id}
                                            pillar={pillar}
                                            outcomeCount={pillar.outcome_ids?.length || 0}
                                            isExpanded={expandedPillarId === pillar.id}
                                            onToggleExpand={(expanded) => handlePillarToggle(pillar.id, expanded)}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Themes Tab */}
                    {activeTab === 'themes' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-foreground">Roadmap Themes</h2>
                                <button className="px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
                                    + Add Theme
                                </button>
                            </div>
                            {themesLoading ? (
                                <div className="text-center py-12 text-muted-foreground">Loading themes...</div>
                            ) : themes.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground">
                                    No themes defined yet. Add one to get started.
                                </div>
                            ) : (
                                <div className="flex flex-col gap-4">
                                    {themes.map((theme) => (
                                        <RoadmapThemeCard
                                            key={theme.id}
                                            theme={theme}
                                            outcomeCount={theme.outcome_ids?.length || 0}
                                            isExpanded={expandedThemeId === theme.id}
                                            onToggleExpand={(expanded) => handleThemeToggle(theme.id, expanded)}
                                        />
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Lore Tab */}
                    {activeTab === 'lore' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-foreground">Lore</h2>
                                <button className="px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
                                    + Add Lore
                                </button>
                            </div>
                            <div className="text-center py-12 text-muted-foreground">
                                No lore defined yet. Add one to get started.
                            </div>
                        </div>
                    )}

                    {/* Continuity Tab */}
                    {activeTab === 'continuity' && (
                        <div className="flex flex-col gap-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-foreground">Continuity</h2>
                                <button className="px-4 py-2 bg-foreground text-background rounded-lg text-sm font-medium hover:opacity-90 transition-opacity">
                                    + Add Item
                                </button>
                            </div>
                            <div className="text-center py-12 text-muted-foreground">
                                No continuity items defined yet. Add one to get started.
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default StoryBiblePage;
