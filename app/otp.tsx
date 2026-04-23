import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { AuthService } from '@/services/auth';
import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { KeyboardAvoidingView, Platform, ScrollView, StatusBar, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function OTPScreen() {
    const { phoneNumber } = useLocalSearchParams<{ phoneNumber: string }>();
    const router = useRouter();
    const { t } = useTranslation();

    const [otp, setOtp] = useState(['', '', '', '', '', '']);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [timer, setTimer] = useState(30);

    const inputRefs = useRef<TextInput[]>([]);

    useEffect(() => {
        let interval: any;
        if (timer > 0) {
            interval = setInterval(() => {
                setTimer((prev) => prev - 1);
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [timer]);

    const handleOtpChange = (value: string, index: number) => {
        if (value.length > 1) {
            // Handle paste if needed, but for now just single digit
            return;
        }

        const newOtp = [...otp];
        newOtp[index] = value;
        setOtp(newOtp);

        if (error) setError(null);

        // Move to next input if value is entered
        if (value !== '' && index < 5) {
            inputRefs.current[index + 1].focus();
        }
    };

    const handleKeyPress = (e: any, index: number) => {
        if (e.nativeEvent.key === 'Backspace' && otp[index] === '' && index > 0) {
            inputRefs.current[index - 1].focus();
        }
    };

    const handleVerify = async () => {
        const otpValue = otp.join('');
        if (otpValue.length < 6) {
            setError(t('invalid_otp', 'Please enter a 6-digit code'));
            return;
        }

        setLoading(true);
        const result = await AuthService.verifyOTP(phoneNumber as string, otpValue);
        setLoading(false);

        if (result.success) {
            router.replace('/setup/profile');
        } else {
            setError(result.error ?? t('wrong_otp', 'Incorrect OTP. Please try again.'));
        }
    };

    const handleResend = async () => {
        if (timer > 0) return;
        setLoading(true);
        const result = await AuthService.sendOTP(phoneNumber as string);
        setLoading(false);
        if (result.success) {
            setTimer(30);
            setError(null);
        } else {
            setError(result.error ?? t('resend_failed', 'Failed to resend OTP. Try again.'));
        }
    };

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
            <StatusBar barStyle="dark-content" />
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={{ flex: 1 }}
            >
                <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
                    <View style={{ flex: 1, padding: SPACING.l }}>
                        <TouchableOpacity
                            onPress={() => router.back()}
                            style={{
                                width: rf(40),
                                height: rf(40),
                                borderRadius: RADIUS.full,
                                backgroundColor: COLORS.card,
                                justifyContent: 'center',
                                alignItems: 'center',
                                ...SHADOWS.light,
                                marginBottom: SPACING.xl
                            }}
                        >
                            <Ionicons name="arrow-back" size={rf(24)} color={COLORS.text} />
                        </TouchableOpacity>

                        <Text style={{ fontSize: rf(28), fontWeight: '800', color: COLORS.text, marginBottom: SPACING.s }}>
                            {t('verify_phone', 'Verify Phone')}
                        </Text>
                        <Text style={{ fontSize: rf(16), color: COLORS.muted, marginBottom: SPACING.xxl }}>
                            {t('otp_sent_to', 'Sent to')} +91 {phoneNumber}
                        </Text>

                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: SPACING.xl }}>
                            {otp.map((digit, index) => (
                                <TextInput
                                    key={index}
                                    ref={(ref) => { if (ref) inputRefs.current[index] = ref; }}
                                    style={{
                                        width: rf(48),
                                        height: rf(56),
                                        borderWidth: 1.5,
                                        borderColor: otp[index] ? COLORS.primary : COLORS.border,
                                        borderRadius: RADIUS.m,
                                        textAlign: 'center',
                                        fontSize: rf(20),
                                        fontWeight: 'bold',
                                        backgroundColor: COLORS.card,
                                        color: COLORS.text,
                                        ...SHADOWS.light
                                    }}
                                    keyboardType="number-pad"
                                    maxLength={1}
                                    value={digit}
                                    onChangeText={(v) => handleOtpChange(v, index)}
                                    onKeyPress={(e) => handleKeyPress(e, index)}
                                />
                            ))}
                        </View>

                        {!!error && (
                            <Text style={{ color: COLORS.error, marginBottom: SPACING.m, fontWeight: '600', textAlign: 'center' }}>
                                {error}
                            </Text>
                        )}

                        <TouchableOpacity
                            style={{
                                backgroundColor: COLORS.primary,
                                paddingVertical: SPACING.m,
                                borderRadius: RADIUS.full,
                                opacity: loading ? 0.7 : 1,
                                ...SHADOWS.medium
                            }}
                            onPress={handleVerify}
                            disabled={loading}
                        >
                            <Text style={{ color: 'white', textAlign: 'center', fontSize: rf(18), fontWeight: 'bold' }}>
                                {loading ? t('verifying', 'Verifying...') : t('verify', 'Verify')}
                            </Text>
                        </TouchableOpacity>

                        <View style={{ flexDirection: 'row', justifyContent: 'center', marginTop: SPACING.xl }}>
                            <Text style={{ color: COLORS.muted, fontSize: rf(14) }}>
                                {t('didnt_receive', 'Didn\'t receive code?')}
                            </Text>
                            <TouchableOpacity onPress={handleResend} disabled={timer > 0}>
                                <Text style={{
                                    color: timer > 0 ? COLORS.muted : COLORS.primary,
                                    fontWeight: 'bold',
                                    marginLeft: SPACING.xs,
                                    fontSize: rf(14)
                                }}>
                                    {timer > 0 ? `Resend in ${timer}s` : t('resend', 'Resend')}
                                </Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}
