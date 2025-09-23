import React from 'react';
import { Message } from '../ChatDialog/ChatDialog';
import MessageHistoryView from './MessageHistoryView';

interface MessageHistoryProps {
    messages: Message[];
    containerRef: React.RefObject<HTMLDivElement>;
    waitingForResponse: boolean;
}

/**
 * Container component that handles message grouping and data transformation
 * for the chat message history
 * 
 * @param {object} props - Component props
 * @param {Message[]} props.messages - The array of messages to display
 * @param {React.RefObject<HTMLDivElement>} props.containerRef - Ref to the container for scrolling
 * @param {boolean} props.waitingForResponse - Whether to show the typing indicator
 * @returns {JSX.Element} The message history container component
 */
const MessageHistory: React.FC<MessageHistoryProps> = ({ messages, containerRef, waitingForResponse }) => {

    return (
        <MessageHistoryView
            messages={messages}
            containerRef={containerRef}
            waitingForResponse={waitingForResponse}
        />
    );
};

export default MessageHistory;
