import { InitiativePayload, TaskPayload, CompletableText, InitiativeDto } from "#types";


export interface formatCompletableTextToJSONReturnType {
    initiatives: InitiativePayload[];
    initiativesToDelete: string[];
    tasksToDelete: string[];
    checklistItemsToDelete: string[];
}

export const formatCompletableTextToJSON = (items: CompletableText[]): formatCompletableTextToJSONReturnType => {
    const initiatives: InitiativePayload[] = [];
    let currentInitiative: InitiativePayload | null = null;
    let currentTask: TaskPayload | null = null;

    let initiativesToDelete: string[] = [];
    let tasksToDelete: string[] = [];
    let checklistItemsToDelete: string[] = [];

    if (items.length === 0) {
        return { initiatives, initiativesToDelete, tasksToDelete, checklistItemsToDelete };
    }

    items.forEach((item, i) => {
        if (item.title == '') {
            return;
        }

        if (item.tabLevel === 0) {
            currentInitiative = {
                id: item.id,
                title: item.title,
                status: item.isCompleted ? 'DONE' : 'TO_DO',
                tasks: [],
            };

            if (item.id && item.tabLevel !== item.originalTabLevel) {
                if (item.originalTabLevel === 1) {
                    tasksToDelete.push(item.id);
                } else if (item.originalTabLevel === 2) {
                    checklistItemsToDelete.push(item.id);
                } else {
                    throw new Error('Invalid tab level');
                }
            }

            initiatives.push(currentInitiative);
            currentTask = null;
        }

        if (item.tabLevel === 1) {
            if (!currentInitiative) {
                throw new Error('Task must be nested under an initiative');
            }

            currentTask = {
                id: item.id,
                title: item.title,
                status: item.isCompleted ? 'DONE' : 'TO_DO',
                checklist: [],
            };

            if (item.id && item.tabLevel !== item.originalTabLevel) {
                if (item.originalTabLevel === 0) {
                    initiativesToDelete.push(item.id);
                } else if (item.originalTabLevel === 2) {
                    checklistItemsToDelete.push(item.id);
                } else {
                    throw new Error('Invalid tab level');
                }
            }
            currentInitiative.tasks.push(currentTask);
        }

        if (item.tabLevel === 2) {
            if (!currentTask) {
                throw new Error('Checklist item must be nested under a task');
            }

            currentTask.checklist.push({
                id: item.id,
                title: item.title,
                is_complete: item.isCompleted,
                order: currentTask.checklist.length
            });

            if (item.id && item.tabLevel !== item.originalTabLevel) {
                if (item.originalTabLevel === 0) {
                    initiativesToDelete.push(item.id);
                } else if (item.originalTabLevel === 1) {
                    tasksToDelete.push(item.id);
                } else {
                    throw new Error('Invalid tab level');
                }
            }
        }
    });

    return { initiatives, initiativesToDelete, tasksToDelete, checklistItemsToDelete };
};

export const submitDataToApi = async (items: CompletableText[]) => {
    const initiatives = formatCompletableTextToJSON(items);

    await fetch('/api/initiative', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(initiatives)
    });
}

export const initiativesDataToCompletableText = (initiativesData: InitiativeDto[]): CompletableText[] => {
    let result: CompletableText[] = [];

    initiativesData.forEach((initiative) => {
        result.push({
            id: initiative.id,
            title: initiative.title,
            isCompleted: initiative.status === 'DONE',
            tabLevel: 0,
            originalTabLevel: 0,
        });

        initiative.tasks.forEach((task) => {
            result.push({
                id: task.id,
                title: task.title || '',
                isCompleted: task.status === 'DONE',
                tabLevel: 1,
                originalTabLevel: 1,
            });

            task.checklist?.forEach((checklistItem) => {
                result.push({
                    id: checklistItem.id,
                    title: checklistItem.title || '',
                    isCompleted: checklistItem.is_complete || false,
                    tabLevel: 2,
                    originalTabLevel: 2,
                });
            });
        });
    });

    return result;
};