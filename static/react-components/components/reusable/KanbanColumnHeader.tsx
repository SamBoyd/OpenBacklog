import React from 'react';

interface KanbanColumnHeaderProps {
  isFirstColumn: boolean;
  isLastColumn: boolean;
  headerText: string;
  numberOfTasks: number;
}

const KanbanColumnHeader = ({ isFirstColumn, isLastColumn, headerText, numberOfTasks }: KanbanColumnHeaderProps) => {
  return (
    <div
      className={`
          px-2 py-4
          header-template-wrap flex items-center justify-center
          bg-background 
          border-border border-b
          ${isFirstColumn ? 'rounded-bl-lg border-l ' : ''}
          ${isLastColumn ? 'rounded-br-lg border-r' : ''}
        `}
    >
      <div className="text-foreground">
        <span>{headerText}</span>
        <span className='pl-2'>({numberOfTasks})</span>        
      </div>
    </div >
  );
};

export default KanbanColumnHeader;
