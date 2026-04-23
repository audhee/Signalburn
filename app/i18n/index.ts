import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Localization from 'expo-localization';
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import en from './locales/en.json';
import hi from './locales/hi.json';
import kn from './locales/kn.json';

const RESOURCES = {
    en: { translation: en },
    hi: { translation: hi },
    kn: { translation: kn },
};

const LANGUAGE_DETECTOR = {
    type: 'languageDetector',
    async: true,
    detect: async (callback: (lang: string) => void) => {
        if (typeof window === 'undefined') return callback('en');

        try {
            const savedLanguage = await AsyncStorage.getItem('user-language');
            if (savedLanguage) {
                return callback(savedLanguage);
            }

            const bestLanguage = Localization.getLocales()[0]?.languageCode;

            // Fallback to English if device language is not supported
            if (bestLanguage && ['en', 'hi', 'kn'].includes(bestLanguage)) {
                return callback(bestLanguage);
            }

            return callback('en');
        } catch (error) {
            console.log('Error reading language', error);
            callback('en');
        }
    },
    init: () => { },
    cacheUserLanguage: async (language: string) => {
        if (typeof window === 'undefined') return;
        try {
            await AsyncStorage.setItem('user-language', language);
        } catch (error) {
            console.log('Error saving language', error);
        }
    },
};

i18n
    .use(initReactI18next)
    .use(LANGUAGE_DETECTOR as any)
    .init({
        resources: RESOURCES,
        fallbackLng: 'en',
        interpolation: {
            escapeValue: false, // react already safes from xss
        },
        react: {
            useSuspense: false
        }
    });

export default i18n;
