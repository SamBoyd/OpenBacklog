import { useRef, useState, useCallback, useEffect } from 'react';

export interface VoiceTranscriptionState {
    isListening: boolean;
    isTranscribing: boolean;
    transcript: string;
    error: string | null;
    elapsedSeconds: number;
}

export interface VoiceTranscriptionActions {
    startRecording: () => Promise<void>;
    stopRecording: () => void;
    cancelRecording: () => void;
    clearError: () => void;
    clearTranscript: () => void;
}

export interface UseVoiceTranscriptionReturn {
    state: VoiceTranscriptionState;
    actions: VoiceTranscriptionActions;
}

/**
 * Custom hook for voice transcription functionality.
 * Handles recording audio, transcribing speech to text, and managing associated states.
 * 
 * @returns {UseVoiceTranscriptionReturn} Object containing state and actions for voice transcription
 */
export const useVoiceTranscription = (): UseVoiceTranscriptionReturn => {
    const [isListening, setIsListening] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [error, setError] = useState<string | null>(null);
    const [elapsedSeconds, setElapsedSeconds] = useState(0);

    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);

    /**
     * Handles errors by setting error state and resetting recording states.
     * @param {string} message - Error message to display
     */
    const handleError = useCallback((message: string) => {
        setError(message);
        setIsListening(false);
        setIsTranscribing(false);
    }, []);

    /**
     * Clears the current error state.
     */
    const clearError = useCallback(() => {
        setError(null);
    }, []);

    /**
     * Clears the current transcript.
     */
    const clearTranscript = useCallback(() => {
        setTranscript('');
    }, []);

    /**
     * Processes recorded audio and sends it for transcription.
     */
    const processAudioAndTranscribe = useCallback(async () => {
        if (audioChunksRef.current.length === 0) {
            handleError("No audio data recorded. Please try speaking for a longer duration.");
            return;
        }

        setIsTranscribing(true);
        setError(null);
        setTranscript('');

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = [];

        const formData = new FormData();
        formData.append("file", audioBlob, "speech.webm");

        try {
            const response = await fetch("/api/transcribe", {
                method: "POST",
                body: formData,
            });

            if (!response.ok) {
                let errorMessage = `Transcription failed: ${response.status} ${response.statusText}`;
                try {
                    const errorData = await response.json();
                    errorMessage = errorData.message || errorData.error || errorMessage;
                } catch (e) {
                    // Failed to parse JSON, stick with the status text
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            if (result.transcript) {
                setTranscript(result.transcript.text);
            } else {
                handleError("Transcription successful, but no transcript was returned by the API.");
            }
        } catch (e: any) {
            console.error("Transcription error:", e);
            handleError(e.message || "An unknown error occurred during transcription.");
        } finally {
            setIsTranscribing(false);
        }
    }, [handleError]);

    /**
     * Starts voice recording by requesting microphone access and initializing MediaRecorder.
     */
    const startRecording = useCallback(async () => {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            handleError("Voice recording is not supported by your browser. Please use a modern browser like Chrome or Firefox.");
            return;
        }

        setError(null);
        setTranscript('');

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            setIsListening(true);
            mediaRecorderRef.current = new MediaRecorder(stream);
            audioChunksRef.current = [];

            mediaRecorderRef.current.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorderRef.current.onstop = processAudioAndTranscribe;

            mediaRecorderRef.current.onerror = (event) => {
                const mediaRecorderError = event as unknown as { error: DOMException };
                console.error("MediaRecorder error:", mediaRecorderError.error);
                handleError(`Recording error: ${mediaRecorderError.error.name} - ${mediaRecorderError.error.message}`);
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorderRef.current.start();

        } catch (err: any) {
            console.error("Error starting voice recording:", err);
            if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
                handleError("Microphone access denied. Please allow microphone access in your browser settings and refresh the page.");
            } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
                handleError("No microphone found. Please ensure a microphone is connected and enabled.");
            } else if (err.name === "NotReadableError") {
                handleError("Microphone is already in use or a hardware error occurred. Please check your microphone settings.");
            } else {
                handleError(`Could not start voice recording: ${err.name}. Please ensure you have a microphone and have granted permission.`);
            }
            setIsListening(false);
        }
    }, [handleError, processAudioAndTranscribe]);

    /**
     * Stops voice recording and processes the recorded audio.
     */
    const stopRecording = useCallback(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
            mediaRecorderRef.current.stop();
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
        }
        setIsListening(false);
    }, []);

    /**
     * Cancels voice recording without processing the audio.
     */
    const cancelRecording = useCallback(() => {
        if (mediaRecorderRef.current) {
            if (mediaRecorderRef.current.state === "recording") {
                mediaRecorderRef.current.stop();
            }
            mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
            mediaRecorderRef.current.onstop = null;
        }
        audioChunksRef.current = [];
        setIsListening(false);
        setError(null);
        setTranscript('');
    }, []);

    // Auto-clear error after 3 seconds
    useEffect(() => {
        if (error) {
            const timer = setTimeout(() => {
                setError(null);
            }, 3000);

            return () => clearTimeout(timer);
        }
        return () => { };
    }, [error]);

    // Timer for recording elapsed time
    useEffect(() => {
        let intervalId: NodeJS.Timeout;
        if (isListening) {
            intervalId = setInterval(() => {
                setElapsedSeconds(prev => prev + 1);
            }, 1000);
        }
        return () => {
            if (intervalId) {
                clearInterval(intervalId);
            }
            setElapsedSeconds(0);
        };
    }, [isListening]);

    const state: VoiceTranscriptionState = {
        isListening,
        isTranscribing,
        transcript,
        error,
        elapsedSeconds,
    };

    const actions: VoiceTranscriptionActions = {
        startRecording,
        stopRecording,
        cancelRecording,
        clearError,
        clearTranscript,
    };

    return {
        state,
        actions,
    };
};

export default useVoiceTranscription; 