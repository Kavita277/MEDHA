import React, { useState } from 'react';
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';
import { MedhaBottomNav } from '../components/medha-bottom-nav';

const moods = [
  { label: 'Overwhelmed', icon: 'sad-outline' as const, bg: '#FFEBF1', color: '#E05375' },
  { label: 'Anxious', icon: 'pulse-outline' as const, bg: '#FFEADB', color: '#E8663F' },
  { label: 'Low', icon: 'cloud-outline' as const, bg: '#E1F2FE', color: '#0284C7' },
  { label: 'Okay', icon: 'ellipse-outline' as const, bg: '#EEE9FA', color: '#7C6EE6' },
  { label: 'Good', icon: 'sunny-outline' as const, bg: '#FFF4D9', color: '#CCA01A' },
  { label: 'Great', icon: 'leaf-outline' as const, bg: '#E2F5E8', color: '#2D8A4E' },
];

const moodChanges = [
  { label: 'Much lower', dotColor: '#E05375' },
  { label: 'A little lower', dotColor: '#E8663F' },
  { label: 'About the same', dotColor: '#0284C7' },
  { label: 'A little better', dotColor: '#2D8A4E' },
  { label: 'Much better', dotColor: '#CCA01A' },
];

let inMemoryAgeSuitability = false;

function getAgeSuitabilityAcknowledged(): boolean {
  if (typeof window !== 'undefined' && window.localStorage) {
    return window.localStorage.getItem('medha_age_suitability_acknowledged') === 'true';
  }
  return inMemoryAgeSuitability;
}

function setAgeSuitabilityAcknowledged(acknowledged: boolean): void {
  if (typeof window !== 'undefined' && window.localStorage) {
    window.localStorage.setItem(
      'medha_age_suitability_acknowledged',
      acknowledged ? 'true' : 'false',
    );
  }
  inMemoryAgeSuitability = acknowledged;
}

