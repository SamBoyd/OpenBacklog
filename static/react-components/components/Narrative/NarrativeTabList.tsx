import React from 'react';

/**
 * Narrative tab type definition
 */
export type NarrativeTabType = 'heroes' | 'villains' | 'pillars' | 'themes' | 'lore' | 'continuity';

/**
 * Props for NarrativeTabList component.
 */
export interface NarrativeTabListProps {
    /**
     * Currently active tab
     */
    activeTab: NarrativeTabType;
    /**
     * Callback when tab is selected
     */
    onTabChange: (tab: NarrativeTabType) => void;
    /**
     * Count of heroes
     */
    heroCount?: number;
    /**
     * Count of villains
     */
    villainCount?: number;
    /**
     * Count of pillars
     */
    pillarCount?: number;
    /**
     * Count of themes
     */
    themeCount?: number;
    /**
     * Count of lore items
     */
    loreCount?: number;
    /**
     * Count of continuity items
     */
    continuityCount?: number;
    /**
     * Additional CSS classes
     */
    className?: string;
    /**
     * Test ID for testing
     */
    dataTestId?: string;
}

/**
 * Tab configuration with labels and counts
 */
interface TabConfig {
    id: NarrativeTabType;
    label: string;
    count: number;
}

/**
 * NarrativeTabList displays tabs for different narrative elements.
 * @param {NarrativeTabListProps} props - Component props
 * @returns {React.ReactElement} The NarrativeTabList component
 */
const NarrativeTabList: React.FC<NarrativeTabListProps> = ({
    activeTab,
    onTabChange,
    heroCount = 0,
    villainCount = 0,
    pillarCount = 0,
    themeCount = 0,
    loreCount = 0,
    continuityCount = 0,
    className = '',
    dataTestId = 'narrative-tab-list',
}) => {
    const tabs: TabConfig[] = [
        { id: 'heroes', label: 'Heroes', count: heroCount },
        { id: 'villains', label: 'Villains', count: villainCount },
        { id: 'pillars', label: 'Pillars', count: pillarCount },
        { id: 'themes', label: 'Themes', count: themeCount },
        { id: 'lore', label: 'Lore', count: loreCount },
        { id: 'continuity', label: 'Continuity', count: continuityCount },
    ];

    return (
        <div
            className={`border-b border-border ${className}`}
            data-testid={dataTestId}
        >
            <div className="flex items-center gap-0" data-testid={`${dataTestId}-container`}>
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => onTabChange(tab.id)}
                        className={`flex-1 px-4 py-3 text-center border-b-2 transition-colors ${
                            activeTab === tab.id
                                ? 'border-foreground text-foreground font-medium'
                                : 'border-transparent text-muted-foreground hover:text-foreground'
                        }`}
                        data-testid={`${dataTestId}-${tab.id}`}
                    >
                        <div className="flex items-center justify-center gap-2">
                            <span className="text-sm font-medium">{tab.label}</span>
                            <span
                                className="inline-flex items-center justify-center min-w-[24px] h-[22px] px-2 py-0.5 rounded bg-background text-muted-foreground text-xs font-medium"
                                data-testid={`${dataTestId}-${tab.id}-badge`}
                            >
                                {tab.count}
                            </span>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
};

export default NarrativeTabList;
