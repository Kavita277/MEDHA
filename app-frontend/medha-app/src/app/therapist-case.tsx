import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { therapistService } from '../services/api';

function ResultCard({
  icon,
  title,
  value,
  description,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  value: string;
  description: string;
}) {
  return (
    <View style={styles.resultCard}>
      <View style={styles.resultIcon}>
        <Ionicons name={icon} size={18} color={COLORS.forest} />
      </View>
      <View style={styles.resultCopy}>
        <Text style={styles.resultTitle}>{title}</Text>
        <Text style={styles.resultValue}>{value}</Text>
        <Text style={styles.resultDescription}>{description}</Text>
      </View>
    </View>
  );
}

const EVENT_CATEGORIES = [
  { id: 'SESSION_NOTE', label: 'Session Note', icon: 'document-text-outline' },
  { id: 'MEDICATION_CHANGE', label: 'Medication', icon: 'medkit-outline' },
  { id: 'PANIC_ATTACK', label: 'Panic Attack', icon: 'flash-outline' },
  { id: 'CRISIS_INCIDENT', label: 'Crisis Incident', icon: 'alert-circle-outline' },
  { id: 'LIFE_STRESSOR', label: 'Life Stressor', icon: 'cloud-outline' },
  { id: 'MILESTONE', label: 'Milestone', icon: 'trophy-outline' },
  { id: 'OTHER', label: 'Other', icon: 'bookmark-outline' },
];

const SEVERITIES = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];

