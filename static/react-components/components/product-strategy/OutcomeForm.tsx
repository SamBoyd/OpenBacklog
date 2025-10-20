import React, { useState } from 'react';

interface OutcomeFormProps {
  mode?: 'create' | 'edit';
  initialData?: {
    name: string;
    description?: string | null;
    metrics?: string | null;
    time_horizon_months?: number | null;
    pillar_ids?: string[];
  };
  availablePillars: Array<{ id: string; name: string }>;
  onSave: (data: {
    name: string;
    description?: string | null;
    metrics?: string | null;
    time_horizon_months?: number | null;
    pillar_ids?: string[];
  }) => void;
  onCancel: () => void;
  isSaving: boolean;
}

export const OutcomeForm: React.FC<OutcomeFormProps> = ({
  mode = 'create',
  initialData,
  availablePillars,
  onSave,
  onCancel,
  isSaving,
}) => {
  const [name, setName] = useState(initialData?.name || '');
  const [description, setDescription] = useState(initialData?.description || '');
  const [metrics, setMetrics] = useState(initialData?.metrics || '');
  const [timeHorizon, setTimeHorizon] = useState(
    initialData?.time_horizon_months?.toString() || ''
  );
  const [selectedPillars, setSelectedPillars] = useState<string[]>(
    initialData?.pillar_ids || []
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    onSave({
      name: name.trim(),
      description: description.trim() || null,
      metrics: metrics.trim() || null,
      time_horizon_months: timeHorizon ? parseInt(timeHorizon, 10) : null,
      pillar_ids: selectedPillars,
    });
  };

  const togglePillar = (pillarId: string) => {
    setSelectedPillars((prev) =>
      prev.includes(pillarId)
        ? prev.filter((id) => id !== pillarId)
        : [...prev, pillarId]
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="outcome-name" className="block text-sm font-medium text-foreground mb-1">
          Name <span className="text-destructive">*</span>
        </label>
        <input
          id="outcome-name"
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          maxLength={150}
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          placeholder="e.g., 80% of users use AI weekly"
          required
        />
        <p className="text-xs text-muted-foreground mt-1">
          {name.length}/150 characters
        </p>
      </div>

      <div>
        <label htmlFor="outcome-description" className="block text-sm font-medium text-foreground mb-1">
          Description
        </label>
        <textarea
          id="outcome-description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={1500}
          rows={3}
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          placeholder="Describe what this outcome represents..."
        />
        <p className="text-xs text-muted-foreground mt-1">
          {description.length}/1500 characters
        </p>
      </div>

      <div>
        <label htmlFor="outcome-metrics" className="block text-sm font-medium text-foreground mb-1">
          Metrics
        </label>
        <textarea
          id="outcome-metrics"
          value={metrics}
          onChange={(e) => setMetrics(e.target.value)}
          maxLength={1000}
          rows={2}
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          placeholder="How will you measure this outcome?"
        />
        <p className="text-xs text-muted-foreground mt-1">
          {metrics.length}/1000 characters
        </p>
      </div>

      <div>
        <label htmlFor="outcome-time-horizon" className="block text-sm font-medium text-foreground mb-1">
          Time Horizon (months)
        </label>
        <input
          id="outcome-time-horizon"
          type="number"
          value={timeHorizon}
          onChange={(e) => setTimeHorizon(e.target.value)}
          min={6}
          max={36}
          className="w-full px-3 py-2 border border-border rounded-md bg-background text-foreground"
          placeholder="6-36 months"
        />
        <p className="text-xs text-muted-foreground mt-1">
          Valid range: 6-36 months
        </p>
      </div>

      {availablePillars.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Link to Strategic Pillars
          </label>
          <div className="space-y-2">
            {availablePillars.map((pillar) => (
              <label key={pillar.id} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={selectedPillars.includes(pillar.id)}
                  onChange={() => togglePillar(pillar.id)}
                  className="rounded border-border"
                />
                <span className="text-sm text-foreground">{pillar.name}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={isSaving || !name.trim()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? 'Saving...' : mode === 'create' ? 'Create Outcome' : 'Update Outcome'}
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

