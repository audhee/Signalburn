import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { useVoiceAgent } from '@/hooks/useVoiceAgent';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
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
    const router = useRouter();
    const {
        error,
        transcript,
        aiResponse,
        submitTextQuery,
        startRecording,
        stopRecordingAndProcess,
        isRecording,
        isProcessing,
    } = useVoiceAgent();

    const [typedText, setTypedText] = useState('');
    const [isTextProcessing, setIsTextProcessing] = useState(false);

    const busy = isProcessing || isTextProcessing;

    // ── Text input handler ──────────────────────────────────────────────
    const handleTextSubmit = async () => {
        const cleanText = typedText.trim();
        if (!cleanText || busy) return;

        setIsTextProcessing(true);
        try {
            await submitTextQuery(cleanText);
            setTypedText('');
        } finally {
            setIsTextProcessing(false);
        }
    };

    // ── Status helpers ──────────────────────────────────────────────────
    const getStatusText = () => {
        if (isRecording) return 'Listening... speak now';
        if (busy) return 'Thinking...';
        return 'Hold to talk or type below';
    };

    const getStatusColor = () => {
        if (isRecording) return COLORS.error;
        if (busy) return COLORS.warning;
        return COLORS.primary;
    };

    // ── Render ──────────────────────────────────────────────────────────
    return (
        <View style={styles.container}>
            {/* Header */}
            <View style={styles.header}>
                <Pressable onPress={() => router.back()} style={styles.backBtn}>
                    <Ionicons name="arrow-back" size={24} color={COLORS.text} />
                </Pressable>
                <Text style={styles.headerTitle}>Arohan AI Assistant</Text>
                <View style={styles.headerSpacer} />
            </View>

            <ScrollView
                style={styles.scrollView}
                contentContainerStyle={styles.scrollContent}
                showsVerticalScrollIndicator={false}
            >
                {/* Status indicator */}
                <View style={styles.statusSection}>
                    <View style={[styles.statusDot, { backgroundColor: getStatusColor() }]} />
                    <Text style={styles.statusText}>{getStatusText()}</Text>
                </View>

                {/* Text input */}
                <View style={styles.textInputSection}>
                    <TextInput
                        style={styles.textInput}
                        placeholder="Type your health question..."
                        placeholderTextColor="#999"
                        value={typedText}
                        onChangeText={setTypedText}
                        multiline
                        numberOfLines={2}
                        editable={!busy}
                    />
                    <Pressable
                        style={[
                            styles.sendButton,
                            (!typedText.trim() || busy) && styles.sendButtonDisabled,
                        ]}
                        onPress={handleTextSubmit}
                        disabled={!typedText.trim() || busy}
                    >
                        {isTextProcessing ? (
                            <ActivityIndicator size="small" color="#fff" />
                        ) : (
                            <Ionicons name="send" size={20} color="#fff" />
                        )}
                    </Pressable>
                </View>

                {/* "You said" box */}
                {transcript.length > 0 && (
                    <View style={styles.transcriptBox}>
                        <View style={styles.labelRow}>
                            <Ionicons name="person-circle" size={18} color={COLORS.primary} />
                            <Text style={styles.labelText}>You said</Text>
                        </View>
                        <Text style={styles.transcriptText}>{transcript}</Text>
                    </View>
                )}

                {/* "Arohan says" box */}
                {aiResponse.length > 0 && (
                    <View style={styles.responseBox}>
                        <View style={styles.labelRow}>
                            <Ionicons name="medical" size={18} color={COLORS.success} />
                            <Text style={styles.labelText}>Arohan says</Text>
                        </View>
                        <Text style={styles.responseText}>{aiResponse}</Text>
                    </View>
                )}

                {/* Error display */}
                {error && (
                    <View style={styles.errorBox}>
                        <Ionicons name="alert-circle" size={20} color={COLORS.error} />
                        <Text style={styles.errorText}>{error}</Text>
                    </View>
                )}

                <View style={styles.scrollSpacer} />
            </ScrollView>

            {/* Mic button — fixed at bottom */}
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
                    {isProcessing ? (
                        <ActivityIndicator size="large" color="#fff" />
                    ) : (
                        <Ionicons
                            name={isRecording ? 'mic' : 'mic-outline'}
                            size={32}
                            color="#fff"
                        />
                    )}
                </Pressable>
                <Text style={styles.micHint}>
                    {isRecording ? 'Release to send' : 'Hold microphone to speak'}
                </Text>
            </View>
        </View>
    );
}