export default function CheckInScreen() {
  const [ageAcknowledged, setAgeAcknowledged] = useState(() => getAgeSuitabilityAcknowledged());
  const [ageConfirmed, setAgeConfirmed] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [moodComparison, setMoodComparison] = useState<string | null>(null);

  const handleConfirmAge = () => {
    if (!ageConfirmed) return;
    setAgeSuitabilityAcknowledged(true);
    setAgeAcknowledged(true);
  };

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* TOP BAR */}
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
              <Ionicons name="arrow-back" size={20} color={COLORS.navy} />
            </Pressable>
          </View>

          {/* AGE SUITABILITY GATE (BEFORE FIRST SENSITIVE CHECK-IN) */}
          {!ageAcknowledged ? (
            <View style={styles.gateCard}>
              <View style={styles.gateBadge}>
                <Ionicons name="shield-checkmark-outline" size={15} color={COLORS.coralDark} />
                <Text style={styles.gateBadgeText}>BEFORE YOU BEGIN</Text>
              </View>

              <Text style={styles.gateTitle}>Age Suitability</Text>
              <Text style={styles.gateDescription}>
                This wellbeing questionnaire is intended for people aged 13 and above.
              </Text>

              <Pressable
                onPress={() => setAgeConfirmed((prev) => !prev)}
                style={({ pressed }) => [
                  styles.checkboxRow,
                  ageConfirmed && styles.checkboxRowActive,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: ageConfirmed }}
              >
                <View style={[styles.checkbox, ageConfirmed && styles.checkboxActive]}>
                  {ageConfirmed && (
                    <Ionicons name="checkmark" size={13} color={COLORS.white} />
                  )}
                </View>
                <Text style={styles.checkboxLabel}>
                  I confirm that this questionnaire is suitable for my age.
                </Text>
              </Pressable>

              <Pressable
                disabled={!ageConfirmed}
                onPress={handleConfirmAge}
                style={({ pressed }) => [
                  styles.button,
                  !ageConfirmed && styles.buttonDisabled,
                  pressed && ageConfirmed && styles.pressed,
                  { marginTop: 22 },
                ]}
                accessibilityRole="button"
                accessibilityLabel="Continue to check-in"
              >
                <Text style={[styles.buttonText, !ageConfirmed && styles.buttonTextDisabled]}>
                  Continue
                </Text>
                <Ionicons
                  name="arrow-forward"
                  size={18}
                  color={ageConfirmed ? COLORS.white : COLORS.navyMuted}
                />
              </Pressable>
            </View>
          ) : (
            <>
              {/* HEADING */}
              <View style={styles.heading}>
                <Text style={styles.eyebrow}>QUICK CHECK-IN</Text>
                <Text style={styles.title}>How are you feeling{'\n'}today?</Text>
                <Text style={styles.subtitle}>It’s okay to feel whatever you feel.</Text>
              </View>

              {/* 2-COLUMN BALANCED MOOD SELECTION GRID */}
              <View style={styles.grid}>
                {moods.map((mood) => {
                  const active = selected === mood.label;
                  return (
                    <Pressable
                      key={mood.label}
                      onPress={() => setSelected(mood.label)}
                      style={({ pressed }) => [
                        styles.moodCard,
                        active && styles.moodCardActive,
                        pressed && styles.pressed,
                      ]}
                      accessibilityRole="button"
                      accessibilityLabel={mood.label}
                      accessibilityState={{ selected: active }}
                    >
                      {active && (
                        <View style={styles.checkBadge}>
                          <Ionicons name="checkmark" size={13} color={COLORS.white} />
                        </View>
                      )}

                      <View style={[styles.moodIconBadge, { backgroundColor: mood.bg }]}>
                        <Ionicons
                          name={mood.icon}
                          size={22}
                          color={mood.color}
                        />
                      </View>

                      <Text style={[styles.moodText, active && styles.activeText]}>
                        {mood.label}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>

              {/* LIGHTWEIGHT MOOD-CHANGE QUESTION */}
              <View style={styles.comparisonSection}>
                <Text style={styles.comparisonTitle}>
                  Compared with your usual days, how has your mood been recently?
                </Text>
                <View style={styles.comparisonOptions}>
                  {moodChanges.map((option) => {
                    const active = moodComparison === option.label;
                    return (
                      <Pressable
                        key={option.label}
                        onPress={() => setMoodComparison(option.label)}
                        style={({ pressed }) => [
                          styles.comparisonPill,
                          active && styles.comparisonPillActive,
                          pressed && styles.pressed,
                        ]}
                        accessibilityRole="button"
                        accessibilityLabel={option.label}
                        accessibilityState={{ selected: active }}
                      >
                        <View
                          style={[
                            styles.comparisonDot,
                            { backgroundColor: option.dotColor },
                          ]}
                        />
                        <Text
                          style={[
                            styles.comparisonText,
                            active && styles.comparisonTextActive,
                          ]}
                        >
                          {option.label}
                        </Text>
                        {active && (
                          <Ionicons
                            name="checkmark"
                            size={14}
                            color={COLORS.navy}
                            style={styles.comparisonCheck}
                          />
                        )}
                      </Pressable>
                    );
                  })}
                </View>
              </View>

              {/* REASSURING NOTE CARD (GENTLE MOTIVATION) */}
              <View style={styles.note}>
                <View style={styles.noteIconBadge}>
                  <Ionicons name="sparkles" size={16} color={COLORS.coralDark} />
                </View>
                <Text style={styles.noteText}>
                  You showed up today. That's a good step — small, consistent check-ins can help you notice how you're feeling over time.
                </Text>
              </View>

              {/* NEXT CTA BUTTON */}
              <Pressable
                disabled={!selected}
                onPress={() =>
                  router.push({
                    pathname: '/check-in-follow-up',
                    params: {
                      mood: selected ?? '',
                      moodComparison: moodComparison ?? '',
                    },
                  })
                }
                style={({ pressed }) => [
                  styles.button,
                  !selected && styles.buttonDisabled,
                  pressed && selected && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Next check-in step"
              >
                <Text style={[styles.buttonText, !selected && styles.buttonTextDisabled]}>
                  Next
                </Text>
                <Ionicons
                  name="arrow-forward"
                  size={18}
                  color={selected ? COLORS.white : COLORS.navyMuted}
                />
              </Pressable>
            </>
          )}
        </ScrollView>

        {/* FLOATING BOTTOM NAVIGATION */}
        <View style={styles.bottomNavContainer}>
          <MedhaBottomNav activeTab="check-in" />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: COLORS.porcelain,
  },
  container: {
    flex: 1,
    position: 'relative',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 110,
  },

  /* TOP BAR */
  topBar: {
    height: 48,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  iconButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },

  /* HEADING */
  heading: {
    marginBottom: 24,
  },
  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.5,
    color: COLORS.coralDark,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 28,
    lineHeight: 34,
    color: COLORS.navy,
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 20,
    color: COLORS.navyMuted,
    marginTop: 6,
  },

  /* MOOD GRID (SPACIOUS 2X3) */
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 18,
  },
  moodCard: {
    width: '48%',
    borderRadius: RADIUS.card,
    backgroundColor: COLORS.white,
    borderWidth: 1.5,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 18,
    paddingHorizontal: 12,
    position: 'relative',
    ...SHADOW.subtle,
  },
  moodCardActive: {
    borderColor: COLORS.navy,
    borderWidth: 2,
  },
  checkBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: COLORS.navy,
    alignItems: 'center',
    justifyContent: 'center',
  },
  moodIconBadge: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  moodText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
    textAlign: 'center',
  },
  activeText: {
    fontFamily: 'Fredoka-SemiBold',
    color: COLORS.navy,
  },

  /* NOTE CARD */
  note: {
    padding: 16,
    borderRadius: RADIUS.card,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center',
    marginBottom: 24,
    ...SHADOW.subtle,
  },
  noteIconBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#FFEADB',
    alignItems: 'center',
    justifyContent: 'center',
  },
  noteText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 18,
    color: COLORS.navyMuted,
  },

  /* BUTTON */
  button: {
    height: 52,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.navy,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    ...SHADOW.subtle,
  },
  buttonDisabled: {
    backgroundColor: 'rgba(24, 30, 44, 0.12)',
  },
  buttonText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.white,
  },
  buttonTextDisabled: {
    color: COLORS.navyMuted,
  },

  /* MOOD COMPARISON SECTION */
  comparisonSection: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 16,
    marginBottom: 16,
    ...SHADOW.subtle,
  },
  comparisonTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14.5,
    lineHeight: 20,
    color: COLORS.navy,
    marginBottom: 12,
  },
  comparisonOptions: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  comparisonPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: RADIUS.pill,
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.06)',
  },
  comparisonPillActive: {
    backgroundColor: COLORS.white,
    borderColor: COLORS.navy,
    borderWidth: 1.5,
  },
  comparisonDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  comparisonText: {
    fontFamily: 'Nunito-Medium',
    fontSize: 13,
    color: COLORS.navyMuted,
  },
  comparisonTextActive: {
    fontFamily: 'Nunito-Bold',
    color: COLORS.navy,
  },
  comparisonCheck: {
    marginLeft: 2,
  },

  /* AGE SUITABILITY GATE CARD */
  gateCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 22,
    marginTop: 8,
    marginBottom: 24,
    ...SHADOW.subtle,
  },
  gateBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    backgroundColor: '#FFEADB',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: RADIUS.pill,
    marginBottom: 12,
  },
  gateBadgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.2,
    color: COLORS.coralDark,
    textTransform: 'uppercase',
  },
  gateTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 24,
    lineHeight: 30,
    color: COLORS.navy,
    marginBottom: 8,
  },
  gateDescription: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 20,
    color: COLORS.navyMuted,
    marginBottom: 20,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FAF9F6',
    borderWidth: 1.5,
    borderColor: 'rgba(0, 0, 0, 0.08)',
    borderRadius: RADIUS.card,
    padding: 16,
    gap: 12,
  },
  checkboxRowActive: {
    borderColor: COLORS.navy,
    backgroundColor: COLORS.white,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 6,
    borderWidth: 1.5,
    borderColor: 'rgba(0, 0, 0, 0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: COLORS.white,
  },
  checkboxActive: {
    backgroundColor: COLORS.navy,
    borderColor: COLORS.navy,
  },
  checkboxLabel: {
    flex: 1,
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13.5,
    lineHeight: 18,
    color: COLORS.navy,
  },

  /* BOTTOM NAV CONTAINER */
  bottomNavContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.88,
  },
});
