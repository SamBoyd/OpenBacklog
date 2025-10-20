import React from 'react';
import { useWorkspaces } from '#hooks/useWorkspaces';
import { useStrategicPillars } from '#hooks/useStrategicPillars';
import { ProductVision } from '#components/product-strategy/ProductVision';
import { StrategicPillars } from '#components/product-strategy/StrategicPillars';
import { ProductOutcomes } from '#components/product-strategy/ProductOutcomes';

/**
 * ProductStrategy page component for managing workspace product vision
 * @returns {React.ReactElement} The product strategy page
 */
const ProductStrategy: React.FC = () => {
  const { currentWorkspace } = useWorkspaces();
  const workspaceId = currentWorkspace?.id || '';

  const { pillars } = useStrategicPillars(workspaceId);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-foreground mb-6">
        Product Strategy
      </h1>

      <ProductVision workspaceId={workspaceId} />

      <StrategicPillars workspaceId={workspaceId} />

      <ProductOutcomes
        workspaceId={workspaceId}
        availablePillars={pillars.map((p) => ({ id: p.id, name: p.name }))}
      />
    </div>
  );
};

export default ProductStrategy;
