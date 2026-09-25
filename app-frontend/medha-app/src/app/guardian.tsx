import React from 'react';
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
import { GUARDIAN_DEMO_DATA } from '../constants/demoData';

export default function GuardianDashboardScreen() {
  const router = useRouter();
  const data = GUARDIAN_DEMO_DATA;

  const handleLogout = () => {
    router.replace('/login');
  };

  const handleOpenSupport = () => {
    router.push('/support');
  };

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" />

        {/* TOP BAR / LOGOUT */}
        <View style={styles.topBar}>
          <View style={styles.roleBadge}>
            <View style={styles.roleDot} />
            <Text style={styles.roleBadgeText}>GUARDIAN SPACE</Text>
          </View>
          <Pressable
            onPress={handleLogout}
            style={({ pressed }) => [styles.logoutBtn, pressed && styles.pressed]}
            accessibilityRole="button"
            accessibilityLabel="Sign out"
          >
            <Ionicons name="log-out-outline" size={17} color={COLORS.navy} />
            <Text style={styles.logoutBtnText}>Exit</Text>
          </Pressable>
        </View>

        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
        >
          {/* HEADER */}
          <View style={styles.header}>
            <Text style={styles.eyebrow}>WELLBEING GUARDIAN</Text>
            <Text style={styles.title}>Your linked care space</Text>
            <Text style={styles.subtitle}>
              Gentle, high-level wellbeing summaries for {data.linkedPatient.name}.
            </Text>
          </View>

          {/* LINKED PATIENT CARD */}
          <View style={styles.patientCard}>
            <View style={styles.patientCardHeader}>
              <View style={styles.avatarWrap}>
                <Ionicons name="person" size={24} color="#0284C7" />
              </View>
              <View style={styles.patientMeta}>
                <Text style={styles.patientName}>{data.linkedPatient.name}</Text>
                <Text style={styles.patientId}>Care ID: {data.linkedPatient.patientId}</Text>
              </View>
              <View style={styles.activePill}>
                <View style={styles.activeDot} />
                <Text style={styles.activePillText}>Active</Text>
              </View>
            </View>

            {/* Wellbeing Status Badge */}
            <View style={styles.statusBox}>
              <View style={styles.statusRow}>
                <Ionicons name="checkmark-circle" size={18} color="#2D8A4E" />
                <Text style={styles.statusLabel}>Current State</Text>
              </View>
              <Text style={styles.statusValue}>{data.linkedPatient.wellbeingStatus}</Text>
            </View>

            {/* Patient Stats Grid */}
            <View style={styles.patientStatsGrid}>
              <View style={styles.statCell}>
                <View style={[styles.statIconBadge, { backgroundColor: '#FFEADB' }]}>
                  <Ionicons name="flame" size={16} color="#E8663F" />
                </View>
                <Text style={styles.statCellNumber}>{data.linkedPatient.streakDays} Days</Text>
                <Text style={styles.statCellLabel}>Consistency Streak</Text>
              </View>

              <View style={styles.statCell}>
                <View style={[styles.statIconBadge, { backgroundColor: '#E1F2FE' }]}>
                  <Ionicons name="time-outline" size={16} color="#0284C7" />
                </View>
                <Text style={styles.statCellNumber}>10:15 AM</Text>
                <Text style={styles.statCellLabel}>Last Check-in</Text>
              </View>
            </View>

            {/* Recent Activity */}
            <View style={styles.activityRow}>
              <Ionicons name="sparkles-outline" size={15} color={COLORS.navyMuted} />
              <Text style={styles.activityText}>
                Last activity: {data.linkedPatient.lastActivity}
              </Text>
            </View>
          </View>

          {/* WELLBEING SUMMARY */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Wellbeing Summary</Text>
            <Text style={styles.sectionSubtitle}>
              Observed trends over the past 7 days
            </Text>

            <View style={styles.summaryCard}>
              <View style={styles.summaryItem}>
                <View style={[styles.summaryIconBadge, { backgroundColor: '#E2F5E8' }]}>
                  <Ionicons name="trending-up" size={18} color="#2D8A4E" />
                </View>
                <View style={styles.summaryCopy}>
                  <Text style={styles.summaryItemTitle}>Mood Trajectory</Text>
                  <Text style={styles.summaryItemDesc}>{data.wellbeingSummary.moodTrendText}</Text>
                </View>
              </View>

              <View style={styles.divider} />

              <View style={styles.summaryItem}>
                <View style={[styles.summaryIconBadge, { backgroundColor: '#FFEADB' }]}>
                  <Ionicons name="calendar-outline" size={18} color="#E8663F" />
                </View>
                <View style={styles.summaryCopy}>
                  <Text style={styles.summaryItemTitle}>Check-in Adherence</Text>
                  <Text style={styles.summaryItemDesc}>
                    {data.wellbeingSummary.checkInConsistencyPct}% consistency this month
                  </Text>
                </View>
              </View>

              <View style={styles.divider} />

              <View style={styles.summaryItem}>
                <View style={[styles.summaryIconBadge, { backgroundColor: '#EEE9FA' }]}>
                  <Ionicons name="heart-outline" size={18} color="#7C6EE6" />
                </View>
                <View style={styles.summaryCopy}>
                  <Text style={styles.summaryItemTitle}>Recent Support Engagement</Text>
                  <Text style={styles.summaryItemDesc}>{data.wellbeingSummary.recentSupportActivity}</Text>
                </View>
              </View>
            </View>
          </View>

          {/* CARE PROFESSIONAL */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Assigned Care Professional</Text>
            <View style={styles.careCard}>
              <View style={styles.careCardTop}>
                <View style={[styles.careAvatarWrap, { backgroundColor: '#E2F5E8' }]}>
                  <Ionicons name="medkit" size={22} color="#2D8A4E" />
                </View>
                <View style={styles.careMeta}>
                  <Text style={styles.careName}>{data.careProfessional.name}</Text>
                  <Text style={styles.careTitle}>{data.careProfessional.title}</Text>
                  <Text style={styles.careClinic}>{data.careProfessional.clinic}</Text>
                </View>
              </View>
              <View style={styles.careActionRow}>
                <Pressable
                  onPress={handleOpenSupport}
                  style={({ pressed }) => [styles.careContactBtn, pressed && styles.pressed]}
                >
                  <Ionicons name="chatbubbles-outline" size={15} color={COLORS.navy} />
                  <Text style={styles.careContactBtnText}>Contact via Care Team</Text>
                </Pressable>
              </View>
            </View>
          </View>

          {/* EMERGENCY & SUPPORT ACCESS */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Safety & Helplines</Text>
            <View style={styles.emergencyCard}>
              <View style={styles.emergencyCardHeader}>
                <View style={[styles.emergencyIconWrap, { backgroundColor: '#FFEBF1' }]}>
                  <Ionicons name="shield-outline" size={20} color="#E8628E" />
                </View>
                <View style={styles.emergencyCopy}>
                  <Text style={styles.emergencyCardTitle}>Need urgent assistance?</Text>
                  <Text style={styles.emergencyCardText}>
                    Access the verified MEDHA Emergency Support protocol and 24/7 national helplines.
                  </Text>
                </View>
              </View>

              <Pressable
                onPress={handleOpenSupport}
                style={({ pressed }) => [styles.emergencyBtn, pressed && styles.pressed]}
                accessibilityRole="button"
                accessibilityLabel="Open Emergency Support"
              >
                <Ionicons name="call" size={17} color={COLORS.white} />
                <Text style={styles.emergencyBtnText}>Open Emergency Support & Helplines</Text>
              </Pressable>
            </View>
          </View>

          {/* PRIVACY NOTICE */}
          <View style={styles.privacyCard}>
            <Ionicons name="lock-closed-outline" size={16} color={COLORS.navyMuted} />
            <Text style={styles.privacyText}>
              Guardian access is limited to high-level wellbeing summaries agreed upon in the patient care plan. Private journals and audio check-in notes remain confidential.
            </Text>
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
    backgroundColor: 'transparent',
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: TOP_HEADER_PADDING - (StatusBar.currentHeight ?? 32) + 6,
    paddingBottom: 8,
  },
  roleBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
  },
  roleDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: '#E8663F',
  },
  roleBadgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    letterSpacing: 0.8,
    color: COLORS.navy,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
  },
  logoutBtnText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    color: COLORS.navy,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 12,
  },
  header: {
    marginBottom: 20,
  },
  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    letterSpacing: 1.2,
    color: '#8A7A64',
    marginBottom: 4,
  },
  title: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 28,
    color: COLORS.navy,
    letterSpacing: -0.3,
    marginBottom: 4,
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 20,
    color: COLORS.navyMuted,
  },
  patientCard: {
    backgroundColor: COLORS.white,
    borderRadius: 22,
    padding: 18,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  patientCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  avatarWrap: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#E1F2FE',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  patientMeta: {
    flex: 1,
  },
  patientName: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 18,
    color: COLORS.navy,
  },
  patientId: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  activePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#E2F5E8',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: RADIUS.pill,
  },
  activeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#2D8A4E',
  },
  activePillText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    color: '#2D8A4E',
  },
  statusBox: {
    backgroundColor: '#F7FAF7',
    borderRadius: 14,
    padding: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#2D8A4E',
    marginBottom: 14,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  statusLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    color: '#2D8A4E',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statusValue: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 14,
    color: COLORS.navy,
  },
  patientStatsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 12,
  },
  statCell: {
    flex: 1,
    backgroundColor: '#F9FAFB',
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.04)',
  },
  statIconBadge: {
    width: 30,
    height: 30,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  statCellNumber: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 16,
    color: COLORS.navy,
  },
  statCellLabel: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  activityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#F0F2F5',
  },
  activityText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    flex: 1,
  },
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 18,
    color: COLORS.navy,
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    color: COLORS.navyMuted,
    marginBottom: 12,
  },
  summaryCard: {
    backgroundColor: COLORS.white,
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  summaryItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 6,
  },
  summaryIconBadge: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  summaryCopy: {
    flex: 1,
  },
  summaryItemTitle: {
    fontFamily: 'Nunito-Bold',
    fontSize: 14,
    color: COLORS.navy,
  },
  summaryItemDesc: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: '#F0F2F5',
    marginVertical: 8,
  },
  careCard: {
    backgroundColor: COLORS.white,
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  careCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  careAvatarWrap: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  careMeta: {
    flex: 1,
  },
  careName: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 16,
    color: COLORS.navy,
  },
  careTitle: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginTop: 1,
  },
  careClinic: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: '#8A92A6',
    marginTop: 1,
  },
  careActionRow: {
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F0F2F5',
  },
  careContactBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 10,
    borderRadius: RADIUS.medium,
    backgroundColor: '#F2F4F7',
  },
  careContactBtnText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 13,
    color: COLORS.navy,
  },
  emergencyCard: {
    backgroundColor: COLORS.white,
    borderRadius: 22,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(232, 98, 142, 0.15)',
    ...SHADOW.card,
  },
  emergencyCardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 14,
  },
  emergencyIconWrap: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  emergencyCopy: {
    flex: 1,
  },
  emergencyCardTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 15,
    color: COLORS.navy,
  },
  emergencyCardText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  emergencyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    borderRadius: RADIUS.medium,
    backgroundColor: '#181E2C',
  },
  emergencyBtnText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 13,
    color: COLORS.white,
  },
  privacyCard: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.65)',
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.04)',
  },
  privacyText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
  },
  pressed: {
    opacity: 0.85,
    transform: [{ scale: 0.98 }],
  },
});
