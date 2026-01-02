import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router';

import NarrativeSummaryCard from '#components/Narrative/NarrativeSummaryCard';
import NarrativeTabList, { NarrativeTabType } from '#components/Narrative/NarrativeTabList';
import NarrativeHeroCard from '#components/Narrative/NarrativeHeroCard';
import NarrativeVillainCard from '#components/Narrative/NarrativeVillainCard';
import StrategicPillarCard from '#components/Narrative/StrategicPillarCard';
import RoadmapThemeCard from '#components/Narrative/RoadmapThemeCard';
import { useStrategicPillars } from '#hooks/useStrategicPillars';
import { useRoadmapThemes } from '#hooks/strategyAndRoadmap/useRoadmapThemes';
import { useHeroes } from '#hooks/useHeroes';
import { useVillains } from '#hooks/useVillains';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useProductOutcomes } from '#hooks/useProductOutcomes';

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
}) => {
    const [activeTab, setActiveTab] = useState<NarrativeTabType>('heroes');
    const [expandedHeroId, setExpandedHeroId] = useState<string | null>(null);
    const [expandedVillainId, setExpandedVillainId] = useState<string | null>(null);
    const [expandedPillarId, setExpandedPillarId] = useState<string | null>(null);
    const [expandedThemeId, setExpandedThemeId] = useState<string | null>(null);

    const { currentWorkspace } = useWorkspaces();
    const workspaceId = currentWorkspace?.id || '';

    const [searchParams ] = useSearchParams();

    // Fetch product outcomes
    const { outcomes } = useProductOutcomes(workspaceId);

    useEffect(() => {
        const tab = searchParams.get('tab');
        if (tab && ['heroes', 'villains', 'pillars', 'themes'].includes(tab)) {
            setActiveTab(tab as NarrativeTabType);
        }
    }, [searchParams])

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
        prioritizedThemes,
        unprioritizedThemes,
        isLoadingPrioritized: prioritizedThemesLoading,
        isLoadingUnprioritized: unprioritizedThemesLoading,
    } = useRoadmapThemes(workspaceId);

    const themesLoading = prioritizedThemesLoading || unprioritizedThemesLoading;
    const themes = [...prioritizedThemes, ...unprioritizedThemes];

    const handleTabChange = (tab: NarrativeTabType) => {
        setActiveTab(tab);
    };

    const getOutcomesForPillar = (pillarOutcomeIds: string[]) => {
        return outcomes.filter(o => pillarOutcomeIds.includes(o.id));
    };

    const getRoadmapThemeCountForHero = (heroId: string): number => {
        return themes.filter(theme => theme.hero_ids?.includes(heroId) ?? false).length;
    };

    const getVillainCountForHero = (heroId: string): number => {
        // Get all themes where this hero is featured
        const heroThemes = themes.filter(theme => theme.hero_ids?.includes(heroId) ?? false);

        // Collect unique villain IDs from all these themes
        const uniqueVillainIds = new Set<string>();
        heroThemes.forEach(theme => {
            theme.villain_ids?.forEach(villainId => uniqueVillainIds.add(villainId));
        });

        return uniqueVillainIds.size;
    };

    const getVillainCounts = (villainId: string) => {
        const themesWithVillain = themes.filter(theme =>
            theme.villain_ids?.includes(villainId) ?? false
        );

        const themeCount = themesWithVillain.length;

        const uniqueHeroIds = new Set<string>();
        themesWithVillain.forEach(theme => {
            theme.hero_ids?.forEach(heroId => uniqueHeroIds.add(heroId));
        });

        const heroCount = uniqueHeroIds.size;

        return { themeCount, heroCount };
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
        <div className="flex flex-col gap-6 pb-6 min-h-screen">
            {/* Tabbed Content Section */}
            <div className="flex flex-col gap-4">
                {/* Tab List */}
                <NarrativeTabList
                    activeTab={activeTab}
                    onTabChange={handleTabChange}
                    heroCount={heroes.length}
                    villainCount={villains.length}
                    pillarCount={pillars.length}
                    themeCount={themes.length}
                />

                {/* Tab Content */}
                <div>
                    {/* Heroes Tab */}
                    {activeTab === 'heroes' && (
                        <div className="flex flex-col gap-4">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-foreground">Heroes</h2>
                                <p className="text-sm text-muted-foreground">{heroes.length} defined</p>
                            </div>
                            {heroesLoading ? (
                                <div className="text-center py-12 text-muted-foreground">Loading heroes...</div>
                            ) : heroes.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-lg">
                                    <p className="text-sm">No heroes defined yet.</p>
                                    <p className="text-xs mt-1">Heroes represent your target users and their needs.</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-3">
                                    {heroes.map((hero) => (
                                        <NarrativeHeroCard
                                            key={hero.id}
                                            hero={hero}
                                            roadmapThemeCount={getRoadmapThemeCountForHero(hero.id)}
                                            villainCount={getVillainCountForHero(hero.id)}
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
                        <div className="flex flex-col gap-4">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-foreground">Villains</h2>
                                <p className="text-sm text-muted-foreground">{villains.length} defined</p>
                            </div>
                            {villainsLoading ? (
                                <div className="text-center py-12 text-muted-foreground">Loading villains...</div>
                            ) : villains.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-lg">
                                    <p className="text-sm">No villains defined yet.</p>
                                    <p className="text-xs mt-1">Villains represent obstacles and problems your heroes face.</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-3">
                                    {villains.map((villain) => {
                                        const { themeCount, heroCount } = getVillainCounts(villain.id);
                                        return (
                                            <NarrativeVillainCard
                                                key={villain.id}
                                                villain={villain}
                                                themeCount={themeCount}
                                                heroCount={heroCount}
                                                isExpanded={expandedVillainId === villain.id}
                                                onToggleExpand={(expanded) => handleVillainToggle(villain.id, expanded)}
                                            />
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Pillars Tab */}
                    {activeTab === 'pillars' && (
                        <div className="flex flex-col gap-4">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-foreground">Strategic Pillars</h2>
                                <p className="text-sm text-muted-foreground">{pillars.length} defined</p>
                            </div>
                            {pillarsLoading ? (
                                <div className="text-center py-12 text-muted-foreground">Loading pillars...</div>
                            ) : pillars.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-lg">
                                    <p className="text-sm">No strategic pillars defined yet.</p>
                                    <p className="text-xs mt-1">Pillars represent the foundational areas of your product strategy.</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-3">
                                    {pillars.map((pillar) => (
                                        <StrategicPillarCard
                                            key={pillar.id}
                                            pillar={pillar}
                                            outcomeCount={pillar.outcome_ids?.length || 0}
                                            outcomes={getOutcomesForPillar(pillar.outcome_ids || [])}
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
                        <div className="flex flex-col gap-4">
                            <div className="flex items-center justify-between">
                                <h2 className="text-lg font-semibold text-foreground">Roadmap Themes</h2>
                                <p className="text-sm text-muted-foreground">{themes.length} defined</p>
                            </div>
                            {themesLoading ? (
                                <div className="text-center py-12 text-muted-foreground">Loading themes...</div>
                            ) : themes.length === 0 ? (
                                <div className="text-center py-12 text-muted-foreground border border-dashed border-border rounded-lg">
                                    <p className="text-sm">No roadmap themes defined yet.</p>
                                    <p className="text-xs mt-1">Themes represent strategic initiatives that connect heroes and villains.</p>
                                </div>
                            ) : (
                                <div className="flex flex-col gap-3">
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
                </div>
            </div>
        </div>
    );
};

export default StoryBiblePage;
