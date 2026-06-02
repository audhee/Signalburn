import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { StorageService } from '@/services/storage';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { SafeAreaView, StatusBar, Text, TouchableOpacity, View } from 'react-native';

export default function SettingsScreen() {
  const router = useRouter();
  const { t } = useTranslation();

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      <StatusBar barStyle="dark-content" />

      <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: SPACING.l, paddingTop: SPACING.xl, paddingBottom: SPACING.l, borderBottomWidth: 1, borderBottomColor: COLORS.border }}>
        <TouchableOpacity onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="Go back">
          <Ionicons name="arrow-back" size={rf(24)} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={{ fontSize: rf(18), fontWeight: '800', marginLeft: SPACING.m, color: COLORS.text }}>{t('settings')}</Text>
      </View>

      <View style={{ flex: 1, padding: SPACING.l }}>
        <TouchableOpacity
          style={{ backgroundColor: COLORS.card, borderRadius: RADIUS.l, padding: SPACING.l, marginBottom: SPACING.m, ...SHADOWS.light, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}
          onPress={() => router.push('/language' as any)}
          accessibilityRole="button"
          accessibilityLabel="Change language"
        >
          <View>
            <Text style={{ fontSize: rf(16), fontWeight: '800', color: COLORS.text }}>{t('language')}</Text>
            <Text style={{ fontSize: rf(12), color: COLORS.muted }}>{t('change_app_language')}</Text>
          </View>
          <Ionicons name="chevron-forward" size={rf(22)} color={COLORS.muted} />
        </TouchableOpacity>

        <TouchableOpacity
          style={{ backgroundColor: COLORS.card, borderRadius: RADIUS.l, padding: SPACING.l, marginBottom: SPACING.m, ...SHADOWS.light, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}
          onPress={() => router.push('/setup/contacts' as any)}
          accessibilityRole="button"
          accessibilityLabel="Emergency contacts"
        >
          <View>
            <Text style={{ fontSize: rf(16), fontWeight: '800', color: COLORS.text }}>{t('emergency_contact')}</Text>
            <Text style={{ fontSize: rf(12), color: COLORS.muted }}>{t('add_edit_contacts')}</Text>
          </View>
          <Ionicons name="chevron-forward" size={rf(22)} color={COLORS.muted} />
        </TouchableOpacity>

        <TouchableOpacity
          style={{
            backgroundColor: '#FEE2E2',
            borderRadius: RADIUS.l,
            padding: SPACING.l,
            marginTop: SPACING.xl,
            flexDirection: 'row',
            justifyContent: 'center',
            alignItems: 'center',
            borderWidth: 1,
            borderColor: '#FECACA'
          }}
          onPress={async () => {
            await StorageService.clearAll();
            router.replace('/language' as any);
          }}
          accessibilityRole="button"
          accessibilityLabel="Logout"
        >
          <Ionicons name="log-out-outline" size={rf(20)} color={COLORS.error} style={{ marginRight: SPACING.s }} />
          <Text style={{ fontSize: rf(16), fontWeight: '800', color: COLORS.error }}>{t('logout')}</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

