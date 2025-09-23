import React from 'react';

// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import ChecklistOverlay from '#components/reusable/ChecklistOverlay';

const meta: Meta<typeof ChecklistOverlay> = {
    title: 'Components/Reusable/ChecklistOverlay',
    component: ChecklistOverlay,
    parameters: {
        layout: 'padded',
    },
    decorators: [
        (Story) => (
            <div style={{ maxWidth: '600px', padding: '20px' }}>
                <Story />
            </div>
        ),
    ],
};

export default meta;

type Story = StoryObj<typeof ChecklistOverlay>;

export const Default: Story = {
    args: {
        onManualEdit: () => console.log('Manual edit clicked'),
        documentationUrl: 'https://docs.anthropic.com/en/docs/claude-code'
    }
};

export const WithoutDocumentationLink: Story = {
    args: {
        onManualEdit: () => console.log('Manual edit clicked'),
        documentationUrl: undefined
    }
};

export const Interactive: Story = {
    args: {
        onManualEdit: () => alert('Manual edit mode activated!'),
        documentationUrl: 'https://docs.anthropic.com/en/docs/claude-code'
    }
};

export const InContext: Story = {
    args: {
        onManualEdit: () => console.log('Manual edit clicked'),
        documentationUrl: 'https://docs.anthropic.com/en/docs/claude-code'
    },
    decorators: [
        (Story) => (
            <div style={{ maxWidth: '600px', padding: '20px' }}>
                <div className="mb-4">
                    <h2 className="text-lg font-semibold mb-2">Task Checklist Section</h2>
                    <p className="text-sm text-muted-foreground mb-4">
                        This shows how the overlay appears in the context of a task view.
                    </p>
                </div>
                <Story />
                <div className="mt-4 text-xs text-muted-foreground">
                    ↑ The overlay would appear above the skeleton checklist items
                </div>
            </div>
        ),
    ],
};