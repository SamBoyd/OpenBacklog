import type { Meta, StoryObj } from '@storybook/react';
import TaskCard from '#components/reusable/TaskCard';
import { TaskStatus } from '#types';
import { fn } from '@storybook/test';

const mockWorkspace = {
  id: 'ws-1',
  name: 'Test Workspace',
  description: 'Test workspace description',
  icon: '',
  user_id: 'user-1',
  is_default: true,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
};

const baseTask = {
  id: 'task-1',
  identifier: 'TASK-001',
  user_id: 'user-1',
  workspace: mockWorkspace,
  initiative_id: 'init-1',
  title: 'Add /get_project_vision MCP command',
  description: 'Implement the MCP command to retrieve project vision. This allows AI agents to access product context directly without manual copy-paste.',
  type: 'FEATURE',
  properties: {},
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  checklist: [],
};

const meta: Meta<typeof TaskCard> = {
  title: 'Components/Reusable/TaskCard',
  component: TaskCard,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
  args: {
    onViewTask: fn(),
  },
  decorators: [
    (Story) => (
      <div className="max-w-2xl">
        <Story />
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof TaskCard>;

/**
 * A completed task with the checkmark emoji and Complete badge
 */
export const Completed: Story = {
  args: {
    task: {
      ...baseTask,
      status: TaskStatus.DONE,
    },
  },
};

/**
 * A task currently in progress with the spinning emoji and In Progress badge
 */
export const InProgress: Story = {
  args: {
    task: {
      ...baseTask,
      id: 'task-2',
      identifier: 'TASK-002',
      title: 'Add /get_initiatives MCP command',
      description: 'Implement the MCP command to list all initiatives with their status and progress.',
      status: TaskStatus.IN_PROGRESS,
    },
  },
};

/**
 * A task not yet started with the circle emoji and To Do badge
 */
export const ToDo: Story = {
  args: {
    task: {
      ...baseTask,
      id: 'task-3',
      identifier: 'TASK-003',
      title: 'Implement MCP authentication layer',
      description: 'Add authentication for secure MCP access to prevent unauthorized queries.',
      status: TaskStatus.TO_DO,
    },
  },
};

/**
 * A blocked task with the no-entry emoji and Blocked badge
 */
export const Blocked: Story = {
  args: {
    task: {
      ...baseTask,
      id: 'task-4',
      identifier: 'TASK-004',
      title: 'Deploy MCP server to production',
      description: 'Blocked by pending security review and infrastructure approval.',
      status: TaskStatus.BLOCKED,
    },
  },
};

/**
 * A task without a description
 */
export const NoDescription: Story = {
  args: {
    task: {
      ...baseTask,
      id: 'task-5',
      identifier: 'TASK-005',
      title: 'Quick fix for typo in documentation',
      description: '',
      status: TaskStatus.TO_DO,
    },
  },
};

/**
 * A task with a very long description that gets truncated to 2 lines
 */
export const LongDescription: Story = {
  args: {
    task: {
      ...baseTask,
      id: 'task-6',
      identifier: 'TASK-006',
      title: 'Implement comprehensive logging system',
      description: 'Create a robust logging system that captures all MCP requests and responses, includes timing metrics, supports multiple output formats (JSON, plaintext), integrates with existing monitoring tools, and provides detailed error tracing for debugging production issues. The system should also support log rotation, compression, and automatic cleanup of old log files.',
      status: TaskStatus.IN_PROGRESS,
    },
  },
};

/**
 * A task without the View Scene button (no callback provided)
 */
export const WithoutViewButton: Story = {
  args: {
    task: {
      ...baseTask,
      status: TaskStatus.DONE,
    },
    onViewTask: undefined,
  },
};
