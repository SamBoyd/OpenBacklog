import React from 'react';
import ViewHeader from './ViewHeader';
import ViewFooter from './ViewFooter';
import ErrorToast from './ErrorToast';

/**
 * ItemView component that provides a common wrapper for viewing items like tasks and initiatives
 * @param {object} props - The component props
 * @returns {React.ReactElement} The ItemView component
 */
type ItemViewProps = {
  identifier?: string;
  status?: string;
  loading: boolean;
  isEntityLocked: boolean;
  error: string | null;
  createdAt?: string;
  updatedAt?: string;
  children: React.ReactNode;
  className?: string;
  onDelete: () => void;
  onRefresh?: () => void;
  dataTestId?: string;
};

const ItemView = ({
  identifier,
  status,
  loading,
  isEntityLocked,
  error,
  createdAt,
  updatedAt,
  children,
  className = "p-2.5 mx-auto rounded w-full relative",
  onDelete,
  onRefresh,
  dataTestId = "item-view",
}: ItemViewProps) => {
  return (
    <div className={className} data-testid={dataTestId}>
      {/* Header */}
      <div>
        <ViewHeader
          identifier={identifier}
          status={status}
          loading={loading}
          onDelete={onDelete}
          onRefresh={onRefresh}
          isEntityLocked={isEntityLocked}
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

export default ItemView;
