import React, { useState } from 'react';
import { Button } from '#components/reusable/Button';
import Modal from '#components/reusable/Modal';
import { Input } from '#components/reusable/Input';

/**
 * Props for the WorkspaceCreateModal component
 */
interface WorkspaceCreateModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (name: string) => void;
    isProcessing: boolean;
    isEnabled: boolean;
}

/**
 * Modal for creating a new workspace
 */
const WorkspaceCreateModal: React.FC<WorkspaceCreateModalProps> = ({
    isOpen,
    onClose,
    onSubmit,
    isProcessing,
    isEnabled,
}) => {
    const [name, setName] = useState('');
    const [error, setError] = useState('');

    if (!isOpen) {
        return null;
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (!name.trim()) {
            setError('Workspace name is required');
            return;
        }

        onSubmit(name.trim());
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <div className="bg-white rounded-lg p-6 w-full max-w-md">
                <h2 className="text-lg font-bold mb-4">Create New Workspace</h2>

                <form onSubmit={handleSubmit}>
                    <div className="mb-4">
                        <label htmlFor="workspace-name" className="block text-sm font-medium text-gray-700 mb-1">
                            Workspace Name
                        </label>
                        <Input
                            id="workspace-name"
                            value={name}
                            onChange={(e) => {
                                setName(e.target.value);
                                if (error) setError('');
                            }}
                            placeholder="Enter workspace name"
                            disabled={isProcessing || !isEnabled}
                            dataTestId="workspace-name-input"
                        />
                        {error && (
                            <p className="mt-1 text-sm text-red-600" data-testid="workspace-name-error">
                                {error}
                            </p>
                        )}
                    </div>


                    {/* Message explaining the single workspace limit */}
                    {!isEnabled && (
                        <div className='border border-red-200 bg-red-50 p-4 rounded-md mb-4'>
                            <p className="text-sm text-red-600">
                                You have reached the maximum number of workspaces allowed. We're looking
                                to increase the limit soon!
                            </p>
                        </div>

                    )}

                    <div className="flex justify-end space-x-3">
                        <Button
                            onClick={onClose}
                            disabled={isProcessing}
                            dataTestId="workspace-create-cancel"
                        >
                            Cancel
                        </Button>
                        <Button
                            disabled={isProcessing || !isEnabled}
                            dataTestId="workspace-create-submit"
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

export default WorkspaceCreateModal;
