import { Mic, X, Check, Loader2, Sparkles } from 'lucide-react';
import React, { useEffect, useRef } from 'react';
import { useVoiceTranscription } from '#hooks/useVoiceTranscription';
import { useTextRewrite } from '#hooks/useTextRewrite';
import { Tooltip } from 'react-tooltip';

const ICON_SIZE = 12;

interface VoiceChatProps {
    /**
     * Callback function invoked when voice input is successfully transcribed.
     * @param {string} input - The transcribed text.
     */
    disabled: boolean;
    onVoiceInput: (input: string) => void;
    shouldDisplayRewriteDialog?: boolean;
    existingDescription?: string;
}

/**
 * A component that allows users to record their voice,
 * sends it for transcription, and invokes a callback with the transcribed text.
 */
const VoiceChat: React.FC<VoiceChatProps> = ({
    disabled,
    onVoiceInput,
    shouldDisplayRewriteDialog = false,
    existingDescription
}) => {
    const { state, actions } = useVoiceTranscription();
    const { isListening, isTranscribing, transcript, error: transcriptionError, elapsedSeconds } = state;
    const { startRecording, stopRecording, cancelRecording } = actions;

    const {
        rewriteText,
        isRewriting,
        error: rewriteError,
        isRewriteEnabled,
        setIsRewriteEnabled
    } = useTextRewrite({ existingDescription });

    const lastTranscriptProcessed = useRef<string | null>(null);

    /**
     * Formats elapsed time in MM:SS format.
     * @param {number} seconds - The elapsed seconds.
     * @returns {string} The formatted time string.
     */
    const formatTime = (seconds: number): string => {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    };

    // Call onVoiceInput when transcript is available
    useEffect(() => {
        if (transcript && transcript !== lastTranscriptProcessed.current) {
            const processTranscript = async () => {
                try {
                    const finalText = await rewriteText(transcript);
                    onVoiceInput(finalText);
                    lastTranscriptProcessed.current = transcript;
                } catch (e) {
                    // Error is already handled in the hook
                }
            };
            processTranscript();
        }
    }, [transcript, rewriteText, onVoiceInput]);

    useEffect(() => {
        if (!shouldDisplayRewriteDialog) {
            setIsRewriteEnabled(false);
        }
    }, [shouldDisplayRewriteDialog, setIsRewriteEnabled]);

    const button_styles = ` 
        hover:bg-primary/50 hover:text-white
        self-end p-1.5 rounded-full text-sm
        text-sidebar-foreground bg-sidebar-foreground/10
        transition-colors
        disabled:opacity-50 disabled:cursor-not-allowed
    `;

    const toggle_button_styles = (active: boolean) => `
        hover:bg-primary/50 hover:text-white
        self-end p-1.5 rounded-full text-sm
        ${active
            ? 'text-foreground bg-primary/30'
            : 'text-sidebar-foreground bg-sidebar-foreground/10'
        }
        transition-colors
        disabled:opacity-50 disabled:cursor-not-allowed
    `;

    const error = transcriptionError || rewriteError;

    return (
        <div className="relative">
           <div className="flex items-center space-x-2">
                {!isTranscribing && !isListening && (
                    <button
                        onClick={startRecording}
                        disabled={disabled || isTranscribing || isRewriting}
                        className={button_styles}
                        aria-label="Start voice recording"
                        data-tooltip-id="start-voice-recording-tooltip"
                        data-tooltip-content="Start recording"
                        data-tooltip-place="bottom"
                        data-tooltip-delay-show={500}
                    >
                        <Mic size={ICON_SIZE} />
                    </button>
                )}

                {!isTranscribing && isListening && (
                    <div className="flex align-center space-x-2">
                        <span className="text-sm text-sidebar-foreground mr-2 cursor-default">
                            {formatTime(elapsedSeconds)}
                        </span>
                        {shouldDisplayRewriteDialog && (
                            <button
                                onClick={() => setIsRewriteEnabled(!isRewriteEnabled)}
                                className={toggle_button_styles(isRewriteEnabled)}
                                aria-label={isRewriteEnabled ? "Disable rewriting" : "Enable rewriting"}
                                data-tooltip-id="rewrite-toggle-tooltip"
                                data-tooltip-content={isRewriteEnabled ? "Rewriting: ON" : "Rewriting: OFF"}
                                data-tooltip-place="bottom"
                                data-tooltip-delay-show={500}
                            >
                                <Sparkles size={ICON_SIZE} />
                            </button>
                        )}
                        <button
                            onClick={cancelRecording}
                            className={button_styles}
                            aria-label="Cancel voice recording"
                            data-tooltip-id="cancel-voice-recording-tooltip"
                            data-tooltip-content="Cancel recording"
                            data-tooltip-place="bottom"
                            data-tooltip-delay-show={500}
                        >
                            <X size={ICON_SIZE} />
                        </button>
                        <button
                            onClick={stopRecording}
                            className={`
                                self-end p-1.5 rounded-full text-sm
                                text-white bg-primary
                                transition-colors
                                disabled:opacity-50 disabled:cursor-not-allowed
                                animate animate-pulse
                            `}
                            aria-label="Confirm voice recording"
                            data-tooltip-id="confirm-voice-recording-tooltip"
                            data-tooltip-content="Confirm recording"
                            data-tooltip-place="bottom"
                            data-tooltip-delay-show={500}
                        >
                            <Check size={ICON_SIZE} />
                        </button>
                    </div>
                )}

                {(isTranscribing || isRewriting) && (
                    <button
                        className={`
                            self-end p-2 rounded-full text-sm
                            text-sidebar-foreground bg-sidebar-foreground/10
                            transition-colors
                            disabled:opacity-50 disabled:cursor-not-allowed
                        `}
                        disabled={true}
                        data-tooltip-id="recording-in-progress-tooltip"
                        data-tooltip-content="Recording in progress"
                        data-tooltip-place="bottom"
                        data-tooltip-delay-show={500}
                    >
                        <Loader2 size={ICON_SIZE} className="animate-spin text-primary" />
                    </button>
                )}
            </div>

            {error && (
                <div className="absolute -top-[100%] right-0 w-64 text-center text-sm text-red-700 p-3 bg-red-100 border border-red-300 rounded-md" role="alert">
                    {error}
                </div>
            )}

            <div className='z-50'>
                <Tooltip id="rewrite-toggle-tooltip" className="custom-tooltip" />
                <Tooltip id="cancel-voice-recording-tooltip" className="custom-tooltip" />
                <Tooltip id="recording-in-progress-tooltip" className="custom-tooltip" />
                <Tooltip id="start-voice-recording-tooltip" className="custom-tooltip" />
                <Tooltip id="confirm-voice-recording-tooltip" className="custom-tooltip" />
            </div>
        </div>
    );
};

export default VoiceChat;