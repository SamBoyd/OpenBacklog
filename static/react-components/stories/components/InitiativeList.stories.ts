// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';
import { useInitiativesContext } from '#contexts/InitiativesContext.mock';

import InitiativeList from '../../components/InitiativesList';
import { mockInitiativesContextReturn } from '#stories/example_data';



const meta: Meta<typeof InitiativeList> = {
    component: InitiativeList,
    async beforeEach() {
        useInitiativesContext.mockReturnValue(mockInitiativesContextReturn);
        return () => {
            useInitiativesContext.mockReset();
        };
    },
};

export default meta;
type Story = StoryObj<typeof InitiativeList>;

export const Primary: Story = {
    args: {},
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

export const LoadingError: Story = {
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

export const NoInitiatives: Story = {
    args: {},

    async beforeEach() {
        useInitiativesContext.mockReturnValue({
            ...mockInitiativesContextReturn,
            initiativesData: [],
        });

        return () => {
            useInitiativesContext.mockReset();
        };
    },
};
