import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { AuthService } from '@/services/auth';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Image, KeyboardAvoidingView, Platform, ScrollView, StatusBar, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function LoginScreen() {
    const router = useRouter();
    const { t } = useTranslation();

    // Login State
    const [phoneNumber, setPhoneNumber] = useState('');
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function checkInitialState() {
            try {
                const savedLanguage = await AsyncStorage.getItem('user-language');
                if (!savedLanguage) {
                    router.replace('/language' as any);
                    return;
                }

                // Temporarily disabled auto-redirect to test login/OTP flow
                /*
                const profile = await StorageService.getUserProfile();
                if (profile) {
                    router.replace('/home' as any);
                }
                */
            } catch {
                router.replace('/language' as any);
            }
        }
        checkInitialState();
    }, [router]);

    const digitsOnly = phoneNumber.replace(/\\D/g, '');
    const isValidPhone = digitsOnly.length === 10;
    const canContinue = isValidPhone;

    // Login UI (Placeholder for next task, but essentially implemented structure here to replace old UI)
    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
            <StatusBar barStyle="dark-content" />
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={{ flex: 1 }}
            >
                <ScrollView contentContainerStyle={{ flexGrow: 1 }}>
                    <View style={{ flex: 1, padding: SPACING.l, justifyContent: 'center' }}>
                        {/* Header with Language Button */}
                        <View style={{ alignItems: 'flex-end', marginBottom: SPACING.m, position: 'absolute', top: SPACING.xl, right: SPACING.l, zIndex: 10 }}>
                            <TouchableOpacity
                                style={{
                                    paddingVertical: SPACING.s,
                                    paddingHorizontal: SPACING.m,
                                    flexDirection: 'row',
                                    alignItems: 'center',
                                    borderRadius: RADIUS.full,
                                    backgroundColor: COLORS.card,
                                    borderWidth: 1,
                                    borderColor: COLORS.border,
                                    ...SHADOWS.light,
                                }}
                                onPress={() => router.push('/language')}
                                accessibilityRole="button"
                                accessibilityLabel={t('change_language')}
                                accessibilityHint="Opens the language selection screen"
                            >
                                <Ionicons name="globe-outline" size={rf(16)} color={COLORS.primary} style={{ marginRight: SPACING.xs }} />
                                <Text style={{ color: COLORS.primary, fontWeight: '700' }}>{t('language')}</Text>
                            </TouchableOpacity>
                        </View>

                        {/* Main Content Area - Centered */}
                        <View style={{ width: '100%', maxWidth: 520, alignSelf: 'center' }}>
                            {/* App Logo */}
                            <Image
                                source={require('../assets/images/logo.png')}
                                style={{
                                    width: rf(120),
                                    height: rf(120),
                                    alignSelf: 'center',
                                    marginBottom: SPACING.l,
                                    borderRadius: RADIUS.m
                                }}
                                resizeMode="contain"
                            />

                            <Text style={{ fontSize: rf(28), fontWeight: '800', color: COLORS.text, marginBottom: SPACING.s, textAlign: 'center' }}>
                                {t('lets_get_setup')}
                            </Text>
                            <Text style={{ fontSize: rf(16), color: COLORS.muted, marginBottom: SPACING.xl, textAlign: 'center' }}>
                                {t('enter_mobile_verify')}
                            </Text>

                            <Text style={{ fontSize: rf(14), fontWeight: '600', color: COLORS.text, marginBottom: SPACING.s, alignSelf: 'flex-start' }}>
                                {t('phone_number')}
                            </Text>
                            <View style={{
                                flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderColor: COLORS.border,
                                borderRadius: RADIUS.m, paddingHorizontal: SPACING.m, backgroundColor: COLORS.card,
                                height: rf(56)
                            }}>
                                <Text style={{ fontSize: rf(16), fontWeight: '600', color: COLORS.text, marginRight: SPACING.s }}>
                                    🇮🇳 +91
                                </Text>
                                <View style={{ width: 1, height: rf(24), backgroundColor: COLORS.border, marginRight: SPACING.s }} />
                                <TextInput
                                    placeholder="000 000 0000"
                                    placeholderTextColor={COLORS.muted}
                                    keyboardType="phone-pad"
                                    style={{ flex: 1, fontSize: rf(18), color: COLORS.text, fontWeight: '600' }}
                                    value={phoneNumber}
                                    onChangeText={(v) => {
                                        setPhoneNumber(v);
                                        if (error) setError(null);
                                    }}
                                />
                            </View>

                            {!!error && (
                                <Text style={{ color: COLORS.error, marginTop: SPACING.s, fontWeight: '600' }}>{error}</Text>
                            )}

                            <TouchableOpacity
                                style={{
                                    backgroundColor: canContinue ? COLORS.primary : COLORS.border,
                                    padding: SPACING.m,
                                    borderRadius: RADIUS.full,
                                    marginTop: SPACING.xl, ...SHADOWS.medium
                                }}
                                onPress={async () => {
                                    if (!canContinue) {
                                        setError(t('invalid_phone'));
                                        return;
                                    }

                                    const result = await AuthService.sendOTP(phoneNumber);
                                    if (!result.success) {
                                        setError(result.error || 'Failed to send OTP');
                                        return;
                                    }

                                    router.push({
                                        pathname: '/otp' as any,
                                        params: { phoneNumber }
                                    });
                                }}
                                accessibilityRole="button"
                                accessibilityLabel={t('get_verification_code')}
                                accessibilityHint="Continues to profile setup"
                            >
                                <Text style={{ color: 'white', textAlign: 'center', fontSize: rf(18), fontWeight: 'bold' }}>
                                    {t('get_verification_code')}
                                </Text>
                            </TouchableOpacity>
                        </View>
                    </View>
                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}
