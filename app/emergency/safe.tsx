import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { SafeAreaView, StatusBar, Text, TouchableOpacity, View } from 'react-native';

export default function SafeScreen() {
    const router = useRouter();
    const { t } = useTranslation();

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }}>
            <StatusBar barStyle="dark-content" />
            <View style={{ flex: 1, padding: SPACING.l, alignItems: 'center', justifyContent: 'center', width: '100%', maxWidth: 500, alignSelf: 'center' }}>

                <View style={{
                    width: rf(160), height: rf(160), borderRadius: rf(80), backgroundColor: '#DCFCE7',
                    alignItems: 'center', justifyContent: 'center', marginBottom: SPACING.xl,
                    ...SHADOWS.medium
                }}>
                    <Ionicons name="checkmark-circle" size={rf(100)} color={COLORS.success} />
                </View>

                <Text style={{ fontSize: rf(32), fontWeight: '900', color: COLORS.success, marginBottom: SPACING.s }}>
                    YOU ARE SAFE
                </Text>

                <View style={{ backgroundColor: '#FEE2E2', paddingHorizontal: SPACING.m, paddingVertical: SPACING.xs, borderRadius: RADIUS.full, marginBottom: SPACING.xl }}>
                    <Text style={{ color: COLORS.error, fontWeight: '700', fontSize: rf(14) }}>EMERGENCY ALERT ENDED</Text>
                </View>

                <Text style={{ fontSize: rf(16), color: COLORS.muted, textAlign: 'center', paddingHorizontal: SPACING.l, marginBottom: SPACING.xxl }}>
                    We have notified your emergency contacts and responders that you are safe.
                </Text>

                <TouchableOpacity
                    style={{
                        backgroundColor: COLORS.primary, paddingVertical: SPACING.l, paddingHorizontal: SPACING.xxl,
                        borderRadius: RADIUS.full, width: '100%', alignItems: 'center', ...SHADOWS.medium
                    }}
                    onPress={() => router.replace('/home')}
                >
                    <Text style={{ color: 'white', fontSize: rf(18), fontWeight: 'bold' }}>Return to Home</Text>
                </TouchableOpacity>
            </View>
        </SafeAreaView>
    );
}
