import React from 'react';

/**
 * Props for the InlineMarkdownPreview component
 */
interface InlineMarkdownPreviewProps {
    /** The markdown content to render inline */
    content: string;
    /** Additional CSS classes */
    className?: string;
    /** Test ID for the component */
    testId?: string;
}

/**
 * Lightweight inline markdown preview for truncated card previews.
 * Renders basic inline markdown elements without full parsing overhead.
 *
 * Supports:
 * - **bold** text
 * - *italic* text
 * - `inline code`
 * - [links](url)
 *
 * Strips block elements (headings, lists, code blocks) for clean truncation.
 *
 * @param {object} props - The component props
 * @param {string} props.content - The markdown content to render
 * @param {string} [props.className=''] - Additional CSS classes
 * @param {string} [props.testId='inline-markdown-preview'] - Test ID
 * @returns {React.ReactElement | null} The rendered inline markdown or null if empty
 */
const InlineMarkdownPreview: React.FC<InlineMarkdownPreviewProps> = ({
    content,
    className = '',
    testId = 'inline-markdown-preview',
}) => {
    if (!content) return null;

    /**
     * Converts basic markdown to React elements.
     * Handles bold, italic, inline code, and links.
     * Strips block-level markdown for clean inline display.
     */
    const renderInlineMarkdown = (text: string): React.ReactNode[] => {
        // Remove markdown block elements to flatten for inline display
        let cleaned = text
            .replace(/^#{1,6}\s+/gm, '') // Remove heading markers
            .replace(/^[-*+]\s+/gm, '') // Remove unordered list markers
            .replace(/^\d+\.\s+/gm, '') // Remove ordered list markers
            .replace(/```[\s\S]*?```/g, '') // Remove fenced code blocks
            .replace(/\n+/g, ' ') // Collapse newlines to spaces
            .trim();

        const elements: React.ReactNode[] = [];
        let lastIndex = 0;
        let keyCounter = 0;

        // Combined regex for inline markdown elements
        // Order matters: bold (**) must come before italic (*) to avoid conflicts
        const inlineRegex = /(\*\*(.+?)\*\*)|(\*(.+?)\*)|(`(.+?)`)|(\[(.+?)\]\((.+?)\))/g;
        let match;

        while ((match = inlineRegex.exec(cleaned)) !== null) {
            // Add plain text before this match
            if (match.index > lastIndex) {
                elements.push(cleaned.slice(lastIndex, match.index));
            }

            if (match[1]) {
                // Bold: **text**
                elements.push(<strong key={keyCounter++}>{match[2]}</strong>);
            } else if (match[3]) {
                // Italic: *text*
                elements.push(<em key={keyCounter++}>{match[4]}</em>);
            } else if (match[5]) {
                // Inline code: `text`
                elements.push(
                    <code
                        key={keyCounter++}
                        className="bg-muted px-1 rounded text-xs font-mono"
                    >
                        {match[6]}
                    </code>
                );
            } else if (match[7]) {
                // Link: [text](url)
                elements.push(
                    <a
                        key={keyCounter++}
                        href={match[9]}
                        className="text-primary hover:underline"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        {match[8]}
                    </a>
                );
            }

            lastIndex = match.index + match[0].length;
        }

        // Add remaining plain text after last match
        if (lastIndex < cleaned.length) {
            elements.push(cleaned.slice(lastIndex));
        }

        return elements.length > 0 ? elements : [cleaned];
    };

    return (
        <span className={className} data-testid={testId}>
            {renderInlineMarkdown(content)}
        </span>
    );
};

export default InlineMarkdownPreview;
