import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { INITIAL_VIEWPORTS } from '@storybook/addon-viewport';

import FieldDefinitionsDropdown from '#components/entityField/FieldDefinitionsDropdown';
import { EntityType } from '#types';

const meta: Meta<typeof FieldDefinitionsDropdown> = {
    component: FieldDefinitionsDropdown,
    parameters: {
        viewport: {
            viewports: INITIAL_VIEWPORTS,
            defaultViewport: "iphone12promax",
        },
    },
    decorators: [
        (Story) => (
            <div className="p-4">
                <Story />
            </div>
        ),
    ],
}

export default meta;
type Story = StoryObj<typeof FieldDefinitionsDropdown>;

export const InitiativeField: Story = {
    args: {
        entityType: EntityType.INITIATIVE,
        onAddField: (fieldDefinition) => {
            console.log('Adding initiative field:', fieldDefinition);
        },
    },
};

export const TaskField: Story = {
    args: {
        entityType: EntityType.TASK,
        onAddField: (fieldDefinition) => {
            console.log('Adding task field:', fieldDefinition);
        },
    },
};
