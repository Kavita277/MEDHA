import React, { useState } from 'react';
import {
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW, TOP_HEADER_PADDING } from '../constants/theme';
import { MedhaScreenBackground } from '../components/medha-screen-background';
import { THERAPIST_DEMO_CASE_DETAILS, TherapistCaseDetail } from '../constants/demoData';

export default function TherapistCaseScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ caseId?: string }>();
  const activeCaseId = params.caseId ?? 'CASE-9021';

  const caseData: TherapistCaseDetail =
    THERAPIST_DEMO_CASE_DETAILS[activeCaseId] ?? THERAPIST_DEMO_CASE_DETAILS['CASE-9021'];

  const [noteModalVisible, setNoteModalVisible] = useState(false);
  const [newNote, setNewNote] = useState('');
  const [notesList, setNotesList] = useState<string[]>([
    'Scheduled for follow-up evaluation. Focus on sleep routine & workload management.',
  ]);

  const handleAddNote = () => {
    if (newNote.trim()) {
      setNotesList((prev) => [newNote.trim(), ...prev]);
      setNewNote('');
      setNoteModalVisible(false);
    }
  };

  const handleOpenEmergencySupport = () => {
    router.push('/support');
  };

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safe} edges={['top', 'bottom']}>
        <StatusBar barStyle="dark-content" backgroundColor="transparent" />

        {/* TOP BAR */}
        <View style={styles.topBar}>
          <Pressable
            onPress={() => router.back()}
            style={({ pressed }) => [styles.backBtn, pressed && styles.pressed]}
            accessibilityRole="button"
            accessibilityLabel="Back to cases"
          >
            <Ionicons name="arrow-back" size={20} color={COLORS.navy} />
          </Pressable>
          <View style={styles.topBarCenter}>
            <Text style={styles.topBarId}>{caseData.caseId}</Text>
            <Text style={styles.topBarPatient}>{caseData.patientName}</Text>
          </View>
          <View
            style={[
              styles.topStatusPill,
              caseData.riskLevel === 'Needs Attention'
                ? styles.pillAttention
                : styles.pillNormal,
            ]}
          >
            <Text
              style={[
                styles.topStatusText,
                caseData.riskLevel === 'Needs Attention'
                  ? styles.textAttention
                  : styles.textNormal,
              ]}
            >
              {caseData.riskLevel}
            </Text>
          </View>
        </View>

        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
        >
          {/* HEADER SUMMARY CARD */}
          <View style={styles.summaryCard}>
            <View style={styles.summaryCardHeader}>
              <View style={styles.patientAvatar}>
                <Ionicons name="person" size={20} color="#0284C7" />
              </View>
              <View style={styles.summaryHeaderCopy}>
                <Text style={styles.patientName}>{caseData.patientName}</Text>
                <Text style={styles.patientSub}>Care ID: {caseData.patientId} • Timepoint: T2</Text>
              </View>
            </View>

            <View style={styles.summaryGrid}>
              <View style={styles.summaryCol}>
                <Text style={styles.gridLabel}>CURRENT STATE</Text>
                <Text style={styles.gridValue}>{caseData.status}</Text>
              </View>
              <View style={styles.summaryCol}>
                <Text style={styles.gridLabel}>7-DAY TRAJECTORY</Text>
                <View style={styles.trendInline}>
                  <Ionicons
                    name={caseData.trend === 'Increasing' ? 'trending-up' : 'trending-down'}
                    size={16}
                    color={caseData.trend === 'Increasing' ? '#E8663F' : '#2D8A4E'}
                  />
                  <Text
                    style={[
                      styles.trendValue,
                      { color: caseData.trend === 'Increasing' ? '#E8663F' : '#2D8A4E' },
                    ]}
                  >
                    {caseData.trend}
                  </Text>
                </View>
              </View>
            </View>

            <View style={styles.metaRow}>
              <Text style={styles.metaText}>Last check-in: {caseData.lastCheckIn}</Text>
              <Text style={styles.metaText}>Interaction: {caseData.lastInteraction}</Text>
            </View>
          </View>

          {/* SAFETY / ALERTS SECTION (VISUALLY DISTINCT) */}
          <View style={styles.safetyCard}>
            <View style={styles.safetyHeader}>
              <View style={styles.safetyIconWrap}>
                <Ionicons name="alert-circle-outline" size={20} color="#E8663F" />
              </View>
              <View style={styles.safetyHeaderCopy}>
                <Text style={styles.safetyTitle}>{caseData.safetyAlert.title}</Text>
                <Text style={styles.safetySub}>Clinical Safety Protocol Notification</Text>
              </View>
            </View>

            <Text style={styles.safetyDescription}>
              {caseData.safetyAlert.description}
            </Text>

            <View style={styles.safetyActionRow}>
              <Pressable
                onPress={handleOpenEmergencySupport}
                style={({ pressed }) => [styles.safetySupportBtn, pressed && styles.pressed]}
                accessibilityRole="button"
                accessibilityLabel="View emergency protocol"
              >
                <Ionicons name="call" size={15} color="#FFFFFF" />
                <Text style={styles.safetySupportBtnText}>View Emergency Protocol & Contacts</Text>
              </Pressable>
            </View>
          </View>

          {/* EXPLAINABILITY SECTION (CORE FEATURE) */}
          <View style={styles.sectionCard}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionIconBadge}>
                <Ionicons name="bulb-outline" size={17} color="#7C6EE6" />
              </View>
              <View style={styles.sectionHeaderCopy}>
                <Text style={styles.sectionEyebrow}>EXPLAINABILITY INSIGHTS</Text>
                <Text style={styles.sectionTitle}>{caseData.explainability.headline}</Text>
              </View>
            </View>

            <Text style={styles.explainNotice}>
              These observations summarize multimodal signals and deviations from personal baseline. They are non-diagnostic decision-support aids.
            </Text>

            <View style={styles.factorsList}>
              {caseData.explainability.factors.map((factor) => (
                <View key={factor.id} style={styles.factorItem}>
                  <View style={styles.factorItemTop}>
                    <View
                      style={[
                        styles.factorTypeTag,
                        factor.severity === 'attention'
                          ? styles.factorTagAttention
                          : styles.factorTagNotice,
                      ]}
                    >
                      <Text
                        style={[
                          styles.factorTypeTagText,
                          factor.severity === 'attention'
                            ? styles.factorTextAttention
                            : styles.factorTextNotice,
                        ]}
                      >
                        {factor.type} Signal
                      </Text>
                    </View>
                    <Text style={styles.factorItemTitle}>{factor.title}</Text>
                  </View>
                  <Text style={styles.factorItemDesc}>{factor.description}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* TEMPORAL / LONGITUDINAL TREND */}
          <View style={styles.sectionCard}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionIconBadge}>
                <Ionicons name="analytics-outline" size={17} color="#2D8A4E" />
              </View>
              <View style={styles.sectionHeaderCopy}>
                <Text style={styles.sectionEyebrow}>LONGITUDINAL CONTEXT</Text>
                <Text style={styles.sectionTitle}>7-Day Trajectory</Text>
              </View>
            </View>

            <Text style={styles.baselineDeviationText}>
              {caseData.temporalTrend.changeFromBaseline}
            </Text>

            {/* Longitudinal Bar Visualization */}
            <View style={styles.chartContainer}>
              <View style={styles.chartBars}>
                {caseData.temporalTrend.points.map((pt, idx) => {
                  const barHeight = Math.max(16, (pt.value / 100) * 80);
                  const isHigh = pt.value > 55;
                  return (
                    <View key={idx} style={styles.barCol}>
                      <Text style={styles.barValText}>{pt.value}%</Text>
                      <View style={styles.barTrack}>
                        <View
                          style={[
                            styles.barFill,
                            {
                              height: barHeight,
                              backgroundColor: isHigh ? '#E8663F' : '#7C6EE6',
                            },
                          ]}
                        />
                      </View>
                      <Text style={styles.barDayText}>{pt.day}</Text>
                    </View>
                  );
                })}
              </View>
            </View>
          </View>

          {/* MODALITY SIGNALS BREAKDOWN */}
          <View style={styles.sectionCard}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionIconBadge}>
                <Ionicons name="layers-outline" size={17} color="#0284C7" />
              </View>
              <View style={styles.sectionHeaderCopy}>
                <Text style={styles.sectionEyebrow}>OBSERVED SPECIALIST SIGNALS</Text>
                <Text style={styles.sectionTitle}>Modality Indicator Breakdown</Text>
              </View>
            </View>

            <View style={styles.modalityList}>
              {[
                {
                  label: 'Text Distress Indicator',
                  data: caseData.modalitySignals.textDistress,
                  icon: 'chatbubble-ellipses-outline',
                },
                {
                  label: 'Voice Acoustic Distress',
                  data: caseData.modalitySignals.voiceDistress,
                  icon: 'mic-outline',
                },
                {
                  label: 'Behavioural Risk Indicator',
                  data: caseData.modalitySignals.behaviouralRisk,
                  icon: 'time-outline',
                },
                {
                  label: 'Structured Intake Response',
                  data: caseData.modalitySignals.structuredIntake,
                  icon: 'clipboard-outline',
                },
                {
                  label: 'Temporal Trajectory Risk',
                  data: caseData.modalitySignals.temporalRisk,
                  icon: 'trending-up-outline',
                },
              ].map((mod, i) => (
                <View key={i} style={styles.modalityRow}>
                  <View style={styles.modalityHeader}>
                    <View style={styles.modalityLabelWrap}>
                      <Ionicons
                        name={mod.icon as keyof typeof Ionicons.glyphMap}
                        size={15}
                        color={COLORS.navy}
                      />
                      <Text style={styles.modalityLabel}>{mod.label}</Text>
                    </View>
                    <Text style={styles.modalityScore}>
                      {mod.data.value !== null ? mod.data.label : 'Not available'}
                    </Text>
                  </View>
                  <Text style={styles.modalityInterp}>
                    {mod.data.value !== null
                      ? mod.data.interpretation
                      : 'Not available for this interaction window'}
                  </Text>
                </View>
              ))}
            </View>
          </View>

          {/* RECOMMENDATIONS ("SUGGESTED NEXT STEPS") */}
          <View style={styles.sectionCard}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionIconBadge}>
                <Ionicons name="compass-outline" size={17} color="#E8663F" />
              </View>
              <View style={styles.sectionHeaderCopy}>
                <Text style={styles.sectionEyebrow}>RECOMMENDATION ENGINE</Text>
                <Text style={styles.sectionTitle}>Suggested Next Steps</Text>
              </View>
            </View>

            <View style={styles.recommendationsList}>
              {caseData.recommendations.map((rec) => (
                <View key={rec.id} style={styles.recCard}>
                  <View style={styles.recTop}>
                    <Text style={styles.recCategory}>{rec.category}</Text>
                    <Pressable
                      style={({ pressed }) => [styles.recActionBtn, pressed && styles.pressed]}
                    >
                      <Text style={styles.recActionBtnText}>{rec.actionLabel}</Text>
                    </Pressable>
                  </View>
                  <Text style={styles.recTitle}>{rec.title}</Text>
                  <Text style={styles.recDesc}>{rec.description}</Text>
                </View>
              ))}
            </View>
          </View>

          {/* RECENT INTERACTIONS TIMELINE */}
          <View style={styles.sectionCard}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionIconBadge}>
                <Ionicons name="hourglass-outline" size={17} color="#7C6EE6" />
              </View>
              <View style={styles.sectionHeaderCopy}>
                <Text style={styles.sectionEyebrow}>ACTIVITY TIMELINE</Text>
                <Text style={styles.sectionTitle}>Recent Patient Interactions</Text>
              </View>
            </View>

            <View style={styles.timelineList}>
              {caseData.recentInteractions.map((item) => (
                <View key={item.id} style={styles.timelineItem}>
                  <View style={styles.timelineDotWrap}>
                    <View style={styles.timelineDot} />
                    <View style={styles.timelineLine} />
                  </View>
                  <View style={styles.timelineContent}>
                    <View style={styles.timelineMetaRow}>
                      <View style={[styles.timelineTypeBadge, { backgroundColor: item.badgeBg }]}>
                        <Text style={[styles.timelineTypeBadgeText, { color: item.badgeColor }]}>
                          {item.type}
                        </Text>
                      </View>
                      <Text style={styles.timelineTime}>{item.timestamp}</Text>
                    </View>
                    <Text style={styles.timelineSummary}>{item.summary}</Text>
                  </View>
                </View>
              ))}
            </View>
          </View>

          {/* CLINICIAN NOTES SECTION */}
          <View style={styles.sectionCard}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionIconBadge}>
                <Ionicons name="document-text-outline" size={17} color="#2D8A4E" />
              </View>
              <View style={styles.sectionHeaderCopy}>
                <Text style={styles.sectionEyebrow}>CLINICIAN NOTES</Text>
                <Text style={styles.sectionTitle}>Encrypted Case Notes</Text>
              </View>
            </View>

            {notesList.map((note, idx) => (
              <View key={idx} style={styles.noteItem}>
                <Ionicons name="create-outline" size={16} color="#7C6EE6" />
                <Text style={styles.noteText}>{note}</Text>
              </View>
            ))}

            <Pressable
              onPress={() => setNoteModalVisible(true)}
              style={({ pressed }) => [styles.addNoteBtn, pressed && styles.pressed]}
              accessibilityRole="button"
              accessibilityLabel="Add clinical note"
            >
              <Ionicons name="add-circle-outline" size={16} color={COLORS.navy} />
              <Text style={styles.addNoteBtnText}>Add Clinician Note</Text>
            </Pressable>
          </View>

          <View style={{ height: 40 }} />
        </ScrollView>

        {/* ADD NOTE MODAL */}
        <Modal
          visible={noteModalVisible}
          transparent={true}
          animationType="fade"
          onRequestClose={() => setNoteModalVisible(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Add Clinician Note</Text>
              <Text style={styles.modalSub}>
                Notes are encrypted and attached to {caseData.caseId}.
              </Text>
              <TextInput
                placeholder="Enter clinical observations, action items, or remarks..."
                placeholderTextColor="#8E97A8"
                multiline
                numberOfLines={4}
                value={newNote}
                onChangeText={setNewNote}
                style={styles.modalInput}
              />
              <View style={styles.modalButtons}>
                <Pressable
                  onPress={() => setNoteModalVisible(false)}
                  style={[styles.modalBtn, styles.modalCancelBtn]}
                >
                  <Text style={styles.modalCancelText}>Cancel</Text>
                </Pressable>
                <Pressable
                  onPress={handleAddNote}
                  style={[styles.modalBtn, styles.modalSaveBtn]}
                >
                  <Text style={styles.modalSaveText}>Save Note</Text>
                </Pressable>
              </View>
            </View>
          </View>
        </Modal>
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
  backBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.card,
  },
  topBarCenter: {
    alignItems: 'center',
  },
  topBarId: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 16,
    color: COLORS.navy,
  },
  topBarPatient: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
  },
  topStatusPill: {
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: RADIUS.pill,
  },
  pillAttention: {
    backgroundColor: '#FFEADB',
  },
  pillNormal: {
    backgroundColor: '#E2F5E8',
  },
  topStatusText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
  },
  textAttention: {
    color: '#E8663F',
  },
  textNormal: {
    color: '#2D8A4E',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 14,
  },
  summaryCard: {
    backgroundColor: COLORS.white,
    borderRadius: 20,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.card,
  },
  summaryCardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 14,
  },
  patientAvatar: {
    width: 42,
    height: 42,
    borderRadius: 14,
    backgroundColor: '#E1F2FE',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  summaryHeaderCopy: {
    flex: 1,
  },
  patientName: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 18,
    color: COLORS.navy,
  },
  patientSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginTop: 1,
  },
  summaryGrid: {
    flexDirection: 'row',
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.03)',
  },
  summaryCol: {
    flex: 1,
  },
  gridLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 9,
    letterSpacing: 0.8,
    color: COLORS.navyMuted,
    marginBottom: 4,
  },
  gridValue: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    color: COLORS.navy,
  },
  trendInline: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  trendValue: {
    fontFamily: 'Nunito-Bold',
    fontSize: 13,
  },
  metaRow: {
    gap: 3,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#F0F2F5',
  },
  metaText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
  },
  safetyCard: {
    backgroundColor: '#FFEADB',
    borderRadius: 20,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1.5,
    borderColor: '#FFC9AC',
    ...SHADOW.card,
  },
  safetyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  safetyIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 12,
    backgroundColor: 'rgba(232, 102, 63, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  safetyHeaderCopy: {
    flex: 1,
  },
  safetyTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 16,
    color: '#E8663F',
  },
  safetySub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 1,
  },
  safetyDescription: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.navy,
    marginBottom: 14,
  },
  safetyActionRow: {
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: 'rgba(232, 102, 63, 0.2)',
  },
  safetySupportBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#181E2C',
    paddingVertical: 11,
    borderRadius: RADIUS.medium,
  },
  safetySupportBtnText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 13,
    color: '#FFFFFF',
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
    marginBottom: 12,
  },
  sectionIconBadge: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: '#F4F5F8',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  sectionHeaderCopy: {
    flex: 1,
  },
  sectionEyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1,
    color: COLORS.navyMuted,
  },
  sectionTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 16,
    color: COLORS.navy,
    marginTop: 1,
  },
  explainNotice: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
    marginBottom: 14,
    backgroundColor: '#F8FAFC',
    padding: 10,
    borderRadius: 10,
  },
  factorsList: {
    gap: 10,
  },
  factorItem: {
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.03)',
  },
  factorItemTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  factorTypeTag: {
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 6,
  },
  factorTagAttention: {
    backgroundColor: '#FFEADB',
  },
  factorTagNotice: {
    backgroundColor: '#EEE9FA',
  },
  factorTypeTagText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
  },
  factorTextAttention: {
    color: '#E8663F',
  },
  factorTextNotice: {
    color: '#7C6EE6',
  },
  factorItemTitle: {
    fontFamily: 'Nunito-Bold',
    fontSize: 13,
    color: COLORS.navy,
    flex: 1,
  },
  factorItemDesc: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navyMuted,
  },
  baselineDeviationText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: '#E8663F',
    marginBottom: 14,
  },
  chartContainer: {
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 14,
  },
  chartBars: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    height: 110,
  },
  barCol: {
    alignItems: 'center',
    flex: 1,
  },
  barValText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 9,
    color: COLORS.navyMuted,
    marginBottom: 4,
  },
  barTrack: {
    width: 14,
    height: 80,
    backgroundColor: '#E2E8F0',
    borderRadius: 7,
    justifyContent: 'flex-end',
    overflow: 'hidden',
  },
  barFill: {
    width: '100%',
    borderRadius: 7,
  },
  barDayText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 10,
    color: COLORS.navy,
    marginTop: 6,
  },
  modalityList: {
    gap: 12,
  },
  modalityRow: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 12,
  },
  modalityHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  modalityLabelWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  modalityLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: COLORS.navy,
  },
  modalityScore: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 13,
    color: '#7C6EE6',
  },
  modalityInterp: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
  },
  recommendationsList: {
    gap: 10,
  },
  recCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.03)',
  },
  recTop: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  recCategory: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 0.8,
    color: '#E8663F',
    textTransform: 'uppercase',
  },
  recActionBtn: {
    backgroundColor: '#181E2C',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: RADIUS.pill,
  },
  recActionBtnText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    color: '#FFFFFF',
  },
  recTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
    marginBottom: 4,
  },
  recDesc: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
  },
  timelineList: {
    paddingLeft: 6,
  },
  timelineItem: {
    flexDirection: 'row',
  },
  timelineDotWrap: {
    alignItems: 'center',
    marginRight: 12,
  },
  timelineDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#7C6EE6',
    marginTop: 4,
  },
  timelineLine: {
    width: 2,
    flex: 1,
    backgroundColor: '#E2E8F0',
    marginVertical: 4,
  },
  timelineContent: {
    flex: 1,
    paddingBottom: 16,
  },
  timelineMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  timelineTypeBadge: {
    paddingHorizontal: 7,
    paddingVertical: 2,
    borderRadius: 6,
  },
  timelineTypeBadgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
  },
  timelineTime: {
    fontFamily: 'Nunito-Regular',
    fontSize: 10,
    color: COLORS.navyMuted,
  },
  timelineSummary: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navy,
  },
  noteItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 12,
    marginBottom: 10,
  },
  noteText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navy,
  },
  addNoteBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: '#F2F4F7',
    paddingVertical: 10,
    borderRadius: RADIUS.medium,
    marginTop: 4,
  },
  addNoteBtnText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navy,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    width: '100%',
    backgroundColor: COLORS.white,
    borderRadius: 22,
    padding: 20,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.08)',
    ...SHADOW.card,
  },
  modalTitle: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 18,
    color: COLORS.navy,
    marginBottom: 4,
  },
  modalSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginBottom: 14,
  },
  modalInput: {
    backgroundColor: '#F8FAFC',
    borderRadius: 14,
    padding: 12,
    color: COLORS.navy,
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    minHeight: 100,
    textAlignVertical: 'top',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.08)',
  },
  modalButtons: {
    flexDirection: 'row',
    gap: 10,
  },
  modalBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: RADIUS.medium,
    alignItems: 'center',
  },
  modalCancelBtn: {
    backgroundColor: '#F2F4F7',
  },
  modalCancelText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    color: COLORS.navy,
  },
  modalSaveBtn: {
    backgroundColor: '#181E2C',
  },
  modalSaveText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 13,
    color: '#FFFFFF',
  },
  pressed: {
    opacity: 0.8,
  },
});
