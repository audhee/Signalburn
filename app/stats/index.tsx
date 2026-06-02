import { rf } from '@/constants/responsive';
import { COLORS, RADIUS, SHADOWS, SPACING } from '@/constants/theme';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useTranslation } from 'react-i18next';
import { SafeAreaView, StatusBar, Text, TouchableOpacity, View } from 'react-native';

export default function StatsScreen() {
  const router = useRouter();
  const { t } = useTranslation();

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: COLORS.background }}>
      <StatusBar barStyle="dark-content" />

      <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: SPACING.l, paddingTop: SPACING.xl, paddingBottom: SPACING.l, borderBottomWidth: 1, borderBottomColor: COLORS.border }}>
        <TouchableOpacity onPress={() => router.back()} accessibilityRole="button" accessibilityLabel="Go back">
          <Ionicons name="arrow-back" size={rf(24)} color={COLORS.text} />
        </TouchableOpacity>
        <Text style={{ fontSize: rf(18), fontWeight: '800', marginLeft: SPACING.m, color: COLORS.text }}>{t('stats')}</Text>
      </View>

      <View style={{ flex: 1, padding: SPACING.l }}>
        <Text style={{ fontSize: rf(16), color: COLORS.muted, marginBottom: SPACING.l }}>
          {t('sample_stats_note')}
        </Text>

        <View style={{ gap: SPACING.m }}>
          <View style={{ backgroundColor: COLORS.card, borderRadius: RADIUS.l, padding: SPACING.m, ...SHADOWS.light }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: SPACING.s }}>
              <Ionicons name="heart" size={rf(18)} color={COLORS.error} style={{ marginRight: SPACING.s }} />
              <Text style={{ fontWeight: '700', color: COLORS.text, fontSize: rf(14) }}>{t('heart_rate_label')}</Text>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'baseline' }}>
              <Text style={{ fontSize: rf(28), fontWeight: '900', color: COLORS.text }}>72</Text>
              <Text style={{ color: COLORS.muted, fontSize: rf(14), marginLeft: SPACING.xs }}>BPM</Text>
            </View>
          </View>

          <View style={{ backgroundColor: COLORS.card, borderRadius: RADIUS.l, padding: SPACING.m, ...SHADOWS.light }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: SPACING.s }}>
              <Ionicons name="water" size={rf(18)} color="#007AFF" style={{ marginRight: SPACING.s }} />
              <Text style={{ fontWeight: '700', color: COLORS.text, fontSize: rf(14) }}>{t('spo2_label')}</Text>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'baseline' }}>
              <Text style={{ fontSize: rf(28), fontWeight: '900', color: COLORS.text }}>98</Text>
              <Text style={{ color: COLORS.muted, fontSize: rf(14), marginLeft: SPACING.xs }}>%</Text>
            </View>
          </View>

          <View style={{ backgroundColor: COLORS.card, borderRadius: RADIUS.l, padding: SPACING.m, ...SHADOWS.light }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: SPACING.s }}>
              <Ionicons name="pulse" size={rf(18)} color="#FF3B30" style={{ marginRight: SPACING.s }} />
              <Text style={{ fontWeight: '700', color: COLORS.text, fontSize: rf(14) }}>{t('bp_label')}</Text>
            </View>
            <View style={{ flexDirection: 'row', alignItems: 'baseline' }}>
              <Text style={{ fontSize: rf(28), fontWeight: '900', color: COLORS.text }}>120/80</Text>
              <Text style={{ color: COLORS.muted, fontSize: rf(14), marginLeft: SPACING.xs }}>mmHg</Text>
            </View>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
}

