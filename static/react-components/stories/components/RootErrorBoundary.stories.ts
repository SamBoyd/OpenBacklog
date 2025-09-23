// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import { ErrorFallback } from '../../components/RootErrorBoundary';

import { postInitiative } from '#api/initiatives.mock';
import { WorkspaceDto } from '#types';
import { mockPostInitiative } from '#stories/example_data';

const meta: Meta<typeof ErrorFallback> = {
    component: ErrorFallback,

};

export default meta;
type Story = StoryObj<typeof ErrorFallback>;

export const Primary: Story = {
    args: {},
};
