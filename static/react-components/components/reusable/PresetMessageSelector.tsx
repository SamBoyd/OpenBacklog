import React from 'react';
import { InitiativeDto, TaskDto } from '#types';
import { PresetMessage } from '../ChatDialog/ChatDialog';

interface PresetMessageSelectorProps {
    currentEntity?: InitiativeDto | TaskDto | null;
    presetMessages: PresetMessage[];
    onSelectMessage: (message: PresetMessage) => void;
}

/**
 * Component to display and select from preset messages
 * 
 * @param {object} props - Component props
 * @param {InitiativeDto | TaskDto} props.currentEntity - The current entity to send the message to
 * @param {PresetMessage[]} props.presetMessages - Array of preset messages that can be selected
 * @param {(messageText: string) => void} props.onSelectMessage - Function to call when a message is selected
 * @returns {JSX.Element} The preset message selector component
 */
const PresetMessageSelector: React.FC<PresetMessageSelectorProps> = ({
    currentEntity,
    presetMessages,
    onSelectMessage
}) => {
    return (
        <div className="flex-grow-0 mx-2 my-4 p-2 rounded-lg bg-muted">
            {/* Current entity */}
            {currentEntity && (
                <div className={
                    `bg-muted
                        border border-muted-foreground rounded
                        flex flex-row p-1 mb-2 max-h-8 max-w-[268px]
                        justify-start items-center flex-shrink-0 min-wz-0`
                }>
                    <p className="text-sm text-muted-foreground truncate min-w-0 cursor-default">
                        {currentEntity?.identifier} - {currentEntity?.title}
                    </p>
                </div>
            )}

            {/* Message shown to the user */}
            {presetMessages.length > 0 ? (
                <div className="text-sm text-muted-foreground mb-2 cursor-default">Select a message to send:</div>
            ) : (
                <div className="text-sm text-muted-foreground mb-2 cursor-default">Select / Create an initiative or task to send a message</div>
            )}

            {/* Preset messages */}
            <div className="flex flex-wrap gap-2">
                {presetMessages.map((preset) => (
                    <div
                        key={preset.id}
                        className="relative group"
                        data-testid={`preset-message-${preset.id}`}
                    >
                        <button
                            onClick={() => onSelectMessage(preset)}
                            className="rounded px-2 py-1 text-sm bg-muted border border-muted-foreground text-muted-foreground hover:bg-selected/10 hover:text-selected-foreground/50 transition-colors"
                        >
                            {preset.shortText}
                        </button>

                        {/* Expanded message on hover */}
                        <div className="absolute bottom-full left-0 mb-2 w-48 p-2 bg-popover text-muted-foreground rounded shadow-md 
                                       opacity-0 group-hover:opacity-100 invisible group-hover:visible 
                                       transition-all duration-200 z-10 text-sm">
                            {preset.fullText}
                            <div className="absolute w-2 h-2 bg-popover rotate-45 -bottom-1 left-3"></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PresetMessageSelector;
