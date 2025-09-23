import React, { useState } from 'react';
import Modal from '#components/reusable/Modal';
import { Button } from '#components/reusable/Button';
import { Input } from '#components/reusable/Input';

/**
 * Props for the CreateFirstWorkspaceModal component
 */
interface CreateFirstWorkspaceModalProps {
  /**
   * Whether the modal is currently open
   */
  isOpen: boolean;

  /**
   * Callback function when the modal is closed without creating a workspace
   */
  onClose: () => void;

  /**
   * Callback function when a workspace is created
   * @param name The name of the new workspace
   */
  onSubmit: (name: string) => void;

  /**
   * Whether a workspace creation operation is in progress
   */
  isProcessing: boolean;

  error?: string | null;
}

/**
 * Modal component shown to new users to create their first workspace
 */
const CreateFirstWorkspaceModal: React.FC<CreateFirstWorkspaceModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isProcessing,
  error = null,
}) => {
  const [workspaceName, setWorkspaceName] = useState('');
  const [errorDisplay, setErrorDisplay] = useState<string | null>(error);

  /**
   * Handles the form submission
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Validate the workspace name
    if (!workspaceName.trim()) {
      setErrorDisplay('Workspace name is required');
      return;
    }

    // Clear any previous errors and submit
    setErrorDisplay(null);
    onSubmit(workspaceName.trim());
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <div className="p-6 max-w-md w-full bg-background rounded-lg">
        <h2 className="text-lg font-bold mb-4 text-foreground">Welcome to Your Workspace</h2>
        <p className="mb-6 text-foreground">
          To get started, you need to create a workspace. A workspace is where you'll organize all your projects and tasks.
          This is a required step to use the platform.
        </p>

        <form>
          <div className="mb-4">
            <label htmlFor="workspace-name" className="block text-sm font-medium text-foreground mb-1">
              Workspace Name
            </label>
            <Input
              id="workspace-name"
              value={workspaceName}
              onChange={(e) => setWorkspaceName(e.target.value)}
              placeholder="My Workspace"
              disabled={isProcessing}
              dataTestId="workspace-name-input"
              autoFocus={true}
            />
            {errorDisplay && <p className="mt-1 text-sm text-destructive" data-testid="error-message">{errorDisplay}</p>}
          </div>

          <div className="flex justify-end mt-6">
            <Button
              disabled={isProcessing}
              dataTestId="create-workspace-button"
              onClick={handleSubmit}
            >
              {isProcessing ? 'Creating...' : 'Create Workspace'}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

export default CreateFirstWorkspaceModal;
