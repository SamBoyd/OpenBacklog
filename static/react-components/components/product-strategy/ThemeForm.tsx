import React, { useState } from 'react';

interface ThemeFormProps {
  mode?: 'create' | 'edit';
  initialData?: {
    name: string;
    problem_statement: string;
    hypothesis?: string | null;
    indicative_metrics?: string | null;
    time_horizon_months?: number | null;
    outcome_ids?: string[];
  };
  availableOutcomes: Array<{ id: string; name: string }>;
  onSave: (data: {
    name: string;
    problem_statement: string;
    hypothesis?: string | null;
    indicative_metrics?: string | null;
    time_horizon_months?: number | null;
    outcome_ids?: string[];
  }) => void;
  onCancel: () => void;
  isSaving: boolean;
}

/**
 * ThemeForm component for creating or editing roadmap themes
 * @param {ThemeFormProps} props - Component props
 * @returns {React.ReactElement} The theme form component
 */
export const ThemeForm: React.FC<ThemeFormProps> = ({
  mode = 'create',
  initialData,
  availableOutcomes,
  onSave,
  onCancel,
  isSaving,
}) => {
  const [name, setName] = useState(initialData?.name || '');
  const [problemStatement, setProblemStatement] = useState(
    initialData?.problem_statement || ''
  );
  const [hypothesis, setHypothesis] = useState(initialData?.hypothesis || '');
  const [indicativeMetrics, setIndicativeMetrics] = useState(
    initialData?.indicative_metrics || ''
  );
  const [timeHorizon, setTimeHorizon] = useState(
    initialData?.time_horizon_months?.toString() || ''
  );
  const [selectedOutcomes, setSelectedOutcomes] = useState<string[]>(
    initialData?.outcome_ids || []
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    onSave({
      name: name.trim(),
      problem_statement: problemStatement.trim(),
      hypothesis: hypothesis.trim() || null,
      indicative_metrics: indicativeMetrics.trim() || null,
      time_horizon_months: timeHorizon ? parseInt(timeHorizon, 10) : null,
      outcome_ids: selectedOutcomes,
    });
  };

  const toggleOutcome = (outcomeId: string) => {
    setSelectedOutcomes((prev) =>
      prev.includes(outcomeId)
        ? prev.filter((id) => id !== outcomeId)
        : [...prev, outcomeId]
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="theme-name" className="block text-sm font-medium text-foreground mb-1">
          Name <span className="text-destructive">*</span>
        </label>
        <input
          id="theme-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={100}
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          placeholder="e.g., First Week Magic"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          {name.length}/100 characters
        </p>
      </div>

      <div>
        <label htmlFor="theme-problem" className="block text-sm font-medium text-foreground mb-1">
          Problem Statement <span className="text-destructive">*</span>
        </label>
        <textarea
          id="theme-problem"
          value={problemStatement}
          onChange={(e) => setProblemStatement(e.target.value)}
          maxLength={1500}
          rows={3}
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          placeholder="What problem are we solving?"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          {problemStatement.length}/1500 characters
        </p>
      </div>

      <div>
        <label htmlFor="theme-hypothesis" className="block text-sm font-medium text-foreground mb-1">
          Hypothesis
        </label>
        <textarea
          id="theme-hypothesis"
          value={hypothesis}
          onChange={(e) => setHypothesis(e.target.value)}
          maxLength={1500}
          rows={3}
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          placeholder="What's your expected outcome?"
        />
        <p className="text-xs text-muted-foreground mt-1">
          {hypothesis.length}/1500 characters
        </p>
      </div>

      <div>
        <label htmlFor="theme-metrics" className="block text-sm font-medium text-foreground mb-1">
          Indicative Metrics
        </label>
        <textarea
          id="theme-metrics"
          value={indicativeMetrics}
          onChange={(e) => setIndicativeMetrics(e.target.value)}
          maxLength={1000}
          rows={2}
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          placeholder="How will you measure success?"
        />
        <p className="text-xs text-muted-foreground mt-1">
          {indicativeMetrics.length}/1000 characters
        </p>
      </div>

      <div>
        <label htmlFor="theme-time-horizon" className="block text-sm font-medium text-foreground mb-1">
          Time Horizon (months)
        </label>
        <input
          id="theme-time-horizon"
          type="number"
          value={timeHorizon}
          onChange={(e) => setTimeHorizon(e.target.value)}
          min={0}
          max={12}
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          placeholder="0-12 months"
        />
        <p className="text-xs text-muted-foreground mt-1">
          Valid range: 0-12 months
        </p>
      </div>

      {availableOutcomes.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Link to Product Outcomes
          </label>
          <div className="space-y-2">
            {availableOutcomes.map((outcome) => (
              <label key={outcome.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={selectedOutcomes.includes(outcome.id)}
                  onChange={() => toggleOutcome(outcome.id)}
                  className="rounded border-border"
                />
                <span className="text-sm text-foreground">{outcome.name}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={isSaving || !name.trim() || !problemStatement.trim()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? 'Saving...' : mode === 'create' ? 'Create Theme' : 'Update Theme'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isSaving}
          className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90 disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};
