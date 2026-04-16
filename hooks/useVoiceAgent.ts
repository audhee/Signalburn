import { Audio } from 'expo-av';
import { useState, useRef, useEffect } from 'react';
import { Platform } from 'react-native';

// Configuration for Backend
// Use the computer's actual local IP address for physical Android testing
const BACKEND_URL = 'http://192.168.68.131:8000/api/v1/ai/process';

export type VoiceState = 'idle' | 'recording' | 'processing' | 'playing' | 'error';

export const useVoiceAgent = () => {
    const [state, setState] = useState<VoiceState>('idle');
    const [error, setError] = useState<string | null>(null);
    
    const recordingRef = useRef<Audio.Recording | null>(null);
    const soundRef = useRef<Audio.Sound | null>(null);
    const isProcessingRef = useRef<boolean>(false);
    const sessionId = useRef<string>(`session-${Date.now()}`);

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

    const startRecording = async () => {
        try {
            if (state === 'playing' || isProcessingRef.current) return;

            // Stop any current sound
            if (soundRef.current) {
                await soundRef.current.stopAsync();
                await soundRef.current.unloadAsync();
                soundRef.current = null;
            }

            console.log('Starting recording...');
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
        // Guard: Prevent double-processing
        if (!recordingRef.current || isProcessingRef.current) return;
        
        isProcessingRef.current = true;
        setState('processing');

        try {
            console.log('Stopping recording...');
            const status = await recordingRef.current.getStatusAsync();
            
            // If the user tapped the record button too fast (under 500ms), cancel the operation.
            // This prevents the "no valid audio data" crash from Expo.
            if (status.canRecord && status.durationMillis < 500) {
                console.log('Recording too short, cancelling.');
                await recordingRef.current.stopAndUnloadAsync().catch(() => {});
                recordingRef.current = null;
                isProcessingRef.current = false;
                setState('idle');
                return;
            }

            if (status.canRecord) {
                await recordingRef.current.stopAndUnloadAsync();
            }
            
            const uri = recordingRef.current.getURI();
            recordingRef.current = null; // Clear immediately
            
            console.log('Recording saved at', uri);
            if (!uri) throw new Error('No recording URI found');

            // Use native browser FormData on Web, else RN's FormData
            const WebFormData = Platform.OS === 'web' ? (globalThis as any).FormData : FormData;
            const formData = new WebFormData();
            
            if (Platform.OS === 'web') {
                // On Web, URI is a blob URL. We must fetch it to get the actual Blob for FormData
                const blobResponse = await fetch(uri);
                const audioBlob = await blobResponse.blob();
                formData.append('audio', audioBlob, 'user_speech.m4a');
            } else {
                // React Native Native behavior
                // @ts-ignore
                formData.append('audio', {
                    uri: Platform.OS === 'ios' ? uri.replace('file://', '') : uri,
                    name: 'user_speech.m4a',
                    type: 'audio/m4a',
                });
            }
            
            formData.append('session_id', sessionId.current);

            console.log('Sending to backend:', BACKEND_URL);
            const response = await fetch(BACKEND_URL, {
                method: 'POST',
                body: formData,
                headers: {
                    'Accept': 'application/json',
                    // IMPORTANT: Do NOT set Content-Type here, fetch will set it with the correct boundary
                },
            });

            if (!response.ok) {
                const errText = await response.text();
                throw new Error(`Backend error: ${response.status} - ${errText}`);
            }

            // Convert Response Blob to Base64 for Native Playback
            const blob = await response.blob();
            const base64Audio = await new Promise<string>((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result as string);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });
            
            console.log('Playing AI response...');
            setState('playing');
            const { sound } = await Audio.Sound.createAsync(
                { uri: base64Audio },
                { shouldPlay: true }
            );
            soundRef.current = sound;

            sound.setOnPlaybackStatusUpdate((status) => {
                if (status.isLoaded && status.didJustFinish) {
                    setState('idle');
                    sound.unloadAsync().catch(() => {});
                }
            });

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
        startRecording,
        stopRecordingAndProcess,
        isRecording: state === 'recording',
        isProcessing: state === 'processing',
        isPlaying: state === 'playing',
    };
};
