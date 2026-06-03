import { Platform } from 'react-native';

/**
 * API base URL for the Arohan backend.
 * - Set EXPO_PUBLIC_API_URL env var for production builds.
 * - On Android emulator, localhost = 10.0.2.2.
 * - On physical device, use your machine's LAN IP.
 * - Fallback: localhost (works on iOS simulator / Expo Go).
 */
const getDefaultUrl = (): string => {
    if (Platform.OS === 'android') {
        // Android emulator resolves 'localhost' to the emulator's loopback,
        // not the host machine.  Use 10.0.2.2 which maps to host localhost.
        // On a real device this won't work, so EXPO_PUBLIC_API_URL must be set.
        return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
};

export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || getDefaultUrl();