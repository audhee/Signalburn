import { Audio } from 'expo-av';
import { useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';
import { apiClient } from '@/services/apiClient';

export type VoiceState = 'idle' | 'recording' | 'processing' | 'error';

export const useVoiceAgent = () => {
    const [state, setState] = useState<VoiceState>('idle');
    const [error, setError] = useState<string | null>(null);
    const [transcript, setTranscript] = useState<string>('');
    const [aiResponse, setAiResponse] = useState<string>('');
    const [sessionId, setSessionId] = useState<string>(`session-${Date.now()}`);

    const recordingRef = useRef<Audio.Recording | null>(null);
    const isProcessingRef = useRef<boolean>(false);

    const resetSession = () => {
        setSessionId(`session-${Date.now()}`);
        setTranscript('');
        setAiResponse('');
        setError(null);
        setState('idle');
    };

    // ── Permissions ─────────────────────────────────────────────────────
    useEffect(() => {
        async function getPermissions() {
            try {
                const { status } = await Audio.requestPermissionsAsync();
                if (status !== 'granted') {
                    setError('Microphone permission denied');
                }
                await Audio.setAudioModeAsync({
                    allowsRecordingIOS: true,
                    playsInSilentModeIOS: true,
                    staysActiveInBackground: false,
                    shouldDuckAndroid: true,
                });
            } catch (err) {
                console.error('Failed to get audio permissions', err);
            }
        }
        getPermissions();

        return () => {
            if (recordingRef.current) {
                recordingRef.current.stopAndUnloadAsync().catch(() => {});
            }
        };
    }, []);

    // ── Voice recording ─────────────────────────────────────────────────
    const startRecording = async () => {
        try {
            if (isProcessingRef.current) return;

            setTranscript('');
            setAiResponse('');
            setError(null);

            const { recording } = await Audio.Recording.createAsync(
                Audio.RecordingOptionsPresets.HIGH_QUALITY,
            );
            recordingRef.current = recording;
            setState('recording');
        } catch (err) {
            console.error('Failed to start recording', err);
            setError('Could not start microphone');
            setState('error');
        }
    };

    const stopRecordingAndProcess = async () => {
        if (!recordingRef.current || isProcessingRef.current) return;

        isProcessingRef.current = true;
        setState('processing');

        try {
            const status = await recordingRef.current.getStatusAsync();

            // Ignore very short recordings (accidental taps)
            if (status.canRecord && status.durationMillis < 500) {
                await recordingRef.current.stopAndUnloadAsync().catch(() => {});
                recordingRef.current = null;
                setState('idle');
                return;
            }

            if (status.canRecord) {
                await recordingRef.current.stopAndUnloadAsync();
            }

            const uri = recordingRef.current.getURI();
            recordingRef.current = null;
            if (!uri) throw new Error('No recording URI found');

            // Build FormData for upload
            const WebFormData =
                Platform.OS === 'web' ? (globalThis as any).FormData : FormData;
            const formData = new WebFormData();

            if (Platform.OS === 'web') {
                const blobResponse = await fetch(uri);
                const audioBlob = await blobResponse.blob();
                formData.append('audio', audioBlob, 'user_speech.m4a');
            } else {
                // @ts-ignore React Native FormData file object shape
                formData.append('audio', {
                    uri: Platform.OS === 'ios' ? uri.replace('file://', '') : uri,
                    name: 'user_speech.m4a',
                    type: 'audio/m4a',
                });
            }

            formData.append('session_id', sessionId);

            // Send to backend → Groq Whisper STT + Groq LLM → JSON
            const response = await apiClient.request('/api/v1/ai/process-voice', {
                method: 'POST',
                body: formData,
                isFormData: true,
            });

            setTranscript(response.transcription || '');
            setAiResponse(response.response || '');
            setState('idle');
        } catch (err: any) {
            console.error('Voice processing failed', err);
            setError(err.message || 'Something went wrong');
            setState('error');
        } finally {
            isProcessingRef.current = false;
        }
    };

    // ── Text query (no audio) ───────────────────────────────────────────
    const submitTextQuery = async (text: string, language: string = 'en-IN') => {
        const cleanText = text.trim();
        if (!cleanText || isProcessingRef.current) return;

        isProcessingRef.current = true;
        setState('processing');
        setError(null);
        setTranscript(cleanText);
        setAiResponse('');

        try {
            const response = await apiClient.request('/api/v1/ai/text-query', {
                method: 'POST',
                body: {
                    text: cleanText,
                    language,
                    context: '',
                },
            });

            setAiResponse(response.response || '');
            setState('idle');
        } catch (err: any) {
            console.error('Text query failed', err);
            setError(err.message || 'Something went wrong');
            setState('error');
        } finally {
            isProcessingRef.current = false;
        }
    };

    return {
        state,
        error,
        transcript,
        aiResponse,
        submitTextQuery,
        startRecording,
        stopRecordingAndProcess,
        isRecording: state === 'recording',
        isProcessing: state === 'processing',
        isPlaying: false, // no audio playback — text only
        sessionId,
        resetSession,
    };
};
