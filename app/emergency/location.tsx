import { hp, rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';
import * as Linking from 'expo-linking';
import { useRouter } from 'expo-router';
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StorageService } from '@/services/storage';
import { Image, SafeAreaView, ScrollView, StatusBar, Text, TouchableOpacity, View } from 'react-native';

export default function LocationScreen() {
    const router = useRouter();
    const { t } = useTranslation();
    const [eta, setEta] = useState(285); // 4:45 in seconds

    const [contacts, setContacts] = useState<any[]>([]);

    useEffect(() => {
        const interval = setInterval(() => {
            setEta((prev) => (prev > 0 ? prev - 1 : 0));
        }, 1000);

        async function loadContacts() {
            const saved = await StorageService.getEmergencyContacts();
            if (saved && Array.isArray(saved)) {
                setContacts(saved);
            }
        }
        loadContacts();

        return () => clearInterval(interval);
    }, []);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')} : ${secs.toString().padStart(2, '0')}`;
    };

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: '#F9FAFB' }}>
            <StatusBar barStyle="dark-content" />

            {/* Map Area */}
            <View style={{ height: hp(45), width: '100%', backgroundColor: '#E5E7EB', position: 'relative' }}>
                {/* Map Placeholder */}
                <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
                    <Ionicons name="map" size={rf(64)} color={COLORS.muted} opacity={0.5} />
                </View>

                {/* Back Button */}
                <TouchableOpacity style={{ position: 'absolute', top: SPACING.xl, left: SPACING.l, backgroundColor: 'white', padding: SPACING.s, borderRadius: RADIUS.full, ...SHADOWS.light }} onPress={() => router.back()}>
                    <Ionicons name="arrow-back" size={rf(24)} color={COLORS.text} />
                </TouchableOpacity>

                {/* Location Pulse */}
                <View style={{ position: 'absolute', top: '50%', left: '50%', marginTop: -rf(40), marginLeft: -rf(40) }}>
                    <View style={{ width: rf(80), height: rf(80), borderRadius: rf(40), backgroundColor: 'rgba(59, 130, 246, 0.2)', alignItems: 'center', justifyContent: 'center' }}>
                        <View style={{ width: rf(40), height: rf(40), borderRadius: rf(20), backgroundColor: 'rgba(59, 130, 246, 0.4)', alignItems: 'center', justifyContent: 'center' }}>
                            <View style={{ width: rf(20), height: rf(20), borderRadius: rf(10), backgroundColor: COLORS.primary, borderWidth: 2, borderColor: 'white' }} />
                        </View>
                    </View>
                </View>
            </View>

            <View style={{ flex: 1, backgroundColor: 'white', borderTopLeftRadius: RADIUS.xl, borderTopRightRadius: RADIUS.xl, marginTop: -SPACING.xl, ...SHADOWS.medium, overflow: 'hidden' }}>
                <ScrollView contentContainerStyle={{ padding: SPACING.l, flexGrow: 1 }}>
                    {/* Status Header */}
                    <View style={{ alignItems: 'center', marginTop: SPACING.s }}>
                        <View style={{ width: rf(40), height: rf(4), backgroundColor: '#E5E7EB', borderRadius: rf(2), marginBottom: SPACING.l }} />
                        <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: '#DCFCE7', paddingHorizontal: SPACING.m, paddingVertical: SPACING.xs, borderRadius: RADIUS.full, marginBottom: SPACING.m }}>
                            <Ionicons name="checkmark-circle" size={rf(16)} color={COLORS.success} style={{ marginRight: SPACING.s }} />
                            <Text style={{ color: COLORS.success, fontWeight: '700', fontSize: rf(14) }}>Location Sent</Text>
                        </View>
                        <Text style={{ fontSize: rf(14), color: COLORS.muted }}>Your location has been shared with all your emergency contacts. Help is arriving shortly.</Text>
                    </View>

                    {/* Timer Card */}
                    <View style={{ backgroundColor: '#FEF2F2', borderRadius: RADIUS.l, padding: SPACING.m, marginVertical: SPACING.l, alignItems: 'center', borderLeftWidth: 4, borderLeftColor: COLORS.error }}>
                        <Text style={{ fontSize: rf(14), fontWeight: '700', color: COLORS.error, marginBottom: SPACING.xs }}>ALERT ACTIVE</Text>
                        <Text style={{ fontSize: rf(16), color: COLORS.text }}>Help is arriving in</Text>
                        <Text style={{ fontSize: rf(32), fontWeight: '900', color: COLORS.text, marginTop: SPACING.xs }}>{formatTime(eta)}</Text>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', width: '60%', marginTop: SPACING.xs }}>
                            <Text style={{ fontSize: rf(10), color: COLORS.muted }}>MINUTES</Text>
                            <Text style={{ fontSize: rf(10), color: COLORS.muted }}>SECONDS</Text>
                        </View>
                    </View>

                    <Text style={{ fontSize: rf(12), fontWeight: '700', color: COLORS.muted, marginBottom: SPACING.m }}>NOTIFIED CONTACTS</Text>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: SPACING.l, marginBottom: SPACING.xl }}>
                        {/* Always show Emergency Services first */}
                        <View style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: '#FEF2F2', padding: SPACING.s, borderRadius: RADIUS.m, borderWidth: 1, borderColor: '#FEE2E2' }}>
                            <View style={{ width: rf(40), height: rf(40), borderRadius: rf(20), backgroundColor: COLORS.error, alignItems: 'center', justifyContent: 'center', marginRight: SPACING.s }}>
                                <Text style={{ color: 'white', fontWeight: 'bold', fontSize: rf(12) }}>108</Text>
                            </View>
                            <View>
                                <Text style={{ fontSize: rf(14), fontWeight: '700', color: COLORS.text }}>Ambulance</Text>
                                <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                    <View style={{ width: rf(6), height: rf(6), borderRadius: rf(3), backgroundColor: COLORS.success, marginRight: SPACING.xs }} />
                                    <Text style={{ fontSize: rf(12), color: COLORS.muted }}>On way</Text>
                                </View>
                            </View>
                        </View>

                        {/* Map over real user contacts */}
                        {contacts.map((contact, idx) => (
                            <View key={contact.id || idx} style={{ flexDirection: 'row', alignItems: 'center', backgroundColor: COLORS.card, padding: SPACING.s, borderRadius: RADIUS.m, borderWidth: 1, borderColor: COLORS.border }}>
                                <View style={{ width: rf(40), height: rf(40), borderRadius: rf(20), backgroundColor: '#E0E7FF', alignItems: 'center', justifyContent: 'center', marginRight: SPACING.s }}>
                                    <Ionicons name="person" size={rf(20)} color={COLORS.primary} />
                                </View>
                                <View>
                                    <Text style={{ fontSize: rf(14), fontWeight: '700', color: COLORS.text }}>{contact.name || contact.relation}</Text>
                                    <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                                        <View style={{ width: rf(6), height: rf(6), borderRadius: rf(3), backgroundColor: COLORS.success, marginRight: SPACING.xs }} />
                                        <Text style={{ fontSize: rf(12), color: COLORS.muted }}>Alerted</Text>
                                    </View>
                                </View>
                            </View>
                        ))}
                    </ScrollView>

                    <View style={{ flexDirection: 'row', gap: SPACING.m }}>
                        <TouchableOpacity
                            style={{ flex: 1, backgroundColor: '#EFF6FF', borderRadius: RADIUS.full, padding: SPACING.m, alignItems: 'center' }}
                            onPress={() => Linking.openURL('tel:911')}
                        >
                            <Text style={{ color: COLORS.primary, fontWeight: '700', fontSize: rf(16) }}>Call Emergency</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={{ flex: 1, backgroundColor: COLORS.error, borderRadius: RADIUS.full, padding: SPACING.m, alignItems: 'center' }}
                            onPress={() => router.push('/emergency/safe')}
                        >
                            <Text style={{ color: 'white', fontWeight: '700', fontSize: rf(16) }}>I AM SAFE</Text>
                        </TouchableOpacity>
                    </View>
                </ScrollView>
            </View>
        </SafeAreaView>
    );
}

