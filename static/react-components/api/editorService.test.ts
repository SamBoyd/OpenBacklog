import { expect, test } from 'vitest'

import { formatCompletableTextToJSON, initiativesDataToCompletableText } from './editorService';
import { CompletableText, InitiativePayload } from '#types';

describe.skip('editorService', () => {
    describe.skip('formatCompletableTextToJSON', () => {
        it('should return a stringified JSON object of the correct form', () => {
            const items: CompletableText[] = [
                {
                    title: 'Item 1',
                    isCompleted: false,
                    tabLevel: 0,
                    originalTabLevel: 0,
                    id: '1',
                },
                {
                    title: 'Item 2',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 1,
                    id: '2',
                },
                {
                    title: 'Item 3',
                    isCompleted: true,
                    tabLevel: 2,
                    originalTabLevel: 2,
                    id: '3',
                },
                {
                    title: 'Item 4',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 1,
                },
                {
                    title: 'Item 5',
                    isCompleted: false,
                    tabLevel: 0,
                    originalTabLevel: 0,
                },
            ];

            const expected: InitiativePayload[] = [
                {
                    id: '1',
                    title: 'Item 1',
                    status: 'TO_DO',
                    tasks: [
                        {
                            id: '2',
                            title: 'Item 2',
                            status: 'TO_DO',
                            checklist: [
                                {
                                    id: '3',
                                    title: 'Item 3',
                                    is_complete: true,
                                    order: 0,
                                }
                            ]
                        },
                        {
                            title: 'Item 4',
                            status: 'TO_DO',
                            checklist: []
                        },
                    ]
                },
                {
                    title: 'Item 5',
                    status: 'TO_DO',
                    tasks: []
                },
            ]
            expect(formatCompletableTextToJSON(items).initiatives).toEqual(expected);
        });

        it('shoud return an empty array if there are no items', () => {
            const items: CompletableText[] = [];

            const expected: InitiativePayload[] = [];
            expect(formatCompletableTextToJSON(items).initiatives).toEqual(expected);
        });

        it('it should return the intiatives to delete which are converted to tasks and checklist items', () => {
            const items: CompletableText[] = [
                {
                    id: '1',
                    title: 'Item 1',
                    isCompleted: false,
                    tabLevel: 0,
                    originalTabLevel: 0,
                },
                {
                    id: '2',
                    title: 'Item 2',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 1,
                },
                {
                    id: '3',
                    title: 'Item 3',
                    isCompleted: true,
                    tabLevel: 2,
                    originalTabLevel: 2,
                },
                {
                    id: '4',
                    title: 'Item 4',
                    isCompleted: false,
                    tabLevel: 2,
                    originalTabLevel: 0,
                },
                {
                    id: '5',
                    title: 'Item 5',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 0,
                },
            ];

            const expected: InitiativePayload[] = [
                {
                    id: '1',
                    title: 'Item 1',
                    status: 'TO_DO',
                    tasks: [
                        {
                            id: '2',
                            title: 'Item 2',
                            status: 'TO_DO',
                            checklist: [
                                {
                                    id: '3',
                                    title: 'Item 3',
                                    is_complete: true,
                                    order: 0,
                                },
                                {
                                    id: '4',
                                    title: 'Item 4',
                                    is_complete: false,
                                    order: 1,
                                },
                            ]
                        },
                        {
                            id: '5',
                            title: 'Item 5',
                            status: 'TO_DO',
                            checklist: []
                        },
                    ]
                },

            ]

            const { initiatives, initiativesToDelete } = formatCompletableTextToJSON(items);
            expect(initiatives).toEqual(expected);
            expect(initiativesToDelete).toEqual(['4', '5']);
        });

        it('it should return the tasks to delete which are converted to intiatives and checklist items', () => {
            const items: CompletableText[] = [
                {
                    id: '1',
                    title: 'Item 1',
                    isCompleted: false,
                    tabLevel: 0,
                    originalTabLevel: 0,
                },
                {
                    id: '2',
                    title: 'Item 2',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 1,
                },
                {
                    id: '3',
                    title: 'Item 3',
                    isCompleted: true,
                    tabLevel: 2,
                    originalTabLevel: 2,
                },
                {
                    id: '4',
                    title: 'Item 4',
                    isCompleted: false,
                    tabLevel: 2,
                    originalTabLevel: 1,
                },
                {
                    id: '5',
                    title: 'Item 5',
                    isCompleted: false,
                    tabLevel: 0,
                    originalTabLevel: 1,
                },
            ];

            const expected: InitiativePayload[] = [
                {
                    id: '1',
                    title: 'Item 1',
                    status: 'TO_DO',
                    tasks: [
                        {
                            id: '2',
                            title: 'Item 2',
                            status: 'TO_DO',
                            checklist: [
                                {
                                    id: '3',
                                    title: 'Item 3',
                                    is_complete: true,
                                    order: 0,
                                },
                                {
                                    id: '4',
                                    title: 'Item 4',
                                    order: 1,
                                    is_complete: false,
                                }
                            ]
                        },

                    ]
                },
                {
                    id: '5',
                    title: 'Item 5',
                    status: 'TO_DO',
                    tasks: []
                }
            ]

            const { initiatives, tasksToDelete } = formatCompletableTextToJSON(items);
            expect(initiatives).toEqual(expected);
            expect(tasksToDelete).toEqual(['4', '5']);
        });

        it('it should return the checklists to delete which are converted to intiatives and tasks', () => {
            const items: CompletableText[] = [
                {
                    id: '1',
                    title: 'Item 1',
                    isCompleted: false,
                    tabLevel: 0,
                    originalTabLevel: 0,
                },
                {
                    id: '2',
                    title: 'Item 2',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 1,
                },
                {
                    id: '3',
                    title: 'Item 3',
                    isCompleted: true,
                    tabLevel: 2,
                    originalTabLevel: 2,
                },
                {
                    id: '4',
                    title: 'Item 4',
                    isCompleted: false,
                    tabLevel: 0,
                    originalTabLevel: 2,
                },
                {
                    id: '5',
                    title: 'Item 5',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 2,
                },
            ];

            const expected: InitiativePayload[] = [
                {
                    id: '1',
                    title: 'Item 1',
                    status: 'TO_DO',
                    tasks: [
                        {
                            id: '2',
                            title: 'Item 2',
                            status: 'TO_DO',
                            checklist: [
                                {
                                    id: '3',
                                    title: 'Item 3',
                                    is_complete: true,
                                    order: 0,
                                }
                            ]
                        },
                    ]
                },
                {
                    id: '4',
                    title: 'Item 4',
                    status: 'TO_DO',
                    tasks: [
                        {
                            id: '5',
                            title: 'Item 5',
                            status: 'TO_DO',
                            checklist: []
                        }
                    ]
                },
            ]

            const { initiatives, checklistItemsToDelete } = formatCompletableTextToJSON(items);
            expect(initiatives).toEqual(expected);
            expect(checklistItemsToDelete).toEqual(['4', '5']);
        });

        it('should throw an error if a checklist item is not nested under a task', async () => {
            const items: CompletableText[] = [
                {
                    title: 'Item 1',
                    isCompleted: false,
                    tabLevel: 0,
                    originalTabLevel: 0,
                },
                {
                    title: 'Item 2',
                    isCompleted: false,
                    tabLevel: 2,
                    originalTabLevel: 2,
                },
            ];

            await expect(() => formatCompletableTextToJSON(items)).toThrowError('Checklist item must be nested under a task');
        });

        it('should throw an error if a task is not nested under an initiative', async () => {
            const items: CompletableText[] = [
                {
                    title: 'Item 1',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 1,
                },
            ];

            await expect(() => formatCompletableTextToJSON(items)).toThrowError('Task must be nested under an initiative');
        });

        it('should ignore items with no title', () => {
            const items: CompletableText[] = [
                {
                    title: 'Item 1',
                    isCompleted: false,
                    tabLevel: 0,
                    originalTabLevel: 0,
                },
                {
                    title: '',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 1,
                },
                {
                    title: 'Item 2',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 1,
                },
                {
                    title: 'Item 3',
                    isCompleted: false,
                    tabLevel: 2,
                    originalTabLevel: 2,
                },
                {
                    title: '',
                    isCompleted: false,
                    tabLevel: 2,
                    originalTabLevel: 2,
                },
                {
                    title: '',
                    isCompleted: false,
                    tabLevel: 0,
                    originalTabLevel: 0,
                }
            ];

            const expected: InitiativePayload[] = [
                {
                    title: 'Item 1',
                    status: 'TO_DO',
                    tasks: [
                        {
                            title: 'Item 2',
                            status: 'TO_DO',
                            checklist: [
                                {
                                    title: 'Item 3',
                                    is_complete: false,
                                    order: 0,
                                }
                            ]
                        },
                    ]
                },
            ]
            expect(formatCompletableTextToJSON(items).initiatives).toEqual(expected);
        });
    });

    describe.skip('initiativesDataToCompletableText', () => {
        it('should map InitiativeDto to an array of CompletableText objects', () => {
            const initiativesData = [
                {
                    id: '1',
                    title: 'Initiative 1',
                    status: 'DONE',
                    tasks: [
                        {
                            id: '2',
                            title: 'Task 1.1',
                            status: 'TO_DO',
                            checklist: [
                                {
                                    id: '3',
                                    title: 'Checklist 1.1.1',
                                    is_complete: false
                                }
                            ]
                        }
                    ]
                }
            ] as any; // Use partial for mocking

            const result = initiativesDataToCompletableText(initiativesData);

            expect(result).toEqual([
                {
                    id: '1',
                    title: 'Initiative 1',
                    isCompleted: true,
                    tabLevel: 0,
                    originalTabLevel: 0
                },
                {
                    id: '2',
                    title: 'Task 1.1',
                    isCompleted: false,
                    tabLevel: 1,
                    originalTabLevel: 1
                },
                {
                    id: '3',
                    title: 'Checklist 1.1.1',
                    isCompleted: false,
                    tabLevel: 2,
                    originalTabLevel: 2
                },
            ]);
        });

    });
});