// ── Styles ──────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: COLORS.background,
    },
    header: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'space-between',
        paddingHorizontal: SPACING.m,
        paddingTop: SPACING.xl + 20,
        paddingBottom: SPACING.m,
        backgroundColor: COLORS.card,
        ...SHADOWS.light,
    },
    backBtn: {
        padding: 8,
    },
    headerTitle: {
        fontSize: rf(18),
        fontWeight: '700',
        color: COLORS.text,
    },
    headerSpacer: {
        width: 40,
    },
    scrollView: {
        flex: 1,
    },
    scrollContent: {
        padding: SPACING.m,
        paddingBottom: SPACING.xl,
    },
    statusSection: {
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        marginBottom: SPACING.l,
        paddingVertical: SPACING.s,
    },
    statusDot: {
        width: 10,
        height: 10,
        borderRadius: 5,
        marginRight: 8,
    },
    statusText: {
        fontSize: rf(14),
        fontWeight: '600',
        color: COLORS.muted,
    },
    textInputSection: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: SPACING.m,
        marginTop: SPACING.s,
    },
    textInput: {
        flex: 1,
        backgroundColor: '#f5f5f5',
        borderRadius: RADIUS.l,
        padding: SPACING.m,
        fontSize: rf(15),
        color: COLORS.text,
        maxHeight: 90,
        borderWidth: 1,
        borderColor: '#e0e0e0',
    },
    sendButton: {
        width: 44,
        height: 44,
        borderRadius: 22,
        backgroundColor: COLORS.primary,
        justifyContent: 'center',
        alignItems: 'center',
        marginLeft: SPACING.s,
    },
    sendButtonDisabled: {
        backgroundColor: '#ccc',
    },
    transcriptBox: {
        backgroundColor: '#E3F2FD',
        borderRadius: RADIUS.l,
        padding: SPACING.m,
        marginBottom: SPACING.m,
        borderLeftWidth: 4,
        borderLeftColor: '#2196F3',
        ...SHADOWS.light,
    },
    labelRow: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 6,
    },
    labelText: {
        fontSize: rf(12),
        fontWeight: '700',
        color: COLORS.muted,
        marginLeft: 6,
        textTransform: 'uppercase',
        letterSpacing: 0.5,
    },
    transcriptText: {
        fontSize: rf(15),
        color: '#1565C0',
        lineHeight: 22,
        fontWeight: '500',
    },
    responseBox: {
        backgroundColor: '#E8F5E9',
        borderRadius: RADIUS.l,
        padding: SPACING.m,
        marginBottom: SPACING.m,
        borderLeftWidth: 4,
        borderLeftColor: '#4CAF50',
        ...SHADOWS.light,
    },
    responseText: {
        fontSize: rf(15),
        color: '#2E7D32',
        lineHeight: 24,
        fontWeight: '500',
    },
    errorBox: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: '#FFEBEE',
        borderRadius: RADIUS.l,
        padding: SPACING.m,
        marginBottom: SPACING.m,
        borderLeftWidth: 4,
        borderLeftColor: COLORS.error,
    },
    errorText: {
        fontSize: rf(14),
        color: COLORS.error,
        marginLeft: 8,
        flex: 1,
    },
    scrollSpacer: {
        minHeight: 50,
    },
    micSection: {
        alignItems: 'center',
        paddingVertical: SPACING.l,
        paddingBottom: SPACING.xl + 20,
        backgroundColor: COLORS.card,
        ...SHADOWS.medium,
    },
    micButton: {
        width: 80,
        height: 80,
        borderRadius: 40,
        justifyContent: 'center',
        alignItems: 'center',
        ...SHADOWS.medium,
    },
    micHint: {
        fontSize: rf(12),
        color: COLORS.muted,
        marginTop: SPACING.s,
    },
});
