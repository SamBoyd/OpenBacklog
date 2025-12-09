import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import NarrativeTabList, { NarrativeTabType } from '#components/Narrative/NarrativeTabList';

const meta: Meta<typeof NarrativeTabList> = {
    title: 'Components/Narrative/NarrativeTabList',
    component: NarrativeTabList,
    parameters: {
        layout: 'fullscreen',
    },
    tags: ['autodocs'],
    decorators: [
        (Story) => (
            <div className="bg-background p-4">
                <Story />
            </div>
        ),
    ],
    argTypes: {
        activeTab: {
            control: 'select',
            options: ['heroes', 'villains', 'pillars', 'themes'],
            description: 'Currently active tab',
        },
        heroCount: {
            control: { type: 'number', min: 0, max: 10 },
            description: 'Number of heroes',
        },
        villainCount: {
            control: { type: 'number', min: 0, max: 10 },
            description: 'Number of villains',
        },
        pillarCount: {
            control: { type: 'number', min: 0, max: 10 },
            description: 'Number of pillars',
        },
        themeCount: {
            control: { type: 'number', min: 0, max: 10 },
            description: 'Number of themes',
        },
        onTabChange: {
            action: 'tab changed',
            description: 'Callback when tab is changed',
        },
    },
};

export default meta;
type Story = StoryObj<typeof NarrativeTabList>;

/**
 * Default tab list with Heroes selected.
 */
export const Default: Story = {
    args: {
        activeTab: 'heroes',
        heroCount: 3,
        villainCount: 2,
        pillarCount: 2,
        themeCount: 2,
    },
};

/**
 * Tab list with Villains selected.
 */
export const VillainsActive: Story = {
    args: {
        activeTab: 'villains',
        heroCount: 3,
        villainCount: 2,
        pillarCount: 2,
        themeCount: 2,
    },
};

/**
 * Tab list with Pillars selected.
 */
export const PillarsActive: Story = {
    args: {
        activeTab: 'pillars',
        heroCount: 3,
        villainCount: 2,
        pillarCount: 2,
        themeCount: 2,
    },
};

/**
 * Tab list with Themes selected.
 */
export const ThemesActive: Story = {
    args: {
        activeTab: 'themes',
        heroCount: 3,
        villainCount: 2,
        pillarCount: 2,
        themeCount: 2,
    },
};

/**
 * Interactive tab list with state management.
 */
export const Interactive: Story = {
    render: (args) => {
        const [activeTab, setActiveTab] = useState<NarrativeTabType>('heroes');
        return (
            <NarrativeTabList
                {...args}
                activeTab={activeTab}
                onTabChange={setActiveTab}
            />
        );
    },
    args: {
        heroCount: 3,
        villainCount: 2,
        pillarCount: 2,
        themeCount: 2,
    },
};

/**
 * Tab list with empty counts.
 */
export const EmptyCounts: Story = {
    args: {
        activeTab: 'heroes',
        heroCount: 0,
        villainCount: 0,
        pillarCount: 0,
        themeCount: 0,
    },
};

/**
 * Tab list with high counts.
 */
export const HighCounts: Story = {
    args: {
        activeTab: 'heroes',
        heroCount: 10,
        villainCount: 8,
        pillarCount: 6,
        themeCount: 9,
    },
};
