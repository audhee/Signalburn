import { apiClient } from '@/services/apiClient';
import { Audio } from 'expo-av';
import { useEffect, useRef, useState } from 'react';
import { Platform } from 'react-native';

export type VoiceState = 'idle' | 'recording' | 'processing' | 'playing' | 'error';

interface UseVoiceAgentOptions {
    onTranscribed?: (text: string) => void;
    getLanguageCode?: () => string;
}

export const useVoiceAgent = (options: UseVoiceAgentOptions = {}) => {
    const [state, setState] = useState<VoiceState>('idle');
    const [error, setError] = useState<string | null>(null);
    const [transcript, setTranscript] = useState<string>('');
    const [aiResponse, setAiResponse] = useState<string>('');

    const recordingRef = useRef<Audio.Recording | null>(null);
    const soundRef = useRef<Audio.Sound | null>(null);
    const isProcessingRef = useRef<boolean>(false);
    const [sessionId, setSessionId] = useState<string>(`session-${Date.now()}`);

    const resetSession = () => setSessionId(`session-${Date.now()}`);

    const enableRecordingMode = async () => {
        await Audio.setAudioModeAsync({
            allowsRecordingIOS: true,
            playsInSilentModeIOS: true,
            staysActiveInBackground: false,
            shouldDuckAndroid: true,
        });
    };

    const disableRecordingMode = async () => {
        await Audio.setAudioModeAsync({
            allowsRecordingIOS: false,
            playsInSilentModeIOS: true,
            staysActiveInBackground: false,
            shouldDuckAndroid: true,
        });
    };

    useEffect(() => {
        async function getPermissions() {
            try {
                const { status } = await Audio.requestPermissionsAsync();
                if (status !== 'granted') {
                    setError('Microphone permission denied');
                }
                await enableRecordingMode();
            } catch (err) {
                console.error('Failed to get audio permissions', err);
            }
        }

        getPermissions();

        return () => {
            if (recordingRef.current) {
                recordingRef.current.stopAndUnloadAsync().catch(() => {});
            }
            if (soundRef.current) {
                soundRef.current.unloadAsync().catch(() => {});
            }
        };
    }, []);

    const playAudioBase64 = async (audioBase64: string) => {
        setState('playing');
        try {
            await disableRecordingMode();
            const { sound } = await Audio.Sound.createAsync(
                { uri: `data:audio/wav;base64,${audioBase64}` },
                { shouldPlay: true }
            );
            soundRef.current = sound;
            sound.setOnPlaybackStatusUpdate((status) => {
                if (status.isLoaded && status.didJustFinish) {
                    setState('idle');
                    sound.unloadAsync().catch(() => {});
                    soundRef.current = null;
                    enableRecordingMode().catch((modeErr) => {
                        console.error('Failed to re-enable recording mode after playback', modeErr);
                    });
                }
            });
        } catch (audioErr) {
            console.error('Audio playback failed:', audioErr);
            setState('idle');
            await enableRecordingMode().catch(() => {});
        }
    };

    const startRecording = async () => {
        try {
            if (isProcessingRef.current) return;

            if (recordingRef.current) {
                await recordingRef.current.stopAndUnloadAsync().catch(() => {});
                recordingRef.current = null;
            }

            if (soundRef.current) {
                await soundRef.current.stopAsync().catch(() => {});
                await soundRef.current.unloadAsync().catch(() => {});
                soundRef.current = null;
            }

            await enableRecordingMode();
            setTranscript('');
            setAiResponse('');
            setError(null);

            const { recording } = await Audio.Recording.createAsync(
                Audio.RecordingOptionsPresets.HIGH_QUALITY
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

            const WebFormData = Platform.OS === 'web' ? (globalThis as any).FormData : FormData;
            const formData = new WebFormData();

            if (Platform.OS === 'web') {
                const blobResponse = await fetch(uri);
                const audioBlob = await blobResponse.blob();
                formData.append('audio', audioBlob, 'user_speech.m4a');
            } else {
                // @ts-ignore React Native FormData file object shape.
                formData.append('audio', {
                    uri: Platform.OS === 'ios' ? uri.replace('file://', '') : uri,
                    name: 'user_speech.m4a',
                    type: 'audio/m4a',
                });
            }

            formData.append('session_id', sessionId);
            formData.append('language_code', options.getLanguageCode?.() || '');

            const transcribeResponse = await apiClient.request('/api/v1/ai/transcribe-only', {
                method: 'POST',
                body: formData,
                isFormData: true,
            });

            if (transcribeResponse.success === false) {
                throw new Error(transcribeResponse.error || 'Could not transcribe audio. Please try again.');
            }

            const transcribedText = transcribeResponse.transcription || '';
            setTranscript(transcribedText);

            if (!transcribedText.trim()) {
                setError('No speech detected. Please try again.');
                setState('error');
                return;
            }

            if (options.onTranscribed && transcribedText) {
                options.onTranscribed(transcribedText);
            }

            setState('idle');
        } catch (err: any) {
            console.error('Voice processing failed', err);
            setError(err.message || 'Something went wrong');
            setState('error');
        } finally {
            recordingRef.current = null;
            isProcessingRef.current = false;
            await enableRecordingMode().catch((modeErr) => {
                console.error('Failed to restore recording mode after processing', modeErr);
            });
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
        isRecording: state === 'recording',
        isProcessing: state === 'processing',
        isPlaying: state === 'playing',
        sessionId,
        resetSession,
    };
};
