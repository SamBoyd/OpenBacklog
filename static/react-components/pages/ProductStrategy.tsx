import React, { useState } from 'react';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useProductVision } from '#hooks/useProductVision';
import { VisionEditor } from '#components/product-strategy/VisionEditor';

/**
 * ProductStrategy page component for managing workspace product vision
 * @returns {React.ReactElement} The product strategy page
 */
const ProductStrategy: React.FC = () => {
  const { currentWorkspace } = useWorkspaces();
  const workspaceId = currentWorkspace?.id || '';

  const {
    vision,
    isLoading,
    error,
    upsertVision,
    isUpserting,
    upsertError,
  } = useProductVision(workspaceId);

  const [isEditing, setIsEditing] = useState(false);

  const handleSave = (text: string) => {
    upsertVision(
      { vision_text: text },
      {
        onSuccess: () => {
          setIsEditing(false);
        },
      }
    );
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-destructive">Error loading vision</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-foreground mb-6">
        Product Strategy
      </h1>

      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">
          Product Vision
        </h2>

        {!isEditing && (
          <div>
            {vision ? (
              <div className="space-y-4">
                <p className="text-foreground whitespace-pre-wrap">
                  {vision.vision_text}
                </p>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  Edit Vision
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-muted-foreground">
                  No vision defined yet. Define your product vision to guide
                  your strategic planning.
                </p>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                >
                  Define Vision
                </button>
              </div>
            )}
          </div>
        )}

        {isEditing && (
          <VisionEditor
            initialText={vision?.vision_text || ''}
            onSave={handleSave}
            onCancel={handleCancel}
            isSaving={isUpserting}
          />
        )}

        {upsertError && (
          <p className="text-destructive mt-4">
            {(upsertError as Error).message}
          </p>
        )}
      </div>
    </div>
  );
};

export default ProductStrategy;
