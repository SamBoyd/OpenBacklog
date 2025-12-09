import React from 'react';
import { UserIcon, SkullIcon, LayersIcon, MapIcon } from 'lucide-react';

/**
 * Narrative tab type definition
 */
export type NarrativeTabType = 'heroes' | 'villains' | 'pillars' | 'themes';

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
     * Additional CSS classes
     */
    className?: string;
    /**
     * Test ID for testing
     */
    dataTestId?: string;
}

/**
 * Tab configuration with labels, counts, and icons
 */
interface TabConfig {
    id: NarrativeTabType;
    label: string;
    count: number;
    icon: React.ReactNode;
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
    className = '',
    dataTestId = 'narrative-tab-list',
}) => {
    const tabs: TabConfig[] = [
        { id: 'heroes', label: 'Heroes', count: heroCount, icon: <UserIcon className="w-4 h-4" /> },
        { id: 'villains', label: 'Villains', count: villainCount, icon: <SkullIcon className="w-4 h-4" /> },
        { id: 'pillars', label: 'Pillars', count: pillarCount, icon: <LayersIcon className="w-4 h-4" /> },
        { id: 'themes', label: 'Themes', count: themeCount, icon: <MapIcon className="w-4 h-4" /> },
    ];

    return (
        <div
            className={`border-b border-border ${className}`}
            data-testid={dataTestId}
        >
            <div className="flex items-center" data-testid={`${dataTestId}-container`}>
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => onTabChange(tab.id)}
                        className={`flex-1 px-4 py-3 text-center border-b-2 transition-colors ${
                            activeTab === tab.id
                                ? 'border-primary text-foreground'
                                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-border'
                        }`}
                        data-testid={`${dataTestId}-${tab.id}`}
                    >
                        <div className="flex items-center justify-center gap-2">
                            <span className={activeTab === tab.id ? 'text-primary' : ''}>{tab.icon}</span>
                            <span className="text-sm font-medium">{tab.label}</span>
                            <span
                                className={`inline-flex items-center justify-center min-w-[20px] h-[20px] px-1.5 py-0.5 rounded-full text-xs font-medium ${
                                    activeTab === tab.id
                                        ? 'bg-primary/20 text-primary'
                                        : 'bg-muted/10 text-muted-foreground'
                                }`}
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
