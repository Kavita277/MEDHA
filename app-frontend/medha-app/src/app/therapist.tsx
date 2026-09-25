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

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW, TOP_HEADER_PADDING } from '../constants/theme';
import { MedhaScreenBackground } from '../components/medha-screen-background';
import { THERAPIST_DEMO_CASES, TherapistCaseSummary } from '../constants/demoData';

export default function TherapistDashboardScreen() {
  const router = useRouter();
  const [filter, setFilter] = useState<'all' | 'attention' | 'stable'>('all');

  const allCases = THERAPIST_DEMO_CASES;
  const filteredCases = allCases.filter((c) => {
    if (filter === 'attention') return c.riskLevel === 'Needs Attention';
    if (filter === 'stable') return c.riskLevel === 'Low';
    return true;
  });

  const handleLogout = () => {
    router.replace('/login');
  };

  const handleOpenCase = (caseId: string) => {
    router.push({
      pathname: '/therapist-case',
      params: { caseId },
    });
  };

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" />

        {/* TOP BAR */}
        <View style={styles.topBar}>
          <View style={styles.topBarLeft}>
            <View style={styles.badge}>
              <View style={styles.badgeDot} />
              <Text style={styles.badgeText}>CLINICAL WORKSPACE</Text>
            </View>
            <Text style={styles.topTitle}>Dr. Ananya Roy</Text>
          </View>
          <Pressable
            onPress={handleLogout}
            style={({ pressed }) => [styles.exitBtn, pressed && styles.pressed]}
            accessibilityRole="button"
            accessibilityLabel="Sign out"
          >
            <Ionicons name="log-out-outline" size={16} color={COLORS.navy} />
            <Text style={styles.exitBtnText}>Sign out</Text>
          </Pressable>
        </View>

        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
        >
          {/* HEADER */}
          <View style={styles.header}>
            <Text style={styles.eyebrow}>PATIENT CASE QUEUE</Text>
            <Text style={styles.title}>Your Care Workspace</Text>
            <Text style={styles.subtitle}>
              Explainability-assisted clinical dashboard for active caseload management.
            </Text>
          </View>

          {/* TOP METRICS SUMMARY */}
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <View style={[styles.metricIconWrap, { backgroundColor: '#E1F2FE' }]}>
                <Ionicons name="folder-open" size={17} color="#0284C7" />
              </View>
              <Text style={styles.metricNumber}>8</Text>
              <Text style={styles.metricLabel}>Active Cases</Text>
            </View>

            <View style={styles.metricCard}>
              <View style={[styles.metricIconWrap, { backgroundColor: '#FFEADB' }]}>
                <Ionicons name="alert-circle" size={17} color="#E8663F" />
              </View>
              <Text style={styles.metricNumber}>2</Text>
              <Text style={styles.metricLabel}>Needs Review</Text>
            </View>

            <View style={styles.metricCard}>
              <View style={[styles.metricIconWrap, { backgroundColor: '#FFEBF1' }]}>
                <Ionicons name="notifications" size={17} color="#E8628E" />
              </View>
              <Text style={styles.metricNumber}>1</Text>
              <Text style={styles.metricLabel}>New Alert</Text>
            </View>

            <View style={styles.metricCard}>
              <View style={[styles.metricIconWrap, { backgroundColor: '#E2F5E8' }]}>
                <Ionicons name="checkmark-done-circle" size={17} color="#2D8A4E" />
              </View>
              <Text style={styles.metricNumber}>14</Text>
              <Text style={styles.metricLabel}>Check-ins (7d)</Text>
            </View>
          </View>

          {/* NOTICE BANNER */}
          <View style={styles.noticeCard}>
            <Ionicons name="shield-checkmark" size={18} color="#2D8A4E" />
            <Text style={styles.noticeText}>
              Outputs are non-diagnostic decision-support indicators. Licensed clinician review is required for all care decisions.
            </Text>
          </View>

          {/* FILTER CHIPS */}
          <View style={styles.filterRow}>
            {[
              { id: 'all', label: 'All Cases (5)' },
              { id: 'attention', label: 'Needs Attention (2)' },
              { id: 'stable', label: 'Stable (3)' },
            ].map((item) => {
              const isSelected = filter === item.id;
              return (
                <Pressable
                  key={item.id}
                  onPress={() => setFilter(item.id as typeof filter)}
                  style={[
                    styles.filterChip,
                    isSelected && styles.filterChipActive,
                  ]}
                >
                  <Text
                    style={[
                      styles.filterChipText,
                      isSelected && styles.filterChipTextActive,
                    ]}
                  >
                    {item.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          {/* CASES LIST */}
          <View style={styles.casesList}>
            {filteredCases.map((c) => {
              const isAttention = c.riskLevel === 'Needs Attention';
              return (
                <View key={c.caseId} style={styles.caseCard}>
                  {/* Case Top Bar */}
                  <View style={styles.caseCardTop}>
                    <View style={styles.caseIdGroup}>
                      <Text style={styles.caseIdText}>{c.caseId}</Text>
                      <Text style={styles.casePatientName}>• {c.patientName}</Text>
                    </View>
                    <View
                      style={[
                        styles.statusPill,
                        isAttention ? styles.statusPillAttention : styles.statusPillNormal,
                      ]}
                    >
                      <Text
                        style={[
                          styles.statusPillText,
                          isAttention ? styles.statusPillTextAttention : styles.statusPillTextNormal,
                        ]}
                      >
                        {c.riskLevel}
                      </Text>
                    </View>
                  </View>

                  {/* Wellbeing Status & Trend */}
                  <View style={styles.caseDetailsRow}>
                    <View style={styles.detailItem}>
                      <Text style={styles.detailLabel}>OBSERVED PATTERN</Text>
                      <Text style={styles.detailValue}>{c.wellbeingStatus}</Text>
                    </View>
                    <View style={styles.detailItemRight}>
                      <Text style={styles.detailLabel}>TREND</Text>
                      <View style={styles.trendRow}>
                        <Ionicons
                          name={
                            c.trend === 'Improving'
                              ? 'trending-down'
                              : c.trend === 'Increasing'
                              ? 'trending-up'
                              : 'remove-outline'
                          }
                          size={15}
                          color={
                            c.trend === 'Improving'
                              ? '#2D8A4E'
                              : c.trend === 'Increasing'
                              ? '#E8663F'
                              : '#5B6478'
                          }
                        />
                        <Text
                          style={[
                            styles.trendText,
                            {
                              color:
                                c.trend === 'Improving'
                                  ? '#2D8A4E'
                                  : c.trend === 'Increasing'
                                  ? '#E8663F'
                                  : '#5B6478',
                            },
                          ]}
                        >
                          {c.trend}
                        </Text>
                      </View>
                    </View>
                  </View>

                  {/* Alert banner if active */}
                  {c.alertActive && (
                    <View style={styles.caseAlertBox}>
                      <Ionicons name="warning" size={14} color="#E8663F" />
                      <Text style={styles.caseAlertText}>{c.alertTitle}</Text>
                    </View>
                  )}

                  {/* Card Footer: Last interaction + View button */}
                  <View style={styles.caseCardFooter}>
                    <View style={styles.lastInteractionRow}>
                      <Ionicons name="time-outline" size={13} color={COLORS.navyMuted} />
                      <Text style={styles.lastInteractionText}>{c.lastInteraction}</Text>
                    </View>
                    <Pressable
                      onPress={() => handleOpenCase(c.caseId)}
                      style={({ pressed }) => [styles.viewCaseBtn, pressed && styles.pressed]}
                      accessibilityRole="button"
                      accessibilityLabel={`View case ${c.caseId}`}
                    >
                      <Text style={styles.viewCaseBtnText}>Open Case</Text>
                      <Ionicons name="arrow-forward" size={14} color="#FFFFFF" />
                    </Pressable>
                  </View>
                </View>
              );
            })}
          </View>

          {/* FOOTER HUMAN REASSURANCE */}
          <View style={styles.footerReassurance}>
            <Ionicons name="shield-outline" size={20} color="#7C6EE6" />
            <View style={styles.footerCopy}>
              <Text style={styles.footerTitle}>Human review stays central</Text>
              <Text style={styles.footerText}>
                MEDHA surfaces objective multi-signal indicators to aid consultation preparation. Clinicians retain full autonomy over diagnostic decisions and emergency outreach.
              </Text>
            </View>
          </View>

          <View style={{ height: 40 }} />
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
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: TOP_HEADER_PADDING - (StatusBar.currentHeight ?? 32) + 6,
    paddingBottom: 12,
  },
  topBarLeft: {
    flex: 1,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: RADIUS.pill,
  },
  badgeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#2D8A4E',
  },
  badgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1,
    color: '#2D8A4E',
  },
  topTitle: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 22,
    color: COLORS.navy,
  },
  exitBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    ...SHADOW.card,
  },
  exitBtnText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navy,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 14,
  },
  header: {
    marginBottom: 18,
  },
  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    letterSpacing: 1.2,
    color: '#7C6EE6',
    marginBottom: 4,
  },
  title: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 26,
    color: COLORS.navy,
    letterSpacing: -0.3,
    marginBottom: 4,
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 19,
    color: COLORS.navyMuted,
  },
  metricsGrid: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 16,
  },
  metricCard: {
    flex: 1,
    backgroundColor: COLORS.white,
    borderRadius: 16,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  metricIconWrap: {
    width: 28,
    height: 28,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  metricNumber: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 20,
    color: COLORS.navy,
  },
  metricLabel: {
    fontFamily: 'Nunito-Regular',
    fontSize: 10,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  noticeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    backgroundColor: '#E2F5E8',
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(45, 138, 78, 0.2)',
    marginBottom: 18,
  },
  noticeText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: '#1E6637',
  },
  filterRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  filterChip: {
    paddingHorizontal: 13,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
  },
  filterChipActive: {
    backgroundColor: '#181E2C',
    borderColor: '#181E2C',
  },
  filterChipText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navyMuted,
  },
  filterChipTextActive: {
    color: '#FFFFFF',
    fontFamily: 'Nunito-Bold',
  },
  casesList: {
    gap: 14,
    marginBottom: 20,
  },
  caseCard: {
    backgroundColor: COLORS.white,
    borderRadius: 20,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  caseCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  caseIdGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  caseIdText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 16,
    color: COLORS.navy,
  },
  casePatientName: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 14,
    color: COLORS.navyMuted,
  },
  statusPill: {
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: RADIUS.pill,
  },
  statusPillAttention: {
    backgroundColor: '#FFEADB',
  },
  statusPillNormal: {
    backgroundColor: '#E2F5E8',
  },
  statusPillText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
  },
  statusPillTextAttention: {
    color: '#E8663F',
  },
  statusPillTextNormal: {
    color: '#2D8A4E',
  },
  caseDetailsRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    marginBottom: 12,
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.03)',
  },
  detailItem: {
    flex: 1,
  },
  detailItemRight: {
    alignItems: 'flex-end',
  },
  detailLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 9,
    letterSpacing: 0.8,
    color: COLORS.navyMuted,
    marginBottom: 3,
  },
  detailValue: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    color: COLORS.navy,
  },
  trendRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  trendText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
  },
  caseAlertBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FFF4EE',
    borderRadius: 10,
    padding: 10,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(232, 102, 63, 0.2)',
  },
  caseAlertText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: '#E8663F',
    flex: 1,
  },
  caseCardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#F0F2F5',
  },
  lastInteractionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    flex: 1,
  },
  lastInteractionText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
  },
  viewCaseBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#181E2C',
    paddingHorizontal: 13,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
  },
  viewCaseBtnText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: '#FFFFFF',
  },
  footerReassurance: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  footerCopy: {
    flex: 1,
  },
  footerTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
    marginBottom: 2,
  },
  footerText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
  },
  pressed: {
    opacity: 0.8,
  },
});
