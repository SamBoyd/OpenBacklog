import React, { useState, useEffect } from 'react';

const MIN_LENGTH = 1;
const MAX_LENGTH = 1000;

export interface VisionEditorProps {
  initialText: string;
  onSave: (text: string) => void;
  onCancel: () => void;
  isSaving: boolean;
}

/**
 * VisionEditor component for editing workspace product vision
 * @param {VisionEditorProps} props - Component props
 * @param {string} props.initialText - Initial vision text
 * @param {Function} props.onSave - Callback when user saves vision
 * @param {Function} props.onCancel - Callback when user cancels editing
 * @param {boolean} props.isSaving - Whether save operation is in progress
 * @returns {React.ReactElement} The vision editor component
 */
export const VisionEditor: React.FC<VisionEditorProps> = ({
  initialText,
  onSave,
  onCancel,
  isSaving,
}) => {
  const [text, setText] = useState(initialText);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setText(initialText);
  }, [initialText]);

  const handleSave = () => {
    if (text.length < MIN_LENGTH) {
      setError('Vision must be at least 1 character');
      return;
    }
    if (text.length > MAX_LENGTH) {
      setError(`Vision must be ${MAX_LENGTH} characters or less`);
      return;
    }

    setError(null);
    onSave(text);
  };

  const handleCancel = () => {
    setText(initialText);
    setError(null);
    onCancel();
  };

  const charCount = text.length;
  const isValid = charCount >= MIN_LENGTH && charCount <= MAX_LENGTH;

  return (
    <div className="space-y-4">
      <div>
        <label
          htmlFor="vision-text"
          className="block text-sm font-medium text-foreground mb-2"
        >
          Product Vision
        </label>
        <textarea
          id="vision-text"
          className="w-full px-3 py-2 bg-background border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
          rows={6}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Enter your product vision..."
          disabled={isSaving}
        />
        <div className="flex justify-between items-center mt-2">
          <span
            className={`text-sm ${
              charCount > MAX_LENGTH ? 'text-destructive' : 'text-muted-foreground'
            }`}
          >
            {charCount} / {MAX_LENGTH} characters
          </span>
        </div>
        {error && <p className="text-sm text-destructive mt-2">{error}</p>}
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleSave}
          disabled={!isValid || isSaving}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSaving ? 'Saving...' : 'Save'}
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
