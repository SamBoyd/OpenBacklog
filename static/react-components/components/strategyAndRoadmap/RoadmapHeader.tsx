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
    <div className="bg-white border-b border-neutral-200">
      {/* Breadcrumb Navigation */}
      <div className="px-8 py-4 border-b border-neutral-200">
        <div className="flex items-center gap-2 text-sm text-neutral-600">
          <button className="font-medium text-neutral-600 hover:text-neutral-900">
            {workspaceName}
          </button>
          <ChevronRight size={16} />
          <button className="font-medium text-neutral-600 hover:text-neutral-900">
            Strategy & Roadmap
          </button>
          <ChevronRight size={16} />
          <span className="text-neutral-900 font-medium">Overview</span>
        </div>
      </div>

      {/* Title & Description Section */}
      <div className="px-8 py-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-medium text-neutral-900 mb-1">Roadmap</h1>
          <p className="text-sm text-neutral-500">Strategic narrative timeline</p>
        </div>

        {/* View Toggle Buttons */}
        <div className="bg-neutral-100 rounded-[10px] p-1 flex gap-1">
          {(['timeline', 'list', 'calendar'] as const).map((view) => (
            <button
              key={view}
              onClick={() => handleViewChange(view)}
              className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                currentView === view
                  ? 'bg-white shadow-sm text-neutral-900'
                  : 'text-neutral-600 hover:text-neutral-900'
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
