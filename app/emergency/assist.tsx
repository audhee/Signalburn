import { hp, rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { StorageService } from '@/services/storage';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useKeepAwake } from 'expo-keep-awake';
import * as Linking from 'expo-linking';
import * as Location from 'expo-location';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Alert, Platform, SafeAreaView, ScrollView, StatusBar, Text, TouchableOpacity, View } from 'react-native';

export default function EmergencyAssist() {
    const router = useRouter();
    const { t } = useTranslation();
    const [userName, setUserName] = useState('');
    useKeepAwake();

    useEffect(() => {
        // Vibrate heavily on entry
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {
            // Haptics can be unavailable on some devices (e.g., web/simulators). Not user-blocking.
        });

        // Load user name
        async function loadProfile() {
            const profile = await StorageService.getUserProfile();
            if (profile?.name) {
                setUserName(profile.name);
            }
        }
        loadProfile();
    }, []);

    const safeCall = async (digits: string, label: string) => {
        const phoneDigits = digits.replace(/\D/g, '');
        const phoneUrl = `tel:${phoneDigits}`;
        try {
            const canOpen = await Linking.canOpenURL(phoneUrl);
            if (!canOpen) {
                Alert.alert(
                    `Cannot call ${label}`,
                    'Calling is not supported on this device. Please dial manually or contact a caregiver.'
                );
                return;
            }
            await Linking.openURL(phoneUrl);
        } catch {
            Alert.alert(
                `Call failed`,
                `We could not start the call to ${label}. Please dial manually or contact a caregiver.`
            );
        }
    };

    const callAmbulance = async () => {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy).catch(() => {
            // Non-blocking if haptics fail.
        });

        await safeCall('108', 'ambulance (108)');
    };

    const notifyFamily = async () => {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy).catch(() => { });

        try {
            // 1. Get Location
            let { status } = await Location.requestForegroundPermissionsAsync();
            if (status !== 'granted') {
                Alert.alert('Permission Denied', 'Location permission is required to send your location to your family.');
                return;
            }

            let location = await Location.getCurrentPositionAsync({});
            const { latitude, longitude } = location.coords;
            const mapsUrl = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;
            const message = t('sos_message_with_location', {
                defaultValue: `SOS! I need help. My location: ${mapsUrl}`,
                url: mapsUrl
            });

            // 2. Get Contacts
            const contacts = await StorageService.getEmergencyContacts();

            if (contacts.length === 0) {
                Alert.alert('No contacts set', 'Please add emergency contacts in settings.');
                return;
            }

            // Join all numbers with platform-specific separator
            const separator = Platform.OS === 'ios' ? ',' : ';';
            const recipients = contacts.map(c => c.phone.replace(/\D/g, '')).join(separator);

            // 3. Send SMS (Open SMS app with link)
            const smsUrl = `sms:${recipients}${Platform.OS === 'ios' ? '&' : '?'}body=${encodeURIComponent(message)}`;
            await Linking.openURL(smsUrl);

            // 4. Show location screen flow
            router.push('/emergency/location');
        } catch (e) {
            console.error('Failed to notify family', e);
            Alert.alert('Error', 'Could not send location. Please try calling directly.');
        }
    };

    const callDoctorOrFamily = async () => {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy).catch(() => { });

        try {
            const contacts = await StorageService.getEmergencyContacts();

            // 1. Look for Doctor
            const doctor =
                contacts.find((c) => (c.relation || '').toLowerCase().includes('doctor')) ||
                contacts.find((c) => (c.name || '').toLowerCase().includes('doctor'));

            if (doctor?.phone) {
                await safeCall(doctor.phone, doctor.name || 'Doctor');
                return;
            }

            // 2. Fallback to Primary or First contact
            const fallback = contacts.find((c) => c.isPrimary) || contacts[0];

            if (!fallback?.phone) {
                Alert.alert(
                    'No contact found',
                    'Please add a doctor or family contact in Emergency Contacts.',
                    [
                        { text: 'Cancel', style: 'cancel' },
                        { text: 'Add now', onPress: () => router.push('/setup/contacts' as any) },
                    ]
                );
                return;
            }

            await safeCall(fallback.phone, fallback.name || 'Emergency Contact');
        } catch {
            Alert.alert(
                'Call unavailable',
                'We could not load your contacts. Please check Emergency Contacts in Settings.'
            );
        }
    };

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }}>
            <StatusBar barStyle="dark-content" />

            {/* Top Bar */}
            <View style={{ paddingHorizontal: SPACING.m, paddingTop: SPACING.xl, paddingBottom: SPACING.m, alignItems: 'center', borderBottomWidth: 1, borderBottomColor: '#E5E7EB', backgroundColor: 'white' }}>
                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <Ionicons name="warning" size={rf(20)} color={COLORS.success} />
                    <Text style={{ fontSize: rf(14), fontWeight: '700', color: COLORS.text, marginLeft: SPACING.s }}>{t('emergency_assistant')}</Text>
                </View>
                <Text style={{ fontSize: rf(12), color: COLORS.muted, marginTop: SPACING.xs }}>{t('hi_user', { name: userName || 'User' })}</Text>
            </View>

            <ScrollView style={{ flex: 1 }} contentContainerStyle={{ flexGrow: 1, padding: SPACING.l, paddingBottom: SPACING.xl }}>
                <View style={{ width: '100%', maxWidth: 500, alignSelf: 'center', flex: 1, justifyContent: 'space-between' }}>

                    <View>
                        {/* Main Call Button */}
                        <TouchableOpacity
                            style={{
                                backgroundColor: COLORS.error, borderRadius: RADIUS.xl, padding: SPACING.m,
                                alignItems: 'center', justifyContent: 'center',
                                height: hp(32), maxHeight: 300, minHeight: 220, width: '100%',
                                shadowColor: COLORS.error, shadowOffset: { width: 0, height: 10 }, shadowOpacity: 0.4, shadowRadius: 20, elevation: 10,
                                marginBottom: SPACING.m
                            }}
                            onPress={callAmbulance}
                            accessibilityRole="button"
                            accessibilityLabel="Call ambulance"
                            accessibilityHint="Starts a phone call to emergency services"
                        >
                            <View style={{ width: rf(60), height: rf(60), borderRadius: rf(30), backgroundColor: 'white', alignItems: 'center', justifyContent: 'center', marginBottom: SPACING.s }}>
                                <Ionicons name="medical" size={rf(32)} color={COLORS.error} />
                            </View>
                            <Text style={{ fontSize: rf(32), fontWeight: '900', color: 'white' }}>{t('call_911')}</Text>
                            <Text style={{ fontSize: rf(14), color: 'white', opacity: 0.9, marginTop: SPACING.xs }}>{t('ambulance').toUpperCase()}</Text>

                            <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.2)', paddingHorizontal: SPACING.m, paddingVertical: SPACING.xs, borderRadius: RADIUS.full, marginTop: SPACING.m }}>
                                <Ionicons name="call" size={rf(14)} color="white" style={{ marginRight: SPACING.s }} />
                                <Text style={{ color: 'white', fontWeight: 'bold', fontSize: rf(14) }}>{t('press_to_call')}</Text>
                            </View>
                        </TouchableOpacity>

                        {/* Secondary Contacts */}
                        <View style={{ flexDirection: 'row', gap: SPACING.m, height: hp(14), minHeight: 100, maxHeight: 120 }}>
                            <TouchableOpacity
                                style={{
                                    flex: 1, backgroundColor: COLORS.success, borderRadius: RADIUS.l,
                                    alignItems: 'center', justifyContent: 'center', ...SHADOWS.medium
                                }}
                                onPress={notifyFamily} // Notify family via SMS with location
                                accessibilityRole="button"
                                accessibilityLabel="Notify family"
                                accessibilityHint="Sends your location to your emergency contacts"
                            >
                                <Ionicons name="people" size={rf(28)} color="white" />
                                <Text style={{ color: 'white', fontWeight: '800', marginTop: SPACING.s, fontSize: rf(14) }}>{t('family').toUpperCase()}</Text>
                            </TouchableOpacity>

                            <TouchableOpacity
                                style={{
                                    flex: 1, backgroundColor: '#8B5CF6', borderRadius: RADIUS.l,
                                    alignItems: 'center', justifyContent: 'center', ...SHADOWS.medium
                                }}
                                onPress={callDoctorOrFamily}
                                accessibilityRole="button"
                                accessibilityLabel="Call doctor or family"
                                accessibilityHint="Calls your doctor, or primary contact if no doctor is set"
                            >
                                <Ionicons name="medkit" size={rf(28)} color="white" />
                                <Text style={{ color: 'white', fontWeight: '800', marginTop: SPACING.s, fontSize: rf(14) }}>{t('doctor', 'DOCTOR')}</Text>
                            </TouchableOpacity>
                        </View>

                        {/* AI Guidance */}
                        <TouchableOpacity
                            style={{
                                marginTop: SPACING.m, backgroundColor: 'white', padding: SPACING.m, borderRadius: RADIUS.l,
                                flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
                                borderWidth: 1, borderColor: '#E5E7EB', ...SHADOWS.light
                            }}
                            onPress={() => router.push('/emergency/ai-guidance')}
                            accessibilityRole="button"
                            accessibilityLabel="AI voice guidance"
                            accessibilityHint="Opens step-by-step CPR and first aid guidance"
                        >
                            <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                <View style={{ width: rf(36), height: rf(36), borderRadius: rf(18), backgroundColor: '#E0F2FE', alignItems: 'center', justifyContent: 'center', marginRight: SPACING.m }}>
                                    <Ionicons name="mic" size={rf(20)} color={COLORS.primary} />
                                </View>
                                <View>
                                    <Text style={{ fontSize: rf(15), fontWeight: '700', color: COLORS.text }}>{t('ai_guidance')}</Text>
                                    <Text style={{ fontSize: rf(12), color: COLORS.muted }}>{t('cpr_first_aid')}</Text>
                                </View>
                            </View>
                            <Ionicons name="chevron-forward" size={rf(20)} color={COLORS.muted} />
                        </TouchableOpacity>
                    </View>

                    {/* Cancel / Safe Button */}
                    <TouchableOpacity
                        style={{
                            marginTop: SPACING.l,
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: SPACING.s,
                            marginBottom: SPACING.s
                        }}
                        onPress={() => router.back()}
                        accessibilityRole="button"
                        accessibilityLabel="Cancel SOS"
                    >
                        <Text style={{ fontSize: rf(16), fontWeight: '700', color: COLORS.muted }}>
                            {t('cancel_sos', 'Cancel SOS / I am Safe')}
                        </Text>
                    </TouchableOpacity>
                </View>
            </ScrollView>
        </SafeAreaView >
    );
}
