import React from 'react';
import MDEditor from '@uiw/react-md-editor';
import { GrDocumentText } from 'react-icons/gr';
import { Skeleton } from './Skeleton';

import '#styles/markdown_preview.css';

/**
 * Props for the MarkdownPreview component
 */
interface MarkdownPreviewProps {
    /** The markdown content to render */
    content: string;
    /** Whether the component is in loading state */
    loading?: boolean;
    /** Test ID for the component */
    testId?: string;
    /** Additional CSS classes */
    className?: string;
    /** Whether to show the header with icon and label */
    showHeader?: boolean;
    /** Label text for the header */
    headerLabel?: string;
}

/**
 * Read-only markdown preview component using MDEditor.Markdown.
 * Renders markdown content with syntax highlighting and proper styling.
 * Uses existing markdown_preview.css styles for consistent appearance.
 *
 * @param {object} props - The component props
 * @param {string} props.content - The markdown content to render
 * @param {boolean} [props.loading=false] - Whether to show loading skeleton
 * @param {string} [props.testId='markdown-preview'] - Test ID for the component
 * @param {string} [props.className=''] - Additional CSS classes
 * @param {boolean} [props.showHeader=true] - Whether to show the header
 * @param {string} [props.headerLabel='Description'] - Label for the header
 * @returns {React.ReactElement} The MarkdownPreview component
 */
const MarkdownPreview: React.FC<MarkdownPreviewProps> = ({
    content,
    loading = false,
    testId = 'markdown-preview',
    className = '',
    showHeader = true,
    headerLabel = 'Description',
}) => {
    if (loading) {
        return (
            <div className={`mt-2 ${className}`} data-testid={testId}>
                {showHeader && (
                    <div className="flex flex-row gap-2 min-w-[13rem] items-baseline font-light text-foreground mb-2">
                        <GrDocumentText />
                        <span className="ml-2.5">{headerLabel}</span>
                    </div>
                )}
                <Skeleton type="paragraph" className="h-[200px] w-full" />
            </div>
        );
    }

    return (
        <div className={`mt-2 text-foreground ${className}`} data-testid={testId}>
            {showHeader && (
                <div className="flex flex-row gap-2 min-w-[13rem] items-baseline font-light mb-2">
                    <GrDocumentText />
                    <span className="ml-2.5">{headerLabel}</span>
                </div>
            )}
            <div data-color-mode="dark" className="w-full p-1.5">
                {content ? (
                    <MDEditor.Markdown
                        source={content}
                        className="wmde-markdown !bg-transparent"
                    />
                ) : (
                    <p className="text-muted-foreground italic">No description</p>
                )}
            </div>
        </div>
    );
};

export default MarkdownPreview;
