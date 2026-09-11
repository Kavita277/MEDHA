import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';

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

import { useEffect, useState } from 'react';
import { therapistService } from '../services/api';

export default function TherapistCaseScreen() {
  const { caseId, victimId } = useLocalSearchParams<{ caseId?: string; victimId?: string }>();
  const [result, setResult] = useState<any>(null);
  const [checkins, setCheckins] = useState<any[]>([]);
  const [voiceRecords, setVoiceRecords] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!caseId || caseId === 'CASE_LAYOUT_PREVIEW') {
      setLoading(false);
      return;
    }
    let mounted = true;
    Promise.all([
      therapistService.getCaseResults(caseId).catch(() => null),
      therapistService.getCaseCheckins(caseId).catch(() => []),
      therapistService.getCaseVoiceRecords(caseId).catch(() => []),
    ]).then(([resData, checkinData, voiceData]) => {
      if (mounted) {
        setResult(resData);
        setCheckins(checkinData || []);
        setVoiceRecords(voiceData || []);
        setLoading(false);
      }
    });
    return () => { mounted = false; };
  }, [caseId]);

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
        <View style={styles.top}>
          <Pressable onPress={() => router.back()} style={styles.back}>
            <Ionicons name="arrow-back" size={19} color={COLORS.deepForest} />
          </Pressable>
          <Text style={styles.topLabel}>CASE REVIEW</Text>
          <View style={styles.backPlaceholder} />
        </View>

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

        {/* RECENT CHECK-INS SECTION */}
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

        {/* VOICE CHECK-IN SAMPLES & PROSODY */}
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
                    {v.voice_score != null ? `Score: ${(v.voice_score * 100).toFixed(1)}%` : 'Processing'}
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
    marginTop: 27,
  },
  eyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.7,
    color: COLORS.forest,
  },
  titleRow: {
    marginTop: 7,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
  },
  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 35,
    color: COLORS.deepForest,
  },
  reviewPill: {
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 10,
    backgroundColor: COLORS.mist,
  },
  reviewPillText: {
    fontFamily: 'Inter-Medium',
    fontSize: 7,
    color: COLORS.forest,
  },
  subtitle: {
    marginTop: 7,
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 15,
    color: COLORS.mutedText,
  },
  banner: {
    marginTop: 20,
    padding: 15,
    borderRadius: 18,
    backgroundColor: COLORS.surfaceWarm,
    flexDirection: 'row',
    gap: 10,
    alignItems: 'flex-start',
  },
  bannerCopy: {
    flex: 1,
  },
  bannerTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.deepForest,
  },
  bannerText: {
    marginTop: 3,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 14,
    color: COLORS.mutedText,
  },
  sectionEyebrow: {
    marginTop: 27,
    marginBottom: 10,
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.7,
    color: COLORS.forest,
  },
  resultCard: {
    minHeight: 95,
    marginBottom: 9,
    padding: 15,
    borderRadius: 18,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    gap: 12,
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
    flex: 1,
  },
  resultTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.mutedText,
  },
  resultValue: {
    marginTop: 2,
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
  whyCard: {
    marginTop: 8,
    padding: 18,
    borderRadius: 20,
    backgroundColor: COLORS.deepForest,
  },
  whyEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.6,
    color: COLORS.lichen,
  },
  whyTitle: {
    marginTop: 8,
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 25,
    color: COLORS.white,
  },
  whyText: {
    marginTop: 6,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 15,
    color: COLORS.stone,
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
