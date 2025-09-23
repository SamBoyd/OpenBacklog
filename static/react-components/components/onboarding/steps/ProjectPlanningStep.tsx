import React from 'react';
import OnboardingStep from '../OnboardingStep';

/**
 * First onboarding step - Project Planning
 * Introduces users to project planning and task management features
 */
const ProjectPlanningStep: React.FC = () => {
  return (
    <OnboardingStep
      title="Plan Your Projects"
      description="Organize your work with intelligent project planning and task management."
      icon="📋"
      content={
        <div className="space-y-4">
          <div className="bg-card border rounded-lg p-3 sm:p-6">
            <h3 className="text-muted-foreground font-semibold mb-2 sm:mb-3 text-sm sm:text-base">Break Down Complex Projects</h3>
            <ul className="space-y-2 text-muted-foreground text-sm sm:text-base">
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Create initiatives, epics, and tasks with clear hierarchies
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Track progress with visual kanban boards and lists
              </li>
              <li className="flex items-start gap-2">
                <span className="text-primary">•</span>
                Set priorities and deadlines to stay on track
              </li>
            </ul>
          </div>
        </div>
      }
    />
  );
};

export default ProjectPlanningStep;