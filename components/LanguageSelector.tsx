import Colors from '@/constants/Colors';
import { rf, wp } from '@/constants/responsive';
import { RADIUS, SPACING } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import React from 'react';
import { useTranslation } from 'react-i18next';
import { Modal, StyleSheet, Text, TouchableOpacity, View } from 'react-native';

interface LanguageSelectorProps {
    visible: boolean;
    onClose: () => void;
}

export default function LanguageSelector({ visible, onClose }: LanguageSelectorProps) {
    const { t, i18n } = useTranslation();

    const changeLanguage = async (lang: string) => {
        i18n.changeLanguage(lang);
        await AsyncStorage.setItem('user-language', lang);
        onClose();
    };

    const languages = [
        { code: 'en', label: 'English', native: 'English' },
        { code: 'hi', label: 'Hindi', native: 'हिंदी' },
        { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ' },
    ];

    if (!visible) return null;

    return (
        <Modal
            transparent
            visible={visible}
            animationType="fade"
            onRequestClose={onClose}
        >
            <View style={styles.overlay}>
                <View style={styles.container}>
                    <Text style={styles.title}>{t('change_language')}</Text>

                    {languages.map((lang) => (
                        <TouchableOpacity
                            key={lang.code}
                            style={[
                                styles.option,
                                i18n.language === lang.code && styles.selectedOption
                            ]}
                            onPress={() => changeLanguage(lang.code)}
                        >
                            <View>
                                <Text style={[
                                    styles.nativeText,
                                    i18n.language === lang.code && styles.selectedText
                                ]}>
                                    {lang.native}
                                </Text>
                                <Text style={[
                                    styles.englishText,
                                    i18n.language === lang.code && styles.selectedText
                                ]}>{lang.label}</Text>
                            </View>
                            {i18n.language === lang.code && (
                                <Ionicons name="checkmark-circle" size={rf(24)} color={Colors.light.background} />
                            )}
                        </TouchableOpacity>
                    ))}

                    <TouchableOpacity style={styles.closeButton} onPress={onClose}>
                        <Text style={styles.closeText}>Close</Text>
                    </TouchableOpacity>
                </View>
            </View>
        </Modal>
    );
}

const styles = StyleSheet.create({
    overlay: {
        flex: 1,
        backgroundColor: 'rgba(0,0,0,0.5)',
        justifyContent: 'center',
        alignItems: 'center',
    },
    container: {
        backgroundColor: Colors.light.background,
        borderRadius: RADIUS.l,
        padding: SPACING.l,
        width: wp(85),
        maxWidth: 400,
        elevation: 5,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3.84,
    },
    title: {
        fontSize: rf(20),
        fontWeight: 'bold',
        marginBottom: SPACING.m,
        textAlign: 'center',
        color: '#000',
    },
    option: {
        padding: SPACING.m,
        borderRadius: RADIUS.m,
        marginBottom: SPACING.m,
        backgroundColor: '#f5f5f5',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    selectedOption: {
        backgroundColor: Colors.light.primary,
    },
    nativeText: {
        fontSize: rf(18),
        fontWeight: 'bold',
        color: '#333',
    },
    englishText: {
        fontSize: rf(14),
        color: '#666',
    },
    selectedText: {
        color: '#fff',
    },
    closeButton: {
        marginTop: SPACING.s,
        padding: SPACING.m,
        alignItems: 'center',
    },
    closeText: {
        color: '#666',
        fontSize: rf(16),
    },
});
