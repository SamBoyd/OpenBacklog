import React, { useState } from 'react';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useProductVision } from '#hooks/useProductVision';
import { useStrategicPillars } from '#hooks/useStrategicPillars';
import { VisionEditor } from '#components/product-strategy/VisionEditor';
import { PillarForm } from '#components/product-strategy/PillarForm';

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

  const {
    pillars,
    isLoading: isPillarsLoading,
    error: pillarsError,
    createPillar,
    isCreating,
    createError,
  } = useStrategicPillars(workspaceId);

  const [isEditingVision, setIsEditingVision] = useState(false);
  const [isAddingPillar, setIsAddingPillar] = useState(false);

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

  const handleSavePillar = (data: {
    name: string;
    description?: string | null;
    anti_strategy?: string | null;
  }) => {
    createPillar(data, {
      onSuccess: () => {
        setIsAddingPillar(false);
      },
    });
  };

  const handleCancelPillar = () => {
    setIsAddingPillar(false);
  };

  const maxPillarsReached = pillars.length >= 5;

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

      {/* Strategic Pillars Section */}
      <div className="bg-card rounded-lg border border-border p-6 mt-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-foreground">
            Strategic Pillars
          </h2>
          {!isAddingPillar && (
            <button
              onClick={() => setIsAddingPillar(true)}
              disabled={maxPillarsReached}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
              title={
                maxPillarsReached
                  ? 'Maximum of 5 pillars reached'
                  : 'Add a new strategic pillar'
              }
            >
              Add Pillar
            </button>
          )}
        </div>

        {isAddingPillar && (
          <div className="mb-6">
            <PillarForm
              onSave={handleSavePillar}
              onCancel={handleCancelPillar}
              isSaving={isCreating}
            />
          </div>
        )}

        {createError && (
          <p className="text-destructive mb-4">
            {(createError as Error).message}
          </p>
        )}

        {isPillarsLoading ? (
          <p className="text-muted-foreground">Loading pillars...</p>
        ) : pillarsError ? (
          <p className="text-destructive">Error loading pillars</p>
        ) : pillars.length === 0 ? (
          <p className="text-muted-foreground">
            No strategic pillars defined yet. Strategic pillars represent
            enduring ways to win that guide your initiatives.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {pillars.map((pillar) => (
              <div
                key={pillar.id}
                className="bg-background border border-border rounded-lg p-4"
              >
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  {pillar.name}
                </h3>
                {pillar.description && (
                  <p className="text-foreground text-sm mb-2">
                    {pillar.description}
                  </p>
                )}
                {pillar.anti_strategy && (
                  <div className="mt-2 pt-2 border-t border-border">
                    <p className="text-xs font-medium text-muted-foreground mb-1">
                      Anti-Strategy:
                    </p>
                    <p className="text-sm text-foreground">
                      {pillar.anti_strategy}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {maxPillarsReached && (
          <p className="text-sm text-muted-foreground mt-4">
            Maximum of 5 strategic pillars reached.
          </p>
        )}
      </div>
    </div>
  );
};

export default ProductStrategy;
