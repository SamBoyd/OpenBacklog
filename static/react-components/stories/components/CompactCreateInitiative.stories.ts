// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import CompactCreateInitiative from '../../components/CompactCreateInitiative';

import { postInitiative } from '#api/initiatives.mock';
import { InitiativeStatus } from '#types';
import { mockFieldDefinitionsReturn, mockInitiativesContextReturn, mockPostInitiative } from '#stories/example_data';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';
import { useFieldDefinitions } from '#hooks/useFieldDefinitions.mock';

const mockOnCreate = () => {
    console.log('onCreate');
}

const meta: Meta<typeof CompactCreateInitiative> = {
    component: CompactCreateInitiative,
    async beforeEach() {
        postInitiative.mockResolvedValue(mockPostInitiative);
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        useFieldDefinitions.mockReturnValue(mockFieldDefinitionsReturn);
        return () => {
            postInitiative.mockReset();
            useInitiativesContext.mockReset();
            useFieldDefinitions.mockReset();
        };
    },
};

export default meta;
type Story = StoryObj<typeof CompactCreateInitiative>;

export const Primary: Story = {
    args: {
        startExpanded: true,
        defaultInitiativeStatus: InitiativeStatus.TO_DO,
        onCreate: mockOnCreate,
        focus: true,
    },
};

export const ApiError: Story = {
    args: {},
    async beforeEach() {
        postInitiative.mockImplementation(() => {
            throw new Error('API error');
        })
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);

        return () => {
            postInitiative.mockReset();
            useInitiativesContext.mockReset();
        };
    },
};
