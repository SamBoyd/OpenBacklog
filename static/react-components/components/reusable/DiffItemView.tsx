import React from 'react';
import ViewFooter from './ViewFooter';
import ErrorToast from './ErrorToast';
import DiffViewHeader from './DiffViewHeader';

/**
 * DiffItemView component that provides a common wrapper for viewing items like tasks and initiatives
 * @param {object} props - The component props
 * @returns {React.ReactElement} The DiffItemView component
 */
type DiffItemViewProps = {
  identifier?: string;
  status?: string;
  loading: boolean;
  hasChanged: boolean;
  error: string | null;
  createdAt?: string;
  updatedAt?: string;
  children: React.ReactNode;
  className?: string;
  allResolved: boolean;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  onSave: () => void;
  onRollbackAll: () => void;
  dataTestId?: string;
};

const DiffItemView = ({
  identifier,
  status,
  loading,
  hasChanged,
  error,
  createdAt,
  updatedAt,
  children,
  className = "p-2.5 mx-auto rounded w-full relative",
  allResolved,
  onAcceptAll,
  onRejectAll,
  onSave,
  onRollbackAll,
  dataTestId = "item-view",
}: DiffItemViewProps) => {
  return (
    <div className={className} data-testid={dataTestId}>
      {/* Header */}
      <div>
        <DiffViewHeader
          identifier={identifier}
          status={status}
          loading={loading}
          hasChanged={hasChanged}
          allResolved={allResolved}
          onAcceptAll={onAcceptAll}
          onRejectAll={onRejectAll}
          onRollbackAll={onRollbackAll}
          onSave={onSave}
        />

        {/* Content */}
        {children}
      </div>

      {/* Footer */}
      <ViewFooter
        createdAt={createdAt}
        updatedAt={updatedAt}
        loading={loading}
      />

      {/* Toast for errors */}
      <ErrorToast error={error} />
    </div>
  );
};

export default DiffItemView;
