import React, { useState } from 'react';
import { ChevronRight } from 'lucide-react';

interface RoadmapHeaderProps {
  workspaceName?: string;
  onViewToggle?: (view: 'timeline' | 'list' | 'calendar') => void;
  activeView?: 'timeline' | 'list' | 'calendar';
}

/**
 * Header for the roadmap overview page.
 * Includes breadcrumb navigation, title, and view toggle buttons.
 */
export const RoadmapHeader: React.FC<RoadmapHeaderProps> = ({
  workspaceName = 'Workspace Name',
  onViewToggle,
  activeView = 'list',
}) => {
  const [currentView, setCurrentView] = useState<'timeline' | 'list' | 'calendar'>(activeView);

  const handleViewChange = (view: 'timeline' | 'list' | 'calendar') => {
    setCurrentView(view);
    onViewToggle?.(view);
  };

  return (
    <div className="bg-background text-foreground   border-b border-border">
      {/* Breadcrumb Navigation */}
      <div className="px-8 py-4 border-b border-border">
        <div className="flex items-center gap-2 text-sm text-foreground">
          <button className="font-medium text-foreground hover:text-foreground">
            {workspaceName}
          </button>
          <ChevronRight size={16} />
          <button className="font-medium text-foreground hover:text-foreground">
            Strategy & Roadmap
          </button>
          <ChevronRight size={16} />
          <span className="text-foreground font-medium">Overview</span>
        </div>
      </div>

      {/* Title & Description Section */}
      <div className="px-8 py-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-medium text-foreground mb-1">Roadmap</h1>
          <p className="text-sm text-foreground">Strategic narrative timeline</p>
        </div>

        {/* View Toggle Buttons */}
        <div className="bg-muted/10 border border-border rounded-[10px] p-1 flex gap-1">
          {(['timeline', 'list', 'calendar'] as const).map((view) => (
            <button
              key={view}
              onClick={() => handleViewChange(view)}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                currentView === view
                  ? 'bg-background text-foreground  border border-border shadow-sm'
                  : 'text-foreground/80 hover:text-foreground bg-transparent'
              }`}
            >
              {view.charAt(0).toUpperCase() + view.slice(1)}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
