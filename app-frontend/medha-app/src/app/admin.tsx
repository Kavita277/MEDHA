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
import { ADMIN_DEMO_DATA } from '../constants/demoData';

type AdminTab = 'overview' | 'patients' | 'therapists' | 'cases' | 'audit';

export default function AdminDashboardScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const data = ADMIN_DEMO_DATA;

  const handleLogout = () => {
    router.replace('/login');
  };

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" />

        {/* TOP BAR */}
        <View style={styles.topBar}>
          <View style={styles.topBarLeft}>
            <View style={styles.adminBadge}>
              <Ionicons name="shield-checkmark" size={14} color="#7C6EE6" />
              <Text style={styles.adminBadgeText}>ADMIN OPS</Text>
            </View>
            <Text style={styles.headerTitle}>System Governance</Text>
          </View>
          <Pressable
            onPress={handleLogout}
            style={({ pressed }) => [styles.logoutBtn, pressed && styles.pressed]}
            accessibilityRole="button"
            accessibilityLabel="Sign out"
          >
            <Ionicons name="log-out-outline" size={16} color={COLORS.navy} />
            <Text style={styles.logoutBtnText}>Sign out</Text>
          </Pressable>
        </View>

        {/* TABS NAVIGATION */}
        <View style={styles.tabsWrapper}>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.tabsScroll}
          >
            {[
              { id: 'overview', label: 'Overview', icon: 'grid-outline' },
              { id: 'patients', label: 'Patients', icon: 'people-outline' },
              { id: 'therapists', label: 'Therapists', icon: 'medkit-outline' },
              { id: 'cases', label: 'Cases & Alerts', icon: 'folder-outline' },
              { id: 'audit', label: 'Audit Trail', icon: 'receipt-outline' },
            ].map((tab) => {
              const isSelected = activeTab === tab.id;
              return (
                <Pressable
                  key={tab.id}
                  onPress={() => setActiveTab(tab.id as AdminTab)}
                  style={[
                    styles.tabChip,
                    isSelected && styles.tabChipActive,
                  ]}
                  accessibilityRole="tab"
                  accessibilityState={{ selected: isSelected }}
                >
                  <Ionicons
                    name={tab.icon as keyof typeof Ionicons.glyphMap}
                    size={14}
                    color={isSelected ? '#FFFFFF' : COLORS.navyMuted}
                  />
                  <Text
                    style={[
                      styles.tabChipText,
                      isSelected && styles.tabChipTextActive,
                    ]}
                  >
                    {tab.label}
                  </Text>
                </Pressable>
              );
            })}
          </ScrollView>
        </View>

        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
        >
          {/* TAB: OVERVIEW */}
          {activeTab === 'overview' && (
            <View>
              {/* TOP METRICS GRID */}
              <View style={styles.metricsGrid}>
                <View style={styles.metricCard}>
                  <View style={[styles.metricIconWrap, { backgroundColor: '#E1F2FE' }]}>
                    <Ionicons name="people" size={18} color="#0284C7" />
                  </View>
                  <Text style={styles.metricValue}>{data.overview.totalPatients}</Text>
                  <Text style={styles.metricLabel}>Total Patients</Text>
                </View>

                <View style={styles.metricCard}>
                  <View style={[styles.metricIconWrap, { backgroundColor: '#FFEADB' }]}>
                    <Ionicons name="folder" size={18} color="#E8663F" />
                  </View>
                  <Text style={styles.metricValue}>{data.overview.activeCases}</Text>
                  <Text style={styles.metricLabel}>Active Cases</Text>
                </View>

                <View style={styles.metricCard}>
                  <View style={[styles.metricIconWrap, { backgroundColor: '#E2F5E8' }]}>
                    <Ionicons name="medkit" size={18} color="#2D8A4E" />
                  </View>
                  <Text style={styles.metricValue}>{data.overview.activeTherapists}</Text>
                  <Text style={styles.metricLabel}>Clinicians</Text>
                </View>

                <View style={styles.metricCard}>
                  <View style={[styles.metricIconWrap, { backgroundColor: '#FFEBF1' }]}>
                    <Ionicons name="alert-circle" size={18} color="#E8628E" />
                  </View>
                  <Text style={styles.metricValue}>{data.overview.openAlerts}</Text>
                  <Text style={styles.metricLabel}>Open Alerts</Text>
                </View>
              </View>

              {/* SYSTEM HEALTH STATUS */}
              <View style={styles.sectionCard}>
                <View style={styles.sectionHeader}>
                  <View style={styles.sectionTitleRow}>
                    <Ionicons name="pulse" size={18} color="#2D8A4E" />
                    <Text style={styles.sectionTitle}>System & Pipeline Health</Text>
                  </View>
                  <View style={styles.liveIndicator}>
                    <View style={styles.liveDot} />
                    <Text style={styles.liveText}>All Systems Normal</Text>
                  </View>
                </View>

                <View style={styles.statusList}>
                  <View style={styles.statusRow}>
                    <View style={styles.statusLeft}>
                      <Ionicons name="server-outline" size={16} color={COLORS.navyMuted} />
                      <Text style={styles.statusServiceName}>FastAPI Core Backend</Text>
                    </View>
                    <View style={styles.statusRight}>
                      <Text style={styles.statusBadgeGreen}>Uptime {data.systemStatus.backend.uptime}</Text>
                      <Text style={styles.statusLatency}>{data.systemStatus.backend.latency}</Text>
                    </View>
                  </View>

                  <View style={styles.statusDivider} />

                  <View style={styles.statusRow}>
                    <View style={styles.statusLeft}>
                      <Ionicons name="hardware-chip-outline" size={16} color={COLORS.navyMuted} />
                      <Text style={styles.statusServiceName}>Explainability & Fusion Engine</Text>
                    </View>
                    <View style={styles.statusRight}>
                      <Text style={styles.statusBadgeGreen}>Uptime {data.systemStatus.aiPipeline.uptime}</Text>
                      <Text style={styles.statusLatency}>{data.systemStatus.aiPipeline.latency}</Text>
                    </View>
                  </View>

                  <View style={styles.statusDivider} />

                  <View style={styles.statusRow}>
                    <View style={styles.statusLeft}>
                      <Ionicons name="notifications-outline" size={16} color={COLORS.navyMuted} />
                      <Text style={styles.statusServiceName}>Celery Worker Queue</Text>
                    </View>
                    <View style={styles.statusRight}>
                      <Text style={styles.statusBadgeGreen}>{data.systemStatus.notifications.activeWorkers} Workers Active</Text>
                    </View>
                  </View>

                  <View style={styles.statusDivider} />

                  <View style={styles.statusRow}>
                    <View style={styles.statusLeft}>
                      <Ionicons name="watch-outline" size={16} color={COLORS.navyMuted} />
                      <Text style={styles.statusServiceName}>Connected Wearable Bridge</Text>
                    </View>
                    <View style={styles.statusRight}>
                      <Text style={styles.statusBadgeGreen}>{data.systemStatus.deviceGateway.connectedDevices} Paired</Text>
                    </View>
                  </View>
                </View>
              </View>

              {/* RECENT ALERTS PREVIEW */}
              <View style={styles.sectionCard}>
                <View style={styles.sectionHeader}>
                  <View style={styles.sectionTitleRow}>
                    <Ionicons name="warning-outline" size={18} color="#E8663F" />
                    <Text style={styles.sectionTitle}>High Priority Queue</Text>
                  </View>
                  <Pressable onPress={() => setActiveTab('cases')}>
                    <Text style={styles.sectionAction}>View all</Text>
                  </Pressable>
                </View>

                {data.alerts.map((alt) => (
                  <View key={alt.id} style={styles.alertItem}>
                    <View
                      style={[
                        styles.alertSeverityDot,
                        {
                          backgroundColor:
                            alt.severity === 'High'
                              ? '#E8663F'
                              : alt.severity === 'Medium'
                              ? '#E8A93D'
                              : '#2D8A4E',
                        },
                      ]}
                    />
                    <View style={styles.alertCopy}>
                      <Text style={styles.alertTitle}>{alt.title}</Text>
                      <Text style={styles.alertMeta}>
                        {alt.caseId} • {alt.timestamp}
                      </Text>
                    </View>
                    <View
                      style={[
                        styles.alertStatusPill,
                        alt.status === 'Pending Review'
                          ? styles.alertStatusPending
                          : styles.alertStatusAck,
                      ]}
                    >
                      <Text
                        style={[
                          styles.alertStatusText,
                          alt.status === 'Pending Review'
                            ? styles.alertStatusTextPending
                            : styles.alertStatusTextAck,
                        ]}
                      >
                        {alt.status}
                      </Text>
                    </View>
                  </View>
                ))}
              </View>
            </View>
          )}

          {/* TAB: PATIENTS */}
          {activeTab === 'patients' && (
            <View style={styles.sectionCard}>
              <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>Enrolled Patients ({data.patients.length})</Text>
              </View>
              {data.patients.map((pt) => (
                <View key={pt.id} style={styles.dataListItem}>
                  <View style={styles.dataListIcon}>
                    <Ionicons name="person-outline" size={18} color="#0284C7" />
                  </View>
                  <View style={styles.dataListCopy}>
                    <Text style={styles.dataListPrimary}>{pt.name}</Text>
                    <Text style={styles.dataListSecondary}>
                      ID: {pt.id} • Assigned: {pt.assignedTherapist}
                    </Text>
                    <Text style={styles.dataListMeta}>Last activity: {pt.lastActivity}</Text>
                  </View>
                  <View
                    style={[
                      styles.statusTag,
                      pt.status === 'Under Review'
                        ? { backgroundColor: '#FFEADB' }
                        : { backgroundColor: '#E2F5E8' },
                    ]}
                  >
                    <Text
                      style={[
                        styles.statusTagText,
                        pt.status === 'Under Review' ? { color: '#E8663F' } : { color: '#2D8A4E' },
                      ]}
                    >
                      {pt.status}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          )}

          {/* TAB: THERAPISTS */}
          {activeTab === 'therapists' && (
            <View style={styles.sectionCard}>
              <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>Registered Clinicians ({data.therapists.length})</Text>
              </View>
              {data.therapists.map((th) => (
                <View key={th.id} style={styles.dataListItem}>
                  <View style={[styles.dataListIcon, { backgroundColor: '#E2F5E8' }]}>
                    <Ionicons name="medkit" size={18} color="#2D8A4E" />
                  </View>
                  <View style={styles.dataListCopy}>
                    <Text style={styles.dataListPrimary}>{th.name}</Text>
                    <Text style={styles.dataListSecondary}>Lic: {th.license}</Text>
                    <Text style={styles.dataListMeta}>{th.activeCases} Active Cases</Text>
                  </View>
                  <View style={[styles.statusTag, { backgroundColor: '#E2F5E8' }]}>
                    <Text style={[styles.statusTagText, { color: '#2D8A4E' }]}>{th.status}</Text>
                  </View>
                </View>
              ))}
            </View>
          )}

          {/* TAB: CASES & ALERTS */}
          {activeTab === 'cases' && (
            <View style={styles.sectionCard}>
              <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>Active Clinical Cases ({data.cases.length})</Text>
              </View>
              {data.cases.map((cs) => (
                <View key={cs.id} style={styles.dataListItem}>
                  <View style={[styles.dataListIcon, { backgroundColor: '#EEE9FA' }]}>
                    <Ionicons name="folder-open" size={18} color="#7C6EE6" />
                  </View>
                  <View style={styles.dataListCopy}>
                    <Text style={styles.dataListPrimary}>{cs.id} · {cs.patientName}</Text>
                    <Text style={styles.dataListSecondary}>Clinician: {cs.therapistName}</Text>
                    <Text style={styles.dataListMeta}>Opened: {cs.openedDate} • {cs.status}</Text>
                  </View>
                  <View
                    style={[
                      styles.statusTag,
                      cs.priority === 'Immediate Review'
                        ? { backgroundColor: '#FFEBF1' }
                        : cs.priority === 'High'
                        ? { backgroundColor: '#FFEADB' }
                        : { backgroundColor: '#F0F2F5' },
                    ]}
                  >
                    <Text
                      style={[
                        styles.statusTagText,
                        cs.priority === 'Immediate Review'
                          ? { color: '#E8628E' }
                          : cs.priority === 'High'
                          ? { color: '#E8663F' }
                          : { color: COLORS.navyMuted },
                      ]}
                    >
                      {cs.priority}
                    </Text>
                  </View>
                </View>
              ))}
            </View>
          )}

          {/* TAB: AUDIT TRAIL */}
          {activeTab === 'audit' && (
            <View style={styles.sectionCard}>
              <View style={styles.sectionHeader}>
                <Text style={styles.sectionTitle}>System Audit Trail</Text>
                <Text style={styles.auditSubtitle}>Compliance log entries</Text>
              </View>
              {data.auditLogs.map((log) => (
                <View key={log.id} style={styles.auditItem}>
                  <View style={styles.auditItemTop}>
                    <Text style={styles.auditAction}>{log.action}</Text>
                    <View
                      style={[
                        styles.auditStatusBadge,
                        log.status === 'SUCCESS' ? styles.auditSuccess : styles.auditDenied,
                      ]}
                    >
                      <Text
                        style={[
                          styles.auditStatusText,
                          log.status === 'SUCCESS' ? styles.auditTextSuccess : styles.auditTextDenied,
                        ]}
                      >
                        {log.status}
                      </Text>
                    </View>
                  </View>
                  <Text style={styles.auditMeta}>
                    Actor: {log.actor} ({log.role}) • Target: {log.resource}
                  </Text>
                  <Text style={styles.auditTimestamp}>{log.timestamp}</Text>
                </View>
              ))}
            </View>
          )}

          {/* DEMO NOTICE */}
          <View style={styles.demoNotice}>
            <Ionicons name="information-circle-outline" size={15} color={COLORS.navyMuted} />
            <Text style={styles.demoNoticeText}>
              Frontend demonstration mode. Live statistics sync with backend audit endpoints when connected.
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
  adminBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginBottom: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    alignSelf: 'flex-start',
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: RADIUS.pill,
  },
  adminBadgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1,
    color: '#7C6EE6',
  },
  headerTitle: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 22,
    color: COLORS.navy,
  },
  logoutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    ...SHADOW.card,
  },
  logoutBtnText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navy,
  },
  tabsWrapper: {
    marginBottom: 6,
  },
  tabsScroll: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    gap: 8,
  },
  tabChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
  },
  tabChipActive: {
    backgroundColor: '#181E2C',
    borderColor: '#181E2C',
  },
  tabChipText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navyMuted,
  },
  tabChipTextActive: {
    color: '#FFFFFF',
    fontFamily: 'Nunito-Bold',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 8,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    marginBottom: 16,
  },
  metricCard: {
    width: '48.5%',
    backgroundColor: COLORS.white,
    borderRadius: 18,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  metricIconWrap: {
    width: 32,
    height: 32,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  metricValue: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 22,
    color: COLORS.navy,
  },
  metricLabel: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  sectionCard: {
    backgroundColor: COLORS.white,
    borderRadius: 20,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  sectionTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 16,
    color: COLORS.navy,
  },
  auditSubtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
  },
  sectionAction: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: '#7C6EE6',
  },
  liveIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#E2F5E8',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: RADIUS.pill,
  },
  liveDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#2D8A4E',
  },
  liveText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    color: '#2D8A4E',
  },
  statusList: {},
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
  },
  statusLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    flex: 1,
  },
  statusServiceName: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    color: COLORS.navy,
  },
  statusRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusBadgeGreen: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    color: '#2D8A4E',
    backgroundColor: '#E2F5E8',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  statusLatency: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
  },
  statusDivider: {
    height: 1,
    backgroundColor: '#F0F2F5',
  },
  alertItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F2F5',
  },
  alertSeverityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 12,
  },
  alertCopy: {
    flex: 1,
  },
  alertTitle: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    color: COLORS.navy,
  },
  alertMeta: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  alertStatusPill: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  alertStatusPending: {
    backgroundColor: '#FFEADB',
  },
  alertStatusAck: {
    backgroundColor: '#E2F5E8',
  },
  alertStatusText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
  },
  alertStatusTextPending: {
    color: '#E8663F',
  },
  alertStatusTextAck: {
    color: '#2D8A4E',
  },
  dataListItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F2F5',
  },
  dataListIcon: {
    width: 38,
    height: 38,
    borderRadius: 12,
    backgroundColor: '#E1F2FE',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  dataListCopy: {
    flex: 1,
  },
  dataListPrimary: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 15,
    color: COLORS.navy,
  },
  dataListSecondary: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginTop: 1,
  },
  dataListMeta: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: '#8A92A6',
    marginTop: 2,
  },
  statusTag: {
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: RADIUS.pill,
  },
  statusTagText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
  },
  auditItem: {
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#F0F2F5',
  },
  auditItemTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  auditAction: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: COLORS.navy,
  },
  auditStatusBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  auditSuccess: {
    backgroundColor: '#E2F5E8',
  },
  auditDenied: {
    backgroundColor: '#FFEBF1',
  },
  auditStatusText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 9,
  },
  auditTextSuccess: {
    color: '#2D8A4E',
  },
  auditTextDenied: {
    color: '#E8628E',
  },
  auditMeta: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
  },
  auditTimestamp: {
    fontFamily: 'Nunito-Regular',
    fontSize: 10,
    color: '#8A92A6',
    marginTop: 2,
  },
  demoNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 12,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    marginTop: 8,
  },
  demoNoticeText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
    flex: 1,
  },
  pressed: {
    opacity: 0.8,
  },
});
