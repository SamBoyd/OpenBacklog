import React, { useState } from 'react';
import { useProductVision } from '#hooks/useProductVision';
import { VisionEditor } from './VisionEditor';

interface ProductVisionProps {
  workspaceId: string;
}

export const ProductVision: React.FC<ProductVisionProps> = ({ workspaceId }) => {
  const {
    vision,
    isLoading,
    error,
    upsertVision,
    isUpserting,
    upsertError,
  } = useProductVision(workspaceId);

  const [isEditingVision, setIsEditingVision] = useState(false);

  const handleSaveVision = (text: string) => {
    upsertVision(
      { vision_text: text },
      {
        onSuccess: () => {
          setIsEditingVision(false);
        },
      }
    );
  };

  const handleCancelVision = () => {
    setIsEditingVision(false);
  };

  if (isLoading) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">
          Product Vision
        </h2>
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-card rounded-lg border border-border p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">
          Product Vision
        </h2>
        <p className="text-destructive">Error loading vision</p>
      </div>
    );
  }

  return (
    <div className="bg-card rounded-lg border border-border p-6">
      <h2 className="text-xl font-semibold text-foreground mb-4">
        Product Vision
      </h2>

      {!isEditingVision && (
        <div>
          {vision ? (
            <div className="space-y-4">
              <p className="text-foreground whitespace-pre-wrap">
                {vision.vision_text}
              </p>
              <button
                onClick={() => setIsEditingVision(true)}
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
                onClick={() => setIsEditingVision(true)}
                className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
              >
                Define Vision
              </button>
            </div>
          )}
        </div>
      )}

      {isEditingVision && (
        <VisionEditor
          initialText={vision?.vision_text || ''}
          onSave={handleSaveVision}
          onCancel={handleCancelVision}
          isSaving={isUpserting}
        />
      )}

      {upsertError && (
        <p className="text-destructive mt-4">
          {(upsertError as Error).message}
        </p>
      )}
    </div>
  );
};

