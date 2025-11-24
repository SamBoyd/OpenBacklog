import type { Meta, StoryObj } from '@storybook/react';
import StorySection from '../../pages/Narrative/StoryArcDetail/StorySection';
import { longStoryText, shortStoryText } from './mockData';

const meta: Meta<typeof StorySection> = {
  title: 'Components/Narrative/StoryArcDetail/StorySection',
  component: StorySection,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default story section with long narrative text.
 * Tests typography and readability for extended content.
 */
export const WithStory: Story = {
  args: {
    storyText: longStoryText,
    isLoading: false,
    onRegenerateClick: () => console.log('Regenerate Story clicked'),
    onEditClick: () => console.log('Edit Story clicked'),
  },
};

/**
 * Short story text to test minimal content.
 * Shows layout with brief narrative.
 */
export const ShortStory: Story = {
  args: {
    storyText: shortStoryText,
    isLoading: false,
    onRegenerateClick: () => console.log('Regenerate Story clicked'),
    onEditClick: () => console.log('Edit Story clicked'),
  },
};

/**
 * Empty state with no story text.
 * Displays placeholder for undefined narrative.
 */
export const EmptyStory: Story = {
  args: {
    storyText: '',
    isLoading: false,
    onRegenerateClick: () => console.log('Regenerate Story clicked'),
    onEditClick: () => console.log('Edit Story clicked'),
  },
};

/**
 * Very long multi-paragraph story.
 * Tests readability and layout with extensive narrative content.
 */
export const VeryLongStory: Story = {
  args: {
    storyText: `${longStoryText}\n\n${longStoryText}\n\nAs the product evolves, we're discovering that narrative structure isn't just a metaphor—it's a practical framework for organizing product knowledge. Every feature becomes a scene in a larger story, every user segment becomes a character with motivations and obstacles, and every quarter becomes an act in an ongoing narrative.

This approach solves multiple problems simultaneously: it makes product context AI-readable, it maintains consistency over time, it provides natural hooks for documentation, and it helps teams communicate more effectively about product direction.

The real magic happens when your AI assistant can understand not just your current codebase, but the entire narrative arc of your product's evolution. It knows why certain decisions were made, what problems were being solved, and how different features fit into the larger story.

This is the future of product management: where AI doesn't just execute tasks, but understands the story you're trying to tell.`,
    isLoading: false,
    onRegenerateClick: () => console.log('Regenerate Story clicked'),
    onEditClick: () => console.log('Edit Story clicked'),
  },
};
