import React from 'react';

import { ChecklistItemDto, TaskDto } from '#types'

const checkedCircle = (
    <div className='bg-background'>
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="size-4">
            <path fillRule="evenodd" d="M2.25 12c0-5.385 4.365-9.75 9.75-9.75s9.75 4.365 9.75 9.75-4.365 9.75-9.75 9.75S2.25 17.385 2.25 12Zm13.36-1.814a.75.75 0 1 0-1.22-.872l-3.236 4.53L9.53 12.22a.75.75 0 0 0-1.06 1.06l2.25 2.25a.75.75 0 0 0 1.14-.094l3.75-5.25Z" clipRule="evenodd" />
        </svg>
    </div>
)

const uncheckedCircle = () => (
    <div className='absolute rounded-full border border-muted size-3 bg-background'></div>
)

interface TaskChecklistProps {
    items: { title: string; is_complete: boolean }[]
    numberOfItemsToShow: number
}

const TaskChecklist = ({ items, numberOfItemsToShow }: TaskChecklistProps) => {
    if (!items || items.length === 0) {
        return null;
    }

    const completedItems = items.filter(item => item.is_complete)
    const incompleteItems = items.filter(item => !item.is_complete)

    const numCompletedItems = completedItems.length
    const numIncompleteItems = incompleteItems.length;

    let itemsToShow: Partial<ChecklistItemDto>[] = [];

    if (numCompletedItems === 0) {
        itemsToShow = incompleteItems.slice(0, numberOfItemsToShow);
    } else if (numIncompleteItems === 0) {
        itemsToShow = completedItems.slice(0, numberOfItemsToShow);
    } else {
        itemsToShow = [completedItems[completedItems.length - 1], ...incompleteItems.slice(0, numberOfItemsToShow - 1)];
    }

    return (
        <div className="">
            <ul role="list" className="mb-2">
                {itemsToShow.map((item, i) => (
                    <li key={i}>
                        <div className="relative pb-2">
                            {i !== Math.min(numberOfItemsToShow, items.length) - 1 ? (
                                <span
                                    aria-hidden="true"
                                    className={
                                        `border-l border-muted -indent-px absolute left-1.5 top-1
                                        ${i === Math.min(itemsToShow.length, items.length) - 1 ? 'h-1/2' : 'h-full'}
                                        `
                                    }
                                />
                            ) : null}

                            <div className="relative flex space-x-2">
                                <div>
                                    <span className={'pt-0.5 flex size-3 items-center justify-center rounded-full text-muted'}>
                                        {item.is_complete ? checkedCircle : uncheckedCircle()}
                                    </span>
                                </div>

                                <div className={`
                                    text-xs text-muted-foreground 
                                    flex-1 min-w-0 whitespace-nowrap overflow-hidden text-ellipsis
                                    ${item.is_complete ? 'line-through' : ''}
                                `} >
                                    {item.title}{' '}
                                </div>
                            </div>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    )
}

export default TaskChecklist;