export default function TherapistCaseScreen() {
  const { caseId, victimId } = useLocalSearchParams<{ caseId?: string; victimId?: string }>();
  const [result, setResult] = useState<any>(null);
  const [checkins, setCheckins] = useState<any[]>([]);
  const [voiceRecords, setVoiceRecords] = useState<any[]>([]);
  const [caseHistory, setCaseHistory] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // --- Case History Modal State ---
  const [historyModalVisible, setHistoryModalVisible] = useState(false);
  const [historySaving, setHistorySaving] = useState(false);
  const [historyForm, setHistoryForm] = useState({
    primary_diagnosis: '',
    secondary_diagnosis: '',
    age: '',
    gender: '',
    pronouns: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: '',
    current_medications: '',
    psychiatric_history: '',
    medical_history: '',
    treatment_goals: '',
    clinical_notes: '',
  });

  // --- Clinical Event Modal State ---
  const [eventModalVisible, setEventModalVisible] = useState(false);
  const [eventSaving, setEventSaving] = useState(false);
  const [eventForm, setEventForm] = useState({
    title: '',
    event_type: 'SESSION_NOTE',
    severity: 'MEDIUM',
    description: '',
    action_taken: '',
  });

  const loadCaseData = () => {
    if (!caseId || caseId === 'CASE_LAYOUT_PREVIEW') {
      setLoading(false);
      return;
    }
    let mounted = true;
    Promise.all([
      therapistService.getCaseResults(caseId).catch(() => null),
      therapistService.getCaseCheckins(caseId).catch(() => []),
      therapistService.getCaseVoiceRecords(caseId).catch(() => []),
      therapistService.getCaseHistory(caseId).catch(() => null),
      therapistService.getCaseEvents(caseId).catch(() => []),
    ]).then(([resData, checkinData, voiceData, historyData, eventsData]) => {
      if (mounted) {
        setResult(resData);
        setCheckins(checkinData || []);
        setVoiceRecords(voiceData || []);
        setCaseHistory(historyData || null);
        setEvents(eventsData || []);
        setLoading(false);
      }
    });
    return () => { mounted = false; };
  };

  useEffect(() => {
    loadCaseData();
  }, [caseId]);

  // Open Edit History Modal with existing data
  const handleOpenEditHistory = () => {
    if (caseHistory) {
      setHistoryForm({
        primary_diagnosis: caseHistory.primary_diagnosis || '',
        secondary_diagnosis: caseHistory.secondary_diagnosis || '',
        age: caseHistory.age != null ? String(caseHistory.age) : '',
        gender: caseHistory.gender || '',
        pronouns: caseHistory.pronouns || '',
        emergency_contact_name: caseHistory.emergency_contact_name || '',
        emergency_contact_phone: caseHistory.emergency_contact_phone || '',
        emergency_contact_relationship: caseHistory.emergency_contact_relationship || '',
        current_medications: caseHistory.current_medications || '',
        psychiatric_history: caseHistory.psychiatric_history || '',
        medical_history: caseHistory.medical_history || '',
        treatment_goals: caseHistory.treatment_goals || '',
        clinical_notes: caseHistory.clinical_notes || '',
      });
    }
    setHistoryModalVisible(true);
  };

  const handleSaveHistory = async () => {
    if (!caseId) return;
    setHistorySaving(true);
    try {
      const payload: any = {
        primary_diagnosis: historyForm.primary_diagnosis.trim() || undefined,
        secondary_diagnosis: historyForm.secondary_diagnosis.trim() || undefined,
        age: historyForm.age.trim() ? parseInt(historyForm.age.trim(), 10) : undefined,
        gender: historyForm.gender.trim() || undefined,
        pronouns: historyForm.pronouns.trim() || undefined,
        emergency_contact_name: historyForm.emergency_contact_name.trim() || undefined,
        emergency_contact_phone: historyForm.emergency_contact_phone.trim() || undefined,
        emergency_contact_relationship: historyForm.emergency_contact_relationship.trim() || undefined,
        current_medications: historyForm.current_medications.trim() || undefined,
        psychiatric_history: historyForm.psychiatric_history.trim() || undefined,
        medical_history: historyForm.medical_history.trim() || undefined,
        treatment_goals: historyForm.treatment_goals.trim() || undefined,
        clinical_notes: historyForm.clinical_notes.trim() || undefined,
      };
      const updated = await therapistService.updateCaseHistory(caseId, payload);
      setCaseHistory(updated);
      setHistoryModalVisible(false);
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to update case history profile');
    } finally {
      setHistorySaving(false);
    }
  };

  const handleSaveEvent = async () => {
    if (!caseId) return;
    if (!eventForm.title.trim()) {
      Alert.alert('Validation', 'Please enter a title for the clinical event.');
      return;
    }
    if (!eventForm.description.trim()) {
      Alert.alert('Validation', 'Please provide clinical observations or notes.');
      return;
    }

    setEventSaving(true);
    try {
      const payload = {
        title: eventForm.title.trim(),
        event_type: eventForm.event_type,
        severity: eventForm.severity,
        description: eventForm.description.trim(),
        action_taken: eventForm.action_taken.trim() || undefined,
      };
      const created = await therapistService.addCaseEvent(caseId, payload);
      setEvents((prev) => [created, ...prev]);
      setEventModalVisible(false);
      setEventForm({
        title: '',
        event_type: 'SESSION_NOTE',
        severity: 'MEDIUM',
        description: '',
        action_taken: '',
      });
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to log clinical event');
    } finally {
      setEventSaving(false);
    }
  };

  const handleDeleteEvent = async (eventId: string) => {
    if (!caseId) return;
    try {
      await therapistService.deleteCaseEvent(caseId, eventId);
      setEvents((prev) => prev.filter((e) => e.id !== eventId));
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to delete clinical event');
    }
  };

  const hasPred = result && result.results_available;
  const ddsScore = hasPred && result.fusion_dds_prediction != null
    ? `${result.fusion_dds_prediction.toFixed(1)}%`
    : 'Unavailable';
  const triage = hasPred ? result.triage_level : 'UNKNOWN';
  const tempRisk = hasPred && result.temporal_risk_score != null
    ? `${(result.temporal_risk_score * 100).toFixed(1)}% risk`
    : 'Insufficient history';

  return (
    <View style={styles.screen}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        {/* TOP BAR */}
        <View style={styles.top}>
          <Pressable onPress={() => router.back()} style={styles.back}>
            <Ionicons name="arrow-back" size={19} color={COLORS.deepForest} />
          </Pressable>
          <Text style={styles.topLabel}>CASE REVIEW</Text>
          <View style={styles.backPlaceholder} />
        </View>

        {/* HEADING */}
        <View style={styles.heading}>
          <Text style={styles.eyebrow}>{victimId || caseId || 'MEDHA CASE'}</Text>
          <View style={styles.titleRow}>
            <Text style={styles.title}>Clinical Review</Text>
            <View style={[styles.reviewPill, triage === 'CRITICAL' && { backgroundColor: '#ffebee' }, triage === 'HIGH' && { backgroundColor: '#fff3e0' }]}>
              <Text style={[styles.reviewPillText, triage === 'CRITICAL' && { color: '#c62828' }, triage === 'HIGH' && { color: '#e65100' }]}>
                {triage} TRIAGE
              </Text>
            </View>
          </View>
          <Text style={styles.subtitle}>
            AI-assisted longitudinal context. Final interpretation remains with the clinician.
          </Text>
        </View>

        {/* STATUS BANNER */}
        <View style={styles.banner}>
          <Ionicons name="time-outline" size={19} color={COLORS.forest} />
          <View style={styles.bannerCopy}>
            <Text style={styles.bannerTitle}>Results Status</Text>
            <Text style={styles.bannerText}>
              {hasPred
                ? `Predictions evaluated for Timepoint T${result.timepoint || 1}. Never fabricated.`
                : 'Awaiting sufficient session observations before computing predictions.'}
            </Text>
          </View>
        </View>

        {/* SUMMARY CARDS */}
        <Text style={styles.sectionEyebrow}>CLINICAL SUMMARY</Text>

        <ResultCard
          icon="pulse-outline"
          title="Multimodal Fusion DDS"
          value={ddsScore}
          description={hasPred ? `Triage classification: ${triage}. Ingests check-in features, text & audio.` : "No validated prediction generated yet."}
        />

        <ResultCard
          icon="trending-up-outline"
          title="Temporal Escalation Risk"
          value={tempRisk}
          description="GRU temporal sequence forecasting for upcoming session window."
        />

        <ResultCard
          icon="shield-outline"
          title="Safety Evaluation"
          value={triage === 'CRITICAL' ? 'Immediate Attention' : triage === 'HIGH' ? 'Elevated Monitoring' : 'Stable'}
          description="Multidisciplinary clinical safeguards and alert monitoring."
        />

        {/* ------------------------------------------------------------- */}
        {/* 1. PATIENT CASE HISTORY & CLINICAL PROFILE                    */}
        {/* ------------------------------------------------------------- */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionEyebrow}>PATIENT CASE HISTORY & INTAKE</Text>
          <Pressable
            onPress={handleOpenEditHistory}
            style={styles.headerActionBtn}
            accessibilityRole="button"
          >
            <Ionicons name="create-outline" size={13} color={COLORS.forest} />
            <Text style={styles.headerActionText}>
              {caseHistory ? 'Edit History' : 'Add History'}
            </Text>
          </Pressable>
        </View>

        <View style={styles.historyCard}>
          {caseHistory ? (
            <View style={{ gap: 10 }}>
              {/* Diagnosis Header */}
              <View style={styles.historyTopRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.historyDiagLabel}>PRIMARY DIAGNOSIS</Text>
                  <Text style={styles.historyDiagValue}>
                    {caseHistory.primary_diagnosis || 'Unspecified Clinical Presentation'}
                  </Text>
                  {caseHistory.secondary_diagnosis && (
                    <Text style={styles.historyDiagSecondary}>
                      Secondary: {caseHistory.secondary_diagnosis}
                    </Text>
                  )}
                </View>
                <View style={styles.historyDemographicBadge}>
                  <Text style={styles.historyDemographicBadgeText}>
                    {caseHistory.age != null ? `${caseHistory.age} yrs` : 'Age N/A'} · {caseHistory.gender || 'Patient'}
                  </Text>
                </View>
              </View>

              {/* Demographics / Contact */}
              <View style={styles.historyDetailsGrid}>
                {caseHistory.emergency_contact_name && (
                  <View style={styles.historyGridItem}>
                    <Text style={styles.gridItemLabel}>EMERGENCY CONTACT</Text>
                    <Text style={styles.gridItemValue}>
                      {caseHistory.emergency_contact_name} ({caseHistory.emergency_contact_relationship || 'Contact'})
                    </Text>
                    {caseHistory.emergency_contact_phone && (
                      <Text style={styles.gridItemSub}>{caseHistory.emergency_contact_phone}</Text>
                    )}
                  </View>
                )}

                {caseHistory.current_medications && (
                  <View style={styles.historyGridItem}>
                    <Text style={styles.gridItemLabel}>CURRENT MEDICATIONS</Text>
                    <Text style={styles.gridItemValue}>{caseHistory.current_medications}</Text>
                  </View>
                )}
              </View>

              {/* Background Paragraphs */}
              {caseHistory.psychiatric_history && (
                <View style={styles.historyTextBlock}>
                  <Text style={styles.gridItemLabel}>PSYCHIATRIC BACKGROUND</Text>
                  <Text style={styles.historyParagraph}>{caseHistory.psychiatric_history}</Text>
                </View>
              )}

              {caseHistory.medical_history && (
                <View style={styles.historyTextBlock}>
                  <Text style={styles.gridItemLabel}>MEDICAL HISTORY</Text>
                  <Text style={styles.historyParagraph}>{caseHistory.medical_history}</Text>
                </View>
              )}

              {caseHistory.treatment_goals && (
                <View style={styles.historyTextBlock}>
                  <Text style={styles.gridItemLabel}>TREATMENT GOALS & CARE PLAN</Text>
                  <Text style={styles.historyParagraph}>{caseHistory.treatment_goals}</Text>
                </View>
              )}

              {caseHistory.clinical_notes && (
                <View style={styles.historyTextBlock}>
                  <Text style={styles.gridItemLabel}>INTAKE CLINICAL NOTES</Text>
                  <Text style={[styles.historyParagraph, { fontStyle: 'italic' }]}>
                    "{caseHistory.clinical_notes}"
                  </Text>
                </View>
              )}
            </View>
          ) : (
            <View style={{ alignItems: 'center', paddingVertical: 12 }}>
              <Ionicons name="folder-open-outline" size={28} color={COLORS.mutedText} />
              <Text style={styles.emptyCardTitle}>No Case History Recorded</Text>
              <Text style={styles.emptyCardSub}>
                Record patient intake, diagnosis, medical background, and emergency contact details.
              </Text>
              <Pressable
                onPress={handleOpenEditHistory}
                style={styles.emptyActionBtn}
              >
                <Ionicons name="add" size={14} color={COLORS.white} />
                <Text style={styles.emptyActionText}>Add Patient Case History</Text>
              </Pressable>
            </View>
          )}
        </View>

        {/* ------------------------------------------------------------- */}
        {/* 2. CLINICAL EVENTS & TIMELINE                                 */}
        {/* ------------------------------------------------------------- */}
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionEyebrow}>CLINICAL EVENTS & TIMELINE ({events.length})</Text>
          <Pressable
            onPress={() => setEventModalVisible(true)}
            style={styles.headerActionBtn}
            accessibilityRole="button"
          >
            <Ionicons name="add-circle-outline" size={14} color={COLORS.forest} />
            <Text style={styles.headerActionText}>Log Event</Text>
          </Pressable>
        </View>

        {events.length === 0 ? (
          <View style={[styles.interactionCard, { padding: 16, alignItems: 'center' }]}>
            <Ionicons name="calendar-outline" size={24} color={COLORS.mutedText} style={{ marginBottom: 6 }} />
            <Text style={{ fontSize: 11, color: COLORS.mutedText, fontFamily: 'Inter-Regular', textAlign: 'center' }}>
              No clinical events or milestones recorded yet for this patient.
            </Text>
            <Pressable
              onPress={() => setEventModalVisible(true)}
              style={[styles.emptyActionBtn, { marginTop: 10 }]}
            >
              <Ionicons name="add" size={14} color={COLORS.white} />
              <Text style={styles.emptyActionText}>Log First Clinical Event</Text>
            </Pressable>
          </View>
        ) : (
          <View style={{ gap: 10, marginBottom: 16 }}>
            {events.map((evt) => {
              const sev = evt.severity?.toUpperCase() || 'MEDIUM';
              const sevColor =
                sev === 'CRITICAL'
                  ? '#c62828'
                  : sev === 'HIGH'
                  ? '#e65100'
                  : sev === 'LOW'
                  ? '#2e7d32'
                  : COLORS.deepForest;
              const sevBg =
                sev === 'CRITICAL'
                  ? '#ffebee'
                  : sev === 'HIGH'
                  ? '#fff3e0'
                  : sev === 'LOW'
                  ? '#e8f5e9'
                  : COLORS.mist;

              const dateStr = evt.occurred_at
                ? new Date(evt.occurred_at).toLocaleDateString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })
                : 'Recent';

              return (
                <View key={evt.id} style={styles.eventCard}>
                  <View style={styles.eventCardHeader}>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, flex: 1 }}>
                      <View style={[styles.eventBadge, { backgroundColor: sevBg }]}>
                        <Text style={[styles.eventBadgeText, { color: sevColor }]}>
                          {evt.event_type.replace('_', ' ')}
                        </Text>
                      </View>
                      <Text style={styles.eventSeverityTag}>· {sev}</Text>
                    </View>
                    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                      <Text style={styles.eventDate}>{dateStr}</Text>
                      <Pressable
                        onPress={() => handleDeleteEvent(evt.id)}
                        hitSlop={8}
                        accessibilityLabel="Delete event"
                      >
                        <Ionicons name="trash-outline" size={14} color={COLORS.mutedText} />
                      </Pressable>
                    </View>
                  </View>

                  <Text style={styles.eventTitle}>{evt.title}</Text>
                  <Text style={styles.eventDescription}>{evt.description}</Text>

                  {evt.action_taken && (
                    <View style={styles.eventActionBox}>
                      <Ionicons name="checkmark-circle-outline" size={13} color={COLORS.forest} />
                      <Text style={styles.eventActionText}>Action: {evt.action_taken}</Text>
                    </View>
                  )}
                </View>
              );
            })}
          </View>
        )}

        {/* ------------------------------------------------------------- */}
        {/* 3. PATIENT DAILY CHECK-INS SECTION                            */}
        {/* ------------------------------------------------------------- */}
        <Text style={styles.sectionEyebrow}>PATIENT DAILY CHECK-INS ({checkins.length})</Text>

        {checkins.length === 0 ? (
          <View style={[styles.interactionCard, { padding: 16 }]}>
            <Text style={{ fontSize: 11, color: COLORS.mutedText, fontFamily: 'Inter-Regular' }}>
              No check-in responses recorded yet for this case.
            </Text>
          </View>
        ) : (
          <View style={{ gap: 10, marginBottom: 16 }}>
            {checkins.slice(0, 3).map((chk) => (
              <View
                key={chk.checkin_id}
                style={{
                  backgroundColor: COLORS.surface,
                  borderRadius: 16,
                  padding: 14,
                  borderWidth: 1,
                  borderColor: COLORS.border,
                }}
              >
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <Text style={{ fontSize: 11, fontFamily: 'Inter-Medium', color: COLORS.deepForest }}>
                    Timepoint T{chk.timepoint} Check-in
                  </Text>
                  <View style={{
                    backgroundColor: chk.status === 'completed' ? '#e8f5e9' : '#fff8e1',
                    paddingHorizontal: 7,
                    paddingVertical: 2,
                    borderRadius: 6,
                  }}>
                    <Text style={{
                      fontSize: 8,
                      fontFamily: 'Inter-Medium',
                      color: chk.status === 'completed' ? '#2e7d32' : '#f57f17',
                      textTransform: 'uppercase',
                    }}>
                      {chk.status}
                    </Text>
                  </View>
                </View>

                {(chk.questions || []).map((q: any) => {
                  const val = q.answer ? Object.values(q.answer)[0] : null;
                  return (
                    <View key={q.question_id} style={{ marginTop: 6, paddingTop: 6, borderTopWidth: 1, borderTopColor: 'rgba(0,0,0,0.04)' }}>
                      <Text style={{ fontSize: 9, color: COLORS.mutedText, fontFamily: 'Inter-Medium' }}>
                        {q.question_id} · {q.domain || 'Assessment'}
                      </Text>
                      <Text style={{ fontSize: 11, fontFamily: 'Inter-Regular', color: COLORS.text, marginVertical: 2 }}>
                        {q.question_text}
                      </Text>
                      <Text style={{ fontSize: 10, fontFamily: 'Inter-Medium', color: '#2e7d32' }}>
                        Answer: {val !== null ? (typeof val === 'number' ? `${val} / 5` : String(val)) : 'Pending'}
                      </Text>
                    </View>
                  );
                })}
              </View>
            ))}
          </View>
        )}

        {/* ------------------------------------------------------------- */}
        {/* 4. VOICE CHECK-IN SAMPLES & PROSODY                          */}
        {/* ------------------------------------------------------------- */}
        <Text style={styles.sectionEyebrow}>VOICE SAMPLES & PROSODY ({voiceRecords.length})</Text>

        {voiceRecords.length === 0 ? (
          <View style={[styles.interactionCard, { padding: 16 }]}>
            <Text style={{ fontSize: 11, color: COLORS.mutedText, fontFamily: 'Inter-Regular' }}>
              No acoustic voice records recorded for this patient.
            </Text>
          </View>
        ) : (
          <View style={{ gap: 10, marginBottom: 16 }}>
            {voiceRecords.slice(0, 3).map((v) => (
              <View
                key={v.id}
                style={{
                  backgroundColor: COLORS.surface,
                  borderRadius: 16,
                  padding: 14,
                  borderWidth: 1,
                  borderColor: COLORS.border,
                }}
              >
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                    <Ionicons name="mic-outline" size={15} color={COLORS.forest} />
                    <Text style={{ fontSize: 11, fontFamily: 'Inter-Medium', color: COLORS.deepForest }}>
                      Voice Check-in ({v.timepoint || 'Recent'})
                    </Text>
                  </View>
                  <Text style={{ fontSize: 10, fontFamily: 'Inter-Medium', color: v.voice_score != null ? COLORS.deepForest : COLORS.mutedText }}>
                    {v.voice_score != null ? `Score: ${(v.voice_score <= 1.0 ? v.voice_score * 100 : v.voice_score).toFixed(1)}%` : 'Processing'}
                  </Text>
                </View>

                {v.transcript && (
                  <View style={{ backgroundColor: 'rgba(0,0,0,0.02)', padding: 8, borderRadius: 8, marginVertical: 4 }}>
                    <Text style={{ fontSize: 10, fontFamily: 'Inter-Regular', color: COLORS.deepForest, fontStyle: 'italic' }}>
                      "{v.transcript}"
                    </Text>
                  </View>
                )}

                <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 4 }}>
                  <Text style={{ fontSize: 9, fontFamily: 'Inter-Regular', color: COLORS.mutedText }}>
                    Duration: {v.duration_seconds != null ? `${v.duration_seconds.toFixed(1)}s` : 'N/A'}
                  </Text>
                  {v.audio_filename && (
                    <Text style={{ fontSize: 9, fontFamily: 'Inter-Regular', color: COLORS.mutedText }}>
                      · File: {v.audio_filename}
                    </Text>
                  )}
                  {v.extracted_features && (
                    <Text style={{ fontSize: 9, fontFamily: 'Inter-Regular', color: '#2e7d32' }}>
                      · Acoustic Features: Extracted
                    </Text>
                  )}
                </View>
              </View>
            ))}
          </View>
        )}

        {/* ------------------------------------------------------------- */}
        {/* 5. SPECIALIST MODALITIES                                      */}
        {/* ------------------------------------------------------------- */}
        <Text style={styles.sectionEyebrow}>SPECIALIST MODALITIES</Text>

        <View style={styles.interactionCard}>
          <Interaction
            icon="clipboard-outline"
            title="Structured Specialist"
            value={hasPred && result.specialists?.struct_pred != null ? `${result.specialists.struct_pred.toFixed(1)}%` : 'Unavailable'}
          />
          <Interaction
            icon="chatbubble-outline"
            title="Text Specialist"
            value={hasPred && result.specialists?.text_pred != null ? `${result.specialists.text_pred.toFixed(1)}%` : 'Unavailable'}
          />
          <Interaction
            icon="mic-outline"
            title="Voice Specialist"
            value={hasPred && result.specialists?.voice_pred != null ? `${result.specialists.voice_pred.toFixed(1)}%` : 'Unavailable'}
          />
        </View>

        <Pressable
          onPress={() => router.replace('/therapist' as any)}
          style={styles.button}
        >
          <Text style={styles.buttonText}>Back to cases</Text>
        </Pressable>
      </ScrollView>

      {/* ============================================================= */}
      {/* MODAL: EDIT PATIENT CASE HISTORY                              */}
      {/* ============================================================= */}
      <Modal
        visible={historyModalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setHistoryModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Patient Case History & Intake</Text>
            <Pressable onPress={() => setHistoryModalVisible(false)} hitSlop={8}>
              <Ionicons name="close" size={22} color={COLORS.deepForest} />
            </Pressable>
          </View>

          <ScrollView style={styles.modalScroll} showsVerticalScrollIndicator={false}>
            <Text style={styles.modalSubtitle}>
              Update the patient's intake background, primary diagnosis, medications, and emergency contacts.
            </Text>

            <Text style={styles.inputLabel}>Primary Diagnosis</Text>
            <TextInput
              style={styles.textInput}
              placeholder="e.g. Generalized Anxiety Disorder, MDD"
              placeholderTextColor={COLORS.mutedText}
              value={historyForm.primary_diagnosis}
              onChangeText={(t) => setHistoryForm({ ...historyForm, primary_diagnosis: t })}
            />

            <Text style={styles.inputLabel}>Secondary Diagnosis (Optional)</Text>
            <TextInput
              style={styles.textInput}
              placeholder="e.g. Insomnia, Panic Disorder"
              placeholderTextColor={COLORS.mutedText}
              value={historyForm.secondary_diagnosis}
              onChangeText={(t) => setHistoryForm({ ...historyForm, secondary_diagnosis: t })}
            />

            <View style={{ flexDirection: 'row', gap: 10 }}>
              <View style={{ flex: 1 }}>
                <Text style={styles.inputLabel}>Age</Text>
                <TextInput
                  style={styles.textInput}
                  placeholder="e.g. 28"
                  keyboardType="numeric"
                  placeholderTextColor={COLORS.mutedText}
                  value={historyForm.age}
                  onChangeText={(t) => setHistoryForm({ ...historyForm, age: t })}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.inputLabel}>Gender</Text>
                <TextInput
                  style={styles.textInput}
                  placeholder="e.g. Female"
                  placeholderTextColor={COLORS.mutedText}
                  value={historyForm.gender}
                  onChangeText={(t) => setHistoryForm({ ...historyForm, gender: t })}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.inputLabel}>Pronouns</Text>
                <TextInput
                  style={styles.textInput}
                  placeholder="she/her"
                  placeholderTextColor={COLORS.mutedText}
                  value={historyForm.pronouns}
                  onChangeText={(t) => setHistoryForm({ ...historyForm, pronouns: t })}
                />
              </View>
            </View>

            <Text style={styles.inputLabel}>Current Medications & Dosages</Text>
            <TextInput
              style={styles.textInput}
              placeholder="e.g. Escitalopram 10mg daily, Clonazepam 0.25mg PRN"
              placeholderTextColor={COLORS.mutedText}
              value={historyForm.current_medications}
              onChangeText={(t) => setHistoryForm({ ...historyForm, current_medications: t })}
            />

            <Text style={styles.inputLabel}>Emergency Contact Name</Text>
            <TextInput
              style={styles.textInput}
              placeholder="Full name"
              placeholderTextColor={COLORS.mutedText}
              value={historyForm.emergency_contact_name}
              onChangeText={(t) => setHistoryForm({ ...historyForm, emergency_contact_name: t })}
            />

            <View style={{ flexDirection: 'row', gap: 10 }}>
              <View style={{ flex: 1 }}>
                <Text style={styles.inputLabel}>Contact Phone</Text>
                <TextInput
                  style={styles.textInput}
                  placeholder="+91 98765 43210"
                  keyboardType="phone-pad"
                  placeholderTextColor={COLORS.mutedText}
                  value={historyForm.emergency_contact_phone}
                  onChangeText={(t) => setHistoryForm({ ...historyForm, emergency_contact_phone: t })}
                />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.inputLabel}>Relationship</Text>
                <TextInput
                  style={styles.textInput}
                  placeholder="Parent / Spouse"
                  placeholderTextColor={COLORS.mutedText}
                  value={historyForm.emergency_contact_relationship}
                  onChangeText={(t) => setHistoryForm({ ...historyForm, emergency_contact_relationship: t })}
                />
              </View>
            </View>

            <Text style={styles.inputLabel}>Psychiatric Background</Text>
            <TextInput
              style={[styles.textInput, styles.textArea]}
              multiline
              numberOfLines={3}
              placeholder="Prior therapy, past episodes, family history..."
              placeholderTextColor={COLORS.mutedText}
              value={historyForm.psychiatric_history}
              onChangeText={(t) => setHistoryForm({ ...historyForm, psychiatric_history: t })}
            />

            <Text style={styles.inputLabel}>Treatment Goals & Care Plan</Text>
            <TextInput
              style={[styles.textInput, styles.textArea]}
              multiline
              numberOfLines={3}
              placeholder="Target symptom reductions, coping milestones..."
              placeholderTextColor={COLORS.mutedText}
              value={historyForm.treatment_goals}
              onChangeText={(t) => setHistoryForm({ ...historyForm, treatment_goals: t })}
            />

            <Text style={styles.inputLabel}>Intake Clinical Notes</Text>
            <TextInput
              style={[styles.textInput, styles.textArea]}
              multiline
              numberOfLines={3}
              placeholder="Clinician observations, presentation, affect..."
              placeholderTextColor={COLORS.mutedText}
              value={historyForm.clinical_notes}
              onChangeText={(t) => setHistoryForm({ ...historyForm, clinical_notes: t })}
            />

            <Pressable
              disabled={historySaving}
              onPress={handleSaveHistory}
              style={[styles.saveBtn, historySaving && { opacity: 0.6 }]}
            >
              {historySaving ? (
                <ActivityIndicator color={COLORS.white} size="small" />
              ) : (
                <Text style={styles.saveBtnText}>Save Patient Case History</Text>
              )}
            </Pressable>
            <View style={{ height: 40 }} />
          </ScrollView>
        </View>
      </Modal>

      {/* ============================================================= */}
      {/* MODAL: LOG CLINICAL EVENT                                     */}
      {/* ============================================================= */}
      <Modal
        visible={eventModalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setEventModalVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Log Clinical Event</Text>
            <Pressable onPress={() => setEventModalVisible(false)} hitSlop={8}>
              <Ionicons name="close" size={22} color={COLORS.deepForest} />
            </Pressable>
          </View>

          <ScrollView style={styles.modalScroll} showsVerticalScrollIndicator={false}>
            <Text style={styles.modalSubtitle}>
              Document a milestone, medication adjustment, crisis episode, or clinical therapy note.
            </Text>

            <Text style={styles.inputLabel}>Event Title *</Text>
            <TextInput
              style={styles.textInput}
              placeholder="e.g. Acute panic attack during exam"
              placeholderTextColor={COLORS.mutedText}
              value={eventForm.title}
              onChangeText={(t) => setEventForm({ ...eventForm, title: t })}
            />

            <Text style={styles.inputLabel}>Category</Text>
            <View style={styles.pillsRow}>
              {EVENT_CATEGORIES.map((cat) => {
                const selected = eventForm.event_type === cat.id;
                return (
                  <Pressable
                    key={cat.id}
                    onPress={() => setEventForm({ ...eventForm, event_type: cat.id })}
                    style={[styles.pillBtn, selected && styles.pillBtnSelected]}
                  >
                    <Ionicons
                      name={cat.icon as any}
                      size={12}
                      color={selected ? COLORS.white : COLORS.deepForest}
                    />
                    <Text style={[styles.pillBtnText, selected && styles.pillBtnTextSelected]}>
                      {cat.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <Text style={styles.inputLabel}>Severity</Text>
            <View style={styles.pillsRow}>
              {SEVERITIES.map((sev) => {
                const selected = eventForm.severity === sev;
                return (
                  <Pressable
                    key={sev}
                    onPress={() => setEventForm({ ...eventForm, severity: sev })}
                    style={[
                      styles.pillBtn,
                      selected && (sev === 'CRITICAL' ? styles.pillCritSelected : styles.pillBtnSelected),
                    ]}
                  >
                    <Text
                      style={[
                        styles.pillBtnText,
                        selected && styles.pillBtnTextSelected,
                      ]}
                    >
                      {sev}
                    </Text>
                  </Pressable>
                );
              })}
            </View>

            <Text style={styles.inputLabel}>Clinical Observations & Context *</Text>
            <TextInput
              style={[styles.textInput, styles.textArea]}
              multiline
              numberOfLines={4}
              placeholder="Describe the incident, observed triggers, severity, and context..."
              placeholderTextColor={COLORS.mutedText}
              value={eventForm.description}
              onChangeText={(t) => setEventForm({ ...eventForm, description: t })}
            />

            <Text style={styles.inputLabel}>Action Taken / Recommendation (Optional)</Text>
            <TextInput
              style={[styles.textInput, styles.textArea]}
              multiline
              numberOfLines={2}
              placeholder="e.g. Guided grounding breathing; reviewed distress tolerance plan..."
              placeholderTextColor={COLORS.mutedText}
              value={eventForm.action_taken}
              onChangeText={(t) => setEventForm({ ...eventForm, action_taken: t })}
            />

            <Pressable
              disabled={eventSaving}
              onPress={handleSaveEvent}
              style={[styles.saveBtn, eventSaving && { opacity: 0.6 }]}
            >
              {eventSaving ? (
                <ActivityIndicator color={COLORS.white} size="small" />
              ) : (
                <Text style={styles.saveBtnText}>Save Clinical Event</Text>
              )}
            </Pressable>
            <View style={{ height: 40 }} />
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

function Interaction({
  icon,
  title,
  value,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  value: string;
}) {
  return (
    <View style={styles.interactionRow}>
      <View style={styles.interactionIcon}>
        <Ionicons name={icon} size={17} color={COLORS.forest} />
      </View>
      <View style={styles.interactionCopy}>
        <Text style={styles.interactionTitle}>{title}</Text>
        <Text style={styles.interactionValue}>{value}</Text>
      </View>
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
    paddingTop: 52,
    paddingBottom: 42,
  },
  top: {
    height: 42,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  back: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backPlaceholder: {
    width: 42,
  },
  topLabel: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.7,
    color: COLORS.forest,
  },
  heading: {
    marginTop: 18,
  },
  eyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 1.8,
    color: COLORS.forest,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 32,
    color: COLORS.deepForest,
  },
  reviewPill: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: COLORS.mist,
  },
  reviewPillText: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 0.8,
    color: COLORS.deepForest,
  },
  subtitle: {
    marginTop: 4,
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 16,
    color: COLORS.subtleText,
  },
  banner: {
    marginTop: 18,
    marginBottom: 14,
    padding: 14,
    borderRadius: 18,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    alignItems: 'center',
  },
  bannerCopy: {
    marginLeft: 12,
    flex: 1,
  },
  bannerTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.deepForest,
  },
  bannerText: {
    marginTop: 2,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 14,
    color: COLORS.subtleText,
  },
  sectionEyebrow: {
    marginTop: 18,
    marginBottom: 8,
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 1.5,
    color: COLORS.forest,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 20,
    marginBottom: 8,
  },
  headerActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: COLORS.mist,
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: 12,
  },
  headerActionText: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.deepForest,
  },
  resultCard: {
    marginBottom: 8,
    padding: 13,
    borderRadius: 18,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    alignItems: 'center',
  },
  resultIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },
  resultCopy: {
    marginLeft: 11,
    flex: 1,
  },
  resultTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.forest,
  },
  resultValue: {
    marginTop: 1,
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 21,
    color: COLORS.deepForest,
  },
  resultDescription: {
    marginTop: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 8,
    lineHeight: 13,
    color: COLORS.subtleText,
  },

  // --- Case History Card Styles ---
  historyCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 18,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 10,
  },
  historyTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.05)',
    paddingBottom: 10,
  },
  historyDiagLabel: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.2,
    color: COLORS.forest,
  },
  historyDiagValue: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 18,
    color: COLORS.deepForest,
    marginTop: 2,
  },
  historyDiagSecondary: {
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    color: COLORS.mutedText,
    marginTop: 2,
  },
  historyDemographicBadge: {
    backgroundColor: COLORS.mist,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  historyDemographicBadgeText: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    color: COLORS.deepForest,
  },
  historyDetailsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    paddingVertical: 4,
  },
  historyGridItem: {
    flex: 1,
    minWidth: 130,
  },
  gridItemLabel: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1,
    color: COLORS.mutedText,
    marginBottom: 2,
  },
  gridItemValue: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.deepForest,
  },
  gridItemSub: {
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    color: COLORS.subtleText,
  },
  historyTextBlock: {
    marginTop: 4,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.04)',
  },
  historyParagraph: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 15,
    color: COLORS.text,
    marginTop: 2,
  },
  emptyCardTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.deepForest,
    marginTop: 6,
  },
  emptyCardSub: {
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    color: COLORS.mutedText,
    textAlign: 'center',
    marginVertical: 4,
    maxWidth: 240,
  },
  emptyActionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: COLORS.forest,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
    marginTop: 6,
  },
  emptyActionText: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.white,
  },

  // --- Clinical Events Timeline Styles ---
  eventCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  eventCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  eventBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  eventBadgeText: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  eventSeverityTag: {
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    color: COLORS.mutedText,
  },
  eventDate: {
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    color: COLORS.mutedText,
  },
  eventTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.deepForest,
    marginBottom: 3,
  },
  eventDescription: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 15,
    color: COLORS.text,
  },
  eventActionBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    marginTop: 6,
    backgroundColor: 'rgba(46, 125, 50, 0.06)',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  eventActionText: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    color: '#2e7d32',
  },

  // --- Modals & Inputs ---
  modalContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingBottom: 14,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  modalTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 22,
    color: COLORS.deepForest,
  },
  modalSubtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.subtleText,
    marginVertical: 10,
    lineHeight: 15,
  },
  modalScroll: {
    flex: 1,
  },
  inputLabel: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 0.8,
    color: COLORS.forest,
    marginTop: 10,
    marginBottom: 4,
    textTransform: 'uppercase',
  },
  textInput: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 9,
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.text,
  },
  textArea: {
    minHeight: 60,
    textAlignVertical: 'top',
  },
  pillsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginVertical: 4,
  },
  pillBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 14,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  pillBtnSelected: {
    backgroundColor: COLORS.forest,
    borderColor: COLORS.forest,
  },
  pillCritSelected: {
    backgroundColor: '#c62828',
    borderColor: '#c62828',
  },
  pillBtnText: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    color: COLORS.deepForest,
  },
  pillBtnTextSelected: {
    color: COLORS.white,
  },
  saveBtn: {
    backgroundColor: COLORS.forest,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 22,
  },
  saveBtnText: {
    fontFamily: 'Inter-Medium',
    fontSize: 12,
    color: COLORS.white,
  },

  interactionCard: {
    borderRadius: 19,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    overflow: 'hidden',
  },
  interactionRow: {
    minHeight: 62,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  interactionIcon: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },
  interactionCopy: {
    marginLeft: 11,
  },
  interactionTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.deepForest,
  },
  interactionValue: {
    marginTop: 3,
    fontFamily: 'Inter-Regular',
    fontSize: 8,
    color: COLORS.subtleText,
  },
  button: {
    marginTop: 22,
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
});
