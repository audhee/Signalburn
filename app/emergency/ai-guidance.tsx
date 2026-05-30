import { useVoiceAgent } from '@/hooks/useVoiceAgent';
import { apiClient } from '@/services/apiClient';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';
import * as ImagePicker from 'expo-image-picker';
import { useRouter } from 'expo-router';
import { useCallback, useEffect, useRef, useState } from 'react';
import {
    ActivityIndicator,
    Alert,
    Image,
    Modal,
    Pressable,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    View,
} from 'react-native';
import Animated, {
    Easing,
    cancelAnimation,
    interpolate,
    useAnimatedStyle,
    useSharedValue,
    withRepeat,
    withSequence,
    withTiming,
} from 'react-native-reanimated';

const DOCTOR_IMG = require('../../assets/images/doctor.png');

type AvatarState = 'idle' | 'listening' | 'thinking' | 'speaking';

// ── SEVERITY COLORS ──────────────────────────────────────────────────
const SEVERITY_COLORS: Record<string, string> = {
    emergency: '#FF1744',
    moderate: '#FF9800',
    minor: '#4CAF50',
    unknown: '#8FA0BD',
};

const SEVERITY_LABELS: Record<string, string> = {
    emergency: 'EMERGENCY — Call 112',
    moderate: 'MODERATE — See a doctor',
    minor: 'MINOR — Home care',
    unknown: 'Analyzing...',
};

