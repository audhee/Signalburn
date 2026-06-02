import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const KEYS = {
    USER_LANGUAGE: 'user-language',
    EMERGENCY_CONTACTS: 'emergency-contacts-v1',
    USER_PROFILE: 'user-profile-v1',
};

// Helper: Secure Store is not supported on Web, so we fallback to AsyncStorage
const isWeb = Platform.OS === 'web';

async function setSecureItem(key: string, value: string) {
    if (isWeb) {
        await AsyncStorage.setItem(key, value);
    } else {
        await SecureStore.setItemAsync(key, value);
    }
}

async function getSecureItem(key: string): Promise<string | null> {
    if (isWeb) {
        return await AsyncStorage.getItem(key);
    } else {
        return await SecureStore.getItemAsync(key);
    }
}

// Abstract Service to handle data persistence.
export const StorageService = {
    // --- Language (Non-sensitive, keep in AsyncStorage) ---
    async getLanguage(): Promise<string | null> {
        try {
            return await AsyncStorage.getItem(KEYS.USER_LANGUAGE);
        } catch (e) {
            console.warn('StorageService: getLanguage failed', e);
            return null;
        }
    },
    async setLanguage(lang: string): Promise<void> {
        try {
            await AsyncStorage.setItem(KEYS.USER_LANGUAGE, lang);
        } catch (e) {
            console.error('StorageService: setLanguage failed', e);
        }
    },

    // --- Profile (Sensitive: Encrypted) ---
    async getUserProfile(): Promise<any | null> {
        try {
            const data = await getSecureItem(KEYS.USER_PROFILE);
            return data ? JSON.parse(data) : null;
        } catch (e) {
            console.warn('StorageService: getUserProfile failed', e);
            return null;
        }
    },
    async saveUserProfile(profile: any): Promise<void> {
        try {
            // Profile contains medical data and name.
            await setSecureItem(KEYS.USER_PROFILE, JSON.stringify(profile));
        } catch (e) {
            console.error('StorageService: saveUserProfile failed', e);
        }
    },

    // --- Contacts (Sensitive: Encrypted) ---
    async getEmergencyContacts(): Promise<any[]> {
        try {
            const data = await getSecureItem(KEYS.EMERGENCY_CONTACTS);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            console.warn('StorageService: getEmergencyContacts failed', e);
            return [];
        }
    },
    async saveEmergencyContacts(contacts: any[]): Promise<void> {
        try {
            // Contact list contains phone numbers of relatives.
            await setSecureItem(KEYS.EMERGENCY_CONTACTS, JSON.stringify(contacts));
        } catch (e) {
            console.error('StorageService: saveEmergencyContacts failed', e);
        }
    },

    async clearAll(): Promise<void> {
        try {
            // Clear all stored data to reset the app
            await AsyncStorage.removeItem(KEYS.USER_LANGUAGE);
            if (isWeb) {
                await AsyncStorage.removeItem(KEYS.USER_PROFILE);
                await AsyncStorage.removeItem(KEYS.EMERGENCY_CONTACTS);
            } else {
                await SecureStore.deleteItemAsync(KEYS.USER_PROFILE);
                await SecureStore.deleteItemAsync(KEYS.EMERGENCY_CONTACTS);
            }
        } catch (e) {
            console.error('StorageService: clearAll failed', e);
        }
    }
};
