import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { API_BASE_URL } from '@/constants/api';

const AUTH_TOKEN_KEY = 'arohan-auth-token';
const AUTH_PHONE_KEY = 'arohan-auth-phone';

// SecureStore is not available on Web — fallback to AsyncStorage
const isWeb = Platform.OS === 'web';

async function saveToken(token: string, phone: string): Promise<void> {
    if (isWeb) {
        await AsyncStorage.setItem(AUTH_TOKEN_KEY, token);
        await AsyncStorage.setItem(AUTH_PHONE_KEY, phone);
    } else {
        await SecureStore.setItemAsync(AUTH_TOKEN_KEY, token);
        await SecureStore.setItemAsync(AUTH_PHONE_KEY, phone);
    }
}

async function clearToken(): Promise<void> {
    if (isWeb) {
        await AsyncStorage.removeItem(AUTH_TOKEN_KEY);
        await AsyncStorage.removeItem(AUTH_PHONE_KEY);
    } else {
        await SecureStore.deleteItemAsync(AUTH_TOKEN_KEY);
        await SecureStore.deleteItemAsync(AUTH_PHONE_KEY);
    }
}

export const AuthService = {
    /**
     * Request a real OTP via Twilio SMS.
     * Returns true if the SMS was sent successfully.
     */
    async sendOTP(phoneNumber: string): Promise<{ success: boolean; error?: string }> {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/request-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone_number: phoneNumber }),
            });

            if (response.ok) {
                return { success: true };
            } else {
                const data = await response.json();
                return { success: false, error: data.detail ?? 'Failed to send OTP' };
            }
        } catch (e) {
            console.error('AuthService.sendOTP error:', e);
            return { success: false, error: 'Cannot reach the server. Check your network.' };
        }
    },

    /**
     * Verify OTP with the backend.
     * Saves the session token to SecureStore on success.
     * Returns true if verified, false otherwise.
     */
    async verifyOTP(
        phoneNumber: string,
        otp: string
    ): Promise<{ success: boolean; error?: string }> {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/verify-otp`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone_number: phoneNumber, user_otp: otp }),
            });

            if (response.ok) {
                const data = await response.json();
                // Persist the session token securely
                await saveToken(data.token, phoneNumber);
                return { success: true };
            } else {
                const data = await response.json();
                return { success: false, error: data.detail ?? 'Incorrect OTP. Please try again.' };
            }
        } catch (e) {
            console.error('AuthService.verifyOTP error:', e);
            return { success: false, error: 'Cannot reach the server. Check your network.' };
        }
    },

    /**
     * Retrieve the stored session token (to check if user is logged in).
     */
    async getToken(): Promise<string | null> {
        try {
            if (isWeb) return await AsyncStorage.getItem(AUTH_TOKEN_KEY);
            return await SecureStore.getItemAsync(AUTH_TOKEN_KEY);
        } catch {
            return null;
        }
    },

    /**
     * Retrieve the stored phone number of the logged-in user.
     */
    async getPhoneNumber(): Promise<string | null> {
        try {
            if (isWeb) return await AsyncStorage.getItem(AUTH_PHONE_KEY);
            return await SecureStore.getItemAsync(AUTH_PHONE_KEY);
        } catch {
            return null;
        }
    },

    /**
     * Log out — clear the stored session token.
     */
    async logout(): Promise<void> {
        await clearToken();
    },
};
