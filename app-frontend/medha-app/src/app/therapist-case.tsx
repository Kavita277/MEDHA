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
import { useAuth } from '../context/AuthContext';
import type {
  CaseResultResponse,
  CaseInsightsResponse,
  CaseRecommendationsResponse,
  SafetyProtocolResponse,
  AlertSummaryResponse,
  CheckinSummaryResponse,
} from '../types/therapist';

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

type TabKey = 'predictions' | 'timeline' | 'history' | 'insights' | 'recommendations' | 'safety' | 'context';

export default function TherapistCaseScreen() {
  const { caseId, victimId } = useLocalSearchParams<{ caseId?: string; victimId?: string }>();
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth();

  // Data states
  const [result, setResult] = useState<CaseResultResponse | null>(null);
  const [insights, setInsights] = useState<CaseInsightsResponse | null>(null);
  const [recommendations, setRecommendations] = useState<CaseRecommendationsResponse | null>(null);
  const [safetyProtocol, setSafetyProtocol] = useState<SafetyProtocolResponse | null>(null);
  const [alerts, setAlerts] = useState<AlertSummaryResponse[]>([]);
  const [checkins, setCheckins] = useState<CheckinSummaryResponse[]>([]);
  const [voiceRecords, setVoiceRecords] = useState<any[]>([]);
  const [caseHistory, setCaseHistory] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);

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

  // UI states
  const [activeTab, setActiveTab] = useState<TabKey>('predictions');
  const [loading, setLoading] = useState(true);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [handlingAlertId, setHandlingAlertId] = useState<string | null>(null);

  // Role guard: prevent patients (USER) and unauthenticated actors
  useEffect(() => {
    if (!authLoading) {
      if (!isAuthenticated) {
        router.replace('/therapist-login' as any);
      } else {
        const role = (user?.role || '').toUpperCase();
        if (role !== 'THERAPIST' && role !== 'ADMIN') {
          router.replace('/home' as any);
        }
      }
    }
  }, [authLoading, isAuthenticated, user]);

  const loadCaseData = async () => {
    if (!caseId || caseId === 'CASE_LAYOUT_PREVIEW') {
      setLoading(false);
      return;
    }

    setLoading(true);
    setErrorStatus(null);
    setErrorMessage(null);

    try {
      const [
        resData,
        insData,
        recData,
        protoData,
        alertData,
        chkData,
        voiceData,
      ] = await Promise.all([
        therapistService.getCaseResults(caseId).catch((e) => {
          if (e?.statusCode === 403 || e?.statusCode === 401) throw e;
          return null;
        }),
        therapistService.getCaseInsights(caseId).catch((e) => {
          if (e?.statusCode === 403 || e?.statusCode === 401) throw e;
          return null;
        }),
        therapistService.getCaseRecommendations(caseId).catch((e) => {
          if (e?.statusCode === 403 || e?.statusCode === 401) throw e;
          return null;
        }),
        therapistService.getCaseSafetyProtocol(caseId).catch((e) => {
          if (e?.statusCode === 403 || e?.statusCode === 401) throw e;
          return null;
        }),
        therapistService.getCaseAlerts(caseId).catch((e) => {
          if (e?.statusCode === 403 || e?.statusCode === 401) throw e;
          return [];
        }),
        therapistService.getCaseCheckins(caseId).catch((e) => {
          if (e?.statusCode === 403 || e?.statusCode === 401) throw e;
          return [];
        }),
        therapistService.getCaseVoiceRecords(caseId).catch((e) => {
          if (e?.statusCode === 403 || e?.statusCode === 401) throw e;
          return [];
        }),
      ]);

      setResult(resData);
      setInsights(insData);
      setRecommendations(recData);
      setSafetyProtocol(protoData);
      setAlerts(alertData || []);
      setCheckins(chkData || []);
      setVoiceRecords(voiceData || []);
    } catch (err: any) {
      const status = err?.statusCode || 500;
      setErrorStatus(status);
      setErrorMessage(err?.detail || err?.message || 'Failed to load case data');
      if (status === 401) {
        logout();
        router.replace('/therapist-login' as any);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      loadCaseData();
    }
  }, [caseId, isAuthenticated]);

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

  const handleResolveAlert = async (alertId: string) => {
    if (!caseId) return;
    setHandlingAlertId(alertId);
    try {
      await therapistService.handleCaseAlert(caseId, alertId, {
        status: 'handled',
        resolution_note: 'Acknowledged and reviewed by clinician',
      });
      // Refresh alerts and safety protocol
      const [updatedAlerts, updatedProto] = await Promise.all([
        therapistService.getCaseAlerts(caseId).catch(() => alerts),
        therapistService.getCaseSafetyProtocol(caseId).catch(() => safetyProtocol),
      ]);
      setAlerts(updatedAlerts || []);
      setSafetyProtocol(updatedProto || null);
    } catch (err: any) {
      console.error('Failed to handle alert:', err);
    } finally {
      setHandlingAlertId(null);
    }
  };

  // Safe computed values for ML predictions
  const hasPred = result && result.results_available;
  const ddsScore =
    hasPred && result.fusion_dds_prediction != null
      ? `${result.fusion_dds_prediction.toFixed(1)}%`
      : 'Unavailable';
  const triage = hasPred ? result.triage_level : 'UNKNOWN';

  // Future risk semantics: null is NEVER zero, LOW, or FALSE
  const tempRisk =
    hasPred && result.temporal_risk_score != null
      ? `${(result.temporal_risk_score * 100).toFixed(1)}% probability`
      : 'Insufficient longitudinal data';

  const futureEscalationText =
    hasPred && result.future_escalation_flag != null
      ? result.future_escalation_flag === 1
        ? 'Escalation Flagged (Potential Deterioration)'
        : 'No Escalation Predicted (Stable Trajectory)'
      : 'Insufficient longitudinal data';

  // Specialists
  const specialists = result?.specialists;
  const structPredText =
    specialists?.struct_available && specialists?.struct_pred != null
      ? `${specialists.struct_pred.toFixed(1)}%`
      : 'Unavailable';
  const textPredText =
    specialists?.text_available && specialists?.text_pred != null
      ? `${specialists.text_pred.toFixed(1)}%`
      : 'Unavailable';
  const voicePredText =
    specialists?.voice_available && specialists?.voice_pred != null
      ? `${specialists.voice_pred.toFixed(1)}%`
      : 'Unavailable';
  const behavPredText =
    specialists?.behav_available && specialists?.behav_pred != null
      ? `${specialists.behav_pred.toFixed(1)}%`
      : 'Behaviour prediction unavailable (Integration blocked)';

  // Patient context
  const patientContext = result?.patient_context;
  const convSummary = patientContext?.conversation_summary;
  const checkinResponses = patientContext?.checkin_responses || [];

  // Triage theme helper
  const getTriageColors = (t: string) => {
    switch (t) {
      case 'CRITICAL':
        return { bg: '#ffebee', text: '#c62828', border: '#ffcdd2' };
      case 'HIGH':
        return { bg: '#fff3e0', text: '#e65100', border: '#ffe0b2' };
      case 'MEDIUM':
        return { bg: '#fffde7', text: '#f57f17', border: '#fff9c4' };
      case 'LOW':
        return { bg: '#e8f5e9', text: '#2e7d32', border: '#c8e6c9' };
      default:
        return { bg: '#f5f5f5', text: '#757575', border: '#e0e0e0' };
    }
  };
  const triageTheme = getTriageColors(triage);

  // 403 Forbidden Screen
  if (errorStatus === 403) {
    return (
      <View style={styles.screen}>
        <View style={styles.content}>
          <View style={styles.top}>
            <Pressable onPress={() => router.back()} style={styles.back}>
              <Ionicons name="arrow-back" size={19} color={COLORS.deepForest} />
            </Pressable>
            <Text style={styles.topLabel}>ACCESS DENIED</Text>
            <View style={styles.backPlaceholder} />
          </View>
          <View style={[styles.errorCard, { marginTop: 40 }]}>
            <Ionicons name="lock-closed" size={36} color="#c62828" />
            <Text style={styles.errorTitle}>Authorization Required</Text>
            <Text style={styles.errorText}>
              You do not have authorization to view this clinical case, or the case does not exist under your credentials.
            </Text>
            <Pressable onPress={() => router.replace('/therapist')} style={styles.button}>
              <Text style={styles.buttonText}>Return to Case Queue</Text>
            </Pressable>
          </View>
        </View>
      </View>
    );
  }

  // Generic Error Screen
  if (errorStatus && errorStatus !== 403) {
    return (
      <View style={styles.screen}>
        <View style={styles.content}>
          <View style={styles.top}>
            <Pressable onPress={() => router.back()} style={styles.back}>
              <Ionicons name="arrow-back" size={19} color={COLORS.deepForest} />
            </Pressable>
            <Text style={styles.topLabel}>SYSTEM NOTICE</Text>
            <View style={styles.backPlaceholder} />
          </View>
          <View style={[styles.errorCard, { marginTop: 40 }]}>
            <Ionicons name="alert-circle-outline" size={36} color="#e65100" />
            <Text style={styles.errorTitle}>Unable to Load Case</Text>
            <Text style={styles.errorText}>
              {errorMessage || 'A network error or backend issue occurred while retrieving clinical records.'}
            </Text>
            <Pressable onPress={loadCaseData} style={styles.button}>
              <Text style={styles.buttonText}>Retry Connection</Text>
            </Pressable>
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.screen}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>
        {/* Top Navigation */}
        <View style={styles.top}>
          <Pressable onPress={() => router.back()} style={styles.back}>
            <Ionicons name="arrow-back" size={19} color={COLORS.deepForest} />
          </Pressable>
          <Text style={styles.topLabel}>CLINICAL REVIEW</Text>
          <Pressable onPress={loadCaseData} style={styles.back}>
            <Ionicons name="refresh" size={18} color={COLORS.forest} />
          </Pressable>
        </View>

        {/* Heading & Triage Badge */}
        <View style={styles.heading}>
          <Text style={styles.eyebrow}>{victimId || caseId || 'MEDHA CASE'}</Text>
          <View style={styles.titleRow}>
            <Text style={styles.title}>Clinical Review</Text>
            <View
              style={[
                styles.reviewPill,
                { backgroundColor: triageTheme.bg, borderColor: triageTheme.border, borderWidth: 1 },
              ]}
            >
              <Text style={[styles.reviewPillText, { color: triageTheme.text }]}>
                {triage} TRIAGE
              </Text>
            </View>
          </View>
          <Text style={styles.subtitle}>
            AI-assisted longitudinal decision support. Final clinical interpretation remains with the therapist.
          </Text>
        </View>

        {/* Status Banner */}
        <View style={styles.banner}>
          <Ionicons name="pulse" size={18} color={COLORS.forest} />
          <View style={styles.bannerCopy}>
            <Text style={styles.bannerTitle}>
              {hasPred ? `Timepoint T${result.timepoint || 1} Assessment` : 'Assessment In Progress'}
            </Text>
            <Text style={styles.bannerText}>
              {hasPred
                ? `Predictions evaluated at ${result.predicted_at ? new Date(result.predicted_at).toLocaleTimeString() : 'record creation'}. Never fabricated.`
                : 'Awaiting sufficient multimodal observations before computing mathematical predictions.'}
            </Text>
          </View>
        </View>

        {/* Tab Selector */}
        <View style={styles.tabContainer}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
            <Pressable
              onPress={() => setActiveTab('predictions')}
              style={[styles.tabButton, activeTab === 'predictions' && styles.tabButtonActive]}
            >
              <Ionicons
                name="stats-chart-outline"
                size={14}
                color={activeTab === 'predictions' ? COLORS.white : COLORS.deepForest}
              />
              <Text style={[styles.tabText, activeTab === 'predictions' && styles.tabTextActive]}>
                Predictions
              </Text>
            </Pressable>

            <Pressable
              onPress={() => setActiveTab('insights')}
              style={[styles.tabButton, activeTab === 'insights' && styles.tabButtonActive]}
            >
              <Ionicons
                name="bulb-outline"
                size={14}
                color={activeTab === 'insights' ? COLORS.white : COLORS.deepForest}
              />
              <Text style={[styles.tabText, activeTab === 'insights' && styles.tabTextActive]}>
                Insights ({insights?.factors?.length || 0})
              </Text>
            </Pressable>

            <Pressable
              onPress={() => setActiveTab('recommendations')}
              style={[styles.tabButton, activeTab === 'recommendations' && styles.tabButtonActive]}
            >
              <Ionicons
                name="list-outline"
                size={14}
                color={activeTab === 'recommendations' ? COLORS.white : COLORS.deepForest}
              />
              <Text style={[styles.tabText, activeTab === 'recommendations' && styles.tabTextActive]}>
                Recommendations ({recommendations?.recommendations?.length || 0})
              </Text>
            </Pressable>

            <Pressable
              onPress={() => setActiveTab('safety')}
              style={[styles.tabButton, activeTab === 'safety' && styles.tabButtonActive]}
            >
              <Ionicons
                name="shield-outline"
                size={14}
                color={activeTab === 'safety' ? COLORS.white : COLORS.deepForest}
              />
              <Text style={[styles.tabText, activeTab === 'safety' && styles.tabTextActive]}>
                Safety & Alerts ({alerts.length})
              </Text>
            </Pressable>

            <Pressable
              onPress={() => setActiveTab('context')}
              style={[styles.tabButton, activeTab === 'context' && styles.tabButtonActive]}
            >
              <Ionicons
                name="chatbubbles-outline"
                size={14}
                color={activeTab === 'context' ? COLORS.white : COLORS.deepForest}
              />
              <Text style={[styles.tabText, activeTab === 'context' && styles.tabTextActive]}>
                Patient Context
              </Text>
            </Pressable>
          </ScrollView>
        </View>

        {loading ? (
          <View style={[styles.emptyCard, { padding: 40 }]}>
            <ActivityIndicator color={COLORS.forest} size="small" style={{ marginBottom: 12 }} />
            <Text style={styles.emptyTitle}>Loading clinical models & context...</Text>
            <Text style={styles.emptyText}>Fetching verified prediction, insights, and session data</Text>
          </View>
        ) : (
          <>
            {/* ========================================================================= */}
            {/* TAB 1: PREDICTIONS & SPECIALIST MODALITIES                                */}
            {/* ========================================================================= */}
            {activeTab === 'predictions' && (
              <View style={{ gap: 12 }}>
                <Text style={styles.sectionEyebrow}>CORE MULTIMODAL FUSION & LONGITUDINAL RISK</Text>

                <ResultCard
                  icon="pulse-outline"
                  title="Multimodal Fusion DDS"
                  value={ddsScore}
                  description={
                    hasPred
                      ? `Authoritative triage level: ${triage}. Mathematical fusion of structured assessment, text sentiment, and acoustic prosody.`
                      : 'No validated prediction generated yet for this timepoint.'
                  }
                  statusPill={ddsScore !== 'Unavailable' ? 'Active' : 'Pending'}
                />

                <ResultCard
                  icon="trending-up-outline"
                  title="Temporal Escalation Risk"
                  value={tempRisk}
                  description="GRU temporal sequence forecasting based on sequential timepoints. Missing value indicates insufficient longitudinal history (<7 timesteps)."
                  statusPill={result?.temporal_risk_score != null ? 'Computed' : 'Insufficient History'}
                />

                <ResultCard
                  icon="alert-circle-outline"
                  title="Future Escalation Flag"
                  value={futureEscalationText}
                  description="Binary risk escalation sentinel derived from GRU trajectory. Never inferred as 0/safe when data is absent."
                  statusPill={result?.future_escalation_flag != null ? 'Evaluated' : 'Unavailable'}
                />

                <Text style={styles.sectionEyebrow}>SPECIALIST MODALITIES (PRESERVING ABSENCE)</Text>

                <View style={styles.interactionCard}>
                  <Interaction
                    icon="clipboard-outline"
                    title="Structured Specialist"
                    value={structPredText}
                    isAvailable={Boolean(specialists?.struct_available && specialists?.struct_pred != null)}
                  />
                  <Interaction
                    icon="chatbubble-outline"
                    title="Text Modality Specialist"
                    value={textPredText}
                    isAvailable={Boolean(specialists?.text_available && specialists?.text_pred != null)}
                  />
                  <Interaction
                    icon="mic-outline"
                    title="Voice Acoustic Specialist"
                    value={voicePredText}
                    isAvailable={Boolean(specialists?.voice_available && specialists?.voice_pred != null)}
                  />
                  <Interaction
                    icon="walk-outline"
                    title="Behaviour Specialist"
                    value={behavPredText}
                    isAvailable={false}
                    notice="Step 10 integration blocked: Engagement_Score generator not recovered. Value is never fabricated as zero."
                  />
                </View>

                <View style={styles.disclaimerCard}>
                  <Ionicons name="information-circle-outline" size={16} color={COLORS.forest} />
                  <Text style={styles.disclaimerText}>
                    Clinical Decision Support Notice: MEDHA predictions assist prioritization. They do not constitute a psychiatric or medical diagnosis.
                  </Text>
                </View>
              </View>
            )}

            {/* ========================================================================= */}
            {/* TAB: CLINICAL EVENTS & TIMELINE */}
        {activeTab === 'timeline' && (
          <View style={{ marginTop: 14 }}>
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
          </View>
        )}

        {/* TAB: PATIENT CASE HISTORY & INTAKE PROFILE */}
        {activeTab === 'history' && (
          <View style={{ marginTop: 14 }}>
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
          </View>
        )}

        {/* TAB 2: CLINICAL INSIGHTS & CONTRIBUTING FACTORS                           */}
            {/* ========================================================================= */}
            {activeTab === 'insights' && (
              <View style={{ gap: 12 }}>
                <Text style={styles.sectionEyebrow}>CLINICAL EXPLAINABILITY & OBSERVATIONS</Text>

                {insights ? (
                  <>
                    <View style={styles.whyCard}>
                      <Text style={styles.whyEyebrow}>OBSERVATIONAL SUMMARY</Text>
                      <Text style={styles.whyTitle}>{insights.summary || 'Summary Available'}</Text>
                      <Text style={styles.whyText}>{insights.disclaimer}</Text>
                    </View>

                    {/* Contributing Factors */}
                    <Text style={styles.sectionEyebrow}>
                      CONTRIBUTING CLINICAL FACTORS ({insights.factors?.length || 0})
                    </Text>
                    {(!insights.factors || insights.factors.length === 0) ? (
                      <View style={styles.emptyCard}>
                        <Text style={styles.emptyTitle}>No specific risk factors detected</Text>
                        <Text style={styles.emptyText}>
                          Routine monitoring; no acute factors identified in the current observations.
                        </Text>
                      </View>
                    ) : (
                      insights.factors.map((f, idx) => (
                        <View key={idx} style={styles.factorCard}>
                          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Text style={styles.factorName}>{f.factor}</Text>
                            <View style={styles.factorTypeBadge}>
                              <Text style={styles.factorTypeText}>{f.type.toUpperCase()}</Text>
                            </View>
                          </View>
                          <Text style={styles.factorDesc}>{f.description}</Text>
                        </View>
                      ))
                    )}

                    {/* Trend Analysis */}
                    <View style={styles.trendCard}>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <Text style={styles.trendTitle}>Longitudinal Trend Trajectory</Text>
                        <View style={[styles.pillBadge, { backgroundColor: insights.trend_available ? '#e8f5e9' : '#eceff1' }]}>
                          <Text style={{ fontSize: 9, fontFamily: 'Inter-Medium', color: insights.trend_available ? '#2e7d32' : '#607d8b' }}>
                            {insights.trend_available ? 'History Available' : 'Insufficient History'}
                          </Text>
                        </View>
                      </View>
                      <Text style={styles.trendDesc}>
                        {insights.trend_explanation || 'Longitudinal trend evaluation requires multiple observed sessions.'}
                      </Text>
                    </View>

                    {/* Signals Summary Grid */}
                    <Text style={styles.sectionEyebrow}>MODALITY DISTRESS SIGNALS (NORMALIZED)</Text>
                    <View style={styles.signalsGrid}>
                      <SignalBlock
                        label="Text Distress"
                        val={insights.signals?.text_distress}
                      />
                      <SignalBlock
                        label="Voice Distress"
                        val={insights.signals?.voice_distress}
                      />
                      <SignalBlock
                        label="Structured Risk"
                        val={insights.signals?.structured_risk}
                      />
                      <SignalBlock
                        label="Behavioural Risk"
                        val={insights.signals?.behavioural_risk}
                        note="Blocked"
                      />
                    </View>

                    {/* Recent Engagement Activity */}
                    <Text style={styles.sectionEyebrow}>RECENT ENGAGEMENT ACTIVITY</Text>
                    <View style={styles.statsRow}>
                      <ActivityStat label="Check-ins" count={insights.recent_activity?.checkins || 0} />
                      <ActivityStat label="Journals" count={insights.recent_activity?.journal_entries || 0} />
                      <ActivityStat label="Voice" count={insights.recent_activity?.voice_interactions || 0} />
                      <ActivityStat label="Chat Turns" count={insights.recent_activity?.text_interactions || 0} />
                    </View>
                  </>
                ) : (
                  <View style={styles.emptyCard}>
                    <Text style={styles.emptyTitle}>No Insights Generated</Text>
                    <Text style={styles.emptyText}>Clinical insights will appear once session data is assessed.</Text>
                  </View>
                )}
              </View>
            )}

            {/* ========================================================================= */}
            {/* TAB 3: CLINICAL RECOMMENDATIONS & SELF-HELP                               */}
            {/* ========================================================================= */}
            {activeTab === 'recommendations' && (
              <View style={{ gap: 12 }}>
                <Text style={styles.sectionEyebrow}>DECISION SUPPORT INTERVENTIONS</Text>

                {recommendations ? (
                  <>
                    {(!recommendations.recommendations || recommendations.recommendations.length === 0) ? (
                      <View style={styles.emptyCard}>
                        <Ionicons name="checkmark-done-circle-outline" size={26} color="#2e7d32" />
                        <Text style={styles.emptyTitle}>Routine Monitoring Recommended</Text>
                        <Text style={styles.emptyText}>
                          No escalated clinical interventions triggered. Continue scheduled supportive check-ins.
                        </Text>
                      </View>
                    ) : (
                      recommendations.recommendations.map((rec) => (
                        <View key={rec.id} style={styles.recCard}>
                          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                            <View style={[styles.priorityBadge, getPriorityStyle(rec.priority)]}>
                              <Text style={styles.priorityText}>{rec.priority}</Text>
                            </View>
                            <Text style={styles.recCategory}>{rec.category.toUpperCase()}</Text>
                          </View>
                          <Text style={styles.recReason}>{rec.reason}</Text>
                          <View style={styles.actionBox}>
                            <Ionicons name="arrow-forward-circle" size={16} color={COLORS.forest} />
                            <Text style={styles.actionText}>{rec.action}</Text>
                          </View>
                        </View>
                      ))
                    )}

                    {/* Tailored Self-Help Psychoeducational Resources */}
                    <Text style={styles.sectionEyebrow}>
                      TAILORED PATIENT SELF-HELP RESOURCES ({recommendations.self_help_resources?.length || 0})
                    </Text>
                    {recommendations.self_help_resources?.map((res) => (
                      <View key={res.id} style={styles.resourceCard}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                          <Ionicons name="book-outline" size={15} color={COLORS.forest} />
                          <Text style={styles.resourceTitle}>{res.title}</Text>
                          <Text style={styles.resourceCategory}>· {res.category}</Text>
                        </View>
                        <Text style={styles.resourceDesc}>{res.description}</Text>
                      </View>
                    ))}

                    <View style={styles.disclaimerCard}>
                      <Text style={styles.disclaimerText}>{recommendations.disclaimer}</Text>
                    </View>
                  </>
                ) : (
                  <View style={styles.emptyCard}>
                    <Text style={styles.emptyTitle}>No Recommendations Available</Text>
                    <Text style={styles.emptyText}>Clinical recommendations will appear once observations are recorded.</Text>
                  </View>
                )}
              </View>
            )}

            {/* ========================================================================= */}
            {/* TAB 4: SAFETY PROTOCOL & ALERTS                                           */}
            {/* ========================================================================= */}
            {activeTab === 'safety' && (
              <View style={{ gap: 12 }}>
                <Text style={styles.sectionEyebrow}>EVALUATED DYNAMIC SAFETY PROTOCOL</Text>

                {safetyProtocol ? (
                  <View
                    style={[
                      styles.safetyCard,
                      safetyProtocol.alert_triggered
                        ? { borderColor: '#c62828', backgroundColor: '#fff8f8' }
                        : { borderColor: COLORS.border, backgroundColor: COLORS.surface },
                    ]}
                  >
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                        <Ionicons
                          name={safetyProtocol.alert_triggered ? 'warning' : 'shield-checkmark'}
                          size={18}
                          color={safetyProtocol.alert_triggered ? '#c62828' : '#2e7d32'}
                        />
                        <Text
                          style={{
                            fontFamily: 'Inter-Medium',
                            fontSize: 12,
                            color: safetyProtocol.alert_triggered ? '#c62828' : '#2e7d32',
                          }}
                        >
                          {safetyProtocol.alert_type}
                        </Text>
                      </View>
                      <View style={[styles.priorityBadge, getPriorityStyle(safetyProtocol.priority)]}>
                        <Text style={styles.priorityText}>{safetyProtocol.priority}</Text>
                      </View>
                    </View>

                    <Text style={styles.safetyTitle}>{safetyProtocol.title}</Text>
                    <Text style={styles.safetyMessage}>{safetyProtocol.message}</Text>

                    <View style={styles.safetyActionBox}>
                      <Text style={{ fontSize: 10, fontFamily: 'Inter-Medium', color: COLORS.deepForest }}>
                        Recommended Action: {safetyProtocol.recommended_action}
                      </Text>
                      {safetyProtocol.reason && (
                        <Text style={{ fontSize: 9, fontFamily: 'Inter-Regular', color: COLORS.mutedText, marginTop: 3 }}>
                          Reason: {safetyProtocol.reason}
                        </Text>
                      )}
                    </View>
                  </View>
                ) : (
                  <View style={styles.emptyCard}>
                    <Text style={styles.emptyTitle}>No Safety Protocol Evaluation</Text>
                    <Text style={styles.emptyText}>Protocol evaluation is pending session ingestion.</Text>
                  </View>
                )}

                {/* Historical Safety Alerts */}
                <Text style={styles.sectionEyebrow}>HISTORICAL SAFETY ALERTS ({alerts.length})</Text>

                {alerts.length === 0 ? (
                  <View style={styles.emptyCard}>
                    <Ionicons name="shield-checkmark-outline" size={24} color="#2e7d32" />
                    <Text style={styles.emptyTitle}>No Safety Alerts Recorded</Text>
                    <Text style={styles.emptyText}>This patient has no active or unresolved clinical safety alerts.</Text>
                  </View>
                ) : (
                  alerts.map((a) => {
                    const isHandled = a.status.toLowerCase() === 'handled' || a.status.toLowerCase() === 'resolved';
                    return (
                      <View key={a.id} style={styles.alertCard}>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                            <Ionicons
                              name={isHandled ? 'checkmark-circle' : 'alert-circle'}
                              size={16}
                              color={isHandled ? '#2e7d32' : '#c62828'}
                            />
                            <Text style={styles.alertEventType}>{a.event_type}</Text>
                          </View>
                          <View
                            style={[
                              styles.pillBadge,
                              { backgroundColor: isHandled ? '#e8f5e9' : '#ffebee' },
                            ]}
                          >
                            <Text
                              style={{
                                fontSize: 9,
                                fontFamily: 'Inter-Medium',
                                color: isHandled ? '#2e7d32' : '#c62828',
                                textTransform: 'uppercase',
                              }}
                            >
                              {a.status}
                            </Text>
                          </View>
                        </View>

                        <Text style={{ fontSize: 10, color: COLORS.mutedText, fontFamily: 'Inter-Regular', marginTop: 4 }}>
                          Detected: {new Date(a.detected_at).toLocaleString()} · Severity: {a.severity.toUpperCase()}
                        </Text>

                        {!isHandled && (
                          <Pressable
                            disabled={handlingAlertId === a.id}
                            onPress={() => handleResolveAlert(a.id)}
                            style={styles.resolveButton}
                          >
                            {handlingAlertId === a.id ? (
                              <ActivityIndicator color={COLORS.white} size="small" />
                            ) : (
                              <>
                                <Ionicons name="checkmark-outline" size={14} color={COLORS.white} />
                                <Text style={styles.resolveButtonText}>Acknowledge & Mark Handled</Text>
                              </>
                            )}
                          </Pressable>
                        )}
                      </View>
                    );
                  })
                )}

                {/* Honest Alert Delivery Disclaimer */}
                <View style={styles.systemNotice}>
                  <Ionicons name="information-circle-outline" size={16} color="#455a64" />
                  <Text style={styles.systemNoticeText}>
                    In-App Clinical Alert Notice: Alerts and protocols are logged in the clinical database and displayed in this dashboard. External emergency notification (SMS/Webhook) delivery is not configured.
                  </Text>
                </View>
              </View>
            )}

            {/* ========================================================================= */}
            {/* TAB 5: PATIENT CONTEXT & CONVERSATIONAL HISTORY                           */}
            {/* ========================================================================= */}
            {activeTab === 'context' && (
              <View style={{ gap: 12 }}>
                <Text style={styles.sectionEyebrow}>PATIENT CONVERSATIONAL SUMMARY (CONTEXTUAL)</Text>

                {convSummary ? (
                  <View style={styles.summaryContainer}>
                    <ContextBlock title="Important Facts" items={convSummary.important_facts} icon="finger-print-outline" />
                    <ContextBlock title="Current Concerns" items={convSummary.current_concerns} icon="alert-outline" />
                    <ContextBlock title="Recent Events" items={convSummary.recent_events} icon="calendar-outline" />
                    <ContextBlock title="Support Context" items={convSummary.support_context} icon="people-outline" />
                    <ContextBlock title="Preferences" items={convSummary.preferences} icon="heart-outline" />
                    <ContextBlock title="Ongoing Topics" items={convSummary.ongoing_topics} icon="repeat-outline" />
                    <ContextBlock title="Unresolved Topics" items={convSummary.unresolved_topics} icon="help-circle-outline" />
                    <ContextBlock title="Important Observations" items={convSummary.important_observations} icon="eye-outline" />
                    {convSummary.updated_at && (
                      <Text style={{ fontSize: 9, color: COLORS.mutedText, fontFamily: 'Inter-Regular', marginTop: 4 }}>
                        Summary updated: {new Date(convSummary.updated_at).toLocaleString()}
                      </Text>
                    )}
                  </View>
                ) : (
                  <View style={styles.emptyCard}>
                    <Text style={styles.emptyTitle}>No Conversation Summary</Text>
                    <Text style={styles.emptyText}>Conversational summary will be generated as chat turns occur.</Text>
                  </View>
                )}

                {/* Recent Check-in Responses from Context */}
                <Text style={styles.sectionEyebrow}>CHECK-IN RESPONSES (SNAPSHOT)</Text>
                {checkinResponses.length === 0 ? (
                  <View style={styles.emptyCard}>
                    <Text style={styles.emptyText}>No check-in answers in latest session snapshot.</Text>
                  </View>
                ) : (
                  checkinResponses.map((q) => (
                    <View key={q.question_id} style={styles.checkinItem}>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text style={{ fontSize: 9, fontFamily: 'Inter-Medium', color: COLORS.mutedText }}>
                          {q.question_id} {q.intent ? `· ${q.intent}` : ''}
                        </Text>
                        {q.timestamp && (
                          <Text style={{ fontSize: 8, color: COLORS.mutedText, fontFamily: 'Inter-Regular' }}>
                            {new Date(q.timestamp).toLocaleTimeString()}
                          </Text>
                        )}
                      </View>
                      <Text style={{ fontSize: 11, fontFamily: 'Inter-Regular', color: COLORS.deepForest, marginVertical: 2 }}>
                        {q.question_text}
                      </Text>
                      <Text style={{ fontSize: 10, fontFamily: 'Inter-Medium', color: '#2e7d32' }}>
                        Answer: {q.response_text || 'Pending response'}
                      </Text>
                    </View>
                  ))
                )}

                {/* Historical Daily Check-ins */}
                <Text style={styles.sectionEyebrow}>HISTORICAL CHECK-IN LOGS ({checkins.length})</Text>
                {checkins.length === 0 ? (
                  <View style={styles.emptyCard}>
                    <Text style={styles.emptyText}>No historical check-in records found for this case.</Text>
                  </View>
                ) : (
                  checkins.slice(0, 5).map((chk) => (
                    <View key={chk.checkin_id} style={styles.checkinLogCard}>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                        <Text style={{ fontSize: 11, fontFamily: 'Inter-Medium', color: COLORS.deepForest }}>
                          Timepoint T{chk.timepoint} Check-in
                        </Text>
                        <View
                          style={[
                            styles.pillBadge,
                            { backgroundColor: chk.status === 'completed' ? '#e8f5e9' : '#fffde7' },
                          ]}
                        >
                          <Text
                            style={{
                              fontSize: 8,
                              fontFamily: 'Inter-Medium',
                              color: chk.status === 'completed' ? '#2e7d32' : '#f57f17',
                              textTransform: 'uppercase',
                            }}
                          >
                            {chk.status}
                          </Text>
                        </View>
                      </View>
                      {(chk.questions || []).map((q) => {
                        const val = q.answer ? Object.values(q.answer)[0] : null;
                        return (
                          <View key={q.question_id} style={styles.checkinSubQuestion}>
                            <Text style={{ fontSize: 9, color: COLORS.mutedText, fontFamily: 'Inter-Medium' }}>
                              {q.question_id} · {q.domain || 'Assessment'}
                            </Text>
                            <Text style={{ fontSize: 10, fontFamily: 'Inter-Regular', color: COLORS.text }}>
                              {q.question_text}
                            </Text>
                            <Text style={{ fontSize: 10, fontFamily: 'Inter-Medium', color: '#2e7d32', marginTop: 2 }}>
                              Answer: {val !== null ? (typeof val === 'number' ? `${val} / 5` : String(val)) : 'Pending'}
                            </Text>
                          </View>
                        );
                      })}
                    </View>
                  ))
                )}

                {/* Voice Check-in Records */}
                <Text style={styles.sectionEyebrow}>VOICE CHECK-IN ACOUSTIC SAMPLES ({voiceRecords.length})</Text>
                {voiceRecords.length === 0 ? (
                  <View style={styles.emptyCard}>
                    <Text style={styles.emptyText}>No acoustic voice records captured for this case.</Text>
                  </View>
                ) : (
                  voiceRecords.slice(0, 3).map((v) => (
                    <View key={v.id} style={styles.voiceCard}>
                      <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                          <Ionicons name="mic-outline" size={15} color={COLORS.forest} />
                          <Text style={{ fontSize: 11, fontFamily: 'Inter-Medium', color: COLORS.deepForest }}>
                            Voice Sample ({v.timepoint ? `T${v.timepoint}` : 'Recent'})
                          </Text>
                        </View>
                        <Text style={{ fontSize: 10, fontFamily: 'Inter-Medium', color: COLORS.deepForest }}>
                          {v.voice_score != null
                            ? `Distress: ${(v.voice_score <= 1.0 ? v.voice_score * 100 : v.voice_score).toFixed(1)}%`
                            : 'Processed'}
                        </Text>
                      </View>
                      {v.transcript && (
                        <View style={styles.transcriptBox}>
                          <Text style={styles.transcriptText}>"{v.transcript}"</Text>
                        </View>
                      )}
                      <Text style={{ fontSize: 9, color: COLORS.mutedText, fontFamily: 'Inter-Regular', marginTop: 4 }}>
                        Duration: {v.duration_seconds != null ? `${v.duration_seconds.toFixed(1)}s` : 'N/A'} · Features: Extracted
                      </Text>
                    </View>
                  ))
                )}
              </View>
            )}
          </>
        )}

        <Pressable onPress={() => router.replace('/therapist')} style={styles.backQueueButton}>
          <Ionicons name="arrow-back" size={16} color={COLORS.deepForest} />
          <Text style={styles.backQueueText}>Back to Case Queue</Text>
        </Pressable>
      </ScrollView>

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

// ---------------------------------------------------------------------------
// Helper Subcomponents
// ---------------------------------------------------------------------------

function ResultCard({
  icon,
  title,
  value,
  description,
  statusPill,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  value: string;
  description: string;
  statusPill?: string;
}) {
  return (
    <View style={styles.resultCard}>
      <View style={styles.resultCardHeader}>
        <View style={styles.resultIcon}>
          <Ionicons name={icon} size={18} color={COLORS.forest} />
        </View>
        <View style={{ flex: 1, marginLeft: 10 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <Text style={styles.resultTitle}>{title}</Text>
            {statusPill && (
              <View style={styles.statusPill}>
                <Text style={styles.statusPillText}>{statusPill}</Text>
              </View>
            )}
          </View>
          <Text style={styles.resultValue}>{value}</Text>
        </View>
      </View>
      <Text style={styles.resultDescription}>{description}</Text>
    </View>
  );
}

function Interaction({
  icon,
  title,
  value,
  isAvailable,
  notice,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  value: string;
  isAvailable?: boolean;
  notice?: string;
}) {
  return (
    <View style={styles.interactionRow}>
      <View style={styles.interactionIcon}>
        <Ionicons name={icon} size={16} color={COLORS.forest} />
      </View>
      <View style={styles.interactionCopy}>
        <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text style={styles.interactionTitle}>{title}</Text>
          <Text
            style={[
              styles.interactionValue,
              !isAvailable && { color: COLORS.mutedText, fontStyle: 'italic' },
            ]}
          >
            {value}
          </Text>
        </View>
        {notice && <Text style={styles.interactionNotice}>{notice}</Text>}
      </View>
    </View>
  );
}

function SignalBlock({ label, val, note }: { label: string; val?: number | null; note?: string }) {
  const displayVal = note ? note : val != null ? `${(val <= 1.0 ? val * 100 : val).toFixed(1)}%` : 'Unavailable';
  return (
    <View style={styles.signalCard}>
      <Text style={styles.signalLabel}>{label}</Text>
      <Text style={[styles.signalValue, displayVal === 'Unavailable' && { color: COLORS.mutedText, fontSize: 11 }]}>
        {displayVal}
      </Text>
    </View>
  );
}

function ActivityStat({ label, count }: { label: string; count: number }) {
  return (
    <View style={styles.activityBlock}>
      <Text style={styles.activityCount}>{count}</Text>
      <Text style={styles.activityLabel}>{label}</Text>
    </View>
  );
}

function ContextBlock({
  title,
  items,
  icon,
}: {
  title: string;
  items: string[];
  icon: keyof typeof Ionicons.glyphMap;
}) {
  if (!items || items.length === 0) return null;
  return (
    <View style={styles.contextCard}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 4 }}>
        <Ionicons name={icon} size={14} color={COLORS.forest} />
        <Text style={styles.contextTitle}>{title}</Text>
      </View>
      {items.map((item, idx) => (
        <View key={idx} style={{ flexDirection: 'row', alignItems: 'flex-start', marginTop: 2, gap: 4 }}>
          <Text style={{ color: COLORS.forest, fontSize: 10 }}>•</Text>
          <Text style={styles.contextText}>{item}</Text>
        </View>
      ))}
    </View>
  );
}

function getPriorityStyle(p: string) {
  switch (p?.toUpperCase()) {
    case 'IMMEDIATE':
    case 'CRITICAL':
      return { backgroundColor: '#ffebee', borderColor: '#ffcdd2' };
    case 'URGENT':
    case 'HIGH':
      return { backgroundColor: '#fff3e0', borderColor: '#ffe0b2' };
    case 'PRIORITY':
    case 'INCREASED':
      return { backgroundColor: '#fffde7', borderColor: '#fff9c4' };
    default:
      return { backgroundColor: '#e3f2fd', borderColor: '#bbdefb' };
  }
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 50,
    paddingBottom: 40,
  },
  top: {
    height: 42,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  back: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  topLabel: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 1.5,
    color: COLORS.forest,
  },
  backPlaceholder: {
    width: 38,
  },
  heading: {
    marginBottom: 14,
  },
  eyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.6,
    color: COLORS.forest,
    marginBottom: 4,
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 26,
    color: COLORS.deepForest,
  },
  subtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.mutedText,
    marginTop: 4,
    lineHeight: 16,
  },
  reviewPill: {
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: 8,
  },
  reviewPillText: {
    fontSize: 9,
    fontFamily: 'Inter-Medium',
    letterSpacing: 0.8,
  },
  banner: {
    backgroundColor: 'rgba(82, 107, 91, 0.08)',
    borderRadius: 14,
    padding: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 16,
  },
  bannerCopy: {
    flex: 1,
  },
  bannerTitle: {
    fontSize: 11,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  bannerText: {
    fontSize: 10,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    marginTop: 1,
  },
  tabContainer: {
    marginBottom: 16,
  },
  tabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  tabButtonActive: {
    backgroundColor: COLORS.forest,
    borderColor: COLORS.forest,
  },
  tabText: {
    fontSize: 10,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  tabTextActive: {
    color: COLORS.white,
  },
  sectionEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.4,
    color: COLORS.forest,
    marginTop: 8,
    marginBottom: 4,
  },
  resultCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  resultCardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  resultIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: 'rgba(82, 107, 91, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  resultTitle: {
    fontSize: 11,
    fontFamily: 'Inter-Medium',
    color: COLORS.mutedText,
  },
  resultValue: {
    fontSize: 15,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
    marginTop: 2,
  },
  resultDescription: {
    fontSize: 10,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    marginTop: 8,
    lineHeight: 14,
  },
  statusPill: {
    backgroundColor: 'rgba(0,0,0,0.04)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  statusPillText: {
    fontSize: 8,
    fontFamily: 'Inter-Medium',
    color: COLORS.mutedText,
  },
  interactionCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: 12,
  },
  interactionRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  interactionIcon: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: 'rgba(82, 107, 91, 0.08)',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
  },
  interactionCopy: {
    flex: 1,
  },
  interactionTitle: {
    fontSize: 11,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  interactionValue: {
    fontSize: 11,
    fontFamily: 'Inter-Medium',
    color: COLORS.forest,
  },
  interactionNotice: {
    fontSize: 9,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    marginTop: 2,
  },
  disclaimerCard: {
    backgroundColor: 'rgba(0,0,0,0.02)',
    borderRadius: 10,
    padding: 10,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  disclaimerText: {
    fontSize: 9,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    flex: 1,
    lineHeight: 13,
  },
  whyCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  whyEyebrow: {
    fontSize: 8,
    fontFamily: 'Inter-Medium',
    letterSpacing: 1.2,
    color: COLORS.forest,
  },
  whyTitle: {
    fontSize: 13,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
    marginVertical: 4,
  },
  whyText: {
    fontSize: 10,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    lineHeight: 15,
  },
  factorCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  factorName: {
    fontSize: 11,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  factorTypeBadge: {
    backgroundColor: 'rgba(82, 107, 91, 0.1)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  factorTypeText: {
    fontSize: 8,
    fontFamily: 'Inter-Medium',
    color: COLORS.forest,
  },
  factorDesc: {
    fontSize: 10,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    marginTop: 4,
    lineHeight: 14,
  },
  trendCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  trendTitle: {
    fontSize: 11,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  trendDesc: {
    fontSize: 10,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    lineHeight: 14,
  },
  pillBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  signalsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  signalCard: {
    flex: 1,
    minWidth: '45%',
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  signalLabel: {
    fontSize: 9,
    fontFamily: 'Inter-Medium',
    color: COLORS.mutedText,
  },
  signalValue: {
    fontSize: 12,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
    marginTop: 2,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
  },
  activityBlock: {
    flex: 1,
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 10,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  activityCount: {
    fontSize: 14,
    fontFamily: 'Inter-Medium',
    color: COLORS.forest,
  },
  activityLabel: {
    fontSize: 8,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    marginTop: 2,
  },
  recCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  priorityBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
  },
  priorityText: {
    fontSize: 8,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  recCategory: {
    fontSize: 9,
    fontFamily: 'Inter-Medium',
    color: COLORS.mutedText,
  },
  recReason: {
    fontSize: 10,
    fontFamily: 'Inter-Regular',
    color: COLORS.text,
    marginVertical: 4,
    lineHeight: 14,
  },
  actionBox: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(82, 107, 91, 0.06)',
    padding: 8,
    borderRadius: 8,
    marginTop: 4,
  },
  actionText: {
    fontSize: 10,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
    flex: 1,
  },
  resourceCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  resourceTitle: {
    fontSize: 11,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  resourceCategory: {
    fontSize: 9,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
  },
  resourceDesc: {
    fontSize: 10,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    marginTop: 2,
  },
  safetyCard: {
    borderRadius: 16,
    padding: 16,
    borderWidth: 1.5,
  },
  safetyTitle: {
    fontSize: 13,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
    marginBottom: 4,
  },
  safetyMessage: {
    fontSize: 11,
    fontFamily: 'Inter-Regular',
    color: COLORS.text,
    lineHeight: 15,
  },
  safetyActionBox: {
    backgroundColor: 'rgba(0,0,0,0.03)',
    borderRadius: 10,
    padding: 10,
    marginTop: 10,
  },
  alertCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  alertEventType: {
    fontSize: 11,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  resolveButton: {
    backgroundColor: COLORS.forest,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 5,
    paddingVertical: 7,
    borderRadius: 8,
    marginTop: 8,
  },
  resolveButtonText: {
    fontSize: 10,
    fontFamily: 'Inter-Medium',
    color: COLORS.white,
  },
  systemNotice: {
    backgroundColor: '#eceff1',
    borderRadius: 12,
    padding: 12,
    flexDirection: 'row',
    gap: 8,
    alignItems: 'flex-start',
  },
  systemNoticeText: {
    fontSize: 9,
    fontFamily: 'Inter-Regular',
    color: '#455a64',
    flex: 1,
    lineHeight: 13,
  },
  summaryContainer: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
    gap: 8,
  },
  contextCard: {
    paddingVertical: 4,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.04)',
  },
  contextTitle: {
    fontSize: 10,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  contextText: {
    fontSize: 10,
    fontFamily: 'Inter-Regular',
    color: COLORS.text,
    flex: 1,
    lineHeight: 14,
  },
  checkinItem: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  checkinLogCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  checkinSubQuestion: {
    marginTop: 6,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.04)',
  },
  voiceCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 14,
    padding: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  transcriptBox: {
    backgroundColor: 'rgba(0,0,0,0.02)',
    padding: 8,
    borderRadius: 8,
    marginVertical: 4,
  },
  transcriptText: {
    fontSize: 10,
    fontStyle: 'italic',
    color: COLORS.deepForest,
  },
  backQueueButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    height: 42,
    borderRadius: 12,
    marginTop: 20,
  },
  backQueueText: {
    fontSize: 11,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  emptyCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    padding: 24,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  emptyTitle: {
    fontSize: 12,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
    marginBottom: 4,
  },
  emptyText: {
    fontSize: 10,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    textAlign: 'center',
    lineHeight: 14,
  },
  errorCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
  },
  errorTitle: {
    fontSize: 15,
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
    marginTop: 10,
    marginBottom: 6,
  },
  errorText: {
    fontSize: 11,
    fontFamily: 'Inter-Regular',
    color: COLORS.mutedText,
    textAlign: 'center',
    lineHeight: 16,
    marginBottom: 16,
  },
  button: {
    backgroundColor: COLORS.forest,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 10,
  },
  buttonText: {
    color: COLORS.white,
    fontFamily: 'Inter-Medium',
    fontSize: 11,
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
  resultCopy: {
    marginLeft: 11,
    flex: 1,
},
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
});
