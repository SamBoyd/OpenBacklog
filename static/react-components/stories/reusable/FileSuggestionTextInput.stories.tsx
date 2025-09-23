import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { within, userEvent, expect } from '@storybook/test';

import FileSuggestionTextInput from '#components/reusable/FileSuggestionTextInput';
import { mockUseGithubReposReturn, useGithubRepos } from '#hooks/useGithubRepos.mock';


const meta: Meta<typeof FileSuggestionTextInput> = {
    title: 'Reusable/FileSuggestionTextInput',
    component: FileSuggestionTextInput,
    parameters: {
        layout: 'padded',
        docs: {
            description: {
                component: `
FileSuggestionTextInput is an enhanced textarea component that provides intelligent file path suggestions when users type "@".

### Features:
- **@ Symbol Detection**: Automatically detects when user types "@" followed by a search query
- **Multi-Repository Search**: Searches across all connected GitHub repositories
- **Keyboard Navigation**: Use arrow keys to navigate suggestions, Enter to select, Escape to close
- **Real-time Filtering**: Suggestions update as you type your search query
- **Auto-resize**: Textarea automatically adjusts height based on content

### Usage:
1. Type normally for regular text input
2. Type "@" followed by a search term to trigger file suggestions
3. Use arrow keys to navigate the dropdown
4. Press Enter or click to select a suggestion
5. Press Escape to close the dropdown

### File Path Format:
Selected suggestions are inserted in the format: \`@repository-name/path/to/file.ext\`
                `
            }
        }
    },
    argTypes: {
        value: {
            control: 'text',
            description: 'Current text value of the input'
        },
        onChange: {
            action: 'changed',
            description: 'Callback fired when text changes'
        },
        placeholder: {
            control: 'text',
            description: 'Placeholder text shown when input is empty'
        },
        disabled: {
            control: 'boolean',
            description: 'Whether the input is disabled'
        },
        loading: {
            control: 'boolean',
            description: 'Whether to show loading skeleton'
        },
        initialRows: {
            control: 'number',
            description: 'Initial number of rows for the textarea'
        },
        submitOnEnter: {
            control: 'boolean',
            description: 'Whether Enter key should submit (prevent newline)'
        }
    },
    decorators: [
        (Story, context) => {
            // Mock useGithubRepos based on story parameters
            // useGithubRepos.mockReturnValue(context.parameters.mockGithubRepos);
            const mockData = context.parameters.mockGithubRepos || mockUseGithubReposReturn;

            // Apply the mock
            // (useGithubRepos as any) = () => mockData;
            useGithubRepos.mockReturnValue(mockData);

            return <Story />;
        }
    ]
};

export default meta;
type Story = StoryObj<typeof meta>;

// Interactive wrapper component for stories
const InteractiveWrapper = (args: any) => {
    const [value, setValue] = useState(args.value || '');

    return (
        <div className="max-w-2xl">
            <FileSuggestionTextInput
                {...args}
                value={value}
                onChange={setValue}
            />
            <div className="mt-4 p-3 bg-muted rounded text-sm">
                <strong>Current value:</strong> <code>{value || '(empty)'}</code>
            </div>
        </div>
    );
};

/**
 * Default state showing normal textarea behavior
 */
export const Default: Story = {
    render: InteractiveWrapper,
    args: {
        placeholder: 'Type your text here...',
        initialRows: 3,
    },
};

/**
 * Demonstrates file path suggestion triggered by "@" symbol
 */
export const WithFilepathSuggestions: Story = {
    render: InteractiveWrapper,
    args: {
        value: 'Please check the @comp',
        placeholder: 'Type @ followed by a search term to see file suggestions...',
        initialRows: 3,
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        const textarea = canvas.getByRole('textbox');

        // Focus the textarea
        await userEvent.click(textarea);

        // Position cursor after '@comp'
        (textarea as HTMLTextAreaElement).setSelectionRange(19, 19);

        // Wait a moment for suggestions to appear
        await new Promise(resolve => setTimeout(resolve, 100));
    },
};

/**
 * Shows multi-repository search capabilities
 */
export const MultiRepositorySearch: Story = {
    render: InteractiveWrapper,
    args: {
        value: 'Check @auth for authentication logic',
        placeholder: 'Search across multiple repositories...',
        initialRows: 3,
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        const textarea = canvas.getByRole('textbox');

        await userEvent.click(textarea);

        // Position cursor after '@auth'
        (textarea as HTMLTextAreaElement).setSelectionRange(11, 11);

        await new Promise(resolve => setTimeout(resolve, 100));
    },
};

/**
 * Demonstrates various file types and extensions
 */
export const DifferentFileTypes: Story = {
    render: InteractiveWrapper,
    args: {
        value: 'Update @package',
        placeholder: 'Try searching for different file types...',
        initialRows: 3,
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        const textarea = canvas.getByRole('textbox');

        await userEvent.click(textarea);
        (textarea as HTMLTextAreaElement).setSelectionRange(15, 15);

        await new Promise(resolve => setTimeout(resolve, 100));
    },
};

