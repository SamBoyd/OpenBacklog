import React from 'react';
import { TaskStatus } from '#types';
import TaskChecklist from '#components/reusable/TaskChecklist';
import TaskProgressBar from '#components/reusable/TaskProgressBar';
import Card from './Card';

export interface UniversalKanbanCardProps {
    identifier: string;
    title: string;
    status?: TaskStatus;
    checklist?: { title: string; is_complete: boolean }[];
}

const UniversalKanbanCard = ({
    identifier,
    title,
    status,
    checklist = [],
}: UniversalKanbanCardProps) => {
    return (
        <Card dataTestId="kanban-card">
            <div className="e-card-content pt-5 px-5 flex flex-col gap-2 rounded">
                <div className="card-template-wrap">
                    {/* Removed style prop, text color is inherited */}
                    <span>{title}</span>
                </div>
                {status === TaskStatus.IN_PROGRESS && checklist.length > 0 && (
                    <>
                        <TaskChecklist items={checklist} numberOfItemsToShow={4} />
                        <TaskProgressBar items={checklist} maxDots={6} />
                    </>
                )}
                <div className="flex justify-end">
                    <div className="text-muted">{identifier}</div>
                </div>
            </div>
        </Card>
    );
};

export default UniversalKanbanCard;
