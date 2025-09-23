import React from 'react';

import { TaskDto } from '#types';
import Card from './Card';
import { Skeleton } from './Skeleton';


type ListItemProps = {
    task: TaskDto;
    onClick: () => void;
};

interface GroupHeaderProps {
    groupStatus: string;
    data: any[];
}


export const ListItem = ({ task, onClick }: ListItemProps) => {
    return (
        <Card
            dataTestId={`list-item-${task.id}`}
            key={task.id}
            className="min-h-10 px-3 h-[1.5rem] border rounded bg-background hover:bg-muted-foreground/10"
            onClick={onClick}
        >
            <div className="flex-grow">
                <span className="text-sm/6 font-semibold text-muted">{task.identifier}</span>
                <span className="ml-4 text-sm/6 font-semibold text-foreground">{task.title}</span>
            </div>
        </Card>
    );
};

export const LoadingListItem = () => {
    return (
        <div
            data-testid="loading-list-item"
            className="flex flex-row justify-start items-start flex-grow space-x-1 px-3 h-[1.5rem] rounded hover:bg-muted-foreground/5 cursor-pointer opacity-40"
        >
            <Skeleton type="text" className="w-[30px]" />
            <Skeleton type="text" className="w-[200px]" />
        </div>
    );
};

export const GroupHeader = ({ groupStatus, data }: GroupHeaderProps) => (
    <div
        className="border border-border rounded bg-background px-3 py-1.5 mb-2 text-foreground font-semibold"
        data-testid="group-header"
    >
        {groupStatus} {data.length > 0 && `(${data.length})`}
    </div>
);

