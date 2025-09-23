// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
// Use require for the addon
// @ts-ignore
const { withRouter } = require('storybook-addon-remix-react-router');

import GroupInitiativesDisplay from '#components/GroupInitiativesDisplay';
import { GroupDto, GroupType, InitiativeStatus } from '#types';
import { mockFieldDefinitionsReturn, mockGroups, mockInitiativeGroupsReturn, mockInitiatives, mockInitiativesContextReturn } from '../example_data';
import { useInitiativeGroups } from '#hooks/useInitiativeGroups.mock';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';

const mockGroup: GroupDto = {
    id: 'group-1',
    name: 'Marketing',
    user_id: 'user-1',
    workspace_id: 'workspace-1',
    description: 'Marketing initiatives',
    group_type: GroupType.EXPLICIT,
    group_metadata: null,
    query_criteria: null,
    parent_group_id: null
};

// Add group reference to some initiatives for testing
const initiativesWithGroups = mockInitiatives.map((initiative, index) => ({
    ...initiative,
    status: InitiativeStatus.BACKLOG,
    groups: index % 2 === 0 ? [{ id: mockGroup.id, name: mockGroup.name }] : []
}));

const meta: Meta<typeof GroupInitiativesDisplay> = {
    component: GroupInitiativesDisplay,
    decorators: [
        withRouter,
        (Story) => (
            <div className="p-4 max-w-4xl mx-auto">
                <Story />
            </div>
        ),
    ],
};

export default meta;
type Story = StoryObj<typeof GroupInitiativesDisplay>;

export const Primary: Story = {
    args: {
        group: mockGroup,
        allInitiatives: initiativesWithGroups,
        selectedStatuses: Object.values(InitiativeStatus)
    },
    async beforeEach() {
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

export const SmartGroup: Story = {
    args: {
        group: mockGroups.find(group => group.group_type === GroupType.SMART),
        allInitiatives: initiativesWithGroups,
        selectedStatuses: Object.values(InitiativeStatus)
    },
    async beforeEach() {
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

export const EmptyGroup: Story = {
    args: {
        group: {
            ...mockGroup,
            id: 'empty-group',
            name: 'Empty Group'
        },
        allInitiatives: initiativesWithGroups,
        selectedStatuses: [InitiativeStatus.BACKLOG]
    },
};