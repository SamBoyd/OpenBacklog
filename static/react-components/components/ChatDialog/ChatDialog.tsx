import React, { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router';

import { useAiImprovementsContext } from '#contexts/AiImprovementsContext';
import useChatMessages from '#hooks/useChatMessages';
import useJobResultProcessor from '#hooks/useJobResultProcessor';
import { useEntityFromUrl } from '#hooks/useEntityFromUrl';
import useAiChat from '#hooks/useAiChat';
import { useBillingUsage } from '#hooks/useBillingUsage';

import ContextSelection from '#components/ChatDialog/ContextSelection';
import MessageHistory from '#components/reusable/MessageHistory';
import ChatErrorView from '#components/ChatDialog/ChatErrorView';
import ChatMessageInput from '#components/ChatDialog/ChatMessageInput';
import ChatHeader from '#components/ChatHeader';
import { useIsDeviceMobile } from '#hooks/isDeviceMobile';

import { LENS, AiJobChatMessage, ManagedInitiativeModel, ManagedTaskModel, AgentMode } from '#types';
import { hasActiveSubscription } from '#constants/userAccountStatus';
import VoiceChat from './VoiceChat';
import { Send } from 'lucide-react';

export interface Message {
    id: string;
    text: string;
    sender: 'user' | 'assistant';
    timestamp: Date;
    entityId: string | null;
    entityTitle: string | null;
    entityIdentifier: string | null;
    lens: LENS;
    suggested_changes?: ManagedTaskModel[] | ManagedInitiativeModel[] | null;
}

export interface PresetMessage {
    id: string;
    shortText: string;
    fullText: string;
    operation: string;
}

interface ChatDialogProps { }

const ChatDialog: React.FC<ChatDialogProps> = () => {
    const [isContextSelectionOpen, setIsContextSelectionOpen] = useState(false);
    const navigate = useNavigate();

    const isMobile = useIsDeviceMobile();

    // Check subscription status
    const { userAccountDetails, isAccountDetailsLoading } = useBillingUsage();
    const hasSubscription = userAccountDetails ? hasActiveSubscription(userAccountDetails.status) : false;

    // Get entity information from the URL
    const {
        lens,
        currentEntity
    } = useEntityFromUrl();

    // Message container reference for scrolling
    const messagesContainerRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);


    // AI chat functionality
    const {
        jobResult,
        error,
        chatDisabled,
        sendMessage,
        clearChat,
        currentContext,
        setCurrentContext,
        removeEntityFromContext
    } = useAiChat({ lens, currentEntity });

    // Message management
    const {
        threadId,
        messages,
        addMessage,
        addUserMessage,
        startNewThread,
    } = useChatMessages();

    // Job result processing
    useJobResultProcessor({
        jobResult,
        currentEntity,
        onMessageReady: (message) => {
            // Only add if not already present
            if (!messages.some(msg => msg.id === message.id)) {
                addMessage(message);
            }
        }
    });

    // Scroll to bottom when messages change
    useEffect(() => {
        if (messagesContainerRef.current) {
            messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
        }
    }, [messages]);

    const { setThreadId } = useAiImprovementsContext();

    useEffect(() => {
        setThreadId(threadId);
    }, [threadId]);

    const handleSendMessage = (messageText: string, mode: AgentMode) => {
        if (!messageText.trim()) return;

        // Add user message to local state FIRST, so it's included in the history sent to AI
        addUserMessage(messageText, lens, currentEntity);

        // Prepare messages for AI service AFTER adding the new user message
        // Need to map the local message format to AiJobChatMessage
        const messagesForApi: AiJobChatMessage[] = messages.map(msg => {
            return {
                role: msg.sender, // Assuming sender is 'user' or 'system'
                content: msg.text,
                suggested_changes: msg.suggested_changes || null,
            }
        });

        // Add the new user message to the array to be sent
        messagesForApi.push({ role: 'user', content: messageText, suggested_changes: null });

        // Send the full message history to AI service
        sendMessage(threadId, messagesForApi, lens, mode);
    };

    const handleNewChat = () => {
        startNewThread();
        clearChat();
        if (inputRef && inputRef.current) {
            inputRef.current.value = '';
            inputRef.current.focus();
        }
    };


    const responseLayoutStyle = isMobile
        ? "flex flex-col bg-sidebar h-fit"
        : "flex flex-col bg-sidebar justify-end overflow-y-auto overflow-x-hidden h-[calc(100vh-4rem)]"

    return (
        <div className={"flex flex-col bg-sidebar justify-end overflow-y-auto overflow-x-hidden h-[calc(100vh-4rem)]"}>

            <ChatHeader onNewChat={handleNewChat} />

            {/* Spacer div */}
            <div className="flex-grow"></div>

            <MessageHistory
                messages={messages}
                containerRef={messagesContainerRef}
                waitingForResponse={
                    (jobResult || false) && !["COMPLETED", "FAILED", "CANCELED"].includes(jobResult?.status || '')
                }
            />

            <ChatErrorView error={error || jobResult?.error_message || null} />

            {/* Subscription required message */}
            {!isAccountDetailsLoading && !hasSubscription && (
                <div className="relative flex-grow-0 mx-2 p-2 mb-2 rounded-sm bg-white/10">
                    <div className="flex flex-col gap-2">
                        {/* Message text in place of textarea */}
                        <div className="w-full bg-transparent text-muted-foreground text-sm p-2">
                            AI chat requires a subscription. Subscribe to unlock AI-powered features. 
                            <span className="cursor-pointer underline ml-1" onClick={() => navigate('/workspace/billing')}>Subscribe here</span>
                        </div>

                        {/* Bottom row with disabled controls and subscribe button */}
                        <div className="flex flex-row gap-2 justify-between items-center">
                            {/* Disabled mode selector placeholder */}
                            <button
                                disabled
                                className="border-0 text-xs text-sidebar-foreground bg-sidebar-foreground/10 rounded px-3 py-1 opacity-50 cursor-not-allowed"
                            >
                                Mode
                            </button>

                            <div className="flex flex-row gap-2 items-center">
                                <VoiceChat disabled={true} onVoiceInput={() => { }} />

                                <button
                                    onClick={() => { }}
                                    className={`
                                    rounded px-3 py-1 text-xs
                                    text-sidebar-foreground bg-sidebar-foreground/10
                                    transition-colors
                                    hover:text-white hover:bg-primary/50
                                    disabled:opacity-50 disabled:cursor-not-allowed
                                `}
                                    disabled={true}
                                    ref={null}
                                    data-testid="chat-send"
                                >
                                    <Send size={14} />
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Context selection and message input */}
            {
                hasSubscription && (
                    <div className='border-t border-border bg-sidebar overflow-visible'>
                        <ContextSelection
                            isOpen={isContextSelectionOpen}
                            disabled={false}
                            onOpenChange={setIsContextSelectionOpen}
                            currentContext={currentContext}
                            onContextChange={setCurrentContext}
                        />

                        <ChatMessageInput
                            onMessageSend={handleSendMessage}
                            disabled={chatDisabled}
                            inputRef={inputRef}
                            onContextSelectionToggle={() => setIsContextSelectionOpen(true)}
                        />
                    </div>
                )
            }
        </div >
    );
};

export default ChatDialog; 
