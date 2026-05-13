import { Audio } from 'expo-av';
import { useState, useRef, useEffect, useCallback } from 'react';
import { Platform } from 'react-native';
import { apiClient } from '@/services/apiClient';

export type VoiceState = 'idle' | 'recording' | 'processing' | 'playing' | 'error';

interface UseVoiceAgentOptions {
    // Called when voice is transcribed — so ai-guidance can feed it into guided flow
    onTranscribed?: (text: string) => void;
    getLanguageCode?: () => string;
}

export const useVoiceAgent = (options: UseVoiceAgentOptions = {}) => {
    const [state, setState]           = useState<VoiceState>('idle');
    const [error, setError]           = useState<string | null>(null);
    const [transcript, setTranscript] = useState<string>('');
    const [aiResponse, setAiResponse] = useState<string>('');

    const recordingRef    = useRef<Audio.Recording | null>(null);
    const soundRef        = useRef<Audio.Sound | null>(null);
    const isProcessingRef = useRef<boolean>(false);
    const [sessionId, setSessionId] = useState<string>(`session-${Date.now()}`);

    const resetSession = () => setSessionId(`session-${Date.now()}`);

    useEffect(() => {
        async function getPermissions() {
            try {
                const { status } = await Audio.requestPermissionsAsync();
                if (status !== 'granted') setError('Microphone permission denied');
                await Audio.setAudioModeAsync({
                    allowsRecordingIOS:      true,
                    playsInSilentModeIOS:    true,
                    staysActiveInBackground: false,
                    shouldDuckAndroid:       true,
                });
            } catch (e) {
                console.error('Failed to get audio permissions', e);
            }
        }
        getPermissions();
        return () => {
            if (recordingRef.current) recordingRef.current.stopAndUnloadAsync().catch(() => {});
            if (soundRef.current) soundRef.current.unloadAsync().catch(() => {});
        };
    }, []);

    const playAudioBase64 = async (audioBase64: string) => {
        setState('playing');
        try {
            await Audio.setAudioModeAsync({
                allowsRecordingIOS:   false,
                playsInSilentModeIOS: true,
                shouldDuckAndroid:    true,
            });
            const { sound } = await Audio.Sound.createAsync(
                { uri: `data:audio/wav;base64,${audioBase64}` },
                { shouldPlay: true }
            );
            soundRef.current = sound;
            sound.setOnPlaybackStatusUpdate((status) => {
                if (status.isLoaded && status.didJustFinish) {
                    setState('idle');
                    sound.unloadAsync().catch(() => {});
                }
            });
        } catch (audioErr) {
            console.error('Audio playback failed:', audioErr);
            setState('idle');
        }
    };

    const startRecording = async () => {
        try {
            if (isProcessingRef.current) return;
            if (soundRef.current) {
                await soundRef.current.stopAsync();
                await soundRef.current.unloadAsync();
                soundRef.current = null;
            }
            setTranscript('');
            setAiResponse('');
            const { recording } = await Audio.Recording.createAsync(
                Audio.RecordingOptionsPresets.HIGH_QUALITY
            );
            recordingRef.current = recording;
            setState('recording');
            setError(null);
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

            if (status.canRecord && status.durationMillis < 500) {
                await recordingRef.current.stopAndUnloadAsync().catch(() => {});
                recordingRef.current    = null;
                isProcessingRef.current = false;
                setState('idle');
                return;
            }

            if (status.canRecord) await recordingRef.current.stopAndUnloadAsync();

            const uri = recordingRef.current.getURI();
            recordingRef.current = null;
            if (!uri) throw new Error('No recording URI found');

            // Step 1 — transcribe audio only (STT)
            const WebFormData = Platform.OS === 'web' ? (globalThis as any).FormData : FormData;
            const formData    = new WebFormData();

            if (Platform.OS === 'web') {
                const blobResponse = await fetch(uri);
                const audioBlob    = await blobResponse.blob();
                formData.append('audio', audioBlob, 'user_speech.m4a');
            } else {
                // @ts-ignore
                formData.append('audio', {
                    uri:  Platform.OS === 'ios' ? uri.replace('file://', '') : uri,
                    name: 'user_speech.m4a',
                    type: 'audio/m4a',
                });
            }
            formData.append('session_id', sessionId);
            formData.append('language_code', options.getLanguageCode?.() || '');

            // Step 2 — transcribe only
            const transcribeResponse = await apiClient.request('/api/v1/ai/transcribe-only', {
                method:     'POST',
                body:       formData,
                isFormData: true,
            });

            const transcribedText = transcribeResponse.transcription || '';
            setTranscript(transcribedText);

            // Step 3 — pass transcribed text to guided flow in ai-guidance
            if (options.onTranscribed && transcribedText) {
                options.onTranscribed(transcribedText);
                setState('idle');
            } else {
                setState('idle');
            }

        } catch (err: any) {
            console.error('Voice processing failed', err);
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
        startRecording,
        stopRecordingAndProcess,
        playAudioBase64,
        isRecording:  state === 'recording',
        isProcessing: state === 'processing',
        isPlaying:    state === 'playing',
        sessionId,
        resetSession,
    };
};

