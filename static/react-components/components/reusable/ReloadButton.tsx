import React from 'react';
import { Button } from './Button';

type ReloadButtonProps = {
  onClick: () => void;
  children?: React.ReactNode;
};

const ReloadButton = ({ onClick, children }: ReloadButtonProps) => {
  return (
    <Button
      onClick={onClick}
      className={`flex justify-center items-center bg-transparent 
        border border-gray-200 rounded-md p-1.5 cursor-pointer 
        hover:bg-gray-100 active:bg-gray-200 focus:outline-none 
        focus-visible:outline-none focus:not-focus-visible:outline-none`}
    >
      {children || 'Reload'}
    </Button>
  );
};

export default ReloadButton;
