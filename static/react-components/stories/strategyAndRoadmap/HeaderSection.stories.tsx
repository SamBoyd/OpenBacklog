import type { Meta, StoryObj } from '@storybook/react';
import HeaderSection from '../../pages/Narrative/StoryArcDetail/HeaderSection';

const meta: Meta<typeof HeaderSection> = {
  title: 'Components/Narrative/StoryArcDetail/HeaderSection',
  component: HeaderSection,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
};

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * Default header showing all sections and action buttons.
 * Displays breadcrumb, title, status badge, and global commands.
 */
export const Default: Story = {
  args: {
    arcTitle: 'AI-Native Product Management',
    arcSubtitle: 'Helping Sarah achieve flow by fighting Context Switching',
    arcStatus: 'planning',
    onEditMode: () => console.log('Edit Mode clicked'),
    onViewRoadmap: () => console.log('View in Roadmap clicked'),
    onShare: () => console.log('Share/Export clicked'),
    onLinkEntity: () => console.log('Link Entity clicked'),
    onDelete: () => console.log('Delete clicked'),
  },
};

/**
 * Header with "In Progress" status badge.
 * Shows active arc state.
 */
export const InProgressStatus: Story = {
  args: {
    arcTitle: 'MCP Integration Phase 1',
    arcSubtitle: 'Building the foundation for AI-native product management',
    arcStatus: 'in_progress',
    onEditMode: () => console.log('Edit Mode clicked'),
    onViewRoadmap: () => console.log('View in Roadmap clicked'),
    onShare: () => console.log('Share/Export clicked'),
    onLinkEntity: () => console.log('Link Entity clicked'),
    onDelete: () => console.log('Delete clicked'),
  },
};

/**
 * Header with "Complete" status showing success.
 * Displays completed arc.
 */
export const CompleteStatus: Story = {
  args: {
    arcTitle: 'Performance Optimization',
    arcSubtitle: 'Improving speed for power users',
    arcStatus: 'complete',
    onEditMode: () => console.log('Edit Mode clicked'),
    onViewRoadmap: () => console.log('View in Roadmap clicked'),
    onShare: () => console.log('Share/Export clicked'),
    onLinkEntity: () => console.log('Link Entity clicked'),
    onDelete: () => console.log('Delete clicked'),
  },
};

/**
 * Header with long title to test text overflow handling.
 * Tests layout with verbose arc naming.
 */
export const LongTitle: Story = {
  args: {
    arcTitle: 'Building a Comprehensive AI-Native Product Management Platform That Integrates Seamlessly With Developer Workflows',
    arcSubtitle: 'This is a very long subtitle that describes the arc in great detail, testing how the component handles overflow and wrapping of text content in the header section.',
    arcStatus: 'in_progress',
    onEditMode: () => console.log('Edit Mode clicked'),
    onViewRoadmap: () => console.log('View in Roadmap clicked'),
    onShare: () => console.log('Share/Export clicked'),
    onLinkEntity: () => console.log('Link Entity clicked'),
    onDelete: () => console.log('Delete clicked'),
  },
};
