import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { StorageService } from '@/services/storage';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  ActivityIndicator,
  Animated,
  Dimensions,
  Image,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TouchableOpacity,
  View
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

const SUPPORTED_LANGUAGES: Array<{ code: 'en' | 'hi' | 'kn'; label: string; native: string; subtitle: string }> = [
  { code: 'en', label: 'English', native: 'English', subtitle: 'Default' },
  { code: 'hi', label: 'Hindi', native: 'हिंदी', subtitle: 'नमस्ते' },
  { code: 'kn', label: 'Kannada', native: 'ಕನ್ನಡ', subtitle: 'ನಮಸ್ಕಾರ' },
];

const { width } = Dimensions.get('window');

export default function LanguageScreen() {
  const router = useRouter();
  const { t, i18n } = useTranslation();
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<'en' | 'hi' | 'kn'>('en');
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  // Check if we can go back (e.g. opened from Login/Settings)
  const canGoBack = router.canGoBack();

  useEffect(() => {
    let cancelled = false;
    async function init() {
      try {
        const saved = await StorageService.getLanguage();
        if (cancelled) return;

        const hasSaved = saved === 'en' || saved === 'hi' || saved === 'kn';

        if (!canGoBack && hasSaved) {
          if (i18n.language !== saved) {
            await i18n.changeLanguage(saved);
          }
          router.replace('/');
          return;
        }

        if (hasSaved && saved !== selected) {
          setSelected(saved as any);
        }
      } catch (e) {
        console.warn('Failed to load language', e);
      } finally {
        if (!cancelled) {
          setLoading(false);
          Animated.parallel([
            Animated.timing(fadeAnim, {
              toValue: 1,
              duration: 600,
              useNativeDriver: true,
            }),
            Animated.timing(slideAnim, {
              toValue: 0,
              duration: 600,
              useNativeDriver: true,
            })
          ]).start();
        }
      }
    }
    init();
    return () => {
      cancelled = true;
    };
  }, [i18n, router, canGoBack]);

  const handleSelect = async (code: 'en' | 'hi' | 'kn') => {
    setSelected(code);
    try {
      await i18n.changeLanguage(code);
      await StorageService.setLanguage(code);
    } catch (e) {
      console.error('Language save failed', e);
    }
  };

  const handleContinue = () => {
    if (canGoBack) {
      router.back();
    } else {
      router.replace('/');
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <StatusBar barStyle="dark-content" />
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentContainerStyle={styles.scrollContainer} showsVerticalScrollIndicator={false}>

        <Animated.View
          style={[
            styles.content,
            { opacity: fadeAnim, transform: [{ translateY: slideAnim }] }
          ]}
        >
          {/* App Logo */}
          <Image
            source={require('../assets/images/logo.png')}
            style={{
              width: rf(100),
              height: rf(100),
              alignSelf: 'center',
              marginBottom: SPACING.l,
              borderRadius: RADIUS.m
            }}
            resizeMode="contain"
          />

          <View style={styles.header}>
            <View style={{ flex: 1 }}>
              <Text style={styles.title}>{t('welcome_title')}</Text>
              <Text style={styles.subtitle}>{t('choose_language_subtitle')}</Text>
            </View>
            {canGoBack && (
              <TouchableOpacity
                style={styles.closeButton}
                onPress={() => router.back()}
                hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              >
                <Ionicons name="close" size={rf(24)} color={COLORS.text} />
              </TouchableOpacity>
            )}
          </View>

          <View style={styles.list}>
            {SUPPORTED_LANGUAGES.map((lang) => {
              const isSelected = selected === lang.code;
              return (
                <TouchableOpacity
                  key={lang.code}
                  style={[
                    styles.optionCard,
                    isSelected && styles.optionCardSelected
                  ]}
                  onPress={() => handleSelect(lang.code)}
                  activeOpacity={0.9} // Better feedback
                >
                  <View style={styles.languageInfo}>
                    <Text style={[styles.nativeName, isSelected && styles.textSelected]}>
                      {lang.native}
                    </Text>
                    <Text style={[styles.labelName, isSelected && styles.textSelectedSubtitle]}>
                      {lang.label} • {lang.subtitle}
                    </Text>
                  </View>

                  <View style={[styles.radioButton, isSelected && styles.radioButtonSelected]}>
                    {isSelected ? (
                      <Ionicons name="checkmark" size={rf(18)} color="white" />
                    ) : null}
                  </View>
                </TouchableOpacity>
              );
            })}
          </View>

          <View style={styles.footer}>
            <TouchableOpacity
              style={styles.continueButton}
              onPress={handleContinue}
              activeOpacity={0.8}
            >
              <Text style={styles.continueButtonText}>{t('continue')}</Text>
              <Ionicons name="arrow-forward" size={rf(20)} color="white" />
            </TouchableOpacity>

            <Text style={styles.footerText}>
              {t('change_anytime_note')}
            </Text>
          </View>

        </Animated.View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  scrollContainer: {
    flexGrow: 1,
    paddingHorizontal: SPACING.l,
    justifyContent: 'center', // Center vertically for better balance
    paddingBottom: SPACING.xl,
  },
  content: {
    width: '100%',
    maxWidth: 500,
    alignSelf: 'center', // Center on tablet
  },
  header: {
    marginBottom: SPACING.xl,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  title: {
    fontSize: rf(32),
    fontWeight: '800',
    color: COLORS.text,
    letterSpacing: -0.5,
    marginBottom: SPACING.xs,
  },
  subtitle: {
    fontSize: rf(16),
    color: COLORS.muted,
  },
  closeButton: {
    padding: SPACING.xs,
    backgroundColor: COLORS.card,
    borderRadius: RADIUS.full,
    ...SHADOWS.light,
  },
  list: {
    marginBottom: SPACING.xl,
  },
  optionCard: {
    backgroundColor: COLORS.card,
    padding: SPACING.l,
    borderRadius: RADIUS.l,
    marginBottom: SPACING.m,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 2,
    borderColor: 'transparent',
    ...SHADOWS.light,
  },
  optionCardSelected: {
    borderColor: COLORS.primary,
    backgroundColor: '#F0F9FF', // Subtle blue tint
    ...SHADOWS.medium,
  },
  languageInfo: {
    flex: 1,
  },
  nativeName: {
    fontSize: rf(20),
    fontWeight: '700',
    color: COLORS.text,
    marginBottom: SPACING.xs,
  },
  labelName: {
    fontSize: rf(14),
    color: COLORS.muted,
    fontWeight: '500',
  },
  textSelected: {
    color: COLORS.primary,
  },
  textSelectedSubtitle: {
    color: COLORS.primary,
    opacity: 0.8,
  },
  radioButton: {
    width: rf(28),
    height: rf(28),
    borderRadius: rf(14),
    borderWidth: 2,
    borderColor: COLORS.muted,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: SPACING.m,
    backgroundColor: 'transparent',
  },
  radioButtonSelected: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primary,
  },
  footer: {
    marginTop: SPACING.m,
  },
  continueButton: {
    backgroundColor: COLORS.primary,
    paddingVertical: SPACING.m,
    paddingHorizontal: SPACING.xl,
    borderRadius: RADIUS.full,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: SPACING.l,
    ...SHADOWS.medium,
  },
  continueButtonText: {
    color: 'white',
    fontSize: rf(18),
    fontWeight: 'bold',
    marginRight: SPACING.s,
  },
  footerText: {
    fontSize: rf(13),
    color: COLORS.muted,
    textAlign: 'center',
  },
});
