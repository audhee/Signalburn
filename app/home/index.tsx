import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { StorageService } from '@/services/storage';
import { Ionicons } from '@expo/vector-icons';
import { useKeepAwake } from 'expo-keep-awake';
import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ScrollView, StatusBar, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function HomeScreen() {
    const router = useRouter();
    const { t } = useTranslation();
    useKeepAwake();
    const [userName, setUserName] = useState('');

    useFocusEffect(
        useCallback(() => {
            const loadProfile = async () => {
                const profile = await StorageService.getUserProfile();
                if (profile && profile.name) {
                    setUserName(profile.name);
                }
            };
            loadProfile();
        }, [])
    );

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB', alignItems: 'center' }}>
            <View style={{ width: '100%', maxWidth: 500, flex: 1 }}>
                <StatusBar barStyle="dark-content" />

                {/* Header - Fixed top */}
                <View style={{ paddingHorizontal: SPACING.l, paddingTop: SPACING.xl, paddingBottom: SPACING.s, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                    <View>
                        <Text style={{ fontSize: rf(24), fontWeight: '800', color: COLORS.text }}>{t('hello_user', { name: userName || 'User' })}</Text>
                        <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: SPACING.xs }}>
                            <View style={{ width: rf(8), height: rf(8), borderRadius: rf(4), backgroundColor: COLORS.success, marginRight: SPACING.s }} />
                            <Text style={{ fontSize: rf(14), color: COLORS.muted }}>{t('device_connected')}</Text>
                        </View>
                    </View>
                    <TouchableOpacity
                        style={{ padding: SPACING.s, backgroundColor: 'white', borderRadius: RADIUS.full, ...SHADOWS.light }}
                        onPress={() => router.push('/emergency/assist')}
                        accessibilityRole="button"
                        accessibilityLabel="SOS"
                        accessibilityHint="Opens emergency assistance"
                    >
                        <Text style={{ fontSize: rf(12), fontWeight: '700', color: COLORS.primary }}>SOS</Text>
                    </TouchableOpacity>
                </View>

                {/* Scrollable Main Content */}
                <ScrollView contentContainerStyle={{ flexGrow: 1, justifyContent: 'center', alignItems: 'center', paddingBottom: SPACING.xl }}>

                    {/* Ripple Effect Layers */}
                    <View style={{ width: rf(220), height: rf(220), borderRadius: rf(110), backgroundColor: '#EFF6FF', alignItems: 'center', justifyContent: 'center', marginTop: SPACING.xl }}>
                        <View style={{ width: rf(170), height: rf(170), borderRadius: rf(85), backgroundColor: '#DBEAFE', alignItems: 'center', justifyContent: 'center' }}>
                            <View style={{
                                width: rf(130), height: rf(130), borderRadius: rf(65), backgroundColor: COLORS.primary,
                                alignItems: 'center', justifyContent: 'center',
                                shadowColor: COLORS.primary, shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.4, shadowRadius: 20, elevation: 15
                            }}>
                                <Ionicons name="shield-checkmark" size={rf(65)} color="white" />
                            </View>
                        </View>
                    </View>

                    <Text style={{ fontSize: rf(22), fontWeight: '800', color: COLORS.text, marginTop: SPACING.m }}>
                        {t('monitoring_active')}
                    </Text>
                    <Text style={{ fontSize: rf(16), color: COLORS.muted, marginTop: SPACING.xs }}>
                        {t('you_are_safe')}
                    </Text>

                    {/* Vitals */}
                    <View style={{ flexDirection: 'row', width: '100%', paddingHorizontal: SPACING.l, marginTop: SPACING.xl, justifyContent: 'space-between', maxWidth: 400 }}>
                        <View style={{ backgroundColor: 'white', padding: SPACING.m, borderRadius: RADIUS.l, alignItems: 'center', width: '48%', ...SHADOWS.light }}>
                            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: SPACING.s }}>
                                <Ionicons name="heart" size={rf(20)} color={COLORS.error} style={{ marginRight: SPACING.s }} />
                                <Text style={{ fontSize: rf(12), color: COLORS.muted }}>{t('heart_rate_label')}</Text>
                            </View>
                            <Text style={{ fontSize: rf(24), fontWeight: '800', color: COLORS.text }}>72 <Text style={{ fontSize: rf(12), fontWeight: '600', color: COLORS.muted }}>BPM</Text></Text>
                            <Text style={{ fontSize: rf(10), color: COLORS.success, marginTop: SPACING.xs }}>{t('normal_status')}</Text>
                        </View>

                        <View style={{ backgroundColor: 'white', padding: SPACING.m, borderRadius: RADIUS.l, alignItems: 'center', width: '48%', ...SHADOWS.light }}>
                            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: SPACING.s }}>
                                <Ionicons name="battery-charging" size={rf(20)} color={COLORS.primary} style={{ marginRight: SPACING.s }} />
                                <Text style={{ fontSize: rf(12), color: COLORS.muted }}>{t('battery')}</Text>
                            </View>
                            <Text style={{ fontSize: rf(24), fontWeight: '800', color: COLORS.text }}>85%</Text>
                            <Text style={{ fontSize: rf(10), color: COLORS.muted, marginTop: SPACING.xs }}>{t('hours_left', { hours: 14 })}</Text>
                        </View>
                    </View>
                </ScrollView>

                {/* Bottom Panel - Fixed */}
                <View style={{ padding: SPACING.l, backgroundColor: 'white', borderTopLeftRadius: RADIUS.xl, borderTopRightRadius: RADIUS.xl, ...SHADOWS.medium }}>
                    <TouchableOpacity
                        style={{
                            backgroundColor: COLORS.error, padding: SPACING.m, borderRadius: RADIUS.full,
                            flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
                            marginBottom: SPACING.s, shadowColor: COLORS.error, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8
                        }}
                        onPress={() => router.push('/emergency/assist')}
                        accessibilityRole="button"
                        accessibilityLabel="Emergency help"
                        accessibilityHint="Opens emergency assistance"
                    >
                        <View style={{ width: rf(24), height: rf(24), borderRadius: rf(12), backgroundColor: 'rgba(255,255,255,0.2)', alignItems: 'center', justifyContent: 'center', marginRight: SPACING.s }}>
                            <Ionicons name="alert-circle" size={rf(16)} color="white" />
                        </View>
                        <Text style={{ color: 'white', fontSize: rf(16), fontWeight: 'bold' }}>{t('emergency_help')}</Text>
                    </TouchableOpacity>

                    <View style={{ flexDirection: 'row', justifyContent: 'space-around', paddingTop: SPACING.xs }}>
                        <View style={{ alignItems: 'center' }}>
                            <Ionicons name="home" size={rf(20)} color={COLORS.primary} />
                            <Text style={{ fontSize: rf(10), color: COLORS.primary, marginTop: 2 }}>{t('home')}</Text>
                        </View>
                        <TouchableOpacity
                            style={{ alignItems: 'center' }}
                            onPress={() => router.push('/stats' as any)}
                            accessibilityRole="button"
                            accessibilityLabel="Stats"
                            accessibilityHint="Opens your health stats"
                        >
                            <Ionicons name="fitness" size={rf(20)} color={COLORS.muted} />
                            <Text style={{ fontSize: rf(10), color: COLORS.muted, marginTop: 2 }}>{t('stats')}</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={{ alignItems: 'center' }}
                            onPress={() => router.push('/shop' as any)}
                            accessibilityRole="button"
                            accessibilityLabel="Shop"
                            accessibilityHint="Opens the shop and services"
                        >
                            <Ionicons name="cart" size={rf(20)} color={COLORS.muted} />
                            <Text style={{ fontSize: rf(10), color: COLORS.muted, marginTop: 2 }}>{t('shop', { defaultValue: 'Shop' })}</Text>
                        </TouchableOpacity>
                        <TouchableOpacity
                            style={{ alignItems: 'center' }}
                            onPress={() => router.push('/settings' as any)}
                            accessibilityRole="button"
                            accessibilityLabel="Settings"
                            accessibilityHint="Opens settings"
                        >
                            <Ionicons name="settings-sharp" size={rf(20)} color={COLORS.muted} />
                            <Text style={{ fontSize: rf(10), color: COLORS.muted, marginTop: 2 }}>{t('settings')}</Text>
                        </TouchableOpacity>
                    </View>
                </View>
            </View>
        </SafeAreaView>
    );
}
