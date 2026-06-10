import { API_BASE_URL } from '@/constants/api';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';

const AUTH_TOKEN_KEY = 'arohan-auth-token';
const isWeb = Platform.OS === 'web';

async function getToken(): Promise<string | null> {
    try {
        if (isWeb) return await AsyncStorage.getItem(AUTH_TOKEN_KEY);
        return await SecureStore.getItemAsync(AUTH_TOKEN_KEY);
    } catch {
        return null;
    }
}

export type ApiRequestOptions = {
    method?: 'GET' | 'POST' | 'PATCH' | 'PUT' | 'DELETE';
    body?: any;
    headers?: Record<string, string>;
    includeAuth?: boolean;
    isFormData?: boolean;
};

export const apiClient = {
    async request<T = any>(endpoint: string, options: ApiRequestOptions = {}): Promise<T> {
        const {
            method = 'GET',
            body,
            headers = {},
            includeAuth = true,
            isFormData = false
        } = options;

        const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
        
        const requestHeaders: Record<string, string> = {
            ...headers,
            'ngrok-skip-browser-warning': 'true',
        };

        if (!isFormData) {
            requestHeaders['Content-Type'] = 'application/json';
        }

        if (includeAuth) {
            const token = await getToken();
            if (token) {
                requestHeaders['Authorization'] = `Bearer ${token}`;
            }
        }

        try {
            const response = await fetch(url, {
                method,
                headers: requestHeaders,
                body: isFormData ? body : JSON.stringify(body),
            });

            if (!response.ok) {
                const text = await response.text();
                let errorData: any;
                try {
                    errorData = JSON.parse(text);
                } catch {
                    errorData = { detail: text };
                }
                throw new Error(errorData.detail || `Request failed with status ${response.status}`);
            }

            // Handle potential empty responses (like 204 No Content)
            if (response.status === 204) return {} as T;

            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            }
            
            // For binary/audio data
            return await response.blob() as any;

        } catch (error: any) {
            console.error(`apiClient Error [${method} ${endpoint}]:`, error);
            throw error;
        }
    },

    get<T = any>(endpoint: string, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}) {
        return this.request<T>(endpoint, { ...options, method: 'GET' });
    },

    post<T = any>(endpoint: string, body: any, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}) {
        return this.request<T>(endpoint, { ...options, method: 'POST', body });
    },

    put<T = any>(endpoint: string, body: any, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}) {
        return this.request<T>(endpoint, { ...options, method: 'PUT', body });
    },

    patch<T = any>(endpoint: string, body: any, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}) {
        return this.request<T>(endpoint, { ...options, method: 'PATCH', body });
    },

    delete<T = any>(endpoint: string, options: Omit<ApiRequestOptions, 'method' | 'body'> = {}) {
        return this.request<T>(endpoint, { ...options, method: 'DELETE' });
    }
};
