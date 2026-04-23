import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { useVoiceAgent } from '@/hooks/useVoiceAgent';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import * as Speech from 'expo-speech';
import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { SafeAreaView, ScrollView, StatusBar, Text, TouchableOpacity, View, ActivityIndicator } from 'react-native';
import Animated, { useAnimatedStyle, withRepeat, withTiming, withSequence, interpolate, useSharedValue } from 'react-native-reanimated';

export default function AIGuidance() {
    const router = useRouter();
    const { t, i18n } = useTranslation();
    const [mode, setMode] = useState<'guidance' | 'assistant'>('assistant');
    const [currentStep, setCurrentStep] = useState(0);

    const { 
        state, 
        isRecording, 
        isProcessing, 
        isPlaying, 
        startRecording, 
        stopRecordingAndProcess,
        error 
    } = useVoiceAgent();

    // Pulse Animation for Recording
    const pulseValue = useSharedValue(1);
    useEffect(() => {
        if (isRecording) {
            pulseValue.value = withRepeat(
                withSequence(
                    withTiming(1.2, { duration: 500 }),
                    withTiming(1, { duration: 500 })
                ),
                -1,
                true
            );
        } else {
            pulseValue.value = withTiming(1);
        }
    }, [isRecording]);

    const pulseStyle = useAnimatedStyle(() => ({
        transform: [{ scale: pulseValue.value }],
        opacity: interpolate(pulseValue.value, [1, 1.2], [1, 0.6]),
    }));

    // Guidance mode logic: CPR Steps
    const CPR_STEPS = useMemo(() => [
        { title: t('cpr_step_1_title'), text: t('cpr_step_1_text') },
        { title: t('cpr_step_2_title'), text: t('cpr_step_2_text') },
        { title: t('cpr_step_3_title'), text: t('cpr_step_3_text') },
        { title: t('cpr_step_4_title'), text: t('cpr_step_4_text') },
    ], [t]);

    const speakGuidance = (text: string) => {
        Speech.stop();
        Speech.speak(text, { language: i18n.language === 'hi' ? 'hi-IN' : 'en-US', rate: 0.9 });
    };

    useEffect(() => {
        if (mode === 'guidance') {
            speakGuidance(CPR_STEPS[currentStep].text);
        }
    }, [currentStep, mode]);

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }}>
            <StatusBar barStyle="dark-content" />

            {/* Header */}
            <View style={{ paddingHorizontal: SPACING.m, paddingTop: SPACING.xl, paddingBottom: SPACING.m, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: 'white', borderBottomWidth: 1, borderBottomColor: COLORS.border }}>
                <View>
                    <Text style={{ fontSize: rf(14), fontWeight: '700', color: COLORS.primary }}>{mode === 'assistant' ? 'LIVE AI ASSISTANT' : t('cpr_guidance_mode')}</Text>
                    <Text style={{ fontSize: rf(12), color: COLORS.muted }}>{t('ai_guidance')}</Text>
                </View>
                <TouchableOpacity onPress={() => router.back()}>
                    <Ionicons name="close-circle" size={rf(32)} color={COLORS.muted} />
                </TouchableOpacity>
            </View>

            {/* Mode Switcher */}
            <View style={{ flexDirection: 'row', padding: SPACING.s, backgroundColor: '#F3F4F6', margin: SPACING.m, borderRadius: RADIUS.full }}>
                <TouchableOpacity 
                    onPress={() => { setMode('assistant'); Speech.stop(); }}
                    style={{ flex: 1, paddingVertical: SPACING.s, alignItems: 'center', backgroundColor: mode === 'assistant' ? 'white' : 'transparent', borderRadius: RADIUS.full, ... (mode === 'assistant' ? SHADOWS.light : {}) }}
                >
                    <Text style={{ fontWeight: '700', color: mode === 'assistant' ? COLORS.primary : COLORS.muted }}>VOICE AGENT</Text>
                </TouchableOpacity>
                <TouchableOpacity 
                    onPress={() => setMode('guidance')}
                    style={{ flex: 1, paddingVertical: SPACING.s, alignItems: 'center', backgroundColor: mode === 'guidance' ? 'white' : 'transparent', borderRadius: RADIUS.full, ... (mode === 'guidance' ? SHADOWS.light : {}) }}
                >
                    <Text style={{ fontWeight: '700', color: mode === 'guidance' ? COLORS.primary : COLORS.muted }}>CPR STEPS</Text>
                </TouchableOpacity>
            </View>

            <ScrollView style={{ flex: 1 }} contentContainerStyle={{ flexGrow: 1, padding: SPACING.l, alignItems: 'center' }}>
                {mode === 'guidance' ? (
                    <>
                        <View style={{ width: '100%', aspectRatio: 1.2, backgroundColor: '#FFEDD5', borderRadius: RADIUS.xl, alignItems: 'center', justifyContent: 'center', marginBottom: SPACING.xl }}>
                            <Ionicons name="body" size={rf(120)} color={COLORS.warning} />
                        </View>
                        <Text style={{ fontSize: rf(24), fontWeight: '800', color: COLORS.text, textAlign: 'center', marginBottom: SPACING.m }}>{CPR_STEPS[currentStep].title}</Text>
                        <Text style={{ fontSize: rf(18), color: COLORS.muted, marginBottom: SPACING.xl, textAlign: 'center' }}>{CPR_STEPS[currentStep].text}</Text>
                        <View style={{ flexDirection: 'row', gap: SPACING.s, marginBottom: SPACING.xl }}>
                            {CPR_STEPS.map((_, index) => (
                                <View key={index} style={{ width: rf(8), height: rf(8), borderRadius: rf(4), backgroundColor: index === currentStep ? COLORS.primary : COLORS.border }} />
                            ))}
                        </View>
                    </>
                ) : (
                    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', width: '100%' }}>
                        <View style={{ width: rf(180), height: rf(180), borderRadius: rf(90), backgroundColor: '#E0F2FE', alignItems: 'center', justifyContent: 'center', marginBottom: SPACING.xl }}>
                            <Ionicons name="mic-outline" size={rf(80)} color={COLORS.primary} />
                            {isRecording && (
                                <Animated.View style={[{ position: 'absolute', width: rf(180), height: rf(180), borderRadius: rf(90), borderWidth: 4, borderColor: COLORS.primary }, pulseStyle]} />
                            )}
                        </View>

                        <Text style={{ fontSize: rf(22), fontWeight: '800', color: COLORS.text, textAlign: 'center', marginBottom: SPACING.s }}>
                            {isRecording ? "Listening..." : isProcessing ? "Thinking..." : isPlaying ? "Arohan Speaking..." : "Hold to Talk"}
                        </Text>
                        <Text style={{ fontSize: rf(16), color: COLORS.muted, textAlign: 'center', marginBottom: SPACING.xl, maxWidth: '80%' }}>
                            {isRecording ? "Release to send your question" : isProcessing ? "Processing your audio with Gemini AI" : "I can help with medical guidance or CPR steps in any language."}
                        </Text>
                        
                        {error && (
                            <Text style={{ color: COLORS.error, marginBottom: SPACING.m, fontWeight: '600' }}>⚠️ Connection Error: {error}</Text>
                        )}

                        {isProcessing && <ActivityIndicator size="large" color={COLORS.primary} />}
                    </View>
                )}
            </ScrollView>

            {/* Controls */}
            {mode === 'guidance' ? (
                <View style={{ padding: SPACING.l, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: 'white', borderTopColor: COLORS.border, borderTopWidth: 1 }}>
                    <TouchableOpacity style={{ alignItems: 'center', padding: SPACING.s }} onPress={() => speakGuidance(CPR_STEPS[currentStep].text)}>
                        <Ionicons name="refresh-circle" size={rf(40)} color={COLORS.muted} />
                        <Text style={{ fontSize: rf(12), fontWeight: '600', color: COLORS.muted }}>{t('repeat')}</Text>
                    </TouchableOpacity>
                    <TouchableOpacity style={{ backgroundColor: COLORS.primary, paddingHorizontal: SPACING.xl, paddingVertical: SPACING.m, borderRadius: RADIUS.full, flexDirection: 'row', alignItems: 'center' }} onPress={() => currentStep < CPR_STEPS.length - 1 ? setCurrentStep(c => c + 1) : router.back()}>
                        <Text style={{ color: 'white', fontWeight: 'bold', marginRight: SPACING.s, fontSize: rf(16) }}>{t('next')}</Text>
                        <Ionicons name="arrow-forward" size={rf(20)} color="white" />
                    </TouchableOpacity>
                </View>
            ) : (
                <View style={{ padding: SPACING.xl, backgroundColor: 'white', borderTopColor: COLORS.border, borderTopWidth: 1, alignItems: 'center' }}>
                    <TouchableOpacity 
                        onLongPress={startRecording}
                        onPressOut={stopRecordingAndProcess}
                        style={{ 
                            width: rf(80), height: rf(80), borderRadius: rf(40), 
                            backgroundColor: isRecording ? COLORS.error : COLORS.primary, 
                            alignItems: 'center', justifyContent: 'center',
                            ...SHADOWS.medium,
                            transform: [{ scale: isRecording ? 1.1 : 1 }]
                        }}
                        activeOpacity={0.7}
                    >
                        <Ionicons name={isRecording ? "stop" : "mic"} size={rf(40)} color="white" />
                    </TouchableOpacity>
                    <Text style={{ marginTop: SPACING.m, color: COLORS.muted, fontWeight: '700', fontSize: rf(14) }}>
                        {isRecording ? "RELEASE TO SEND" : "HOLD MICROPHONE TO TALK"}
                    </Text>
                </View>
            )}
        </SafeAreaView>
    );
}
