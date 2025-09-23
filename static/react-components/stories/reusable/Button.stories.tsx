import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { 
    Button, 
    PrimaryButton, 
    SecondaryButton, 
    NoBorderButton, 
    IconButton, 
    DangerButton, 
    ExpandingIconButton, 
    CompactButton 
} from '#components/reusable/Button';
import { ChevronDownIcon, PlusIcon, TrashIcon, CogIcon } from '@heroicons/react/24/outline';

const meta: Meta<typeof Button> = {
    title: 'Components/Reusable/Buttons',
    component: Button,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    argTypes: {
        children: {
            control: 'text',
            description: 'Button content',
        },
        className: {
            control: 'text',
            description: 'Additional CSS classes',
        },
        disabled: {
            control: 'boolean',
            description: 'Disable the button',
        },
        onClick: {
            action: 'clicked',
            description: 'Click handler',
        },
    },
};

export default meta;
type Story = StoryObj<typeof Button>;

const mockOnClick = () => {
    console.log('Button clicked');
};

export const AllButtonVariants: Story = {
    render: () => (
        <div className="flex flex-col gap-4 p-6">
            <div className="flex flex-wrap gap-3">
                <Button onClick={mockOnClick}>Default</Button>
                <PrimaryButton onClick={mockOnClick}>Primary</PrimaryButton>
                <SecondaryButton onClick={mockOnClick}>Secondary</SecondaryButton>
                <NoBorderButton onClick={mockOnClick}>No Border</NoBorderButton>
                <DangerButton onClick={mockOnClick}>Danger</DangerButton>
                <CompactButton onClick={mockOnClick}>Compact</CompactButton>
            </div>
            
            <div className="flex flex-wrap gap-3">
                <IconButton 
                    onClick={mockOnClick}
                    icon={<PlusIcon className="w-4 h-4" />}
                    title="Add"
                >
                    Add
                </IconButton>
                <IconButton 
                    onClick={mockOnClick}
                    icon={<CogIcon className="w-4 h-4" />}
                    title="Settings"
                    active={true}
                >
                    Settings
                </IconButton>
                <ExpandingIconButton 
                    onClick={mockOnClick}
                    icon={<TrashIcon className="w-4 h-4" />}
                    title="Delete Item"
                />
            </div>
            
            <div className="flex flex-wrap gap-3">
                <Button onClick={mockOnClick} disabled>Default Disabled</Button>
                <PrimaryButton onClick={mockOnClick} disabled>Primary Disabled</PrimaryButton>
                <SecondaryButton onClick={mockOnClick} disabled>Secondary Disabled</SecondaryButton>
                <DangerButton onClick={mockOnClick} disabled>Danger Disabled</DangerButton>
            </div>
        </div>
    ),
};

// Basic Button Stories
export const DefaultButton: Story = {
    args: {
        children: 'Default Button',
        onClick: mockOnClick,
    },
};

export const DefaultButtonDisabled: Story = {
    args: {
        children: 'Disabled Button',
        onClick: mockOnClick,
        disabled: true,
    },
};

export const DefaultButtonNoBorder: Story = {
    args: {
        children: 'No Border Button',
        onClick: mockOnClick,
        noBorder: true,
    },
};

// Primary Button Stories
export const Primary: Story = {
    render: (args) => (
        <PrimaryButton {...args}>
            {args.children || 'Primary Button'}
        </PrimaryButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const PrimaryDisabled: Story = {
    render: (args) => (
        <PrimaryButton {...args} disabled>
            Primary Disabled
        </PrimaryButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const PrimaryNoBorder: Story = {
    render: (args) => (
        <PrimaryButton {...args} noBorder>
            Primary No Border
        </PrimaryButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

// Secondary Button Stories
export const Secondary: Story = {
    render: (args) => (
        <SecondaryButton {...args}>
            {args.children || 'Secondary Button'}
        </SecondaryButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const SecondaryDisabled: Story = {
    render: (args) => (
        <SecondaryButton {...args} disabled>
            Secondary Disabled
        </SecondaryButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

// No Border Button Stories
export const NoBorder: Story = {
    render: (args) => (
        <NoBorderButton {...args}>
            {args.children || 'No Border Button'}
        </NoBorderButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const NoBorderDisabled: Story = {
    render: (args) => (
        <NoBorderButton {...args} disabled>
            No Border Disabled
        </NoBorderButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

// Icon Button Stories
export const IconButtonStory: Story = {
    render: (args) => (
        <IconButton 
            {...args}
            icon={<PlusIcon className="w-4 h-4" />}
            title="Add Item"
        >
            Add Item
        </IconButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const IconButtonActive: Story = {
    render: (args) => (
        <IconButton 
            {...args}
            icon={<CogIcon className="w-4 h-4" />}
            title="Settings"
            active={true}
        >
            Settings
        </IconButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const IconButtonDisabled: Story = {
    render: (args) => (
        <IconButton 
            {...args}
            icon={<TrashIcon className="w-4 h-4" />}
            title="Delete"
            disabled={true}
        >
            Delete
        </IconButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const IconButtonNoBorder: Story = {
    render: (args) => (
        <IconButton 
            {...args}
            icon={<ChevronDownIcon className="w-4 h-4" />}
            title="Dropdown"
            noBorder={true}
        >
            Dropdown
        </IconButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

// Danger Button Stories
export const Danger: Story = {
    render: (args) => (
        <DangerButton {...args}>
            {args.children || 'Delete Item'}
        </DangerButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const DangerDisabled: Story = {
    render: (args) => (
        <DangerButton {...args} disabled>
            Delete Disabled
        </DangerButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

// Expanding Icon Button Stories
export const ExpandingIcon: Story = {
    render: (args) => (
        <ExpandingIconButton 
            {...args}
            icon={<PlusIcon className="w-4 h-4" />}
            title="Add New Task"
        />
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const ExpandingIconActive: Story = {
    render: (args) => (
        <ExpandingIconButton 
            {...args}
            icon={<CogIcon className="w-4 h-4" />}
            title="Settings Menu"
            active={true}
        />
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const ExpandingIconDisabled: Story = {
    render: (args) => (
        <ExpandingIconButton 
            {...args}
            icon={<TrashIcon className="w-4 h-4" />}
            title="Delete Item"
            disabled={true}
        />
    ),
    args: {
        onClick: mockOnClick,
    },
};

// Compact Button Stories
export const Compact: Story = {
    render: (args) => (
        <CompactButton {...args}>
            {args.children || 'Compact'}
        </CompactButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};

export const CompactDisabled: Story = {
    render: (args) => (
        <CompactButton {...args} disabled>
            Compact Disabled
        </CompactButton>
    ),
    args: {
        onClick: mockOnClick,
    },
};
