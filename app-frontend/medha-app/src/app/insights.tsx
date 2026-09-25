import React, { useState } from 'react';
import {
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { RADIUS, SHADOW, TOP_HEADER_PADDING } from '../constants/theme';
import { MedhaScreenBackground } from '../components/medha-screen-background';

type TrendStatus = 'Improving' | 'Stable' | 'Needs Attention';

interface TrendData {
  status: TrendStatus;
  message: string;
  period: string;
  contributors: string[];
  explanation: string;
}

const mockTrend: TrendData = {
  status: 'Improving',
  message: 'Your recent moments show a little more steadiness.',
  period: 'Compared with your recent activity',
  contributors: [
    'You checked in more consistently.',
    'You spent some time writing your thoughts down.',
    'Your recent conversations with MEDHA have been more regular.',
  ],
  explanation:
    'This reflection is based on changes in your recent activity over time. It looks at the moments you chose to check in, write, or talk — rather than trying to label how you feel.',
};

export default function InsightsScreen() {
  const router = useRouter();
  const [showWhy, setShowWhy] = useState(false);

  const trend = mockTrend;

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safe}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" />
        <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* TOP BAR: BACK BUTTON */}
        <View style={styles.topBar}>
          <Pressable
            onPress={() => router.back()}
            style={({ pressed }) => [
              styles.iconButton,
              pressed && styles.pressed,
            ]}
            hitSlop={12}
            accessibilityRole="button"
            accessibilityLabel="Back"
          >
            <Ionicons name="arrow-back" size={20} color="#181E2C" />
          </Pressable>
        </View>

        {/* HEADER */}
        <View style={styles.header}>
          <Text style={styles.eyebrow}>YOUR PATTERNS</Text>
          <Text style={styles.title}>A gentle overview</Text>
          <Text style={styles.subtitle}>
            Gentle reflections from your recent moments — not labels or diagnoses.
          </Text>
        </View>

        {/* HERO TREND CARD */}
        <View style={styles.heroCard}>
          <View style={styles.heroHeader}>
            <View style={styles.trendBadge}>
              <Ionicons name="leaf-outline" size={16} color="#2D8A4E" />
              <Text style={styles.trendBadgeText}>{trend.status}</Text>
            </View>
            <Text style={styles.periodText}>{trend.period}</Text>
          </View>

          <Text style={styles.heroMessage}>{trend.message}</Text>
        </View>

        {/* INSIGHT SUMMARY (COMPACT ROWS IN CLEAN WHITE CARD) */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>OBSERVATIONS</Text>
        </View>

        <View style={styles.summaryCard}>
          {/* Category 1: Mood & Balance */}
          <View style={styles.summaryRow}>
            <View style={[styles.categoryIconBadge, { backgroundColor: '#E2F5E8' }]}>
              <Ionicons name="leaf-outline" size={18} color="#2D8A4E" />
            </View>
            <View style={styles.categoryInfo}>
              <Text style={styles.categoryTitle}>Mood & Balance</Text>
              <Text style={styles.categoryDesc}>Steadier over recent days</Text>
            </View>
            <View style={[styles.pillBadge, { backgroundColor: '#E2F5E8' }]}>
              <Text style={[styles.pillBadgeText, { color: '#2D8A4E' }]}>Steadier</Text>
            </View>
          </View>

          <View style={styles.divider} />

          {/* Category 2: Daily Check-ins */}
          <View style={styles.summaryRow}>
            <View style={[styles.categoryIconBadge, { backgroundColor: '#E1F2FE' }]}>
              <Ionicons name="checkmark-circle-outline" size={18} color="#0284C7" />
            </View>
            <View style={styles.categoryInfo}>
              <Text style={styles.categoryTitle}>Check-in Rhythm</Text>
              <Text style={styles.categoryDesc}>More consistent daily check-ins</Text>
            </View>
            <View style={[styles.pillBadge, { backgroundColor: '#E1F2FE' }]}>
              <Text style={[styles.pillBadgeText, { color: '#0284C7' }]}>Active</Text>
            </View>
          </View>

          <View style={styles.divider} />

          {/* Category 3: Reflection & Journaling */}
          <View style={styles.summaryRow}>
            <View style={[styles.categoryIconBadge, { backgroundColor: '#EEE9FA' }]}>
              <Ionicons name="book-outline" size={18} color="#6C5CE7" />
            </View>
            <View style={styles.categoryInfo}>
              <Text style={styles.categoryTitle}>Writing Thoughts</Text>
              <Text style={styles.categoryDesc}>Taking time to write down moments</Text>
            </View>
            <View style={[styles.pillBadge, { backgroundColor: '#EEE9FA' }]}>
              <Text style={[styles.pillBadgeText, { color: '#6C5CE7' }]}>Regular</Text>
            </View>
          </View>

          <View style={styles.divider} />

          {/* Category 4: Conversations */}
          <View style={styles.summaryRow}>
            <View style={[styles.categoryIconBadge, { backgroundColor: '#FFEADB' }]}>
              <Ionicons name="chatbubble-outline" size={18} color="#E8663F" />
            </View>
            <View style={styles.categoryInfo}>
              <Text style={styles.categoryTitle}>Conversations</Text>
              <Text style={styles.categoryDesc}>More regular talks with MEDHA</Text>
            </View>
            <View style={[styles.pillBadge, { backgroundColor: '#FFEADB' }]}>
              <Text style={[styles.pillBadgeText, { color: '#E8663F' }]}>Supportive</Text>
            </View>
          </View>
        </View>

        {/* WEEKLY VISUAL (PRESERVED BAR CHART IN CLEAN WHITE CARD) */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>THE WEEK IN GENTLE SHAPES</Text>
        </View>

        <View style={styles.weekCard}>
          <View style={styles.week}>
            {[
              ['M', 0.35],
              ['T', 0.55],
              ['W', 0.72],
              ['T', 0.48],
              ['F', 0.82],
              ['S', 0.62],
              ['S', 0.42],
            ].map(([day, height], index) => (
              <View key={`${day}-${index}`} style={styles.day}>
                <View style={styles.barTrack}>
                  <View
                    style={[
                      styles.bar,
                      {
                        height: `${Number(height) * 100}%`,
                      },
                    ]}
                  />
                </View>
                <Text style={styles.dayText}>{day}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* SUPPORTIVE SUMMARY (PASTEL LAVENDER CARD) */}
        <View style={styles.supportiveCard}>
          <View style={styles.supportiveIconBadge}>
            <Ionicons name="sparkles" size={18} color="#FF735C" />
          </View>
          <View style={styles.supportiveContent}>
            <Text style={styles.supportiveTitle}>Something worth noticing</Text>
            <Text style={styles.supportiveBody}>
              Your check-ins seem to happen more often when your days feel full.
            </Text>
          </View>
        </View>

        {/* VIEW DETAILS ACTION */}
        <View style={styles.actionContainer}>
          <Pressable
            onPress={() => setShowWhy(!showWhy)}
            style={({ pressed }) => [
              styles.viewDetailsButton,
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel={showWhy ? 'Hide details' : 'View details'}
          >
            <Text style={styles.viewDetailsText}>
              {showWhy ? 'Hide details' : 'View details'}
            </Text>
            <Ionicons
              name={showWhy ? 'chevron-up' : 'arrow-forward'}
              size={16}
              color="#181E2C"
            />
          </Pressable>
        </View>

        {/* EXPANDABLE DETAILS */}
        {showWhy && (
          <View style={styles.detailsCard}>
            <Text style={styles.detailsTitle}>What influenced this?</Text>
            <Text style={styles.detailsBody}>{trend.explanation}</Text>

            <View style={styles.contributorsList}>
              {trend.contributors.map((contributor, idx) => (
                <View key={idx} style={styles.contributorRow}>
                  <View style={styles.contributorDot} />
                  <Text style={styles.contributorText}>{contributor}</Text>
                </View>
              ))}
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: '#FAF3D6',
  },
  safe: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: TOP_HEADER_PADDING,
    paddingBottom: 40,
  },

  /* TOP BAR */
  topBar: {
    height: 48,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },

  /* HEADER */
  header: {
    marginBottom: 20,
  },
  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.5,
    color: '#E8663F',
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 26,
    lineHeight: 32,
    color: '#181E2C',
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 20,
    color: '#5B6478',
    marginTop: 6,
  },

  /* HERO CARD */
  heroCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    marginBottom: 22,
    ...SHADOW.subtle,
  },
  heroHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  trendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#E2F5E8',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
  },
  trendBadgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: '#2D8A4E',
  },
  periodText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: '#8E97A8',
  },
  heroMessage: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 18,
    lineHeight: 25,
    color: '#181E2C',
  },

  /* SECTION */
  sectionHeader: {
    marginBottom: 10,
    marginTop: 4,
  },
  sectionTitle: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    letterSpacing: 1.5,
    color: '#8E97A8',
    textTransform: 'uppercase',
  },

  /* SUMMARY CARD */
  summaryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    marginBottom: 22,
    ...SHADOW.subtle,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  categoryIconBadge: {
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  categoryInfo: {
    flex: 1,
  },
  categoryTitle: {
    fontFamily: 'Nunito-Bold',
    fontSize: 14,
    color: '#181E2C',
  },
  categoryDesc: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: '#5B6478',
    marginTop: 2,
  },
  pillBadge: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: RADIUS.pill,
  },
  pillBadgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
  },
  divider: {
    height: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.04)',
    marginVertical: 4,
  },

  /* WEEK VISUAL */
  weekCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    marginBottom: 22,
    ...SHADOW.subtle,
  },
  week: {
    height: 120,
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    paddingHorizontal: 6,
  },
  day: {
    alignItems: 'center',
    gap: 8,
  },
  barTrack: {
    height: 85,
    width: 20,
    borderRadius: 10,
    backgroundColor: 'rgba(24, 30, 44, 0.06)',
    justifyContent: 'flex-end',
    overflow: 'hidden',
  },
  bar: {
    width: '100%',
    backgroundColor: '#7FA88A',
    borderRadius: 10,
  },
  dayText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 11,
    color: '#8E97A8',
  },

  /* SUPPORTIVE CARD */
  supportiveCard: {
    backgroundColor: '#EEE9FA',
    borderRadius: 22,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 14,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: 'rgba(108, 92, 231, 0.12)',
  },
  supportiveIconBadge: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
    ...SHADOW.subtle,
  },
  supportiveContent: {
    flex: 1,
  },
  supportiveTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 16,
    color: '#181E2C',
  },
  supportiveBody: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 19,
    color: '#3A4454',
    marginTop: 4,
  },

  /* ACTION */
  actionContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  viewDetailsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingHorizontal: 22,
    paddingVertical: 14,
    borderRadius: RADIUS.pill,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.08)',
    ...SHADOW.subtle,
  },
  viewDetailsText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 14,
    color: '#181E2C',
  },

  /* DETAILS CARD */
  detailsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    marginBottom: 20,
    ...SHADOW.subtle,
  },
  detailsTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 16,
    color: '#181E2C',
    marginBottom: 6,
  },
  detailsBody: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 19,
    color: '#5B6478',
    marginBottom: 14,
  },
  contributorsList: {
    gap: 10,
  },
  contributorRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  contributorDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#FF735C',
    marginTop: 6,
  },
  contributorText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 12.5,
    lineHeight: 18,
    color: '#181E2C',
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.88,
  },
});