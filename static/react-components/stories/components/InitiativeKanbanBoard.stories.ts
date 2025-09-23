// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import InitiativesKanbanBoard from '#components/InitiativesKanbanBoard';

import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useTasksContext } from '#contexts/TasksContext.mock';

import { InitiativeDto, InitiativeStatus, TaskStatus } from '#types';

import {
    mockInitiativesContextReturn,
    mockUseTasksContext,
    mockWorkspace,
} from '#stories/example_data';

import { loremIpsum } from 'lorem-ipsum';
import { LexoRank } from 'lexorank';

const meta: Meta<typeof InitiativesKanbanBoard> = {
    component: InitiativesKanbanBoard,
    async beforeEach() {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useTasksContext.mockReturnValue(mockUseTasksContext);

        return () => {
            useInitiativesContext.mockReset();
            useTasksContext.mockReset();
        };
    },
};

export default meta;
type Story = StoryObj<typeof InitiativesKanbanBoard>;

export const Primary: Story = {
    args: {},
};

export const LotsOfCards: Story = {
    args: {},
    async beforeEach() {
        let rank = LexoRank.middle()

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [...Array(100).keys()].map(i => (
                {
                    type: "FEATURE",
                    id: `${i}`,
                    identifier: `I-${i}`,
                    user_id: '776ece4a-47c6-497a-bc2f-475c49d623d0',
                    title: loremIpsum({ count: 1, units: 'sentences' }),
                    description: loremIpsum({ count: 3, units: 'sentences' }),
                    order: i,
                    created_at: '2025-02-01T15:00:00.000000',
                    updated_at: '2025-02-01T15:00:00.000001',
                    status: TaskStatus.TO_DO,
                    tasks: [],
                    has_pending_job: null,
                    workspace: mockWorkspace
                } as InitiativeDto)
            ).map((initiative: InitiativeDto) => ({
                ...initiative,
                position: rank.genNext().toString(),
                orderingId: initiative.id
            }))
        });
        useTasksContext.mockReturnValue(mockUseTasksContext);

        return () => {
            useInitiativesContext.mockReset();
            useTasksContext.mockReset();
        };
    },
};


export const Loading: Story = {
    args: {},
    async beforeEach() {
        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: null,
            shouldShowSkeleton: true
        });

        return () => {
            useInitiativesContext.mockReset();
        };
    },
};

export const Error: Story = {
    args: {},
    async beforeEach() {
        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: null,
            error: 'This is the error message'
        });

        return () => {
            useInitiativesContext.mockReset();
        };
    },
};

export const LoadingMore: Story = {
    args: {},
    async beforeEach() {
        let rank = LexoRank.middle()

        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [
                ...mockInitiativesContextReturn.initiativesData?.map(initiative => ({ ...initiative, status: InitiativeStatus.IN_PROGRESS } as InitiativeDto)) || [],
                ...mockInitiativesContextReturn.initiativesData?.map(initiative => ({ ...initiative, status: InitiativeStatus.IN_PROGRESS } as InitiativeDto)) || [],
                ...mockInitiativesContextReturn.initiativesData?.map(initiative => ({ ...initiative, status: InitiativeStatus.TO_DO } as InitiativeDto)) || [],
                ...mockInitiativesContextReturn.initiativesData?.map(initiative => ({ ...initiative, status: InitiativeStatus.DONE } as InitiativeDto)) || [],
            ].map((initiative: InitiativeDto) => ({
                ...initiative,
                position: rank.genNext().toString(),
                orderingId: initiative.id
            })),
            shouldShowSkeleton: false
        });
        useTasksContext.mockReturnValue(mockUseTasksContext);

        return () => {
            useInitiativesContext.mockReset();
            useTasksContext.mockReset();
        };
    },
};
