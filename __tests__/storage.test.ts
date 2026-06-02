import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { StorageService } from '../services/storage';

jest.mock('@react-native-async-storage/async-storage', () => ({
    setItem: jest.fn(),
    getItem: jest.fn(),
}));

jest.mock('expo-secure-store', () => ({
    setItemAsync: jest.fn(),
    getItemAsync: jest.fn(),
}));

describe('StorageService', () => {
    beforeEach(() => {
        jest.clearAllMocks();
    });

    it('should save and get user profile using SecureStore', async () => {
        const profile = { name: 'Test User', age: '80' };
        await StorageService.saveUserProfile(profile);
        expect(SecureStore.setItemAsync).toHaveBeenCalledWith('user-profile-v1', JSON.stringify(profile));

        (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(JSON.stringify(profile));
        const retrieved = await StorageService.getUserProfile();
        expect(retrieved).toEqual(profile);
    });

    it('should save and get emergency contacts using SecureStore', async () => {
        const contacts = [{ name: 'Son', phone: '1234567890' }];
        await StorageService.saveEmergencyContacts(contacts);
        expect(SecureStore.setItemAsync).toHaveBeenCalledWith('emergency-contacts-v1', JSON.stringify(contacts));

        (SecureStore.getItemAsync as jest.Mock).mockResolvedValue(JSON.stringify(contacts));
        const retrieved = await StorageService.getEmergencyContacts();
        expect(retrieved).toEqual(contacts);
    });

    it('should save and get language using AsyncStorage', async () => {
        const lang = 'kn';
        await StorageService.setLanguage(lang);
        expect(AsyncStorage.setItem).toHaveBeenCalledWith('user-language', lang);

        (AsyncStorage.getItem as jest.Mock).mockResolvedValue(lang);
        const retrieved = await StorageService.getLanguage();
        expect(retrieved).toEqual(lang);
    });
});
