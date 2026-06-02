import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { StorageService } from '@/services/storage';
import { apiClient } from '@/services/apiClient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useMemo, useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, Switch, Text, TextInput, TouchableOpacity, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

type Contact = {
    id: string;
    name: string;
    relation: string;
    phone: string; // digits only recommended
    age?: string;
    isPrimary: boolean;
};

export default function EmergencyContacts() {
    const router = useRouter();
    const [contacts, setContacts] = useState<Contact[]>([]);
    const [loading, setLoading] = useState(true);

    const [showAdd, setShowAdd] = useState(false);
    const [newName, setNewName] = useState('');
    const [newRelation, setNewRelation] = useState('');
    const [newPhone, setNewPhone] = useState('');
    const [newAge, setNewAge] = useState('');
    const [nameError, setNameError] = useState('');
    const [relationError, setRelationError] = useState('');
    const [ageError, setAgeError] = useState('');
    const [phoneError, setPhoneError] = useState('');

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                const parsed = await StorageService.getEmergencyContacts();
                if (cancelled) return;
                if (Array.isArray(parsed)) setContacts(parsed);
            } catch {
                // If storage is corrupted/unavailable, start fresh (don't block setup).
                setContacts([]);
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => {
            cancelled = true;
        };
    }, []);

    const contactsCountLabel = useMemo(() => `${contacts.length} of 3 contacts added`, [contacts.length]);

    const persist = async (next: Contact[]) => {
        setContacts(next);
        try {
            await StorageService.saveEmergencyContacts(next);
            
            // Sync to PostgreSQL backend via PUT /contacts
            try {
                const apiPayload = next.map(c => ({
                    name: c.name,
                    phone_number: c.phone,
                    relationship: c.relation
                }));
                await apiClient.put('/api/v1/user/contacts', apiPayload);
            } catch (e) {
                console.error('Failed to sync contacts to backend:', e);
            }
        } catch {
            // Persist failure shouldn't block UI, but warn so user knows it may not save.
            Alert.alert('Not saved', 'Your contacts could not be saved on this device. Please try again.');
        }
    };

    const setPrimary = async (id: string, isPrimary: boolean) => {
        const next = contacts.map((c) => (c.id === id ? { ...c, isPrimary } : { ...c, isPrimary: false }));
        await persist(next);
    };

    const addContact = async () => {
        if (contacts.length >= 3) {
            Alert.alert('Limit reached', 'You can add up to 3 emergency contacts.');
            return;
        }
        const name = newName.trim();
        const relation = newRelation.trim();
        const ageVal = newAge.trim();
        const phoneVal = newPhone.trim();

        // Clear previous errors
        setNameError('');
        setRelationError('');
        setAgeError('');
        setPhoneError('');

        if (!name || !relation || !ageVal || !phoneVal) {
            if (!name) setNameError('Please fill all the fields correctly.');
            if (!relation) setRelationError('Please fill all the fields correctly.');
            if (!ageVal) setAgeError('Please fill all the fields correctly.');
            if (!phoneVal) setPhoneError('Please fill all the fields correctly.');
            return;
        }

        const nameRegex = /^[a-zA-Z\s]+$/;
        if (!nameRegex.test(name)) {
            setNameError('enter in alphabets only');
            return;
        }

        const ageRegex = /^[0-9]+$/;
        if (!ageRegex.test(ageVal)) {
            setAgeError('enter in numbers');
            return;
        }

        const phoneRegex = /^[0-9]+$/;
        if (!phoneRegex.test(phoneVal)) {
            setPhoneError('enter in numbers');
            return;
        }

        if (phoneVal.length < 8) {
            setPhoneError('Please enter a valid phone number.');
            return;
        }

        const nextContact: Contact = {
            id: `${Date.now()}`,
            name,
            relation,
            phone: phoneVal,
            age: ageVal,
            isPrimary: contacts.length === 0, // first contact defaults to primary
        };
        const next = [...contacts, nextContact].map((c) => ({ ...c, isPrimary: nextContact.isPrimary ? c.id === nextContact.id : c.isPrimary }));
        await persist(next);

        setNewName('');
        setNewRelation('');
        setNewPhone('');
        setNewAge('');
        setNameError('');
        setRelationError('');
        setAgeError('');
        setPhoneError('');
        setShowAdd(false);
    };

    const removeContact = async (id: string) => {
        const removedWasPrimary = contacts.find((c) => c.id === id)?.isPrimary;
        let next = contacts.filter((c) => c.id !== id);
        if (removedWasPrimary && next.length > 0) {
            next = next.map((c, idx) => ({ ...c, isPrimary: idx === 0 }));
        }
        await persist(next);
    };

    return (
        <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: SPACING.l, paddingTop: SPACING.xl, paddingBottom: SPACING.l, borderBottomWidth: 1, borderBottomColor: COLORS.border }}>
                <TouchableOpacity onPress={() => router.back()}>
                    <Ionicons name="arrow-back" size={rf(24)} color={COLORS.text} />
                </TouchableOpacity>
                <Text style={{ fontSize: rf(18), fontWeight: '700', marginLeft: SPACING.m, color: COLORS.text }}>Setup</Text>
            </View>

            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={{ flex: 1 }}
                keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
            >
                <ScrollView contentContainerStyle={{ flexGrow: 1, padding: SPACING.l, width: '100%', maxWidth: 500, alignSelf: 'center' }}>
                    <Text style={{ fontSize: rf(22), marginBottom: SPACING.s, fontWeight: '800', color: COLORS.text }}>
                        Emergency Contacts
                    </Text>
                    <Text style={{ fontSize: rf(16), color: COLORS.muted, marginBottom: SPACING.xl }}>
                        Add up to 3 people to notify in an emergency. We will alert them immediately when you press SOS.
                    </Text>

                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: SPACING.m }}>
                        <Text style={{ fontSize: rf(14), fontWeight: '600', color: COLORS.muted }}>
                            {loading ? 'Loading…' : contactsCountLabel}
                        </Text>
                        <TouchableOpacity onPress={() => setShowAdd((v) => !v)} accessibilityRole="button" accessibilityLabel="Add contact">
                            <Text style={{ fontSize: rf(14), fontWeight: '700', color: COLORS.primary }}>+ Add Contact</Text>
                        </TouchableOpacity>
                    </View>

                    {showAdd && (
                        <View
                            style={{
                                backgroundColor: COLORS.card,
                                borderRadius: RADIUS.m,
                                padding: SPACING.m,
                                marginBottom: SPACING.l,
                                borderWidth: 1,
                                borderColor: COLORS.border,
                                ...SHADOWS.light,
                            }}
                        >
                            <Text style={{ fontSize: rf(16), fontWeight: '800', color: COLORS.text, marginBottom: SPACING.m }}>Add Contact</Text>

                            <Text style={{ fontSize: rf(14), fontWeight: '700', color: COLORS.text, marginBottom: SPACING.xs }}>Name <Text style={{ color: COLORS.error }}>*</Text></Text>
                            <TextInput
                                value={newName}
                                onChangeText={(text) => {
                                    setNewName(text);
                                    if (/[^a-zA-Z\s]/.test(text)) {
                                        setNameError('enter in alphabets only');
                                    } else {
                                        setNameError('');
                                    }
                                }}
                                placeholder="e.g., Raj Kumar"
                                placeholderTextColor={COLORS.muted}
                                style={{ borderWidth: 1, borderColor: nameError ? COLORS.error : COLORS.border, borderRadius: RADIUS.m, padding: SPACING.m, backgroundColor: COLORS.background, marginBottom: SPACING.xs, fontSize: rf(16) }}
                            />
                            {nameError ? (
                                <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: SPACING.m }}>
                                    <Ionicons name="alert-circle" size={rf(14)} color={COLORS.error} style={{ marginRight: 4 }} />
                                    <Text style={{ color: COLORS.error, fontSize: rf(12), fontWeight: '600' }}>{nameError}</Text>
                                </View>
                            ) : (
                                <View style={{ marginBottom: SPACING.m }} />
                            )}

                            <Text style={{ fontSize: rf(14), fontWeight: '700', color: COLORS.text, marginBottom: SPACING.xs }}>Relation <Text style={{ color: COLORS.error }}>*</Text></Text>
                            <TextInput
                                value={newRelation}
                                onChangeText={(text) => {
                                    setNewRelation(text);
                                    if (relationError) setRelationError('');
                                }}
                                placeholder="e.g., Son / Daughter / Doctor"
                                placeholderTextColor={COLORS.muted}
                                style={{ borderWidth: 1, borderColor: relationError ? COLORS.error : COLORS.border, borderRadius: RADIUS.m, padding: SPACING.m, backgroundColor: COLORS.background, marginBottom: SPACING.xs, fontSize: rf(16) }}
                            />
                            {relationError ? (
                                <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: SPACING.m }}>
                                    <Ionicons name="alert-circle" size={rf(14)} color={COLORS.error} style={{ marginRight: 4 }} />
                                    <Text style={{ color: COLORS.error, fontSize: rf(12), fontWeight: '600' }}>{relationError}</Text>
                                </View>
                            ) : (
                                <View style={{ marginBottom: SPACING.m }} />
                            )}

                            <Text style={{ fontSize: rf(14), fontWeight: '700', color: COLORS.text, marginBottom: SPACING.xs }}>Age <Text style={{ color: COLORS.error }}>*</Text></Text>
                            <TextInput
                                value={newAge}
                                onChangeText={(text) => {
                                    setNewAge(text);
                                    if (/[^0-9]/.test(text)) {
                                        setAgeError('enter in numbers');
                                    } else {
                                        setAgeError('');
                                    }
                                }}
                                placeholder="e.g., 45"
                                placeholderTextColor={COLORS.muted}
                                keyboardType="default"
                                style={{ borderWidth: 1, borderColor: ageError ? COLORS.error : COLORS.border, borderRadius: RADIUS.m, padding: SPACING.m, backgroundColor: COLORS.background, marginBottom: SPACING.xs, fontSize: rf(16) }}
                            />
                            {ageError ? (
                                <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: SPACING.m }}>
                                    <Ionicons name="alert-circle" size={rf(14)} color={COLORS.error} style={{ marginRight: 4 }} />
                                    <Text style={{ color: COLORS.error, fontSize: rf(12), fontWeight: '600' }}>{ageError}</Text>
                                </View>
                            ) : (
                                <View style={{ marginBottom: SPACING.m }} />
                            )}

                            <Text style={{ fontSize: rf(14), fontWeight: '700', color: COLORS.text, marginBottom: SPACING.xs }}>Phone <Text style={{ color: COLORS.error }}>*</Text></Text>
                            <TextInput
                                value={newPhone}
                                onChangeText={(text) => {
                                    setNewPhone(text);
                                    if (/[^0-9]/.test(text)) {
                                        setPhoneError('enter in numbers');
                                    } else {
                                        setPhoneError('');
                                    }
                                }}
                                placeholder="Phone number"
                                placeholderTextColor={COLORS.muted}
                                keyboardType="default"
                                style={{ borderWidth: 1, borderColor: phoneError ? COLORS.error : COLORS.border, borderRadius: RADIUS.m, padding: SPACING.m, backgroundColor: COLORS.background, marginBottom: SPACING.xs, fontSize: rf(16) }}
                            />
                            {phoneError ? (
                                <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: SPACING.m }}>
                                    <Ionicons name="alert-circle" size={rf(14)} color={COLORS.error} style={{ marginRight: 4 }} />
                                    <Text style={{ color: COLORS.error, fontSize: rf(12), fontWeight: '600' }}>{phoneError}</Text>
                                </View>
                            ) : (
                                <View style={{ marginBottom: SPACING.m }} />
                            )}

                            <View style={{ flexDirection: 'row', gap: SPACING.m }}>
                                <TouchableOpacity
                                    style={{ flex: 1, backgroundColor: COLORS.border, padding: SPACING.m, borderRadius: RADIUS.full, alignItems: 'center' }}
                                    onPress={() => setShowAdd(false)}
                                    accessibilityRole="button"
                                    accessibilityLabel="Cancel adding contact"
                                >
                                    <Text style={{ fontWeight: '800', color: COLORS.text, fontSize: rf(14) }}>Cancel</Text>
                                </TouchableOpacity>
                                <TouchableOpacity
                                    style={{ flex: 1, backgroundColor: COLORS.primary, padding: SPACING.m, borderRadius: RADIUS.full, alignItems: 'center' }}
                                    onPress={addContact}
                                    accessibilityRole="button"
                                    accessibilityLabel="Save contact"
                                >
                                    <Text style={{ fontWeight: '800', color: 'white', fontSize: rf(14) }}>Save</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                    )}

                    {contacts.map((c) => (
                        <View
                            key={c.id}
                            style={{
                                backgroundColor: COLORS.card,
                                borderRadius: RADIUS.m,
                                padding: SPACING.m,
                                marginBottom: SPACING.l,
                                borderWidth: 1,
                                borderColor: COLORS.border,
                                ...SHADOWS.light,
                            }}
                        >
                            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: SPACING.m }}>
                                <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1, marginRight: SPACING.s }}>
                                    <View style={{ width: rf(48), height: rf(48), borderRadius: rf(24), backgroundColor: '#E0E7FF', alignItems: 'center', justifyContent: 'center', marginRight: SPACING.m, overflow: 'hidden' }}>
                                        <Ionicons name="person-circle" size={rf(44)} color={COLORS.primary} />
                                    </View>
                                    <View style={{ flex: 1 }}>
                                        <Text style={{ fontSize: rf(16), fontWeight: '800', color: COLORS.text }} numberOfLines={1}>{c.name}</Text>
                                        <Text style={{ fontSize: rf(14), color: COLORS.muted }} numberOfLines={1}>{c.relation} {c.age ? `(Age: ${c.age})` : ''}</Text>
                                        <Text style={{ fontSize: rf(12), color: COLORS.muted, marginTop: 2 }}>+{c.phone}</Text>
                                    </View>
                                </View>

                                <TouchableOpacity
                                    onPress={() => removeContact(c.id)}
                                    hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                                    style={{
                                        backgroundColor: '#FEE2E2', // Light red bg
                                        padding: SPACING.s,
                                        borderRadius: RADIUS.full,
                                        width: rf(44), height: rf(44),
                                        alignItems: 'center', justifyContent: 'center'
                                    }}
                                    accessibilityRole="button"
                                    accessibilityLabel={`Remove contact ${c.name}`}
                                >
                                    <Ionicons name="trash" size={rf(20)} color={COLORS.error} />
                                </TouchableOpacity>
                            </View>

                            <View style={{ height: 1, backgroundColor: COLORS.border, marginBottom: SPACING.m }} />

                            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: SPACING.m }}>
                                <Text style={{ fontSize: rf(16), fontWeight: '700', color: COLORS.text }}>Primary SOS Contact</Text>
                                <Switch
                                    trackColor={{ false: COLORS.muted, true: COLORS.primary }}
                                    thumbColor={'#fff'}
                                    ios_backgroundColor="#3e3e3e"
                                    onValueChange={(v) => setPrimary(c.id, v)}
                                    value={c.isPrimary}
                                    accessibilityLabel={`Set ${c.name} as primary contact`}
                                />
                            </View>
                            <Text style={{ fontSize: rf(12), color: COLORS.muted, marginTop: -SPACING.s, marginBottom: SPACING.m }}>
                                This person will be called first.
                            </Text>
                        </View>
                    ))}

                    <View style={{ flex: 1 }} />

                    <TouchableOpacity
                        style={{
                            backgroundColor: COLORS.primary, padding: SPACING.m, borderRadius: RADIUS.full,
                            marginBottom: SPACING.l, ...SHADOWS.medium
                        }}
                        onPress={() => router.push('/home' as any)}
                    >
                        <Text style={{ color: 'white', textAlign: 'center', fontSize: rf(18), fontWeight: 'bold' }}>
                            Save & Continue
                        </Text>
                    </TouchableOpacity>
                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}
