import React from 'react';

// eslint-disable-next-line n/no-unpublished-import
import type { Meta, StoryObj } from '@storybook/react';

import ChecklistSkeleton from '#components/reusable/ChecklistSkeleton';

const meta: Meta<typeof ChecklistSkeleton> = {
    title: 'Components/Reusable/ChecklistSkeleton',
    component: ChecklistSkeleton,
    parameters: {
        layout: 'padded',
    },
    decorators: [
        (Story) => (
            <div style={{ maxWidth: '500px', padding: '20px' }}>
                <Story />
            </div>
        ),
    ],
};

export default meta;

type Story = StoryObj<typeof ChecklistSkeleton>;

export const Default: Story = {
    args: {
        itemCount: 3
    }
};

export const ThreeItems: Story = {
    args: {
        itemCount: 3
    }
};

export const FourItems: Story = {
    args: {
        itemCount: 4
    }
};

export const FiveItems: Story = {
    args: {
        itemCount: 5
    }
};

export const TwoItems: Story = {
    args: {
        itemCount: 2
    }
};

export const WithCustomStyling: Story = {
    args: {
        itemCount: 3,
        className: 'p-4 border border-border rounded'
    }
};

export const InContext: Story = {
    args: {
        itemCount: 3
    },
    decorators: [
        (Story) => (
            <div style={{ maxWidth: '500px', padding: '20px' }}>
                <div className="mb-4">
                    <h3 className="text-lg font-semibold mb-2">Checklist Preview</h3>
                    <p className="text-sm text-muted-foreground mb-4">
                        This skeleton shows what the checklist will look like when populated.
                    </p>
                </div>
                <div className="border border-border rounded p-4 bg-muted/5">
                    <Story />
                </div>
            </div>
        ),
    ],
};

export const StaticPreview: Story = {
    args: {
        itemCount: 4,
        animated: false
    }
};

export const AnimatedVsStatic: Story = {
    args: {
        itemCount: 3
    },
    decorators: [
        (Story) => (
            <div style={{ maxWidth: '700px', padding: '20px' }}>
                <div className="grid grid-cols-2 gap-6">
                    <div>
                        <h3 className="text-lg font-semibold mb-2">Animated (Default)</h3>
                        <div className="border border-border rounded p-4 bg-muted/5">
                            <ChecklistSkeleton itemCount={3} animated={true} />
                        </div>
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold mb-2">Static Preview</h3>
                        <div className="border border-border rounded p-4 bg-muted/5">
                            <ChecklistSkeleton itemCount={3} animated={false} />
                        </div>
                    </div>
                </div>
            </div>
        ),
    ],
};