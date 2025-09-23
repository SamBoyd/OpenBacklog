import React from 'react';
import { GrBraille } from 'react-icons/gr';
import { useNavigate } from 'react-router';

import { Button, PrimaryButton } from './Button';
import { ResolveAllButtons } from '#components/diffs/reusable/ActionButtons';
import { Skeleton } from './Skeleton';
import { TaskStatus, statusDisplay } from '#types';

/**
 * Props for the DiffViewHeader component
 * @param {object} props - The component props
 * @param {string} props.identifier - The identifier of the item (task/initiative ID)
 * @param {string} props.status - The current status
 * @param {boolean} props.loading - Whether the data is loading
 * @param {boolean} props.hasChanged - Whether there are unsaved changes
 * @param {() => void} props.onSave - Function to call when saving changes
 * @returns {React.ReactElement} The header component
 */
interface DiffViewHeaderProps {
  identifier?: string;
  status?: string;
  loading?: boolean;
  hasChanged?: boolean;
  allResolved?: boolean;
  onAcceptAll: () => void;
  onRejectAll: () => void;
  onRollbackAll: () => void;
  onSave: () => void;
}

const DiffViewHeader: React.FC<DiffViewHeaderProps> = ({
  identifier,
  status,
  loading = false,
  hasChanged = false,
  allResolved = false,
  onAcceptAll,
  onRejectAll,
  onRollbackAll,
  onSave,
}) => {
  const navigate = useNavigate();

  return (
    <div
      className={`sticky top-0 z-10 flex justify-between items-center bg-background border border-border rounded px-4 py-2 `}
      data-testid="view-header"
    >
      <div className="flex justify-between items-center text-foreground" data-testid="header-left">
        <Button
          onClick={() => navigate(-1)}
          dataTestId="navigation-button"
          noBorder={true}
          className="mr-4"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="size-5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3" />
          </svg>
        </Button>

        <GrBraille size={20} />

        <div className="border-l pl-2 ml-2" data-testid="item-info">
          {!loading && identifier ? (
            <>
              {identifier} / {statusDisplay(status as TaskStatus)}
            </>
          ) : (
            <Skeleton type="text" className="w-[200px]" />
          )}
        </div>
      </div>


      <ResolveAllButtons
        loading={loading}
        hasAnyResolution={false}
        allSuggestionsResolved={allResolved}
        acceptAllSuggestions={onAcceptAll}
        rejectAllSuggestions={onRejectAll}
        rollbackAllSuggestions={onRollbackAll}
        onSaveChanges={onSave}
      />
    </div>
  );
};

export default DiffViewHeader;
