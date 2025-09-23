import React from 'react';
import MDEditor from '@uiw/react-md-editor';
import { ChevronDown } from 'lucide-react';
import { Button } from './Button';

import { Message } from '../ChatDialog/ChatDialog';
import ChangesDisplay from '#components/diffs/ChangesDisplay';
import { useIsDeviceMobile } from '#hooks/isDeviceMobile';

interface MessageHistoryViewProps {
    messages: Message[];
    containerRef: React.RefObject<HTMLDivElement>;
    waitingForResponse: boolean;
}

/**
 * Presentation component to display the chat message history
 * 
 * @param {object} props - Component props
 * @param {Message[]} props.messages - The array of messages to display
 * @param {React.RefObject<HTMLDivElement>} props.containerRef - Ref to the container for scrolling
 * @param {boolean} props.waitingForResponse - Whether to show the typing indicator
 * @returns {JSX.Element} The message history view component
 */
const MessageHistoryView: React.FC<MessageHistoryViewProps> = ({
    messages,
    containerRef,
    waitingForResponse
}) => {
    const [showScrollToBottom, setShowScrollToBottom] = React.useState(false);
    const isMobile = useIsDeviceMobile();

    /**
     * Handles scroll event to determine if the scroll-to-bottom button should be shown
     */
    React.useEffect(() => {
        const container = containerRef.current;
        if (!container) return;

        const handleScroll = () => {
            // Show button if not at the bottom (allowing a 10px buffer)
            const atBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 10;
            setShowScrollToBottom(!atBottom);
        };

        container.addEventListener('scroll', handleScroll);
        // Check on mount
        handleScroll();
        return () => {
            container.removeEventListener('scroll', handleScroll);
        };
    }, [containerRef]);

    /**
     * Scrolls the container to the bottom smoothly
     */
    const scrollToBottom = React.useCallback(() => {
        const container = containerRef.current;
        if (container) {
            container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
        }
    }, [containerRef]);

    // Scroll to bottom when new messages arrive
    React.useEffect(() => {
        if (!showScrollToBottom) {
            scrollToBottom();
        }
    }, [messages, showScrollToBottom, scrollToBottom]);

    const messagesDeduplicated = messages.filter((message, index, self) =>
        index === self.findIndex((t) => t.id === message.id)
    );

    const messageContainerStyle = isMobile
        ? "relative flex-grow-1 hide-scrollbar"
        : "flex-grow-1 overflow-y-auto relative minimal-scrollbar  max-w-[58rem] mx-auto";

    return (
        <div ref={containerRef} className={messageContainerStyle}>
            {/* Messages */}
            {messagesDeduplicated.map((message: Message) => (
                <div
                    key={message.id}
                    className={`flex flex-col justify-start`}
                >
                    <div
                        className={`rounded-lg m-2 py-3 px-5
                            ${message.sender === 'user'
                                // needs a max width
                                ? 'bg-black/30 text-neutral-200 w-4/5 max-w-[42rem] self-end'
                                : 'bg-sidebar text-muted-foreground/95 '
                            }`}
                    >
                        <MDEditor.Markdown
                            source={message.text}
                            style={{
                                backgroundColor: 'transparent',
                                color: 'inherit',
                                fontSize: '14px',
                                fontFamily: 'inherit',
                                fontWeight: 'inherit',
                                fontStyle: 'inherit',
                                fontStretch: 'inherit',
                                lineHeight: '18px'
                            }}
                        />
                    </div>
                </div>
            ))}

            {waitingForResponse && (
                <div className="flex justify-start items-center ml-2">
                    {/* Typing animation (3 dots) */}
                    <div className="flex items-center space-x-1 rounded p-3 bg-transparent">
                        <div className="w-2 h-2 bg-sidebar-foreground rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-sidebar-foreground rounded-full animate-pulse delay-150"></div>
                        <div className="w-2 h-2 bg-sidebar-foreground rounded-full animate-pulse delay-300"></div>
                    </div>
                </div>
            )}

            <ChangesDisplay />

            {showScrollToBottom && (
                <div className="sticky bottom-1 flex justify-center z-20 pointer-events-none">
                    <div className="pointer-events-auto">
                        <Button
                            onClick={scrollToBottom}
                            title="Scroll to bottom"
                            className="border-0 bg-primary/15 text-primary-foreground shadow-lg hover:bg-primary/30 p-1 rounded-full"
                            dataTestId="scroll-to-bottom-btn"
                        >
                            <ChevronDown className="w-3 h-3" />
                        </Button>
                    </div>
                </div>
            )}

        </div>
    );
};

export default MessageHistoryView; 