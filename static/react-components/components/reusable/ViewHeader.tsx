import React from 'react';
import { GrBraille, } from 'react-icons/gr';
import { RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router';
import { Button, DangerButton, NoBorderButton, PrimaryButton } from './Button';

import { TaskStatus, statusDisplay } from '#types';
import { Skeleton } from './Skeleton';

/**
 * Props for the ViewHeader component
 * @param {object} props - The component props
 * @param {string} props.identifier - The identifier of the item (task/initiative ID)
 * @param {string} props.status - The current status
 * @param {boolean} props.loading - Whether the data is loading
 * @param {boolean} props.hasChanged - Whether there are unsaved changes
 * @param {() => void} props.onSave - Function to call when saving changes
 * @param {() => void} props.onDelete - Function to call when deleting
 * @returns {React.ReactElement} The header component
 */
interface ViewHeaderProps {
  identifier?: string;
  status?: string;
  loading?: boolean;
  isEntityLocked?: boolean;
  hasChanged?: boolean;
  onSave?: () => void;
  onDelete?: () => void;
  onRefresh?: () => void;
}

const ViewHeader: React.FC<ViewHeaderProps> = ({
  identifier,
  status,
  loading = false,
  isEntityLocked = false,
  hasChanged = false,
  onSave,
  onDelete,
  onRefresh,
}) => {
  const [isDeleteModalOpen, setIsDeleteModalOpen] = React.useState(false);
  const [isRefreshing, setIsRefreshing] = React.useState(false);
  const navigate = useNavigate();


  const handleConfirmDelete = () => {
    if (onDelete) {
      onDelete();
    }
    setIsDeleteModalOpen(false);
    navigate(-1);
  };

  const handleRefresh = async () => {
    if (onRefresh && !isRefreshing) {
      setIsRefreshing(true);
      try {
        await onRefresh();
      } catch (error) {
        console.error('Refresh failed:', error);
      }
      // Keep spinning for a minimum duration for visual feedback
      setTimeout(() => setIsRefreshing(false), 500);
    }
  };

  return (
    <>
      <div
        className={`flex justify-between items-center border border-border rounded p-4 h-16 `}
        data-testid="view-header"
      >
        <div className="flex justify-between items-center text-foreground" data-testid="header-left">

          <Button
            onClick={() => navigate(-1)}
            dataTestId="navigation-button"
            noBorder={true}
            className="mr-4"
            disabled={isEntityLocked}
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="size-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 15 3 9m0 0 6-6M3 9h12a6 6 0 0 1 0 12h-3" />
            </svg>
          </Button>
          <GrBraille size={20} />
          <div className="border-l pl-2 ml-2 h-[20px]" data-testid="item-info">
            {loading && (
              <Skeleton type="text" className="w-[200px]" />
            )}

            {!loading && identifier && !isEntityLocked && (
              <>
                {identifier} / {statusDisplay(status as TaskStatus)}
              </>
            )}

            {isEntityLocked && !loading && (
              <>
                <span>
                  Generating
                </span>
                <span className="animate-dots">
                  <span>.</span><span>.</span><span>.</span><span>.</span><span>.</span><span>.</span>
                </span>
              </>
            )}
          </div>
        </div>

        <div className="flex flex-row gap-x-2" data-testid="header-right">
          {hasChanged && onSave && (
            <PrimaryButton
              onClick={onSave}
              dataTestId="save-button-top"
            >
              Save
            </PrimaryButton>
          )}

          {onRefresh && (
            <NoBorderButton
              onClick={handleRefresh}
              disabled={loading || isRefreshing}
              dataTestId="refresh-button"
              title="Refresh data"
            >
              <RefreshCw className={`size-6 transition-transform duration-500 ${isRefreshing ? 'animate-spin' : ''}`} />
            </NoBorderButton>
          )}

          <div className="relative">
            <NoBorderButton
              onClick={() => setIsDeleteModalOpen(true)}
              disabled={loading}
              dataTestId="more-menu-button"
            >
              {/* Trash bin icon */}
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-6">
                <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
              </svg>

            </NoBorderButton>
          </div>
        </div>
      </div >

      {/* Delete Modal */}
      {
        isDeleteModalOpen && !isEntityLocked && (
          <div
            onClick={() => setIsDeleteModalOpen(false)}
            className="fixed inset-0 bg-foreground bg-opacity-5 z-50"
            data-testid="delete-modal"
          >
            <div className="mt-20 bg-background border border-border rounded-md text-foreground my-10 mx-auto p-10  w-fit flex flex-col gap-4 items-center justify-center">
              <div>
                <p>Are you sure? </p>
                <p>Once deleted, it can't be recovered.</p>
              </div>

              <div className="flex flex-row justify-around w-full m-2 gap-4">
                <DangerButton
                  onClick={handleConfirmDelete}
                  dataTestId="confirm-delete"
                  className='bg-background'
                >
                  Yes, delete it
                </DangerButton>
                <Button
                  onClick={() => setIsDeleteModalOpen(false)}
                  dataTestId="cancel-delete"
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        )
      }
    </>
  );
};

export default ViewHeader;
