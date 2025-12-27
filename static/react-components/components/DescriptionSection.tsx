import React from 'react';
import MarkdownPreview from './reusable/MarkdownPreview';

/**
 * Props for the DescriptionSection component
 */
interface DescriptionSectionProps {
    /** The description content (markdown supported) */
    description: string;
    /** Whether the component is in loading state */
    loading?: boolean;
    /** Test ID for the component */
    testId?: string;
    /** Additional CSS classes */
    className?: string;
}

/**
 * Read-only description section with markdown rendering.
 * Descriptions are created/updated via MCP tools by LLM agents.
 *
 * This component replaces the editable EntityDescriptionEditor for
 * MCP-native workflows where descriptions are managed by AI agents.
 *
 * @param {object} props - The component props
 * @param {string} props.description - The description content (markdown)
 * @param {boolean} [props.loading=false] - Whether to show loading skeleton
 * @param {string} [props.testId='description-section'] - Test ID
 * @param {string} [props.className=''] - Additional CSS classes
 * @returns {React.ReactElement} The DescriptionSection component
 */
const DescriptionSection: React.FC<DescriptionSectionProps> = ({
    description,
    loading = false,
    testId = 'description-section',
    className = '',
}) => {
    return (
        <MarkdownPreview
            content={description}
            loading={loading}
            testId={testId}
            className={className}
            showHeader={true}
            headerLabel="Description"
        />
    );
};

export default DescriptionSection;
