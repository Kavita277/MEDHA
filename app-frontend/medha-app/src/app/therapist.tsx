<<<<<<< HEAD
import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
=======
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
<<<<<<< HEAD

function Stat({ value, label }: { value: string; label: string }) {
=======
import { therapistService } from '../services/api';

function Stat({ value, label }: { value: string | number; label: string }) {
>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export default function TherapistDashboardScreen() {
<<<<<<< HEAD
=======
  const [cases, setCases] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Enrollment state
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [enrollName, setEnrollName] = useState('');
  const [enrollEmail, setEnrollEmail] = useState('');
  const [enrollPassword, setEnrollPassword] = useState('Patient2026!');
  const [enrollMobile, setEnrollMobile] = useState('');
  const [enrollSubmitting, setEnrollSubmitting] = useState(false);
  const [enrollError, setEnrollError] = useState<string | null>(null);
  const [enrollSuccess, setEnrollSuccess] = useState<any | null>(null);

  const loadCases = () => {
    setLoading(true);
    therapistService.getCases()
      .then((data) => {
        setCases(data || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err?.message || "Failed to load clinical cases");
        setLoading(false);
      });
  };

  useEffect(() => {
    loadCases();
  }, []);

  const handleEnrollPatient = async () => {
    if (!enrollName.trim() || !enrollEmail.trim() || !enrollPassword.trim()) {
      setEnrollError('Name, email, and initial password are required.');
      return;
    }
    setEnrollSubmitting(true);
    setEnrollError(null);
    try {
      const res = await therapistService.createPatient({
        name: enrollName.trim(),
        email: enrollEmail.trim(),
        password: enrollPassword.trim(),
        mobile: enrollMobile.trim() || undefined,
      });
      setEnrollSuccess({
        name: enrollName.trim(),
        email: enrollEmail.trim(),
        password: enrollPassword.trim(),
        victim_id: res.victim_id,
      });
      setEnrollName('');
      setEnrollEmail('');
      setEnrollMobile('');
      loadCases();
    } catch (err: any) {
      setEnrollError(err?.message || 'Failed to enroll patient');
    } finally {
      setEnrollSubmitting(false);
    }
  };

  const activeCases = cases.filter(c => c.status === 'active').length;

>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c
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
<<<<<<< HEAD
          <Pressable style={styles.profile}>
=======
          <Pressable style={styles.profile} onPress={() => router.push('/profile')}>
>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c
            <Ionicons name="person-outline" size={18} color={COLORS.deepForest} />
          </Pressable>
        </View>

        <View style={styles.stats}>
<<<<<<< HEAD
          <Stat value="—" label="Active cases" />
          <Stat value="—" label="High priority" />
          <Stat value="—" label="Follow-ups" />
          <Stat value="—" label="Patients" />
=======
          <Stat value={loading ? '...' : activeCases} label="Active cases" />
          <Stat value={loading ? '...' : cases.length} label="Patients" />
          <Stat value="V2" label="Pipeline" />
          <Stat value="Active" label="Status" />
>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c
        </View>

        <View style={styles.notice}>
          <Ionicons name="information-circle-outline" size={18} color={COLORS.forest} />
          <Text style={styles.noticeText}>
<<<<<<< HEAD
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

=======
            Cases strictly isolated to your authenticated clinician credentials.
            Missing predictions remain unavailable and are never fabricated as zero.
          </Text>
        </View>

        {/* ENROLL PATIENT MODAL / CARD */}
        {showEnrollModal && (
          <View style={{
            backgroundColor: COLORS.surface,
            borderRadius: 20,
            padding: 18,
            marginTop: 18,
            borderWidth: 1.5,
            borderColor: COLORS.forest,
          }}>
            <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <Ionicons name="person-add" size={16} color={COLORS.forest} />
                <Text style={{ fontFamily: 'Inter-Medium', fontSize: 13, color: COLORS.deepForest }}>
                  Enroll New Patient
                </Text>
              </View>
              <Pressable onPress={() => { setShowEnrollModal(false); setEnrollSuccess(null); }}>
                <Ionicons name="close-circle-outline" size={20} color={COLORS.mutedText} />
              </Pressable>
            </View>

            {enrollSuccess ? (
              <View style={{ backgroundColor: '#e8f5e9', padding: 14, borderRadius: 12, marginVertical: 6 }}>
                <Text style={{ fontFamily: 'Inter-Medium', fontSize: 12, color: '#2e7d32', marginBottom: 4 }}>
                  Patient Enrolled Successfully!
                </Text>
                <Text style={{ fontSize: 10, color: COLORS.deepForest, fontFamily: 'Inter-Regular' }}>
                  Hand these credentials to your patient for app login:
                </Text>
                <Text style={{ fontSize: 11, fontFamily: 'Inter-Medium', color: COLORS.deepForest, marginTop: 4 }}>
                  Email: {enrollSuccess.email}
                </Text>
                <Text style={{ fontSize: 11, fontFamily: 'Inter-Medium', color: COLORS.deepForest }}>
                  Password: {enrollSuccess.password}
                </Text>
                <Pressable
                  onPress={() => { setEnrollSuccess(null); setShowEnrollModal(false); }}
                  style={{
                    marginTop: 10,
                    backgroundColor: COLORS.forest,
                    paddingVertical: 8,
                    borderRadius: 8,
                    alignItems: 'center',
                  }}
                >
                  <Text style={{ color: COLORS.white, fontFamily: 'Inter-Medium', fontSize: 11 }}>Done</Text>
                </Pressable>
              </View>
            ) : (
              <View style={{ gap: 8 }}>
                {enrollError && (
                  <Text style={{ fontSize: 10, color: '#c62828', fontFamily: 'Inter-Medium' }}>
                    {enrollError}
                  </Text>
                )}
                <View>
                  <Text style={{ fontSize: 9, fontFamily: 'Inter-Medium', color: COLORS.mutedText, marginBottom: 3 }}>
                    FULL NAME
                  </Text>
                  <TextInput
                    value={enrollName}
                    onChangeText={setEnrollName}
                    placeholder="e.g. Maya Sharma"
                    placeholderTextColor={COLORS.mutedText}
                    style={{
                      height: 38,
                      borderWidth: 1,
                      borderColor: COLORS.border,
                      borderRadius: 10,
                      paddingHorizontal: 10,
                      fontSize: 12,
                      fontFamily: 'Inter-Regular',
                      color: COLORS.deepForest,
                      backgroundColor: COLORS.background,
                    }}
                  />
                </View>

                <View>
                  <Text style={{ fontSize: 9, fontFamily: 'Inter-Medium', color: COLORS.mutedText, marginBottom: 3 }}>
                    PATIENT EMAIL
                  </Text>
                  <TextInput
                    value={enrollEmail}
                    onChangeText={setEnrollEmail}
                    placeholder="maya.s@medha.test"
                    placeholderTextColor={COLORS.mutedText}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    style={{
                      height: 38,
                      borderWidth: 1,
                      borderColor: COLORS.border,
                      borderRadius: 10,
                      paddingHorizontal: 10,
                      fontSize: 12,
                      fontFamily: 'Inter-Regular',
                      color: COLORS.deepForest,
                      backgroundColor: COLORS.background,
                    }}
                  />
                </View>

                <View>
                  <Text style={{ fontSize: 9, fontFamily: 'Inter-Medium', color: COLORS.mutedText, marginBottom: 3 }}>
                    INITIAL TEMPORARY PASSWORD
                  </Text>
                  <TextInput
                    value={enrollPassword}
                    onChangeText={setEnrollPassword}
                    placeholder="Temporary password"
                    placeholderTextColor={COLORS.mutedText}
                    autoCapitalize="none"
                    style={{
                      height: 38,
                      borderWidth: 1,
                      borderColor: COLORS.border,
                      borderRadius: 10,
                      paddingHorizontal: 10,
                      fontSize: 12,
                      fontFamily: 'Inter-Regular',
                      color: COLORS.deepForest,
                      backgroundColor: COLORS.background,
                    }}
                  />
                </View>

                <View>
                  <Text style={{ fontSize: 9, fontFamily: 'Inter-Medium', color: COLORS.mutedText, marginBottom: 3 }}>
                    MOBILE NUMBER (OPTIONAL)
                  </Text>
                  <TextInput
                    value={enrollMobile}
                    onChangeText={setEnrollMobile}
                    placeholder="+91 98765 43210"
                    placeholderTextColor={COLORS.mutedText}
                    keyboardType="phone-pad"
                    style={{
                      height: 38,
                      borderWidth: 1,
                      borderColor: COLORS.border,
                      borderRadius: 10,
                      paddingHorizontal: 10,
                      fontSize: 12,
                      fontFamily: 'Inter-Regular',
                      color: COLORS.deepForest,
                      backgroundColor: COLORS.background,
                    }}
                  />
                </View>

                <Pressable
                  disabled={enrollSubmitting}
                  onPress={handleEnrollPatient}
                  style={{
                    backgroundColor: COLORS.forest,
                    height: 42,
                    borderRadius: 12,
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginTop: 6,
                    flexDirection: 'row',
                    gap: 6,
                  }}
                >
                  {enrollSubmitting ? (
                    <ActivityIndicator color={COLORS.white} size="small" />
                  ) : (
                    <>
                      <Ionicons name="checkmark-circle-outline" size={16} color={COLORS.white} />
                      <Text style={{ color: COLORS.white, fontFamily: 'Inter-Medium', fontSize: 11 }}>
                        Create Patient Account
                      </Text>
                    </>
                  )}
                </Pressable>
              </View>
            )}
          </View>
        )}

        <View style={styles.sectionHeader}>
          <View>
            <Text style={styles.sectionEyebrow}>CASE QUEUE</Text>
            <Text style={styles.sectionTitle}>Assigned cases ({cases.length})</Text>
          </View>
          <Pressable
            onPress={() => { setShowEnrollModal(!showEnrollModal); setEnrollSuccess(null); }}
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              gap: 5,
              backgroundColor: COLORS.forest,
              paddingHorizontal: 12,
              paddingVertical: 7,
              borderRadius: 20,
            }}
          >
            <Ionicons name="person-add-outline" size={13} color={COLORS.white} />
            <Text style={{ fontFamily: 'Inter-Medium', fontSize: 10, color: COLORS.white }}>
              {showEnrollModal ? 'Close' : 'Enroll Patient'}
            </Text>
          </Pressable>
        </View>

        {loading ? (
          <View style={[styles.emptyCard, { padding: 30 }]}>
            <Text style={styles.emptyTitle}>Loading clinical cases...</Text>
          </View>
        ) : cases.length === 0 ? (
          <View style={styles.emptyCard}>
            <View style={styles.emptyIcon}>
              <Ionicons name="folder-open-outline" size={22} color={COLORS.forest} />
            </View>
            <Text style={styles.emptyTitle}>No cases assigned</Text>
            <Text style={styles.emptyText}>
              You currently have no active cases assigned in your clinical queue.
            </Text>
          </View>
        ) : (
          <View style={{ gap: 10, marginVertical: 6 }}>
            {cases.map((c) => (
              <Pressable
                key={c.case_id}
                onPress={() =>
                  router.push({
                    pathname: '/therapist-case' as any,
                    params: { caseId: c.case_id, victimId: c.victim_id },
                  })
                }
                style={{
                  backgroundColor: COLORS.surface,
                  borderRadius: 18,
                  padding: 16,
                  borderWidth: 1,
                  borderColor: COLORS.border,
                  flexDirection: 'row',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                }}
              >
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <Text style={{ fontFamily: 'Inter-Medium', fontSize: 13, color: COLORS.deepForest }}>
                      {c.patient_name || c.victim_id}
                    </Text>
                    <View style={{
                      backgroundColor: c.status === 'active' ? 'rgba(46, 125, 50, 0.1)' : 'rgba(0,0,0,0.05)',
                      paddingHorizontal: 8,
                      paddingVertical: 2,
                      borderRadius: 6,
                    }}>
                      <Text style={{
                        fontSize: 9,
                        fontFamily: 'Inter-Medium',
                        color: c.status === 'active' ? '#2e7d32' : COLORS.mutedText,
                        textTransform: 'uppercase'
                      }}>
                        {c.status}
                      </Text>
                    </View>
                  </View>
                  <Text style={{ fontSize: 10, color: COLORS.mutedText, fontFamily: 'Inter-Regular' }}>
                    ID: {c.victim_id} · Timepoint T{c.current_timepoint}
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={COLORS.forest} />
              </Pressable>
            ))}
          </View>
        )}

>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c
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
