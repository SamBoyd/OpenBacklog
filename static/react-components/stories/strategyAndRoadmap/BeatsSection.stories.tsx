import type { Meta, StoryObj } from '@storybook/react';
import BeatsSection from '../../pages/Narrative/StoryArcDetail/BeatsSection';
import { mockBeats } from './mockData';
import { BeatItem } from '#hooks/initiatives/useInitiativesByTheme';

const meta: Meta<typeof BeatsSection> = {
  title: 'Components/Narrative/StoryArcDetail/BeatsSection',
  component: BeatsSection,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Multiple beats with different statuses and progress levels.
 * Shows done, in-progress, and planned beats in a grid layout.
 */
export const MultipleBeats: Story = {
  args: {
    beats: mockBeats,
    arcId: 'arc-1',
    isLoading: false,
    onViewBeat: (initiativeId: string) => console.log('View Beat:', initiativeId),
    onAddBeat: () => console.log('Add Beat clicked'),
  },
};

/**
 * Single beat display.
 * Tests layout with minimal data.
 */
export const SingleBeat: Story = {
  args: {
    beats: [mockBeats[0]],
    arcId: 'arc-1',
    isLoading: false,
    onViewBeat: (initiativeId: string) => console.log('View Beat:', initiativeId),
    onAddBeat: () => console.log('Add Beat clicked'),
  },
};

/**
 * Empty state with no beats defined.
 * Shows placeholder messaging.
 */
export const NoBeats: Story = {
  args: {
    beats: [],
    arcId: 'arc-1',
    isLoading: false,
    onViewBeat: (initiativeId: string) => console.log('View Beat:', initiativeId),
    onAddBeat: () => console.log('Add Beat clicked'),
  },
};

/**
 * All beats complete with 100% progress.
 * Shows successful arc completion.
 */
export const HighProgress: Story = {
  args: {
    beats: mockBeats.map((beat) => ({
      ...beat,
      status: 'done' as const,
      progressPercent: 100,
      tasks: beat.tasks.map((task) => ({ ...task, status: 'DONE' as const })),
    })) as BeatItem[],
    arcId: 'arc-1',
    isLoading: false,
    onViewBeat: (initiativeId: string) => console.log('View Beat:', initiativeId),
    onAddBeat: () => console.log('Add Beat clicked'),
  },
};

/**
 * All beats in progress with varying completion percentages.
 * Tests visual differentiation of progress states.
 */
export const AllInProgress: Story = {
  args: {
    beats: mockBeats.map((beat, index) => {
      const totalTasks = beat.tasks.length;
      const completedCount = index + 1;
      const progressPercent = Math.round((completedCount / totalTasks) * 100);

      return {
        ...beat,
        status: 'in_progress' as const,
        progressPercent,
        tasks: beat.tasks.map((task, taskIndex) => ({
          ...task,
          status: (taskIndex < completedCount ? 'DONE' : 'IN_PROGRESS') as 'DONE' | 'IN_PROGRESS',
        })),
      };
    }) as BeatItem[],
    arcId: 'arc-1',
    isLoading: false,
    onViewBeat: (initiativeId: string) => console.log('View Beat:', initiativeId),
    onAddBeat: () => console.log('Add Beat clicked'),
  },
};
