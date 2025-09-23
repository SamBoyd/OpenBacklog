import { PresetMessage } from '#components/ChatDialog/ChatDialog';


export enum InitiativeOperations {
    REWRITE_REPHRASE_RESTRUCTURE = "rewrite_rephrase_restructure",
    BREAK_DOWN = "break_down",
    PRIORITIZE = "prioritize",
    GENERATE_TASKS = "generate_tasks",
}

export enum TaskOperations {
    REWRITE_REPHRASE_RESTRUCTURE = "rewrite_rephrase_restructure",
    BREAK_DOWN = "break_down",
    PRIORITIZE = "prioritize",
    GENERATE_CHECKLIST = "generate_checklist",
}

export const INITIATIVE_PRESET_MESSAGES: PresetMessage[] = [
    {
        id: '1',
        shortText: 'Rewrite, rephrase, restructure',
        fullText: 'Rewrite, rephrase, restructure the initiative to make it more clear and concise',
        operation: InitiativeOperations.REWRITE_REPHRASE_RESTRUCTURE
    },
    {
        id: '2',
        shortText: 'Break down',
        fullText: 'Break down the initiative into smaller, more manageable tasks',
        operation: InitiativeOperations.BREAK_DOWN
    },
    {
        id: '3',
        shortText: 'Prioritize',
        fullText: 'Prioritize the initiative based on the most important tasks',
        operation: InitiativeOperations.PRIORITIZE
    },
    {
        id: '4',
        shortText: 'Generate tasks',
        fullText: 'Generate tasks to be completed to achieve the initiative',
        operation: InitiativeOperations.GENERATE_TASKS
    },
];

export const TASK_PRESET_MESSAGES: PresetMessage[] = [
    {
        id: '1',
        shortText: 'Rewrite, rephrase, restructure',
        fullText: 'Rewrite, rephrase, restructure the task to make it more clear and concise',
        operation: TaskOperations.REWRITE_REPHRASE_RESTRUCTURE
    },
    {
        id: '2',
        shortText: 'Break down',
        fullText: 'Break down the task into smaller, more manageable steps',
        operation: TaskOperations.BREAK_DOWN
    },
    {
        id: '3',
        shortText: 'Prioritize',
        fullText: 'Prioritize the task based on the most important steps',
        operation: TaskOperations.PRIORITIZE
    },
    {
        id: '4',
        shortText: 'Generate checklist',
        fullText: 'Generate a checklist to be completed to achieve the task',
        operation: TaskOperations.GENERATE_CHECKLIST
    }
];

