import React from 'react';
import { Button } from '#components/reusable/Button';
import { ThemeDto } from '#api/productStrategy';

/**
 * Props for the ThemeFilter component.
 * @param {ThemeDto[]} prioritizedThemes - Themes currently being actively worked on
 * @param {ThemeDto[]} unprioritizedThemes - Themes in the backlog
 * @param {string[]} selectedThemeIds - The currently selected theme IDs (including special values)
 * @param {(themeId: string) => void} onThemeToggle - Function called when a theme is toggled
 * @param {() => void} onClose - Function to close the filter view
 */
interface ThemeFilterProps {
    prioritizedThemes: ThemeDto[];
    unprioritizedThemes: ThemeDto[];
    selectedThemeIds: string[];
    onThemeToggle: (themeId: string) => void;
    onClose: () => void;
}

/**
 * A component to display filtering options for roadmap themes.
 * Renders as a popover/card when active, similar to StatusFilter.
 * @param {ThemeFilterProps} props - The component props.
 * @returns {React.ReactElement} The filter component.
 */
const ThemeFilter: React.FC<ThemeFilterProps> = ({
    prioritizedThemes,
    unprioritizedThemes,
    selectedThemeIds,
    onThemeToggle,
    onClose,
}) => {
    const handleToggle = (themeId: string) => {
        onThemeToggle(themeId);
    };

    /**
     * Check if a theme ID is selected
     */
    const isSelected = (themeId: string) => {
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

    return (
        <>
            <div onClick={onClose} className="fixed inset-0 z-20 w-full h-full"> </div>
            <div className="absolute top-full right-0 mt-2 z-30 w-80 shadow-lg rounded border border-border bg-background text-card-foreground max-h-96 overflow-y-auto">
                <div className="p-4">
                    <div className="flex justify-between items-center mb-3">
                        <h3 className="text-foreground font-semibold">Themes</h3>
                        <Button onClick={onClose} className="p-1 h-auto" title="Close filter">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                            </svg>
                        </Button>
                    </div>

                    {/* Prioritized Themes Section */}
                    {(prioritizedThemes.length > 0 || unprioritizedThemes.length > 0) && (
                        <div className="mb-4">
                            <h4 className="text-sm font-medium text-muted-foreground mb-2">
                                Prioritized
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {/* "All Prioritized" special option */}
                                <button
                                    onClick={() => handleToggle('all-prioritized-themes')}
                                    className={`
                                        px-3 py-1 rounded-full text-sm border
                                        ${isSelected('all-prioritized-themes')
                                            ? 'bg-background text-foreground border-border'
                                            : 'bg-muted/5 text-muted-foreground border-border/10 hover:bg-primary/90 hover:text-accent-foreground'
                                        }
                                        transition-colors duration-150 ease-in-out
                                    `}
                                    aria-pressed={isSelected('all-prioritized-themes')}
                                    data-testid="filter-theme-all-prioritized"
                                >
                                    All Prioritized
                                </button>

                                {/* Individual prioritized themes */}
                                {prioritizedThemes.map((theme) => (
                                    <button
                                        key={theme.id}
                                        onClick={() => handleToggle(theme.id)}
                                        className={`
                                            px-3 py-1 rounded-full text-sm border
                                            ${isSelected(theme.id)
                                                ? 'bg-background text-foreground border-border'
                                                : 'bg-muted/5 text-muted-foreground border-border/10 hover:bg-primary/90 hover:text-accent-foreground'
                                            }
                                            transition-colors duration-150 ease-in-out
                                        `}
                                        aria-pressed={isSelected(theme.id)}
                                        data-testid={`filter-theme-${theme.id}`}
                                        title={theme.problem_statement}
                                    >
                                        {theme.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Unprioritized Themes Section */}
                    {(prioritizedThemes.length > 0 || unprioritizedThemes.length > 0) && (
                        <div>
                            <h4 className="text-sm font-medium text-muted-foreground mb-2">
                                Unprioritized
                            </h4>
                            <div className="flex flex-wrap gap-2">
                                {/* "Unthemed" special option */}
                                <button
                                    onClick={() => handleToggle('unthemed')}
                                    className={`
                                        px-3 py-1 rounded-full text-sm border opacity-70
                                        ${isSelected('unthemed')
                                            ? 'bg-background text-foreground border-border opacity-100'
                                            : 'bg-muted/5 text-muted-foreground border-border/10 hover:bg-primary/90 hover:text-accent-foreground'
                                        }
                                        transition-colors duration-150 ease-in-out
                                    `}
                                    aria-pressed={isSelected('unthemed')}
                                    data-testid="filter-theme-unthemed"
                                >
                                    Unthemed Initiatives
                                </button>

                                {/* Individual unprioritized themes */}
                                {unprioritizedThemes.map((theme) => (
                                    <button
                                        key={theme.id}
                                        onClick={() => handleToggle(theme.id)}
                                        className={`
                                            px-3 py-1 rounded-full text-sm border opacity-70
                                            ${isSelected(theme.id)
                                                ? 'bg-background text-foreground border-border opacity-100'
                                                : 'bg-muted/5 text-muted-foreground border-border/10 hover:bg-primary/90 hover:text-accent-foreground'
                                            }
                                            transition-colors duration-150 ease-in-out
                                        `}
                                        aria-pressed={isSelected(theme.id)}
                                        data-testid={`filter-theme-${theme.id}`}
                                        title={theme.problem_statement}
                                    >
                                        {theme.name}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Empty state */}
                    {prioritizedThemes.length === 0 && unprioritizedThemes.length === 0 && (
                        <p className="text-sm text-muted-foreground text-center py-4">
                            No themes available
                        </p>
                    )}
                </div>
            </div>
        </>
    );
};

export default ThemeFilter;