export default function AIGuidanceScreen() {
    const router = useRouter();
    const scrollRef = useRef<ScrollView>(null);

    // ── AVATAR STATE ───────────────────────────────────────────────────
    const [avatarState, setAvatarState] = useState<AvatarState>('idle');

    const avatarScale = useSharedValue(1);
    const glowOpacity = useSharedValue(0.3);
    const ringRotate = useSharedValue(0);
    const wave1 = useSharedValue(0);
    const wave2 = useSharedValue(0);
    const wave3 = useSharedValue(0);
    const wave4 = useSharedValue(0);
    const wave5 = useSharedValue(0);

    const stopAvatarAnimations = useCallback(() => {
        cancelAnimation(avatarScale);
        cancelAnimation(glowOpacity);
        cancelAnimation(ringRotate);
        cancelAnimation(wave1);
        cancelAnimation(wave2);
        cancelAnimation(wave3);
        cancelAnimation(wave4);
        cancelAnimation(wave5);
        avatarScale.value = withTiming(1, { duration: 300 });
        glowOpacity.value = withTiming(0.3, { duration: 300 });
        wave1.value = withTiming(0, { duration: 200 });
        wave2.value = withTiming(0, { duration: 200 });
        wave3.value = withTiming(0, { duration: 200 });
        wave4.value = withTiming(0, { duration: 200 });
        wave5.value = withTiming(0, { duration: 200 });
    }, [avatarScale, glowOpacity, ringRotate, wave1, wave2, wave3, wave4, wave5]);

    useEffect(() => {
        stopAvatarAnimations();
        if (avatarState === 'listening') {
            glowOpacity.value = withRepeat(withSequence(
                withTiming(0.95, { duration: 900, easing: Easing.inOut(Easing.ease) }),
                withTiming(0.4, { duration: 900, easing: Easing.inOut(Easing.ease) })
            ), -1, false);
            avatarScale.value = withRepeat(withSequence(
                withTiming(1.04, { duration: 900 }),
                withTiming(1, { duration: 900 })
            ), -1, false);
            ringRotate.value = withRepeat(
                withTiming(360, { duration: 8000, easing: Easing.linear }), -1, false
            );
        } else if (avatarState === 'thinking') {
            glowOpacity.value = withRepeat(withSequence(
                withTiming(0.7, { duration: 700 }),
                withTiming(0.3, { duration: 700 })
            ), -1, false);
        } else if (avatarState === 'speaking') {
            glowOpacity.value = withRepeat(withSequence(
                withTiming(0.85, { duration: 600 }),
                withTiming(0.45, { duration: 600 })
            ), -1, false);
            const startWave = (sv: typeof wave1, delay: number) => {
                sv.value = withRepeat(withSequence(
                    withTiming(1, { duration: 350 + delay, easing: Easing.inOut(Easing.ease) }),
                    withTiming(0, { duration: 350 + delay, easing: Easing.inOut(Easing.ease) })
                ), -1, false);
            };
            startWave(wave1, 0);
            startWave(wave2, 80);
            startWave(wave3, 160);
            startWave(wave4, 100);
            startWave(wave5, 60);
        } else {
            glowOpacity.value = withRepeat(withSequence(
                withTiming(0.55, { duration: 1800 }),
                withTiming(0.3, { duration: 1800 })
            ), -1, false);
        }
    }, [avatarState]);

    const avatarAnimStyle = useAnimatedStyle(() => ({ transform: [{ scale: avatarScale.value }] }));
    const glowAnimStyle = useAnimatedStyle(() => ({ opacity: glowOpacity.value }));
    const ringStyle = useAnimatedStyle(() => ({ transform: [{ rotate: `${ringRotate.value}deg` }] }));
    const bar1Style = useAnimatedStyle(() => ({ height: interpolate(wave1.value, [0, 1], [8, 30]) }));
    const bar2Style = useAnimatedStyle(() => ({ height: interpolate(wave2.value, [0, 1], [14, 36]) }));
    const bar3Style = useAnimatedStyle(() => ({ height: interpolate(wave3.value, [0, 1], [22, 44]) }));
    const bar4Style = useAnimatedStyle(() => ({ height: interpolate(wave4.value, [0, 1], [16, 38]) }));
    const bar5Style = useAnimatedStyle(() => ({ height: interpolate(wave5.value, [0, 1], [10, 32]) }));

    const glowColor = avatarState === 'listening' ? '#3FE0C5' : '#5B8CFF';

    // ── APP STATE ──────────────────────────────────────────────────────
    const [typedText, setTypedText] = useState('');
    const [isTextProcessing, setIsTextProcessing] = useState(false);
    const [textError, setTextError] = useState<string | null>(null);
    const [initialQuery, setInitialQuery] = useState('');
    const [collectedAnswers, setCollectedAnswers] = useState<string[]>([]);
    const [currentQuestion, setCurrentQuestion] = useState<string>('');
    const [questionNum, setQuestionNum] = useState(0);
    const [totalQuestions, setTotalQuestions] = useState(5);
    const [finalResponse, setFinalResponse] = useState('');
    const [mode, setMode] = useState<'idle' | 'questioning' | 'answered'>('idle');

    // ── MEDIA UPLOAD STATE ───────────────────────────────────────────
    const [isUploading, setIsUploading] = useState(false);
    const [uploadedMediaUri, setUploadedMediaUri] = useState<string | null>(null);
    const [uploadedMediaType, setUploadedMediaType] = useState<string>('image');
    const [severityBadge, setSeverityBadge] = useState<string>('unknown');
    const [showMediaPicker, setShowMediaPicker] = useState(false);

    // ── LANGUAGE LOCK ────────────────────────────────────────────────
    const [lockedLanguage, setLockedLanguage] = useState<string>('');

    const handleVoiceAnswerRef = useRef<((text: string) => void) | null>(null);

    const {
        error,
        transcript,
        startRecording,
        stopRecordingAndProcess,
        isRecording,
        isProcessing,
    } = useVoiceAgent({
        onTranscribed: (voiceText: string) => {
            if (handleVoiceAnswerRef.current) {
                handleVoiceAnswerRef.current(voiceText);
            }
        },
        getLanguageCode: () => lockedLanguage
    });

    const busy = isProcessing || isTextProcessing || isUploading;

    // ── PLAY AUDIO ─────────────────────────────────────────────────────
    const playAudio = async (base64: string) => {
        setAvatarState('speaking');
        try {
            await Audio.setAudioModeAsync({
                allowsRecordingIOS: false,
                playsInSilentModeIOS: true,
                shouldDuckAndroid: true,
            });
            const { sound } = await Audio.Sound.createAsync(
                { uri: `data:audio/wav;base64,${base64}` },
                { shouldPlay: true }
            );
            sound.setOnPlaybackStatusUpdate((status) => {
                if (status.isLoaded && status.didJustFinish) {
                    sound.unloadAsync().catch(() => { });
                    setAvatarState('idle');
                }
            });
        } catch (e) {
            console.error('Audio playback failed:', e);
            setAvatarState('idle');
        }
    };

    // ── PLAY AUDIO FROM BYTES (for multipart response) ───────────────
    const playAudioFromBlob = async (blob: Blob) => {
        setAvatarState('speaking');
        try {
            const reader = new FileReader();
            const base64Promise = new Promise<string>((resolve) => {
                reader.onloadend = () => {
                    const base64 = (reader.result as string).split(',')[1];
                    resolve(base64);
                };
            });
            reader.readAsDataURL(blob);
            const base64 = await base64Promise;

            await Audio.setAudioModeAsync({
                allowsRecordingIOS: false,
                playsInSilentModeIOS: true,
                shouldDuckAndroid: true,
            });
            const { sound } = await Audio.Sound.createAsync(
                { uri: `data:audio/wav;base64,${base64}` },
                { shouldPlay: true }
            );
            sound.setOnPlaybackStatusUpdate((status) => {
                if (status.isLoaded && status.didJustFinish) {
                    sound.unloadAsync().catch(() => { });
                    setAvatarState('idle');
                }
            });
        } catch (e) {
            console.error('Audio blob playback failed:', e);
            setAvatarState('idle');
        }
    };

    // ── CALL BACKEND ───────────────────────────────────────────────────
    const callGuidedQuery = async (query: string, answers: string[], lang: string) => {
        const response = await apiClient.request('/api/v1/ai/guided-query', {
            method: 'POST',
            body: {
                text: query,
                context: answers.join('\n'),
                language: lang,
            },
        });
        return response;
    };

    // ── SHARED ANSWER PROCESSOR ────────────────────────────────────────
    const processAnswer = async (
        answerText: string,
        currentMode: string,
        currentInitialQuery: string,
        currentAnswers: string[],
        currentQText: string
    ) => {
        setIsTextProcessing(true);
        setTextError(null);
        setAvatarState('thinking');

        let newAnswers: string[];
        let queryText: string;
        let langToUse: string;

        if (currentMode === 'idle') {
            setInitialQuery(answerText);
            setCollectedAnswers([]);
            setFinalResponse('');
            setMode('questioning');
            newAnswers = [];
            queryText = answerText;
            langToUse = '';
        } else {
            newAnswers = [...currentAnswers, `Q: ${currentQText}\nA: ${answerText}`];
            setCollectedAnswers(newAnswers);
            queryText = currentInitialQuery;
            langToUse = lockedLanguage;
        }

        try {
            const res = await callGuidedQuery(queryText, newAnswers, langToUse);

            if (res.detected_language && !lockedLanguage) {
                setLockedLanguage(res.detected_language);
            }

            if (res.mode === 'question') {
                setCurrentQuestion(res.question);
                setQuestionNum(res.question_num);
                setTotalQuestions(res.total_questions);
                setAvatarState('idle');
            } else if (res.mode === 'answer') {
                setFinalResponse(res.response || '');
                setMode('answered');
                if (res.audio_base64) {
                    await playAudio(res.audio_base64);
                } else {
                    setAvatarState('idle');
                }
            }
        } catch (err: any) {
            setTextError(err.message || 'Failed to get response');
            if (currentMode === 'idle') setMode('idle');
            setAvatarState('idle');
        } finally {
            setIsTextProcessing(false);
            scrollRef.current?.scrollToEnd({ animated: true });
        }
    };

    // ── TEXT SEND ──────────────────────────────────────────────────────
    const handleSend = async () => {
        const cleanText = typedText.trim();
        if (!cleanText || busy) return;
        setTypedText('');
        await processAnswer(cleanText, mode, initialQuery, collectedAnswers, currentQuestion);
    };

    // ── VOICE ANSWER ───────────────────────────────────────────────────
    handleVoiceAnswerRef.current = (voiceText: string) => {
        if (!voiceText.trim() || isTextProcessing) return;
        processAnswer(voiceText, mode, initialQuery, collectedAnswers, currentQuestion);
    };

    // ── RESET ──────────────────────────────────────────────────────────
    const handleReset = () => {
        setMode('idle');
        setInitialQuery('');
        setCollectedAnswers([]);
        setCurrentQuestion('');
        setFinalResponse('');
        setTextError(null);
        setTypedText('');
        setQuestionNum(0);
        setAvatarState('idle');
        setLockedLanguage('');
        setUploadedMediaUri(null);
        setUploadedMediaType('image');
        setSeverityBadge('unknown');
    };

    // ── MIC PRESS ─────────────────────────────────────────────────────
    const handleMicPressIn = () => {
        setAvatarState('listening');
        startRecording();
    };

    const handleMicPressOut = () => {
        setAvatarState('thinking');
        stopRecordingAndProcess();
    };

    // ═══════════════════════════════════════════════════════════════════
    // ═══ MEDIA UPLOAD FUNCTIONS ═══════════════════════════════════════
    // ═══════════════════════════════════════════════════════════════════

    // ── REQUEST PERMISSIONS ────────────────────────────────────────────
    const requestCameraPermission = async () => {
        const { status } = await ImagePicker.requestCameraPermissionsAsync();
        if (status !== 'granted') {
            Alert.alert('Permission Denied', 'Camera access is needed to capture photos of injuries.');
            return false;
        }
        return true;
    };

    const requestGalleryPermission = async () => {
        const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
        if (status !== 'granted') {
            Alert.alert('Permission Denied', 'Gallery access is needed to upload photos/videos.');
            return false;
        }
        return true;
    };

    // ── CAPTURE FROM CAMERA ────────────────────────────────────────────
    const handleCameraCapture = async () => {
        setShowMediaPicker(false);
        const hasPermission = await requestCameraPermission();
        if (!hasPermission) return;

        try {
            const result = await ImagePicker.launchCameraAsync({
                mediaTypes: ImagePicker.MediaTypeOptions.All,
                allowsEditing: true,
                quality: 0.85,
                aspect: [4, 3],
            });

            if (!result.canceled && result.assets && result.assets.length > 0) {
                const asset = result.assets[0];
                await uploadMedia(asset.uri, asset.type || 'image/jpeg', asset.fileName || 'camera_capture.jpg');
            }
        } catch (e) {
            console.error('Camera error:', e);
            Alert.alert('Camera Error', 'Failed to capture photo/video.');
        }
    };

    // ── PICK FROM GALLERY ──────────────────────────────────────────────
    const handleGalleryPick = async () => {
        setShowMediaPicker(false);
        const hasPermission = await requestGalleryPermission();
        if (!hasPermission) return;

        try {
            const result = await ImagePicker.launchImageLibraryAsync({
                mediaTypes: ImagePicker.MediaTypeOptions.All,
                allowsEditing: true,
                quality: 0.85,
                aspect: [4, 3],
            });

            if (!result.canceled && result.assets && result.assets.length > 0) {
                const asset = result.assets[0];
                await uploadMedia(asset.uri, asset.type || 'image/jpeg', asset.fileName || 'gallery_pick.jpg');
            }
        } catch (e) {
            console.error('Gallery error:', e);
            Alert.alert('Gallery Error', 'Failed to pick photo/video.');
        }
    };

    // ── UPLOAD MEDIA TO BACKEND ────────────────────────────────────────
    const uploadMedia = async (uri: string, mimeType: string, fileName: string) => {
        setIsUploading(true);
        setTextError(null);
        setAvatarState('thinking');
        setUploadedMediaUri(uri);
        setUploadedMediaType(
            mimeType.startsWith('video') ? 'video' :
                (mimeType === 'application/pdf' ? 'document' : 'image')
        );

        try {
            // Build FormData — handle web vs native differently
            const formData = new FormData();

            const isWeb = typeof window !== 'undefined' && !!(window as any).document;
            if (isWeb) {
                // On web: fetch the URI as a blob and append it
                const response = await fetch(uri);
                const blob = await response.blob();
                const file = new File([blob], fileName, { type: mimeType });
                formData.append('media', file);
            } else {
                // On React Native: use the { uri, type, name } convention
                formData.append('media', {
                    uri: uri,
                    type: mimeType,
                    name: fileName,
                } as any);
            }

            formData.append('text', typedText.trim());
            formData.append('session_id', `session_${Date.now()}`);

            // Use regular request with FormData — backend now returns JSON
            const res = await apiClient.request<{
                success: boolean;
                response: string;
                severity: string;
                language_code: string;
                session_id: string;
                audio_base64: string | null;
                media_filename: string;
                media_type: string;
            }>('/api/v1/ai/multimodal-upload', {
                method: 'POST',
                body: formData,
                isFormData: true,
            });

            // Update UI with response
            const answerText = res.response || '';
            const severity = res.severity || 'unknown';
            const languageCode = res.language_code || 'en-IN';

            setFinalResponse(answerText);
            setSeverityBadge(severity);
            setMode('answered');
            setInitialQuery(typedText.trim() || `Uploaded: ${fileName}`);

            if (!lockedLanguage && languageCode) {
                setLockedLanguage(languageCode);
            }

            if (typedText.trim()) {
                setTypedText('');
            }

            // Play audio if available
            if (res.audio_base64) {
                await playAudio(res.audio_base64);
            } else {
                setAvatarState('idle');
            }

            console.log(`[Upload] Success — Severity: ${severity}, Lang: ${languageCode}`);

        } catch (err: any) {
            console.error('Media upload error:', err);
            setTextError(typeof err?.message === 'string' ? err.message : 'Failed to analyze the uploaded media.');
            setAvatarState('idle');
        } finally {
            setIsUploading(false);
            scrollRef.current?.scrollToEnd({ animated: true });
        }
    };

    // ── REMOVE UPLOADED MEDIA PREVIEW ──────────────────────────────────
    const handleRemoveMedia = () => {
        setUploadedMediaUri(null);
        setUploadedMediaType('image');
    };

    // ── STATUS ─────────────────────────────────────────────────────────
    const getStatusText = () => {
        if (isRecording) return 'Listening... speak now';
        if (isUploading) return 'Analyzing your photo/video...';
        if (busy) return 'Thinking...';
        if (mode === 'questioning') return `Question ${questionNum} of ${totalQuestions}`;
        if (mode === 'answered') return 'Done! Ask another question.';
        return 'Describe your health problem or upload a photo';
    };

    const displayError = error || textError;

    // ── RENDER ─────────────────────────────────────────────────────────
    return (
        <View style={styles.container}>

            {/* Header */}
            <View style={styles.header}>
                <Pressable onPress={() => router.back()} style={styles.backBtn}>
                    <Ionicons name="arrow-back" size={24} color="#fff" />
                </Pressable>
                <Text style={styles.headerTitle}>EMERGENCY ASSISTANT</Text>
                {mode !== 'idle'
                    ? <Pressable onPress={handleReset} style={styles.resetBtn}>
                        <Ionicons name="refresh" size={20} color="#3FE0C5" />
                    </Pressable>
                    : <View style={styles.headerSpacer} />
                }
            </View>

            {/* ── AVATAR SECTION ── */}
            <View style={styles.avatarSection}>
                <View style={styles.bgGlowTop} />
                <View style={styles.bgGlowBottom} />

                <Animated.View style={[
                    styles.glow,
                    { shadowColor: glowColor, backgroundColor: glowColor + '22' },
                    glowAnimStyle,
                ]} />

                {avatarState === 'listening' && (
                    <Animated.View style={[styles.tickRingContainer, ringStyle]} pointerEvents="none">
                        {Array.from({ length: 60 }).map((_, i) => (
                            <View key={i} style={[
                                styles.tick,
                                {
                                    transform: [{ rotate: `${i * 6}deg` }, { translateY: -110 }],
                                    opacity: i % 2 === 0 ? 0.9 : 0.3,
                                    backgroundColor: i % 6 === 0 ? '#FFD96A' : '#3FE0C5',
                                },
                            ]} />
                        ))}
                    </Animated.View>
                )}

                <Animated.View style={[styles.avatarOuter, avatarAnimStyle]}>
                    <View style={[styles.avatarBorder, { borderColor: glowColor + 'AA' }]}>
                        <Image source={DOCTOR_IMG} style={styles.avatar} />
                    </View>
                </Animated.View>

                {avatarState === 'speaking' && (
                    <View style={styles.waveRow}>
                        <Animated.View style={[styles.waveBar, bar1Style]} />
                        <Animated.View style={[styles.waveBar, bar2Style]} />
                        <Animated.View style={[styles.waveBar, bar3Style]} />
                        <Animated.View style={[styles.waveBar, bar4Style]} />
                        <Animated.View style={[styles.waveBar, bar5Style]} />
                    </View>
                )}

                <Text style={styles.avatarStatus}>
                    {avatarState === 'idle' ? "I'm here to help" :
                        avatarState === 'listening' ? "I'm listening..." :
                            avatarState === 'thinking' ? isUploading ? 'Analyzing your photo...' : 'Analyzing situation...' :
                                'AI is speaking...'}
                </Text>
            </View>

            {/* ── CHAT SECTION ── */}
            <ScrollView
                ref={scrollRef}
                style={styles.scrollView}
                contentContainerStyle={styles.scrollContent}
                showsVerticalScrollIndicator={false}
            >
                <View style={styles.statusSection}>
                    <Text style={styles.statusText}>{getStatusText()}</Text>
                </View>

                {/* ── SEVERITY BADGE (shown after media analysis) ── */}
                {severityBadge !== 'unknown' && mode === 'answered' && (
                    <View style={[
                        styles.severityBadge,
                        { backgroundColor: SEVERITY_COLORS[severityBadge] + '22', borderColor: SEVERITY_COLORS[severityBadge] }
                    ]}>
                        <View style={[styles.severityDot, { backgroundColor: SEVERITY_COLORS[severityBadge] }]} />
                        <Text style={[styles.severityText, { color: SEVERITY_COLORS[severityBadge] }]}>
                            {SEVERITY_LABELS[severityBadge]}
                        </Text>
                    </View>
                )}

                {/* ── UPLOADED MEDIA PREVIEW ── */}
                {uploadedMediaUri && (
                    <View style={styles.mediaPreviewContainer}>
                        <View style={styles.mediaPreviewHeader}>
                            <Ionicons
                                name={uploadedMediaType === 'video' ? 'videocam' : (uploadedMediaType === 'document' ? 'document' : 'image')}
                                size={16}
                                color="#5B8CFF"
                            />
                            <Text style={styles.mediaPreviewLabel}>
                                {uploadedMediaType === 'video' ? 'Video uploaded' : (uploadedMediaType === 'document' ? 'Document uploaded' : 'Photo uploaded')}
                            </Text>
                            <Pressable onPress={handleRemoveMedia} style={styles.removeMediaBtn}>
                                <Ionicons name="close-circle" size={20} color="#FF5252" />
                            </Pressable>
                        </View>
                        {uploadedMediaType !== 'document' && (
                            <Image source={{ uri: uploadedMediaUri }} style={styles.mediaPreviewImage} resizeMode="cover" />
                        )}
                    </View>
                )}

                {mode === 'questioning' && (
                    <View style={styles.progressContainer}>
                        <View style={styles.progressBar}>
                            <View style={[
                                styles.progressFill,
                                { width: `${((questionNum - 1) / totalQuestions) * 100}%` }
                            ]} />
                        </View>
                        <Text style={styles.progressText}>{questionNum - 1}/{totalQuestions} answered</Text>
                    </View>
                )}

                {initialQuery.length > 0 && (
                    <View style={styles.transcriptBox}>
                        <View style={styles.labelRow}>
                            <Ionicons name="person-circle" size={18} color="#3FE0C5" />
                            <Text style={styles.labelText}>Your complaint</Text>
                        </View>
                        <Text style={styles.transcriptText}>{initialQuery}</Text>
                    </View>
                )}

                {mode === 'questioning' && currentQuestion.length > 0 && (
                    <View style={styles.questionBox}>
                        <View style={styles.labelRow}>
                            <Ionicons name="help-circle" size={18} color="#5B8CFF" />
                            <Text style={[styles.labelText, { color: '#5B8CFF' }]}>Doctor asks</Text>
                        </View>
                        <Text style={styles.questionText}>{currentQuestion}</Text>
                    </View>
                )}

                {collectedAnswers.map((qa, i) => (
                    <View key={i} style={styles.answeredBox}>
                        <Text style={styles.answeredText}>{qa}</Text>
                    </View>
                ))}

                {mode === 'answered' && finalResponse.length > 0 && (
                    <View style={styles.responseBox}>
                        <View style={styles.labelRow}>
                            <Ionicons name="medical" size={18} color="#3FE0C5" />
                            <Text style={styles.labelText}>Doctor says</Text>
                        </View>
                        <Text style={styles.responseText}>{finalResponse}</Text>
                    </View>
                )}

                {transcript.length > 0 && (
                    <View style={styles.transcriptBox}>
                        <View style={styles.labelRow}>
                            <Ionicons name="mic" size={18} color="#3FE0C5" />
                            <Text style={styles.labelText}>You said</Text>
                        </View>
                        <Text style={styles.transcriptText}>{transcript}</Text>
                    </View>
                )}

                {displayError && (
                    <View style={styles.errorBox}>
                        <Ionicons name="alert-circle" size={20} color="#FF5252" />
                        <Text style={styles.errorText}>{displayError}</Text>
                    </View>
                )}

                {mode === 'answered' && (
                    <Pressable style={styles.newQueryBtn} onPress={handleReset}>
                        <Ionicons name="add-circle-outline" size={20} color="#fff" />
                        <Text style={styles.newQueryText}>Ask Another Question</Text>
                    </Pressable>
                )}

                <View style={styles.scrollSpacer} />
            </ScrollView>

            {/* ── BOTTOM INPUT + MIC + CAMERA ── */}
            <View style={styles.bottomSection}>

                {/* Media Upload Preview Row */}
                {uploadedMediaUri && (
                    <View style={styles.mediaUploadRow}>
                        <Text style={styles.mediaUploadText}>Ready to analyze</Text>
                    </View>
                )}

                <View style={styles.textInputSection}>
                    <TextInput
                        style={styles.textInput}
                        placeholder={
                            mode === 'idle' ? 'Describe your health problem...' :
                                mode === 'questioning' ? 'Type your answer...' :
                                    'Ask another question...'
                        }
                        placeholderTextColor="#555"
                        value={typedText}
                        onChangeText={setTypedText}
                        multiline
                        numberOfLines={2}
                        editable={!busy}
                    />
                    <Pressable
                        style={[styles.sendButton, (!typedText.trim() || busy) && styles.sendButtonDisabled]}
                        onPress={handleSend}
                        disabled={!typedText.trim() || busy}
                    >
                        {isTextProcessing
                            ? <ActivityIndicator size="small" color="#fff" />
                            : <Ionicons name="send" size={20} color="#fff" />
                        }
                    </Pressable>
                </View>

                {/* ── ACTION BUTTONS ROW: MIC + CAMERA ── */}
                <View style={styles.actionButtonsRow}>
                    {/* Camera / Gallery Button */}
                    <Pressable
                        onPress={() => setShowMediaPicker(true)}
                        style={({ pressed }) => [
                            styles.cameraButton,
                            {
                                transform: [{ scale: pressed ? 0.95 : 1 }],
                                opacity: busy ? 0.5 : 1,
                            },
                        ]}
                        disabled={busy}
                    >
                        {isUploading
                            ? <ActivityIndicator size="small" color="#fff" />
                            : <Ionicons name="camera" size={24} color="#fff" />
                        }
                    </Pressable>

                    <View style={styles.actionSpacer} />

                    {/* Mic Button */}
                    <Pressable
                        onPressIn={handleMicPressIn}
                        onPressOut={handleMicPressOut}
                        style={({ pressed }) => [
                            styles.micButton,
                            {
                                backgroundColor: isRecording ? '#FF5252' : '#1A6BE3',
                                transform: [{ scale: pressed || isRecording ? 0.95 : 1 }],
                                opacity: busy ? 0.5 : 1,
                            },
                        ]}
                        disabled={busy}
                    >
                        {isProcessing || isUploading
                            ? <ActivityIndicator size="large" color="#fff" />
                            : <Ionicons name={isRecording ? 'mic' : 'mic-outline'} size={32} color="#fff" />
                        }
                    </Pressable>

                    <View style={styles.actionSpacer} />

                    {/* Gallery Button (separate quick access) */}
                    <Pressable
                        onPress={handleGalleryPick}
                        style={({ pressed }) => [
                            styles.galleryButton,
                            {
                                transform: [{ scale: pressed ? 0.95 : 1 }],
                                opacity: busy ? 0.5 : 1,
                            },
                        ]}
                        disabled={busy}
                    >
                        <Ionicons name="images" size={22} color="#5B8CFF" />
                    </Pressable>
                </View>

                <Text style={styles.micHint}>
                    {isRecording ? 'Release to send' :
                        isUploading ? 'Analyzing...' :
                            busy ? 'Please wait...' :
                                'Hold mic to speak • Tap camera to upload'}
                </Text>
            </View>

            {/* ── MEDIA PICKER MODAL ── */}
            <Modal
                visible={showMediaPicker}
                transparent
                animationType="slide"
                onRequestClose={() => setShowMediaPicker(false)}
            >
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <Text style={styles.modalTitle}>Upload Photo / Video</Text>
                        <Text style={styles.modalSubtitle}>Capture or select a photo/video of the injury</Text>

                        <Pressable style={styles.modalButton} onPress={handleCameraCapture}>
                            <Ionicons name="camera" size={28} color="#fff" />
                            <Text style={styles.modalButtonText}>Take Photo / Video</Text>
                        </Pressable>

                        <Pressable style={[styles.modalButton, styles.modalButtonSecondary]} onPress={handleGalleryPick}>
                            <Ionicons name="images" size={28} color="#5B8CFF" />
                            <Text style={[styles.modalButtonText, styles.modalButtonTextSecondary]}>Choose from Gallery</Text>
                        </Pressable>

                        <Pressable style={styles.modalCancel} onPress={() => setShowMediaPicker(false)}>
                            <Text style={styles.modalCancelText}>Cancel</Text>
                        </Pressable>
                    </View>
                </View>
            </Modal>

        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: '#06091A' },
    header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingTop: 50, paddingBottom: 12, backgroundColor: '#06091A' },
    backBtn: { padding: 8 },
    resetBtn: { padding: 8 },
    headerTitle: { fontSize: 13, fontWeight: '600', color: '#D8DEEA', letterSpacing: 3 },
    headerSpacer: { width: 40 },

    // Avatar
    avatarSection: { height: 260, alignItems: 'center', justifyContent: 'center', position: 'relative' },
    bgGlowTop: { position: 'absolute', top: -60, left: -40, width: 200, height: 200, borderRadius: 100, backgroundColor: '#0E2A4A', opacity: 0.55 },
    bgGlowBottom: { position: 'absolute', bottom: -80, right: -40, width: 220, height: 220, borderRadius: 110, backgroundColor: '#0A3D3A', opacity: 0.4 },
    glow: { position: 'absolute', width: 200, height: 200, borderRadius: 100, shadowOffset: { width: 0, height: 0 }, shadowOpacity: 1, shadowRadius: 40, elevation: 30 },
    tickRingContainer: { position: 'absolute', width: 240, height: 240, alignItems: 'center', justifyContent: 'center' },
    tick: { position: 'absolute', width: 2, height: 10, borderRadius: 1 },
    avatarOuter: { width: 170, height: 170, alignItems: 'center', justifyContent: 'center' },
    avatarBorder: { width: 160, height: 160, borderRadius: 80, borderWidth: 3, overflow: 'hidden', backgroundColor: '#0c1320' },
    avatar: { width: '100%', height: '100%', resizeMode: 'cover' },
    waveRow: { flexDirection: 'row', alignItems: 'center', height: 36, gap: 5, marginTop: 8 },
    waveBar: { width: 4, backgroundColor: '#5B8CFF', borderRadius: 2 },
    avatarStatus: { color: '#3FE0C5', fontSize: 13, fontWeight: '600', marginTop: 8, letterSpacing: 1 },

    // Scroll
    scrollView: { flex: 1 },
    scrollContent: { padding: 16, paddingBottom: 24 },
    statusSection: { alignItems: 'center', marginBottom: 12 },
    statusText: { fontSize: 13, fontWeight: '600', color: '#8FA0BD' },

    // Severity Badge
    severityBadge: { flexDirection: 'row', alignItems: 'center', alignSelf: 'center', paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, borderWidth: 1, marginBottom: 12 },
    severityDot: { width: 8, height: 8, borderRadius: 4, marginRight: 8 },
    severityText: { fontSize: 13, fontWeight: '700', letterSpacing: 0.5 },

    // Media Preview
    mediaPreviewContainer: { backgroundColor: '#0D1B3E', borderRadius: 12, marginBottom: 12, overflow: 'hidden', borderWidth: 1, borderColor: 'rgba(91,140,255,0.3)' },
    mediaPreviewHeader: { flexDirection: 'row', alignItems: 'center', padding: 10, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.05)' },
    mediaPreviewLabel: { fontSize: 12, color: '#8FA0BD', marginLeft: 6, flex: 1 },
    removeMediaBtn: { padding: 4 },
    mediaPreviewImage: { width: '100%', height: 180, borderBottomLeftRadius: 12, borderBottomRightRadius: 12 },

    // Progress
    progressContainer: { marginBottom: 12 },
    progressBar: { height: 4, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 2, overflow: 'hidden' },
    progressFill: { height: 4, backgroundColor: '#5B8CFF', borderRadius: 2 },
    progressText: { fontSize: 11, color: '#8FA0BD', marginTop: 4, textAlign: 'right' },

    // Chat bubbles
    questionBox: { backgroundColor: '#0D1B3E', borderRadius: 12, padding: 14, marginBottom: 12, borderLeftWidth: 4, borderLeftColor: '#5B8CFF' },
    questionText: { fontSize: 15, color: '#A8C0FF', lineHeight: 22, fontWeight: '600' },
    answeredBox: { backgroundColor: '#0A1020', borderRadius: 8, padding: 10, marginBottom: 8, borderLeftWidth: 3, borderLeftColor: '#2A3A4A' },
    answeredText: { fontSize: 13, color: '#8FA0BD', lineHeight: 20 },
    transcriptBox: { backgroundColor: '#0A1A2A', borderRadius: 12, padding: 14, marginBottom: 12, borderLeftWidth: 4, borderLeftColor: '#3FE0C5' },
    labelRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
    labelText: { fontSize: 11, fontWeight: '700', color: '#8FA0BD', marginLeft: 6, textTransform: 'uppercase', letterSpacing: 0.5 },
    transcriptText: { fontSize: 15, color: '#C8D8E8', lineHeight: 22, fontWeight: '500' },
    responseBox: { backgroundColor: '#0A1A15', borderRadius: 12, padding: 14, marginBottom: 12, borderLeftWidth: 4, borderLeftColor: '#3FE0C5' },
    responseText: { fontSize: 15, color: '#90D4B8', lineHeight: 24, fontWeight: '500' },
    errorBox: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#1A0A0A', borderRadius: 12, padding: 14, marginBottom: 12, borderLeftWidth: 4, borderLeftColor: '#FF5252' },
    errorText: { fontSize: 14, color: '#FF5252', marginLeft: 8, flex: 1 },
    newQueryBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#1A6BE3', borderRadius: 12, padding: 14, marginBottom: 12 },
    newQueryText: { color: '#fff', fontWeight: '700', fontSize: 15, marginLeft: 8 },
    scrollSpacer: { minHeight: 40 },

    // Bottom input
    bottomSection: { backgroundColor: '#0A0E1A', paddingBottom: 30, borderTopWidth: 1, borderTopColor: 'rgba(255,255,255,0.08)' },
    mediaUploadRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 6 },
    mediaUploadText: { fontSize: 12, color: '#5B8CFF', fontWeight: '600' },
    textInputSection: { flexDirection: 'row', alignItems: 'center', padding: 12, paddingBottom: 8 },
    textInput: { flex: 1, backgroundColor: '#141824', borderRadius: 12, padding: 12, fontSize: 15, color: '#fff', maxHeight: 90, borderWidth: 1, borderColor: 'rgba(255,255,255,0.1)' },
    sendButton: { width: 44, height: 44, borderRadius: 22, backgroundColor: '#1A6BE3', justifyContent: 'center', alignItems: 'center', marginLeft: 8 },
    sendButtonDisabled: { backgroundColor: '#1A2030' },

    // Action buttons row
    actionButtonsRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 12, paddingHorizontal: 40 },
    cameraButton: { width: 52, height: 52, borderRadius: 26, backgroundColor: '#E53935', justifyContent: 'center', alignItems: 'center', shadowColor: '#E53935', shadowOpacity: 0.4, shadowRadius: 10, elevation: 6 },
    galleryButton: { width: 48, height: 48, borderRadius: 24, backgroundColor: '#141824', justifyContent: 'center', alignItems: 'center', borderWidth: 1, borderColor: 'rgba(91,140,255,0.3)' },
    actionSpacer: { width: 24 },
    micButton: { width: 72, height: 72, borderRadius: 36, justifyContent: 'center', alignItems: 'center', shadowColor: '#1A6BE3', shadowOpacity: 0.5, shadowRadius: 12, elevation: 8 },
    micHint: { fontSize: 12, color: '#8FA0BD', marginTop: 6, textAlign: 'center' },

    // Modal
    modalOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.7)', justifyContent: 'flex-end' },
    modalContent: { backgroundColor: '#0D1220', borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: 24, paddingBottom: 40 },
    modalTitle: { fontSize: 20, fontWeight: '700', color: '#fff', textAlign: 'center', marginBottom: 4 },
    modalSubtitle: { fontSize: 13, color: '#8FA0BD', textAlign: 'center', marginBottom: 24 },
    modalButton: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#1A6BE3', borderRadius: 14, padding: 16, marginBottom: 12 },
    modalButtonSecondary: { backgroundColor: '#141824', borderWidth: 1, borderColor: 'rgba(91,140,255,0.3)' },
    modalButtonText: { fontSize: 16, fontWeight: '600', color: '#fff', marginLeft: 12 },
    modalButtonTextSecondary: { color: '#5B8CFF' },
    modalCancel: { alignItems: 'center', paddingVertical: 12, marginTop: 4 },
    modalCancelText: { fontSize: 15, color: '#8FA0BD', fontWeight: '600' },
});
