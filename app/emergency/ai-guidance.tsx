import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { useVoiceAgent } from '@/hooks/useVoiceAgent';
import { apiClient } from '@/services/apiClient';
import { Ionicons } from '@expo/vector-icons';
import { Audio } from 'expo-av';
import { useRouter } from 'expo-router';
import { useRef, useState } from 'react';
import {
    ActivityIndicator,
    Pressable,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    View,
} from 'react-native';

export default function AIGuidanceScreen() {
    const router    = useRouter();
    const scrollRef = useRef<ScrollView>(null);

    // ── ALL STATE FIRST ────────────────────────────────────────────────
    const [typedText,          setTypedText]          = useState('');
    const [isTextProcessing,   setIsTextProcessing]   = useState(false);
    const [textError,          setTextError]          = useState<string | null>(null);
    const [initialQuery,       setInitialQuery]       = useState('');
    const [collectedAnswers,   setCollectedAnswers]   = useState<string[]>([]);
    const [currentQuestion,    setCurrentQuestion]    = useState<string>('');
    const [questionNum,        setQuestionNum]        = useState(0);
    const [totalQuestions,     setTotalQuestions]     = useState(5);
    const [finalResponse,      setFinalResponse]      = useState('');
    const [mode,               setMode]               = useState<'idle' | 'questioning' | 'answered'>('idle');

    // ── VOICE HOOK — uses handleVoiceAnswer via ref so no ordering issue ──
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
        }
    });

    const busy = isProcessing || isTextProcessing;

    // ── PLAY AUDIO ─────────────────────────────────────────────────────
    const playAudio = async (base64: string) => {
        try {
            await Audio.setAudioModeAsync({
                allowsRecordingIOS:   false,
                playsInSilentModeIOS: true,
                shouldDuckAndroid:    true,
            });
            const { sound } = await Audio.Sound.createAsync(
                { uri: `data:audio/wav;base64,${base64}` },
                { shouldPlay: true }
            );
            sound.setOnPlaybackStatusUpdate((status) => {
                if (status.isLoaded && status.didJustFinish) {
                    sound.unloadAsync().catch(() => {});
                }
            });
        } catch (e) {
            console.error('Audio playback failed:', e);
        }
    };

    // ── CALL BACKEND ───────────────────────────────────────────────────
    const callGuidedQuery = async (query: string, answers: string[]) => {
        const response = await apiClient.request('/api/v1/ai/guided-query', {
            method: 'POST',
            body: {
                text:     query,
                context:  answers.join('\n'),
                language: 'hi-IN',
            },
        });
        return response;
    };

    // ── SHARED ANSWER PROCESSOR (used by both text and voice) ──────────
    const processAnswer = async (answerText: string, currentMode: string, currentInitialQuery: string, currentAnswers: string[], currentQText: string) => {
        setIsTextProcessing(true);
        setTextError(null);

        let newAnswers: string[];
        let queryText: string;

        if (currentMode === 'idle') {
            setInitialQuery(answerText);
            setCollectedAnswers([]);
            setFinalResponse('');
            setMode('questioning');
            newAnswers = [];
            queryText  = answerText;
        } else {
            newAnswers = [...currentAnswers, `Q: ${currentQText}\nA: ${answerText}`];
            setCollectedAnswers(newAnswers);
            queryText  = currentInitialQuery;
        }

        try {
            const res = await callGuidedQuery(queryText, newAnswers);
            if (res.mode === 'question') {
                setCurrentQuestion(res.question);
                setQuestionNum(res.question_num);
                setTotalQuestions(res.total_questions);
            } else if (res.mode === 'answer') {
                setFinalResponse(res.response || '');
                setMode('answered');
                if (res.audio_base64) await playAudio(res.audio_base64);
            }
        } catch (err: any) {
            setTextError(err.message || 'Failed to get response');
            if (currentMode === 'idle') setMode('idle');
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

    // ── VOICE ANSWER — assign to ref so hook can call it ──────────────
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
    };

    // ── STATUS ─────────────────────────────────────────────────────────
    const getStatusText = () => {
        if (isRecording)            return 'Listening... speak now';
        if (busy)                   return 'Thinking...';
        if (mode === 'questioning') return `Question ${questionNum} of ${totalQuestions}`;
        if (mode === 'answered')    return 'Done! Ask another question.';
        return 'Describe your health problem below';
    };

    const getStatusColor = () => {
        if (isRecording)            return COLORS.error;
        if (busy)                   return '#FF9800';
        if (mode === 'questioning') return '#9C27B0';
        if (mode === 'answered')    return '#4CAF50';
        return COLORS.primary;
    };

    const displayError = error || textError;

    // ── RENDER ─────────────────────────────────────────────────────────
    return (
        <View style={styles.container}>

            {/* Header */}
            <View style={styles.header}>
                <Pressable onPress={() => router.back()} style={styles.backBtn}>
                    <Ionicons name="arrow-back" size={24} color={COLORS.text} />
                </Pressable>
                <Text style={styles.headerTitle}>Arohan AI Assistant</Text>
                {mode !== 'idle'
                    ? <Pressable onPress={handleReset} style={styles.resetBtn}>
                        <Ionicons name="refresh" size={20} color={COLORS.primary} />
                      </Pressable>
                    : <View style={styles.headerSpacer} />
                }
            </View>

            <ScrollView
                ref={scrollRef}
                style={styles.scrollView}
                contentContainerStyle={styles.scrollContent}
                showsVerticalScrollIndicator={false}
            >
                {/* Status */}
                <View style={styles.statusSection}>
                    <View style={[styles.statusDot, { backgroundColor: getStatusColor() }]} />
                    <Text style={styles.statusText}>{getStatusText()}</Text>
                </View>

                {/* Progress bar */}
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

                {/* Initial complaint */}
                {initialQuery.length > 0 && (
                    <View style={styles.transcriptBox}>
                        <View style={styles.labelRow}>
                            <Ionicons name="person-circle" size={18} color={COLORS.primary} />
                            <Text style={styles.labelText}>Your complaint</Text>
                        </View>
                        <Text style={styles.transcriptText}>{initialQuery}</Text>
                    </View>
                )}

                {/* Current question */}
                {mode === 'questioning' && currentQuestion.length > 0 && (
                    <View style={styles.questionBox}>
                        <View style={styles.labelRow}>
                            <Ionicons name="help-circle" size={18} color="#9C27B0" />
                            <Text style={[styles.labelText, { color: '#9C27B0' }]}>Arohan asks</Text>
                        </View>
                        <Text style={styles.questionText}>{currentQuestion}</Text>
                    </View>
                )}

                {/* Collected Q&A */}
                {collectedAnswers.map((qa, i) => (
                    <View key={i} style={styles.answeredBox}>
                        <Text style={styles.answeredText}>{qa}</Text>
                    </View>
                ))}

                {/* Final response */}
                {mode === 'answered' && finalResponse.length > 0 && (
                    <View style={styles.responseBox}>
                        <View style={styles.labelRow}>
                            <Ionicons name="medical" size={18} color="#4CAF50" />
                            <Text style={styles.labelText}>Arohan says</Text>
                        </View>
                        <Text style={styles.responseText}>{finalResponse}</Text>
                    </View>
                )}

                {/* Voice transcript shown */}
                {transcript.length > 0 && (
                    <View style={styles.transcriptBox}>
                        <View style={styles.labelRow}>
                            <Ionicons name="mic" size={18} color={COLORS.primary} />
                            <Text style={styles.labelText}>You said (voice)</Text>
                        </View>
                        <Text style={styles.transcriptText}>{transcript}</Text>
                    </View>
                )}

                {/* Error */}
                {displayError && (
                    <View style={styles.errorBox}>
                        <Ionicons name="alert-circle" size={20} color={COLORS.error} />
                        <Text style={styles.errorText}>{displayError}</Text>
                    </View>
                )}

                {/* New question button */}
                {mode === 'answered' && (
                    <Pressable style={styles.newQueryBtn} onPress={handleReset}>
                        <Ionicons name="add-circle-outline" size={20} color="#fff" />
                        <Text style={styles.newQueryText}>Ask Another Question</Text>
                    </Pressable>
                )}

                <View style={styles.scrollSpacer} />
            </ScrollView>

            {/* Bottom input + mic */}
            <View style={styles.bottomSection}>
                <View style={styles.textInputSection}>
                    <TextInput
                        style={styles.textInput}
                        placeholder={
                            mode === 'idle'        ? 'Describe your health problem...' :
                            mode === 'questioning' ? 'Type your answer...' :
                                                     'Ask another question...'
                        }
                        placeholderTextColor="#999"
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

                <View style={styles.micSection}>
                    <Pressable
                        onPressIn={startRecording}
                        onPressOut={stopRecordingAndProcess}
                        style={({ pressed }) => [
                            styles.micButton,
                            {
                                backgroundColor: isRecording ? COLORS.error : COLORS.primary,
                                transform: [{ scale: pressed || isRecording ? 0.95 : 1 }],
                            },
                        ]}
                        disabled={busy}
                    >
                        {isProcessing
                            ? <ActivityIndicator size="large" color="#fff" />
                            : <Ionicons name={isRecording ? 'mic' : 'mic-outline'} size={32} color="#fff" />
                        }
                    </Pressable>
                    <Text style={styles.micHint}>
                        {isRecording ? 'Release to send' : 'Hold to speak'}
                    </Text>
                </View>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container:         { flex: 1, backgroundColor: COLORS.background },
    header:            { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: SPACING.m, paddingTop: SPACING.xl + 20, paddingBottom: SPACING.m, backgroundColor: COLORS.card, ...SHADOWS.light },
    backBtn:           { padding: 8 },
    resetBtn:          { padding: 8 },
    headerTitle:       { fontSize: rf(18), fontWeight: '700', color: COLORS.text },
    headerSpacer:      { width: 40 },
    scrollView:        { flex: 1 },
    scrollContent:     { padding: SPACING.m, paddingBottom: SPACING.xl },
    statusSection:     { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginBottom: SPACING.m, paddingVertical: SPACING.s },
    statusDot:         { width: 10, height: 10, borderRadius: 5, marginRight: 8 },
    statusText:        { fontSize: rf(14), fontWeight: '600', color: COLORS.muted },
    progressContainer: { marginBottom: SPACING.m },
    progressBar:       { height: 6, backgroundColor: '#E0E0E0', borderRadius: 3, overflow: 'hidden' },
    progressFill:      { height: 6, backgroundColor: '#9C27B0', borderRadius: 3 },
    progressText:      { fontSize: rf(11), color: COLORS.muted, marginTop: 4, textAlign: 'right' },
    questionBox:       { backgroundColor: '#F3E5F5', borderRadius: RADIUS.l, padding: SPACING.m, marginBottom: SPACING.m, borderLeftWidth: 4, borderLeftColor: '#9C27B0', ...SHADOWS.light },
    questionText:      { fontSize: rf(15), color: '#6A1B9A', lineHeight: 22, fontWeight: '600' },
    answeredBox:       { backgroundColor: '#F5F5F5', borderRadius: RADIUS.m, padding: SPACING.s, marginBottom: SPACING.s, borderLeftWidth: 3, borderLeftColor: '#BDBDBD' },
    answeredText:      { fontSize: rf(13), color: '#757575', lineHeight: 20 },
    transcriptBox:     { backgroundColor: '#E3F2FD', borderRadius: RADIUS.l, padding: SPACING.m, marginBottom: SPACING.m, borderLeftWidth: 4, borderLeftColor: '#2196F3', ...SHADOWS.light },
    labelRow:          { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
    labelText:         { fontSize: rf(12), fontWeight: '700', color: COLORS.muted, marginLeft: 6, textTransform: 'uppercase', letterSpacing: 0.5 },
    transcriptText:    { fontSize: rf(15), color: '#1565C0', lineHeight: 22, fontWeight: '500' },
    responseBox:       { backgroundColor: '#E8F5E9', borderRadius: RADIUS.l, padding: SPACING.m, marginBottom: SPACING.m, borderLeftWidth: 4, borderLeftColor: '#4CAF50', ...SHADOWS.light },
    responseText:      { fontSize: rf(15), color: '#2E7D32', lineHeight: 24, fontWeight: '500' },
    errorBox:          { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFEBEE', borderRadius: RADIUS.l, padding: SPACING.m, marginBottom: SPACING.m, borderLeftWidth: 4, borderLeftColor: COLORS.error },
    errorText:         { fontSize: rf(14), color: COLORS.error, marginLeft: 8, flex: 1 },
    newQueryBtn:       { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: COLORS.primary, borderRadius: RADIUS.l, padding: SPACING.m, marginBottom: SPACING.m },
    newQueryText:      { color: '#fff', fontWeight: '700', fontSize: rf(15), marginLeft: 8 },
    scrollSpacer:      { minHeight: 50 },
    bottomSection:     { backgroundColor: COLORS.card, ...SHADOWS.medium, paddingBottom: SPACING.xl + 10 },
    textInputSection:  { flexDirection: 'row', alignItems: 'center', padding: SPACING.m, paddingBottom: SPACING.s },
    textInput:         { flex: 1, backgroundColor: '#f5f5f5', borderRadius: RADIUS.l, padding: SPACING.m, fontSize: rf(15), color: COLORS.text, maxHeight: 90, borderWidth: 1, borderColor: '#e0e0e0' },
    sendButton:        { width: 44, height: 44, borderRadius: 22, backgroundColor: COLORS.primary, justifyContent: 'center', alignItems: 'center', marginLeft: SPACING.s },
    sendButtonDisabled:{ backgroundColor: '#ccc' },
    micSection:        { alignItems: 'center', paddingVertical: SPACING.m },
    micButton:         { width: 80, height: 80, borderRadius: 40, justifyContent: 'center', alignItems: 'center', ...SHADOWS.medium },
    micHint:           { fontSize: rf(12), color: COLORS.muted, marginTop: SPACING.s },
});