import React from 'react';
import { useNavigate } from 'react-router';

interface ChatHeaderProps {
    onNewChat: () => void;
}


const ChatHeader: React.FC<ChatHeaderProps> = ({ onNewChat }) => {
    const navigate = useNavigate();

    return (
        <div className="flex justify-end items-center p-2">
            <button
                onClick={() => navigate('/workspace/context')}
                className={`
                        self-end rounded px-2 py-1 text-sm w-16
                        text-sidebar-foreground/40
                        hover:text-sidebar-foreground/50
                        transition-colors
                    `}
            >
                Context
            </button>

            {/* New Chat Button */}
            <button
                onClick={onNewChat}
                className={`
                 rounded 
                 text-sidebar-foreground/40
                 border border-sidebar-foreground/40
                 hover:bg-primary/15
                 hover:text-sidebar-foreground/50
                 hover:border-sidebar-foreground/50
                 flex items-center justify-center
                 gap-x-1.5 p-0.5
                `}
            >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-4">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
                </svg>
            </button>
        </div>
    );
};

export default ChatHeader;