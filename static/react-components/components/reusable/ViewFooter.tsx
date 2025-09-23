import React from 'react';
import dayjs from 'dayjs';
import { Button } from './Button';
import { Skeleton } from './Skeleton';


/**
 * Footer component for task and initiative views
 * @param {object} props - The component props
 * @param {string} props.createdAt - The creation timestamp
 * @param {string} props.updatedAt - The last update timestamp
 * @param {boolean} props.loading - Whether the data is loading
 * @param {boolean} props.hasChanged - Whether there are unsaved changes
 * @param {() => void} props.onSave - Function to call when saving changes
 * @returns {React.ReactElement} The footer component
 */
interface ViewFooterProps {
  createdAt?: string;
  updatedAt?: string;
  loading?: boolean;
  hasChanged?: boolean;
  onSave?: () => void;
}

const ViewFooter: React.FC<ViewFooterProps> = ({
  createdAt,
  updatedAt,
  loading = false,
  hasChanged = false,
  onSave
}) => {
  return (
    <div
      className="p-2 flex justify-between items-center"
      data-testid="view-footer"
    >
      {!loading && createdAt && updatedAt ? (
        <div className="text-gray-400 text-sm">
          <div data-testid="created-date">
            Created - {dayjs(createdAt).format('D MMM YYYY')}
          </div>
          <div data-testid="updated-date">
            Last updated - {dayjs(updatedAt).format('D MMM YYYY')}
          </div>
        </div>
      ) : (
        <Skeleton type="text" className="w-[100px]" />
      )}

      {/* Save Button */}
      {hasChanged && onSave && (
        <div className="" data-testid="save-button-container">
          <Button
            onClick={onSave}
            dataTestId="save-button"
          >
            Save
          </Button>
        </div>
      )}
    </div>
  );
};

export default ViewFooter;