/**
 * Shows loading state while fetching repository data
 */
export const LoadingState: Story = {
    render: InteractiveWrapper,
    args: {
        value: 'Looking for @test',
        placeholder: 'Searching...',
        initialRows: 3,
    },
    parameters: {
        mockGithubRepos: {
            repositories: [],
            isLoading: true,
            error: null,
            getRepositoryByName: () => null,
            refresh: () => {},
            totalRepositories: 0,
        }
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        const textarea = canvas.getByRole('textbox');

        await userEvent.click(textarea);
        (textarea as HTMLTextAreaElement).setSelectionRange(16, 16);

        await new Promise(resolve => setTimeout(resolve, 100));
    },
};

/**
 * Shows error state when repository fetching fails
 */
export const ErrorState: Story = {
    render: InteractiveWrapper,
    args: {
        value: 'Check @file',
        placeholder: 'Error loading repositories...',
        initialRows: 3,
    },
    parameters: {
        mockGithubRepos: {
            repositories: [],
            isLoading: false,
            error: new Error('Failed to fetch repositories'),
            getRepositoryByName: () => null,
            refresh: () => {},
            totalRepositories: 0,
        }
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        const textarea = canvas.getByRole('textbox');

        await userEvent.click(textarea);
        (textarea as HTMLTextAreaElement).setSelectionRange(11, 11);

        await new Promise(resolve => setTimeout(resolve, 100));
    },
};

/**
 * Shows empty repository state
 */
export const EmptyRepositories: Story = {
    render: InteractiveWrapper,
    args: {
        value: 'No files found for @missing',
        placeholder: 'No repositories connected...',
        initialRows: 3,
    },
    parameters: {
        mockGithubRepos: {
            repositories: [],
            isLoading: false,
            error: null,
            getRepositoryByName: () => null,
            refresh: () => {},
            totalRepositories: 0,
        }
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        const textarea = canvas.getByRole('textbox');

        await userEvent.click(textarea);
        (textarea as HTMLTextAreaElement).setSelectionRange(26, 26);

        await new Promise(resolve => setTimeout(resolve, 100));
    },
};

/**
 * Shows disabled state
 */
export const Disabled: Story = {
    render: InteractiveWrapper,
    args: {
        value: 'This input is disabled @component',
        placeholder: 'Disabled input...',
        disabled: true,
        initialRows: 3,
    },
};

/**
 * Shows component in loading skeleton state
 */
export const ComponentLoading: Story = {
    render: InteractiveWrapper,
    args: {
        loading: true,
        initialRows: 3,
    },
};

/**
 * Demonstrates keyboard navigation
 */
export const KeyboardNavigation: Story = {
    render: InteractiveWrapper,
    args: {
        value: 'Navigate with @comp',
        placeholder: 'Use arrow keys to navigate suggestions...',
        initialRows: 3,
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        const textarea = canvas.getByRole('textbox');

        await userEvent.click(textarea);
        (textarea as HTMLTextAreaElement).setSelectionRange(18, 18);

        // Wait for dropdown to appear
        await new Promise(resolve => setTimeout(resolve, 200));

        // Demonstrate arrow key navigation
        await userEvent.keyboard('{ArrowDown}');
        await new Promise(resolve => setTimeout(resolve, 200));

        await userEvent.keyboard('{ArrowDown}');
        await new Promise(resolve => setTimeout(resolve, 200));

        await userEvent.keyboard('{ArrowUp}');
        await new Promise(resolve => setTimeout(resolve, 200));
    },
};

/**
 * Shows complex text with multiple @ symbols
 */
export const MultipleAtSymbols: Story = {
    render: InteractiveWrapper,
    args: {
        value: 'Check @user/frontend-app/src/components/Button.tsx and @auth',
        placeholder: 'Multiple @ symbols in text...',
        initialRows: 4,
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        const textarea = canvas.getByRole('textbox');

        await userEvent.click(textarea);

        // Position cursor after the second '@auth'
        (textarea as HTMLTextAreaElement).setSelectionRange(64, 64);

        await new Promise(resolve => setTimeout(resolve, 100));
    },
};

/**
 * Demonstrates text insertion and replacement
 */
export const TextInsertion: Story = {
    render: InteractiveWrapper,
    args: {
        value: 'Fix the bug in @btn',
        placeholder: 'Select a suggestion to see text replacement...',
        initialRows: 3,
    },
    play: async ({ canvasElement }) => {
        const canvas = within(canvasElement);
        const textarea = canvas.getByRole('textbox');

        await userEvent.click(textarea);
        (textarea as HTMLTextAreaElement).setSelectionRange(18, 18);

        await new Promise(resolve => setTimeout(resolve, 200));

        // Try to select first suggestion
        await userEvent.keyboard('{Enter}');
    },
};