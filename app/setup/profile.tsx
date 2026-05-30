import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { StorageService } from '@/services/storage';
import { apiClient } from '@/services/apiClient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function ProfileSetup() {
    const router = useRouter();
    const { t } = useTranslation();
    const [selectedConditions, setSelectedConditions] = useState<string[]>([]);
    const [name, setName] = useState('');
    const [age, setAge] = useState('');
    const [otherCondition, setOtherCondition] = useState('');

    const CONDITIONS = [
        'Diabetes',
        'High blood pressure',
        'Heart condition',
        'Asthma',
        'Stroke history',
        'Epilepsy',
        'Arthritis',
        'Kidney disease',
        'Allergy',
    ];

    const toggleCondition = (name: string) => {
        setSelectedConditions((prev) => (prev.includes(name) ? prev.filter((c) => c !== name) : [...prev, name]));
    };

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: SPACING.l, paddingTop: SPACING.xl, paddingBottom: SPACING.l, borderBottomWidth: 1, borderBottomColor: COLORS.border }}>
                <TouchableOpacity onPress={() => router.back()}>
                    <Ionicons name="arrow-back" size={rf(24)} color={COLORS.text} />
                </TouchableOpacity>
                <Text style={{ fontSize: rf(18), fontWeight: '700', marginLeft: SPACING.m, color: COLORS.text }}>{t('setup')}</Text>
            </View>

            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={{ flex: 1 }}
                keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
            >
                <ScrollView contentContainerStyle={{ flexGrow: 1, padding: SPACING.l, width: '100%', maxWidth: 500, alignSelf: 'center' }}>
                    <Text style={{ fontSize: rf(22), marginBottom: SPACING.s, fontWeight: '800', color: COLORS.text }}>
                        {t('create_profile_title')}
                    </Text>
                    <Text style={{ fontSize: rf(16), color: COLORS.muted, marginBottom: SPACING.xl }}>
                        {t('enter_details_desc')}
                    </Text>

                    <Text style={{ fontSize: rf(16), marginBottom: SPACING.xs, fontWeight: '600', color: COLORS.text }}>{t('full_name')} <Text style={{ color: COLORS.error }}>*</Text></Text>
                    <TextInput
                        placeholder={t('name_placeholder')}
                        placeholderTextColor={COLORS.muted}
                        value={name}
                        onChangeText={(text) => setName(text.replace(/\d/g, ''))}
                        style={{
                            borderWidth: 1, borderColor: COLORS.border, marginBottom: SPACING.l,
                            padding: SPACING.m, borderRadius: RADIUS.m, fontSize: rf(16), backgroundColor: COLORS.card
                        }}
                    />

                    <Text style={{ fontSize: rf(16), marginBottom: SPACING.xs, fontWeight: '600', color: COLORS.text }}>{t('age')}</Text>
                    <TextInput
                        placeholder={t('age_placeholder')}
                        placeholderTextColor={COLORS.muted}
                        keyboardType="numeric"
                        maxLength={3}
                        value={age}
                        onChangeText={(text) => setAge(text.replace(/\D/g, '').slice(0, 3))}
                        style={{
                            borderWidth: 1, borderColor: COLORS.border, marginBottom: SPACING.l,
                            padding: SPACING.m, borderRadius: RADIUS.m, fontSize: rf(16), backgroundColor: COLORS.card
                        }}
                    />

                    <Text style={{ fontSize: rf(16), marginBottom: SPACING.xs, fontWeight: '600', color: COLORS.text }}>{t('health_conditions')}</Text>
                    <View
                        style={{
                            borderWidth: 1,
                            borderColor: COLORS.border,
                            borderRadius: RADIUS.m,
                            backgroundColor: COLORS.card,
                            padding: SPACING.m,
                            marginBottom: SPACING.l,
                        }}
                    >
                        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: SPACING.s }}>
                            {CONDITIONS.map((c) => {
                                const active = selectedConditions.includes(c);
                                return (
                                    <TouchableOpacity
                                        key={c}
                                        onPress={() => toggleCondition(c)}
                                        style={{
                                            paddingVertical: SPACING.s,
                                            paddingHorizontal: SPACING.m,
                                            borderRadius: RADIUS.full,
                                            borderWidth: 1,
                                            borderColor: active ? COLORS.primary : COLORS.border,
                                            backgroundColor: active ? '#EFF6FF' : COLORS.background,
                                        }}
                                        accessibilityRole="button"
                                        accessibilityLabel={`Condition ${c}`}
                                        accessibilityHint={active ? 'Selected' : 'Not selected'}
                                    >
                                        <Text style={{ color: active ? COLORS.primary : COLORS.text, fontWeight: '700', fontSize: rf(14) }}>{c}</Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </View>
                    </View>

                    <Text style={{ fontSize: rf(14), marginBottom: SPACING.xs, fontWeight: '600', color: COLORS.text }}>{t('other_optional')}</Text>
                    <TextInput
                        placeholder={t('other_condition_placeholder')}
                        placeholderTextColor={COLORS.muted}
                        style={{
                            borderWidth: 1,
                            borderColor: COLORS.border,
                            marginBottom: SPACING.xl,
                            padding: SPACING.m,
                            borderRadius: RADIUS.m,
                            fontSize: rf(16),
                            backgroundColor: COLORS.card,
                        }}
                        value={otherCondition}
                        onChangeText={(text) => setOtherCondition(text.replace(/\d/g, ''))}
                    />

                    <View style={{ flex: 1 }} />

                    <TouchableOpacity
                        style={{
                            backgroundColor: COLORS.primary, padding: SPACING.m, borderRadius: RADIUS.full,
                            marginBottom: SPACING.l, ...SHADOWS.medium
                        }}
                        onPress={async () => {
                            if (!name.trim()) {
                                Alert.alert(t('error'), t('name_required'));
                                return;
                            }
                            if (/\d/.test(name)) {
                                Alert.alert(t('error'), 'Name cannot contain numbers.');
                                return;
                            }
                            if (age) {
                                const ageNum = parseInt(age, 10);
                                if (isNaN(ageNum) || ageNum < 0 || ageNum > 100) {
                                    Alert.alert('Invalid age', 'Age must be between 0 and 100.');
                                    return;
                                }
                            }
                            if (otherCondition && /\d/.test(otherCondition)) {
                                Alert.alert('Invalid condition', 'Health condition cannot contain numbers.');
                                return;
                            }
                            const profile = { name, age, conditions: selectedConditions, other: otherCondition };
                            await StorageService.saveUserProfile(profile);

                            // Sync to backend PostgreSQL
                            try {
                                await apiClient.patch('/api/v1/user/profile', {
                                    full_name: name,
                                    age: age ? parseInt(age, 10) : null
                                });

                                await apiClient.put('/api/v1/user/medical', {
                                    conditions: selectedConditions,
                                    other: otherCondition || null
                                });
                            } catch (e) {
                                console.error('Failed to sync profile to backend:', e);
                                Alert.alert('Backend Sync Failed', 'Check your Ngrok URL or Network Connection. Data saved locally only.');
                                // Continues to fallback gracefully offline
                            }

                            router.push('/setup/contacts' as any);
                        }}
                    >
                        <Text style={{ color: 'white', textAlign: 'center', fontSize: rf(18), fontWeight: 'bold' }}>
                            {t('save_profile')}
                        </Text>
                    </TouchableOpacity>
                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}
