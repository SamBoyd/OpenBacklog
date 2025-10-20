import React, { useState } from 'react';

const MIN_NAME_LENGTH = 1;
const MAX_NAME_LENGTH = 100;
const MAX_DESCRIPTION_LENGTH = 1000;
const MAX_ANTI_STRATEGY_LENGTH = 1000;

export interface PillarFormProps {
  onSave: (data: {
    name: string;
    description?: string | null;
    anti_strategy?: string | null;
  }) => void;
  onCancel: () => void;
  isSaving: boolean;
}

/**
 * PillarForm component for creating new strategic pillars
 * @param {PillarFormProps} props - Component props
 * @param {Function} props.onSave - Callback when user saves pillar
 * @param {Function} props.onCancel - Callback when user cancels
 * @param {boolean} props.isSaving - Whether save operation is in progress
 * @returns {React.ReactElement} The pillar form component
 */
export const PillarForm: React.FC<PillarFormProps> = ({
  onSave,
  onCancel,
  isSaving,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [antiStrategy, setAntiStrategy] = useState('');
  const [error, setError] = useState<string | null>(null);

  const handleSave = () => {
    if (name.length < MIN_NAME_LENGTH) {
      setError('Pillar name must be at least 1 character');
      return;
    }
    if (name.length > MAX_NAME_LENGTH) {
      setError(`Pillar name must be ${MAX_NAME_LENGTH} characters or less`);
      return;
    }
    if (description.length > MAX_DESCRIPTION_LENGTH) {
      setError(
        `Description must be ${MAX_DESCRIPTION_LENGTH} characters or less`
      );
      return;
    }
    if (antiStrategy.length > MAX_ANTI_STRATEGY_LENGTH) {
      setError(
        `Anti-strategy must be ${MAX_ANTI_STRATEGY_LENGTH} characters or less`
      );
      return;
    }

    setError(null);
    onSave({
      name,
      description: description.trim() || null,
      anti_strategy: antiStrategy.trim() || null,
    });
  };

  const handleCancel = () => {
    setName('');
    setDescription('');
    setAntiStrategy('');
    setError(null);
    onCancel();
  };

  const isNameValid =
    name.length >= MIN_NAME_LENGTH && name.length <= MAX_NAME_LENGTH;

  return (
    <div className="space-y-4 bg-card rounded-lg border border-border p-6">
      <h3 className="text-lg font-semibold text-foreground mb-4">
        Add Strategic Pillar
      </h3>

      <div>
        <label
          htmlFor="pillar-name"
          className="block text-sm font-medium text-foreground mb-2"
        >
          Name <span className="text-destructive">*</span>
        </label>
        <input
          id="pillar-name"
          type="text"
          className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g., Developer Experience"
          disabled={isSaving}
        />
        <div className="flex justify-between items-center mt-1">
          <span
            className={`text-sm ${
              name.length > MAX_NAME_LENGTH
                ? 'text-destructive'
                : 'text-muted-foreground'
            }`}
          >
            {name.length} / {MAX_NAME_LENGTH} characters
          </span>
        </div>
      </div>

      <div>
        <label
          htmlFor="pillar-description"
          className="block text-sm font-medium text-foreground mb-2"
        >
          Description (Optional)
        </label>
        <textarea
          id="pillar-description"
          className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What does this pillar represent?"
          disabled={isSaving}
        />
        <div className="flex justify-between items-center mt-1">
          <span
            className={`text-sm ${
              description.length > MAX_DESCRIPTION_LENGTH
                ? 'text-destructive'
                : 'text-muted-foreground'
            }`}
          >
            {description.length} / {MAX_DESCRIPTION_LENGTH} characters
          </span>
        </div>
      </div>

      <div>
        <label
          htmlFor="pillar-anti-strategy"
          className="block text-sm font-medium text-foreground mb-2"
        >
          Anti-Strategy (Optional)
        </label>
        <textarea
          id="pillar-anti-strategy"
          className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          rows={3}
          value={antiStrategy}
          onChange={(e) => setAntiStrategy(e.target.value)}
          placeholder="What won't you do to achieve this?"
          disabled={isSaving}
        />
        <div className="flex justify-between items-center mt-1">
          <span
            className={`text-sm ${
              antiStrategy.length > MAX_ANTI_STRATEGY_LENGTH
                ? 'text-destructive'
                : 'text-muted-foreground'
            }`}
          >
            {antiStrategy.length} / {MAX_ANTI_STRATEGY_LENGTH} characters
          </span>
        </div>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={!isNameValid || isSaving}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? 'Saving...' : 'Save Pillar'}
        </button>
        <button
          onClick={handleCancel}
          disabled={isSaving}
          className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90 disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};
