import { jest } from '@jest/globals';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
    require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock SecureStore
jest.mock('expo-secure-store', () => ({
    setItemAsync: jest.fn(),
    getItemAsync: jest.fn(),
    deleteItemAsync: jest.fn(),
}));

// Mock Haptics
jest.mock('expo-haptics', () => ({
    impactAsync: jest.fn(() => Promise.resolve()),
    notificationAsync: jest.fn(() => Promise.resolve()),
    ImpactFeedbackStyle: { Medium: 'medium', Heavy: 'heavy' },
    NotificationFeedbackType: { Error: 'error', Success: 'success' },
}));

// Mock Location
jest.mock('expo-location', () => ({
    requestForegroundPermissionsAsync: jest.fn(),
    getCurrentPositionAsync: jest.fn(),
}));

// Mock Linking
jest.mock('expo-linking', () => ({
    openURL: jest.fn(),
    canOpenURL: jest.fn(),
    createURL: jest.fn(),
}));

// Mock KeepAwake
jest.mock('expo-keep-awake', () => ({
    useKeepAwake: jest.fn(),
}));

// Mock Translations
jest.mock('react-i18next', () => ({
    useTranslation: () => ({
        t: (key, options) => {
            if (options?.url) return `${key}:${options.url}`;
            if (options?.link) return `${key}:${options.link}`;
            return options?.defaultValue || key;
        },
    }),
}));
