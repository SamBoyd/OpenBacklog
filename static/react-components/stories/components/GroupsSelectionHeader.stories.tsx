import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';

import GroupsSelectionHeader from '#components/groups/GroupsSelectionHeader';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';
import { useUserPreferences } from '#hooks/useUserPreferences.mock';
import { GroupType } from '#types';

import {
    mockInitiativeGroupsReturn,
    mockInitiativesContextReturn,
    mockFieldDefinitionsReturn,
    mockInitiatives,
    mockUserPreferencesReturn
} from '../example_data';

const meta: Meta<typeof GroupsSelectionHeader> = {
    component: GroupsSelectionHeader,
    decorators: [
        (Story) => (
            <div className="p-4">
                <Story />
            </div>
        ),
    ],
}

export default meta;
type Story = StoryObj<typeof GroupsSelectionHeader>;

export const Primary: Story = {
    args: {},

    beforeEach: async () => {
        useInitiativeGroups.mockReturnValue(mockInitiativeGroupsReturn);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);
        return () => {
            useInitiativeGroups.mockClear();
            useInitiativesContext.mockClear();
            useFieldDefinitions.mockClear();
        }
    },
};


export const withManyGroups: Story = {
    args: {},
    beforeEach: async () => {
        useInitiativeGroups.mockReturnValue({
            ...mockInitiativeGroupsReturn,
            allGroupsInWorkspace: [
                {
                    id: '1',
                    name: 'Getting to Launch',
                    description: 'The minimum set of initiatives to get to launch',
                    group_type: GroupType.EXPLICIT,
                    user_id: '1',
                    query_criteria: null,
                    initiatives: mockInitiatives.slice(0, 2),
                    workspace_id: 'workspace-1',
                    group_metadata: {},
                    parent_group_id: null
                },
                {
                    id: '2',
                    group_type: GroupType.SMART,
                    user_id: '1',
                    workspace_id: 'workspace-1',
                    name: 'All Bugs',
                    description: '',
                    query_criteria: {
                        type: "BUGFIX"
                    },
                    initiatives: mockInitiatives,
                    group_metadata: null,
                    parent_group_id: null
                },
                {
                    id: '3',
                    name: 'High Priority Features',
                    description: 'Critical features for Q2',
                    group_type: GroupType.EXPLICIT,
                    user_id: '1',
                    query_criteria: null,
                    initiatives: mockInitiatives.slice(2, 4),
                    workspace_id: 'workspace-1',
                    group_metadata: {},
                    parent_group_id: null
                },
                {
                    id: '4',
                    name: 'In Progress',
                    description: 'Currently active initiatives',
                    group_type: GroupType.SMART,
                    user_id: '1',
                    query_criteria: {
                        status: "IN_PROGRESS"
                    },
                    initiatives: mockInitiatives.slice(1, 3),
                    workspace_id: 'workspace-1',
                    group_metadata: null,
                    parent_group_id: null
                },
                {
                    id: '5',
                    name: 'Backend Team',
                    description: 'Initiatives owned by backend team',
                    group_type: GroupType.SMART,
                    user_id: '1',
                    query_criteria: {
                    },
                    initiatives: mockInitiatives.slice(0, 3),
                    workspace_id: 'workspace-1',
                    group_metadata: null,
                    parent_group_id: null
                },
                {
                    id: '6',
                    name: 'Q2 Objectives',
                    description: 'Key initiatives for Q2 2024',
                    group_type: GroupType.EXPLICIT,
                    user_id: '1',
                    query_criteria: null,
                    initiatives: mockInitiatives.slice(1, 4),
                    workspace_id: 'workspace-1',
                    group_metadata: {},
                    parent_group_id: null
                },
                {
                    id: '7',
                    name: 'Performance Improvements',
                    description: 'System optimization initiatives',
                    group_type: GroupType.SMART,
                    user_id: '1',
                    query_criteria: {
                        type: "FEATURE"
                    },
                    initiatives: mockInitiatives.slice(2, 5),
                    workspace_id: 'workspace-1',
                    group_metadata: null,
                    parent_group_id: null
                },
                {
                    id: '8',
                    name: 'Documentation Tasks',
                    description: 'Documentation and knowledge base updates',
                    group_type: GroupType.SMART,
                    user_id: '1',
                    query_criteria: {
                        type: "DOCUMENTATION"
                    },
                    initiatives: mockInitiatives.slice(0, 2),
                    workspace_id: 'workspace-1',
                    group_metadata: null,
                    parent_group_id: null
                }
            ]
        });
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);
        useUserPreferences.mockReturnValue({
            ...mockUserPreferencesReturn,
            preferences: {
                ...mockUserPreferencesReturn.preferences,
                selectedGroupIds: ['1', '2', '3', '4', '5', '6', '7', '8']
            }
        });
        return () => {
            useInitiativeGroups.mockClear();
            useInitiativesContext.mockClear();
            useFieldDefinitions.mockClear();
        }
    },
};
