import React, { useEffect, useRef, useState } from 'react';

import { AgentMode, InitiativeDto, TaskDto } from '#types';
import VoiceChat from './VoiceChat';
import { CompactSelectBox } from '#components/reusable/Selectbox';
import { useBillingUsage } from '#hooks/useBillingUsage';
import { UserAccountStatus } from '#constants/userAccountStatus';
import { useContainerWidth } from '#hooks/useContainerWidth';
import { CornerDownLeft, Send, SendHorizontal } from 'lucide-react';
import { SafeStorage } from '#hooks/useUserPreferences';

const MAX_MESSAGE_LENGTH = 3000;
const CHAT_DRAFT_KEY = 'chatMessageDraft';

// Validator for chat draft string
const isString = (value: unknown): value is string => typeof value === 'string';

interface ChatMessageInputProps {
    onMessageSend: (message: string, mode: AgentMode) => void;
    disabled?: boolean;
    inputRef?: React.RefObject<HTMLTextAreaElement>;
    onContextSelectionToggle?: () => void;
}

/**
 * Component to display and select from preset messages
 * 
 * @param {object} props - Component props
 * @param {InitiativeDto | TaskDto} props.currentEntity - The current entity to send the message to
 * @param {(messageText: string, mode: AgentMode) => void} props.onMessageSend - Function to call when a message is sent
 * @param {boolean} props.disabled - Whether the message input is disabled
 * @param {React.RefObject<HTMLTextAreaElement>} props.inputRef - Ref to the text area input
 * @param {() => void} props.onContextSelectionToggle - Function to call when the context selection is toggled
 * @returns {JSX.Element} The chat message input component
 */
const ChatMessageInput: React.FC<ChatMessageInputProps> = ({
    onMessageSend,
    inputRef,
    onContextSelectionToggle,
    disabled=false,
}) => {
    const [message, setMessage] = useState('');
    const sendButtonRef = useRef<HTMLButtonElement>(null);
    const [mode, setMode] = useState(AgentMode.EDIT);

    // Load saved draft on mount
    useEffect(() => {
        const savedDraft = SafeStorage.safeGet(CHAT_DRAFT_KEY, isString, '');
        if (savedDraft) {
            setMessage(savedDraft);
        }
    }, []);

    const localTextareaRef = useRef<HTMLTextAreaElement>(null);
    // Use the provided inputRef or fall back to our local ref
    const textareaRef = inputRef || localTextareaRef;

    // Container width tracking for responsive behavior
    const containerRef = useRef<HTMLDivElement>(null);

    /**
     * Adjusts the height of the textarea based on its content
     */
    const adjustTextareaHeight = () => {
        if (textareaRef?.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
        }
    };

    // Set up ResizeObserver to handle width changes
    useEffect(() => {
        const textarea = textareaRef?.current;
        if (!textarea) return;

        const resizeObserver = new ResizeObserver(() => {
            adjustTextareaHeight();
        });

        resizeObserver.observe(textarea);

        return () => {
            resizeObserver.disconnect();
        };
    }, [textareaRef]);

    // Adjust height when message content changes
    useEffect(() => {
        adjustTextareaHeight();
    }, [message]);

    // Save draft when message changes
    useEffect(() => {
        SafeStorage.safeSet(CHAT_DRAFT_KEY, message);
    }, [message]);

    const handleSendMessage = () => {
        onMessageSend(message, mode);
        setMessage('');

        // Reset the textarea height after the state has been updated
        setTimeout(() => {
            adjustTextareaHeight();
        }, 0);
    }

    const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        // Backspace to delete the last line
        if (e.key === 'Backspace' && message.endsWith('\n')) {
            setMessage(message.slice(0, -1));
        }

        // Enter to submit the message
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }

        // 'p' key to open context selection
        if ((e.key === 'p' || e.key === 'P') && e.shiftKey && e.ctrlKey && onContextSelectionToggle) {
            e.preventDefault();
            onContextSelectionToggle();
        }
    }

    const handleContainerClick = () => {
        if (textareaRef?.current) {
            textareaRef.current.focus();
        }
    }

    const handleVoiceInput = (input: string) => {
        setMessage(prev => prev + input);
    }

    return (
        <>
            {/* Chat message input */}
            <div
                ref={containerRef}
                className={
                    `relative flex-grow-0 mx-2 p-2 mb-2 rounded-sm  bg-white/10
                     transition-colors cursor-text`
                }
                onClick={handleContainerClick}
            >


                {/* message container */}
                <div className="flex flex-col gap-2" >
                    <textarea
                        className={`
                            w-full max-h-48 bg-transparent 
                            text-white
                            ${disabled ? 'placeholder:text-muted/50': 'placeholder:text-muted-foreground' }
                            text-sm
                            p-2 resize-none focus:outline-none
                         `}
                        rows={1}
                        style={{ overflow: 'hidden' }}
                        value={message || ''}
                        placeholder={"What are we doing today?"}
                        onInput={adjustTextareaHeight}
                        onKeyDown={onKeyDown}
                        onChange={e => setMessage(e.target.value)}
                        disabled={disabled}
                        ref={textareaRef}
                        maxLength={3000}
                        data-testid="chat-textbox"
                    />


                    <div className='flex flex-row gap-2 justify-between items-center'>
                        <CompactSelectBox
                            id="mode"
                            name="mode"
                            value={mode}
                            onChange={(value) => setMode(value as AgentMode)}
                            className={`
                                border-0 text-xs
                                text-sidebar-foreground bg-sidebar-foreground/10
                                transition-colors
                                hover:text-white hover:bg-primary/50
                                disabled:opacity-50 disabled:cursor-not-allowed
                                rounded
                            `}
                            dataTestId="chat-mode"
                            disabled={disabled}
                            placeholder='Mode'
                            direction='up'
                            options={[
                                {
                                    label: 'Discuss',
                                    value: AgentMode.DISCUSS,
                                },
                                {
                                    label: 'Edit',
                                    value: AgentMode.EDIT,
                                },
                            ]}
                        />

                        <div className='flex flex-row gap-2 items-center'>
                            <VoiceChat disabled={disabled} onVoiceInput={handleVoiceInput} />

                            <button
                                onClick={handleSendMessage}
                                className={`
                                    rounded px-3 py-1 text-xs
                                    text-sidebar-foreground bg-sidebar-foreground/10
                                    transition-colors
                                    hover:text-white hover:bg-primary/50
                                    disabled:opacity-50 disabled:cursor-not-allowed
                                `}
                                disabled={disabled}
                                ref={sendButtonRef}
                                data-testid="chat-send"
                            >
                                <Send size={14} />
                            </button>
                        </div>
                    </div>
                </div>
            </div>

        </>
    );
};

export default ChatMessageInput;
