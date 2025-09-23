// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { ManagedEntityAction, ManagedInitiativeModel } from '#types';
import ChangesDisplay from '#components/diffs/ChangesDisplay';
import { useAiImprovementsContext } from '#contexts/AiImprovementsContext.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { mockAiImprovementsContextReturn, mockInitiativesContextReturn } from '#stories/example_data';

const meta: Meta<typeof ChangesDisplay> = {
    title: 'Components/Diffs/Components/ChangesDisplay',
    component: ChangesDisplay,
    parameters: {
        layout: 'padded',
    },
    beforeEach() {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);

        return () => {
            useInitiativesContext.mockReset();
            useAiImprovementsContext.mockReset();
        };
    },
};

export default meta;
type Story = StoryObj<typeof ChangesDisplay>;

// Mock initiative improvements
const mockInitiativeImprovements: Record<string, ManagedInitiativeModel> = {
    'I-245': {
        action: ManagedEntityAction.UPDATE,
        identifier: 'I-245',
        title: 'Enhanced authentication system',
        description: 'Updated authentication system with improved security features.',
        type: 'FEATURE',
    },
    'I-246': {
        action: ManagedEntityAction.CREATE,
        title: 'New dashboard analytics',
        description: 'Create a comprehensive analytics dashboard for user insights.',
        type: 'FEATURE',
        workspace_identifier: 'workspace-1',
    },
    'I-247': {
        action: ManagedEntityAction.DELETE,
        identifier: 'I-247',
    },
};

const mockSingleImprovement: Record<string, ManagedInitiativeModel> = {
    'I-245': {
        action: ManagedEntityAction.UPDATE,
        identifier: 'I-245',
        title: 'Update user authentication flow',
        description: 'Improve the user authentication process with better error handling.',
        type: 'FEATURE',
    },
};

const mockManyImprovements: Record<string, ManagedInitiativeModel> = {
    'I-245': {
        action: ManagedEntityAction.UPDATE,
        identifier: 'I-245',
        title: 'Enhanced authentication system',
        description: 'Updated authentication system with improved security features.',
        type: 'FEATURE',
    },
    'I-246': {
        action: ManagedEntityAction.CREATE,
        title: 'New dashboard analytics',
        description: 'Create a comprehensive analytics dashboard for user insights.',
        type: 'FEATURE',
        workspace_identifier: 'workspace-1',
    },
    'I-247': {
        action: ManagedEntityAction.DELETE,
        identifier: 'I-247',
    },
    'I-248': {
        action: ManagedEntityAction.CREATE,
        title: 'Mobile app optimization',
        description: 'Optimize mobile app performance and user experience.',
        type: 'FEATURE',
        workspace_identifier: 'workspace-1',
    },
    'I-249': {
        action: ManagedEntityAction.UPDATE,
        identifier: 'I-249',
        title: 'API rate limiting implementation',
        description: 'Add rate limiting to prevent API abuse and ensure fair usage.',
        type: 'FEATURE',
    },
};

export const Primary: Story = {
    beforeEach() {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            isEntityLocked: false,
        });

        return () => {
            useInitiativesContext.mockReset();
            useAiImprovementsContext.mockReset();
        };
    },
};

export const Loading: Story = {
    beforeEach() {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockInitiativeImprovements,
            isEntityLocked: true,
        });

        return () => {
            useInitiativesContext.mockReset();
            useAiImprovementsContext.mockReset();
        };
    },
};

export const SingleImprovement: Story = {
    beforeEach() {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockSingleImprovement,
            isEntityLocked: false,
        });

        return () => {
            useInitiativesContext.mockReset();
            useAiImprovementsContext.mockReset();
        };
    },
};

export const ManyImprovements: Story = {
    beforeEach() {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: mockManyImprovements,
            isEntityLocked: false,
        });

        return () => {
            useInitiativesContext.mockReset();
            useAiImprovementsContext.mockReset();
        };
    },
};

export const EmptyState: Story = {
    beforeEach() {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useAiImprovementsContext.mockReturnValue({
            ...mockAiImprovementsContextReturn,
            initiativeImprovements: {},
            isEntityLocked: false,
        });

        return () => {
            useInitiativesContext.mockReset();
            useAiImprovementsContext.mockReset();
        };
    },
};