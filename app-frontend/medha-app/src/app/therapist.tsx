import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export default function TherapistDashboardScreen() {
  return (
    <View style={styles.screen}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        <View style={styles.header}>
          <View>
            <Text style={styles.eyebrow}>MEDHA · CLINICAL VIEW</Text>
            <Text style={styles.title}>Therapist Dashboard</Text>
            <Text style={styles.subtitle}>
              Support tomorrow’s conversations.
            </Text>
          </View>
          <Pressable style={styles.profile}>
            <Ionicons name="person-outline" size={18} color={COLORS.deepForest} />
          </Pressable>
        </View>

        <View style={styles.stats}>
          <Stat value="—" label="Active cases" />
          <Stat value="—" label="High priority" />
          <Stat value="—" label="Follow-ups" />
          <Stat value="—" label="Patients" />
        </View>

        <View style={styles.notice}>
          <Ionicons name="information-circle-outline" size={18} color={COLORS.forest} />
          <Text style={styles.noticeText}>
            Live case values will appear when the therapist API returns them.
            Missing predictions remain unavailable and are never shown as zero.
          </Text>
        </View>

        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionEyebrow}>CASE QUEUE</Text>
            <Text style={styles.sectionTitle}>Recent cases</Text>
          </View>
          <Text style={styles.viewAll}>Live data</Text>
        </View>

        <View style={styles.emptyCard}>
          <View style={styles.emptyIcon}>
            <Ionicons name="folder-open-outline" size={22} color={COLORS.forest} />
          </View>
          <Text style={styles.emptyTitle}>No case data connected yet</Text>
          <Text style={styles.emptyText}>
            The visual dashboard is ready. Connect the existing therapist-owned
            case listing API before showing real patient records.
          </Text>
          <Pressable
            onPress={() =>
              router.push({
                pathname: '/therapist-case',
                params: { caseId: 'CASE_LAYOUT_PREVIEW' },
              })
            }
            style={styles.previewButton}
          >
            <Text style={styles.previewButtonText}>Open case layout</Text>
            <Ionicons name="arrow-forward" size={16} color={COLORS.white} />
          </Pressable>
        </View>

        <View style={styles.footerCard}>
          <Ionicons name="shield-checkmark-outline" size={23} color={COLORS.forest} />
          <View style={styles.footerCopy}>
            <Text style={styles.footerTitle}>Human review stays central.</Text>
            <Text style={styles.footerText}>
              MEDHA assists prioritisation. The therapist makes the final decision.
            </Text>
          </View>
        </View>

        <Pressable onPress={() => router.replace('/home')} style={styles.exit}>
          <Text style={styles.exitText}>Return to patient experience</Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    paddingHorizontal: 22,
    paddingTop: 56,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  eyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.8,
    color: COLORS.forest,
    marginBottom: 8,
  },
  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 32,
    color: COLORS.deepForest,
  },
  subtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.mutedText,
    marginTop: 4,
  },
  profile: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  stats: {
    flexDirection: 'row',
    marginTop: 25,
    gap: 8,
  },
  stat: {
    flex: 1,
    minHeight: 82,
    padding: 11,
    borderRadius: 17,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: 'center',
  },
  statValue: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 25,
    color: COLORS.deepForest,
  },
  statLabel: {
    fontFamily: 'Inter-Regular',
    fontSize: 8,
    lineHeight: 12,
    color: COLORS.mutedText,
    marginTop: 2,
  },
  notice: {
    marginTop: 13,
    padding: 14,
    borderRadius: 17,
    backgroundColor: COLORS.mist,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 9,
  },
  noticeText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 14,
    color: COLORS.mutedText,
  },
  sectionHeader: {
    marginTop: 30,
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
  },
  sectionEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.7,
    color: COLORS.forest,
  },
  sectionTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 25,
    color: COLORS.deepForest,
    marginTop: 4,
  },
  viewAll: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    color: COLORS.mutedText,
  },
  emptyCard: {
    padding: 20,
    borderRadius: 21,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  emptyIcon: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyTitle: {
    marginTop: 15,
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 23,
    color: COLORS.deepForest,
    textAlign: 'center',
  },
  emptyText: {
    marginTop: 6,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 15,
    color: COLORS.mutedText,
    textAlign: 'center',
  },
  previewButton: {
    marginTop: 18,
    minHeight: 46,
    paddingHorizontal: 18,
    borderRadius: 23,
    backgroundColor: COLORS.forest,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  previewButtonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.white,
  },
  footerCard: {
    marginTop: 22,
    padding: 17,
    borderRadius: 20,
    backgroundColor: COLORS.deepForest,
    flexDirection: 'row',
    gap: 12,
    alignItems: 'flex-start',
  },
  footerCopy: {
    flex: 1,
  },
  footerTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 20,
    color: COLORS.white,
  },
  footerText: {
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 14,
    color: COLORS.stone,
    marginTop: 4,
  },
  exit: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  exitText: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.mutedText,
  },
});
