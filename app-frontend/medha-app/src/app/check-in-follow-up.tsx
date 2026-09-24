import React, { useState } from 'react';
import {
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

export interface AdaptiveTopic {
  id: string;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  bg: string;
  color: string;
  adaptiveQuestion: string;
  adaptiveOptions: string[];
}

const topics: AdaptiveTopic[] = [
  {
    id: 'relationships',
    label: 'Relationships / Social support',
    icon: 'heart-outline',
    bg: '#FFEBF1',
    color: '#E05375',
    adaptiveQuestion: 'Have you felt emotionally supported by people around you recently?',
    adaptiveOptions: ['Well supported', 'A little supported', 'Feeling isolated', 'Prefer not to say'],
  },
  {
    id: 'case_legal',
    label: 'Case / Legal process',
    icon: 'document-text-outline',
    bg: '#FFF4D9',
    color: '#CCA01A',
    adaptiveQuestion: 'Has the case or administrative process been causing extra strain or exhaustion?',
    adaptiveOptions: ['Significant strain', 'Moderate strain', 'Manageable right now', 'Not applicable'],
  },
  {
    id: 'safety',
    label: 'Personal safety & surroundings',
    icon: 'shield-outline',
    bg: '#FFEADB',
    color: '#E03E3E',
    adaptiveQuestion: 'Do you feel physically and emotionally safe in your daily environment right now?',
    adaptiveOptions: ['I feel safe right now', 'Somewhat uneasy', 'I do not feel safe'],
  },
  {
    id: 'health',
    label: 'Health & daily energy',
    icon: 'fitness-outline',
    bg: '#E2F5E8',
    color: '#2D8A4E',
    adaptiveQuestion: 'How has your physical energy or sleep been over the past few days?',
    adaptiveOptions: ['Restful & steady', 'A bit low', 'Disrupted / exhausted'],
  },
  {
    id: 'financial',
    label: 'Work, studies or financial concerns',
    icon: 'briefcase-outline',
    bg: '#EEE9FA',
    color: '#6C5CE7',
    adaptiveQuestion: 'Has routine workload or practical pressure felt overwhelming recently?',
    adaptiveOptions: ['Manageable', 'Somewhat heavy', 'Overwhelming'],
  },
  {
    id: 'something_else',
    label: 'General wellbeing / Something else',
    icon: 'ellipsis-horizontal-outline',
    bg: '#E1F2FE',
    color: '#0284C7',
    adaptiveQuestion: 'Would you like to share a few quiet thoughts or speak freely?',
    adaptiveOptions: ['Speak freely in Voice', 'Reflect quietly in Journal', 'Chat with MEDHA'],
  },
];

export default function CheckInFollowUpScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ mood?: string; moodComparison?: string }>();

  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [selectedAdaptiveAnswer, setSelectedAdaptiveAnswer] = useState<string | null>(null);

  const currentTopic = topics.find((t) => t.id === selectedTopic);

  const handleSelectTopic = (topicId: string) => {
    setSelectedTopic(topicId);
    setSelectedAdaptiveAnswer(null);
  };

  const handleContinue = () => {
    if (!selectedTopic) return;

    router.push({
      pathname: '/voice',
      params: {
        mood: params.mood ?? '',
        moodComparison: params.moodComparison ?? '',
        topic: currentTopic?.label ?? selectedTopic,
        adaptiveQuestion: currentTopic?.adaptiveQuestion ?? '',
        adaptiveAnswer: selectedAdaptiveAnswer ?? '',
      },
    });
  };

  return (
    <SafeAreaView style={styles.safe}>
      <StatusBar barStyle="dark-content" backgroundColor="#FAF9F6" />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* TOP BAR: BACK & PROGRESS INDICATOR */}
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

          <View style={styles.progressBadge}>
            <View style={styles.progressTrack}>
              <View style={styles.progressFill} />
            </View>
            <Text style={styles.progressText}>Step 2 of 3</Text>
          </View>
        </View>

        {/* HEADING */}
        <View style={styles.heading}>
          <Text style={styles.eyebrow}>CHECK-IN</Text>
          <Text style={styles.title}>What’s been taking up most of your mind?</Text>
          <Text style={styles.subtitle}>
            {params.mood
              ? `You chose ${params.mood.toLowerCase()}. You can tell me a little more.`
              : 'Choose what feels closest right now.'}
          </Text>
        </View>

        {/* CLEAN WHITE QUESTION CARD WITH BALANCED PASTEL OPTIONS */}
        <View style={styles.questionCard}>
          <View style={styles.list}>
            {topics.map((topic) => {
              const active = selectedTopic === topic.id;

              return (
                <Pressable
                  key={topic.id}
                  onPress={() => handleSelectTopic(topic.id)}
                  style={({ pressed }) => [
                    styles.topicOption,
                    { backgroundColor: topic.bg },
                    active && styles.topicOptionActive,
                    pressed && styles.pressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel={topic.label}
                  accessibilityState={{ selected: active }}
                >
                  <View style={styles.topicLeft}>
                    <View style={styles.iconCircle}>
                      <Ionicons
                        name={topic.icon}
                        size={18}
                        color={topic.color}
                      />
                    </View>

                    <Text style={[styles.topicText, active && styles.topicTextActive]}>
                      {topic.label}
                    </Text>
                  </View>

                  {active ? (
                    <View style={styles.checkBadge}>
                      <Ionicons name="checkmark" size={13} color="#FFFFFF" />
                    </View>
                  ) : (
                    <Ionicons
                      name="chevron-forward"
                      size={16}
                      color="rgba(24, 30, 44, 0.28)"
                    />
                  )}
                </Pressable>
              );
            })}
          </View>
        </View>

        {/* ADAPTIVE FOLLOW-UP CARD */}
        {currentTopic && (
          <View style={styles.adaptiveCard}>
            <View style={styles.adaptiveBadge}>
              <Ionicons name="sparkles" size={13} color={COLORS.coralDark} />
              <Text style={styles.adaptiveBadgeText}>ADAPTIVE FOLLOW-UP</Text>
            </View>
            <Text style={styles.adaptiveTitle}>
              {currentTopic.adaptiveQuestion}
            </Text>

            <View style={styles.adaptiveOptionsWrap}>
              {currentTopic.adaptiveOptions.map((opt) => {
                const active = selectedAdaptiveAnswer === opt;
                return (
                  <Pressable
                    key={opt}
                    onPress={() => setSelectedAdaptiveAnswer(opt)}
                    style={({ pressed }) => [
                      styles.adaptivePill,
                      active && styles.adaptivePillActive,
                      pressed && styles.pressed,
                    ]}
                    accessibilityRole="button"
                    accessibilityLabel={opt}
                    accessibilityState={{ selected: active }}
                  >
                    <Text
                      style={[
                        styles.adaptivePillText,
                        active && styles.adaptivePillTextActive,
                      ]}
                    >
                      {opt}
                    </Text>
                    {active && (
                      <Ionicons
                        name="checkmark-circle"
                        size={15}
                        color={COLORS.navy}
                      />
                    )}
                  </Pressable>
                );
              })}
            </View>

            {/* SAFETY SUPPORT PROMPT IF "I do not feel safe" */}
            {selectedTopic === 'safety' &&
              selectedAdaptiveAnswer === 'I do not feel safe' && (
                <View style={styles.safetySupportBanner}>
                  <Ionicons name="alert-circle-outline" size={18} color="#E03E3E" />
                  <View style={{ flex: 1 }}>
                    <Text style={styles.safetySupportTitle}>
                      Immediate Support is Available
                    </Text>
                    <Text style={styles.safetySupportSub}>
                      If you are in danger or need someone to speak to immediately, support is free, confidential, and available 24/7.
                    </Text>
                    <Pressable
                      onPress={() => router.push('/support')}
                      style={styles.safetySupportBtn}
                      accessibilityRole="button"
                      accessibilityLabel="View Helpline and Support"
                    >
                      <Text style={styles.safetySupportBtnText}>
                        View Helpline & Support (14416 / 112)
                      </Text>
                    </Pressable>
                  </View>
                </View>
              )}
          </View>
        )}

        {/* BOTTOM SECTION: PRIMARY CONTINUE BUTTON & SUPPORTIVE HINT */}
        <View style={styles.bottomSection}>
          <Pressable
            disabled={!selectedTopic}
            onPress={handleContinue}
            style={({ pressed }) => [
              styles.button,
              !selectedTopic && styles.buttonDisabled,
              pressed && selectedTopic && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Continue to voice check-in"
          >
            <Text style={[styles.buttonText, !selectedTopic && styles.buttonTextDisabled]}>
              Continue
            </Text>
            <Ionicons
              name="mic-outline"
              size={18}
              color={selectedTopic ? COLORS.white : 'rgba(24, 30, 44, 0.4)'}
            />
          </Pressable>

          <Text style={styles.hint}>
            Next, MEDHA will listen. You can speak freely for a moment.
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: '#FAF9F6',
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) + 10 : 12,
    paddingBottom: 40,
  },

  /* TOP BAR */
  topBar: {
    height: 48,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  iconButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },
  progressBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  progressTrack: {
    width: 44,
    height: 5,
    borderRadius: 2.5,
    backgroundColor: 'rgba(24, 30, 44, 0.08)',
    overflow: 'hidden',
  },
  progressFill: {
    width: '66%',
    height: '100%',
    borderRadius: 2.5,
    backgroundColor: '#FF735C',
  },
  progressText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    color: '#5B6478',
  },

  /* HEADING */
  heading: {
    marginBottom: 20,
  },
  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.5,
    color: '#E8663F',
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 26,
    lineHeight: 32,
    color: '#181E2C',
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 20,
    color: '#5B6478',
    marginTop: 6,
  },

  /* QUESTION CARD */
  questionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    marginBottom: 24,
    ...SHADOW.subtle,
  },
  list: {
    gap: 10,
  },
  topicOption: {
    minHeight: 56,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderWidth: 1.5,
    borderColor: 'transparent',
  },
  topicOptionActive: {
    borderColor: '#FF735C',
  },
  topicLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.72)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  topicText: {
    flex: 1,
    fontFamily: 'Nunito-SemiBold',
    fontSize: 14.5,
    color: '#181E2C',
  },
  topicTextActive: {
    fontFamily: 'Nunito-Bold',
    color: '#181E2C',
  },
  checkBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: '#FF735C',
    alignItems: 'center',
    justifyContent: 'center',
  },

  /* BOTTOM SECTION */
  bottomSection: {
    width: '100%',
  },
  button: {
    height: 52,
    borderRadius: RADIUS.pill,
    backgroundColor: '#181E2C',
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
    color: '#FFFFFF',
  },
  buttonTextDisabled: {
    color: '#5B6478',
  },

  hint: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    textAlign: 'center',
    color: '#5B6478',
    marginTop: 14,
  },

  /* ADAPTIVE FOLLOW-UP CARD */
  adaptiveCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    marginBottom: 20,
    ...SHADOW.subtle,
  },
  adaptiveBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    backgroundColor: '#FFEADB',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: RADIUS.pill,
    marginBottom: 10,
  },
  adaptiveBadgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.2,
    color: '#E8663F',
    textTransform: 'uppercase',
  },
  adaptiveTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 15.5,
    lineHeight: 22,
    color: '#181E2C',
    marginBottom: 14,
  },
  adaptiveOptionsWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  adaptivePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 9,
    paddingHorizontal: 14,
    borderRadius: RADIUS.pill,
    backgroundColor: '#F8F9FA',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.06)',
  },
  adaptivePillActive: {
    backgroundColor: '#FFFFFF',
    borderColor: '#181E2C',
    borderWidth: 1.5,
  },
  adaptivePillText: {
    fontFamily: 'Nunito-Medium',
    fontSize: 13,
    color: '#5B6478',
  },
  adaptivePillTextActive: {
    fontFamily: 'Nunito-Bold',
    color: '#181E2C',
  },

  /* SAFETY SUPPORT BANNER */
  safetySupportBanner: {
    marginTop: 14,
    backgroundColor: '#FFF1F1',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#FFD1D1',
    padding: 14,
    flexDirection: 'row',
    gap: 12,
  },
  safetySupportTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 14,
    color: '#E03E3E',
    marginBottom: 3,
  },
  safetySupportSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: '#7A2E2E',
    marginBottom: 10,
  },
  safetySupportBtn: {
    alignSelf: 'flex-start',
    backgroundColor: '#E03E3E',
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
  },
  safetySupportBtnText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 12,
    color: '#FFFFFF',
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.88,
  },
});
