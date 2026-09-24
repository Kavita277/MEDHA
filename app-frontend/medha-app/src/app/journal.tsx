import React, { useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { MedhaScreen } from '../components/medha-screen';
import { MedhaButton } from '../components/medha-button';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

const moods = [
  { label: 'Calm', emoji: '🌿', color: COLORS.greenSoft, border: COLORS.green },
  { label: 'Grateful', emoji: '🌸', color: COLORS.pinkSoft, border: COLORS.pink },
  { label: 'Stressed', emoji: '⚡', color: COLORS.yellowSoft, border: COLORS.yellow },
  { label: 'Hopeful', emoji: '☀️', color: COLORS.blueSoft, border: COLORS.blue },
  { label: 'Tired', emoji: '🌙', color: '#F3EFFF', border: COLORS.lavender },
  { label: 'Unsure', emoji: '💭', color: COLORS.creamSecondary, border: COLORS.peach },
];

export default function JournalScreen() {
  const router = useRouter();
  const [text, setText] = useState('');
  const [mood, setMood] = useState<string | null>(null);

  // Dynamic formatted date
  const today = new Date();
  const dateString = today.toLocaleDateString('en-US', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  return (
    <MedhaScreen
      eyebrow="Today’s Journal"
      title="A space just for you."
      subtitle="Write without needing to make sense of everything."
      onBack={() => router.back()}
      withBackground={true}
    >
      {/* CALENDAR / DATE PILL */}
      <View style={styles.datePill}>
        <View style={styles.calendarIconWrap}>
          <Ionicons name="calendar-outline" size={14} color={COLORS.coralDark} />
        </View>
        <Text style={styles.dateText}>{dateString || 'Today'}</Text>
      </View>

      {/* PAPER WRITING CARD (Pink-soft themed per HTML benchmark) */}
      <View style={styles.paperCard}>
        <View style={styles.paperHeader}>
          <Text style={styles.paperPrompt}>What’s on your mind today?</Text>
          <Ionicons name="pencil-outline" size={15} color={COLORS.pinkDark} />
        </View>

        <TextInput
          value={text}
          onChangeText={setText}
          multiline
          placeholder="Start writing freely... You can say as little or as much as you like."
          placeholderTextColor={COLORS.subtleText}
          style={styles.input}
          textAlignVertical="top"
        />

        <View style={styles.paperFooter}>
          <Ionicons name="lock-closed-outline" size={12} color={COLORS.navyMuted} />
          <Text style={styles.privateText}>Private to you</Text>
        </View>
      </View>

      {/* MOOD SELECTION */}
      <View style={styles.moodSection}>
        <Text style={styles.moodHeading}>HOW ARE YOU FEELING RIGHT NOW?</Text>

        <View style={styles.moodGrid}>
          {moods.map((item) => {
            const active = mood === item.label;

            return (
              <Pressable
                key={item.label}
                onPress={() => setMood(active ? null : item.label)}
                style={({ pressed }) => [
                  styles.moodChip,
                  { backgroundColor: item.color, borderColor: item.border },
                  active && styles.moodChipActive,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel={`Feeling ${item.label}`}
                accessibilityState={{ selected: active }}
              >
                <Text style={styles.moodEmoji}>{item.emoji}</Text>
                <Text
                  style={[
                    styles.moodText,
                    active && styles.moodTextActive,
                  ]}
                >
                  {item.label}
                </Text>
                {active && (
                  <View style={styles.activeCheck}>
                    <Ionicons name="checkmark" size={12} color={COLORS.white} />
                  </View>
                )}
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* SAVE ACTION */}
      <View style={styles.saveWrapper}>
        <MedhaButton
          title="Save Entry"
          variant="coral"
          size="lg"
          icon="checkmark-circle"
          iconPosition="right"
          onPress={() => router.push('/home')}
        />
      </View>

      <Text style={styles.reassuranceText}>
        Entries are stored locally on your device for your own reflection.
      </Text>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  datePill: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.95)',
    marginBottom: 16,
    ...SHADOW.card,
  },
  calendarIconWrap: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: COLORS.creamSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dateText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 12,
    color: COLORS.navy,
  },

  /* PAPER WRITING CARD */
  paperCard: {
    minHeight: 250,
    backgroundColor: COLORS.pinkSoft,
    borderRadius: RADIUS.card + 4,
    borderWidth: 1.5,
    borderColor: COLORS.pink,
    padding: 18,
    ...SHADOW.soft,
  },
  paperHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(232, 98, 142, 0.2)',
    paddingBottom: 8,
  },
  paperPrompt: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
  },
  input: {
    flex: 1,
    minHeight: 160,
    fontFamily: 'Nunito-Regular',
    fontSize: 15,
    lineHeight: 23,
    color: COLORS.navy,
    paddingTop: 4,
  },
  paperFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    alignSelf: 'flex-end',
    marginTop: 8,
  },
  privateText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 10,
    color: COLORS.navyMuted,
  },

  /* MOOD SELECTION */
  moodSection: {
    marginTop: 24,
  },
  moodHeading: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.4,
    color: COLORS.coralDark,
    marginBottom: 12,
  },
  moodGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  moodChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: RADIUS.pill,
    borderWidth: 1.5,
    gap: 7,
    ...SHADOW.card,
  },
  moodChipActive: {
    backgroundColor: COLORS.charcoal,
    borderColor: COLORS.charcoal,
  },
  moodEmoji: {
    fontSize: 14,
  },
  moodText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: COLORS.navy,
  },
  moodTextActive: {
    color: COLORS.white,
    fontFamily: 'Fredoka-Medium',
  },
  activeCheck: {
    width: 16,
    height: 16,
    borderRadius: 8,
    backgroundColor: COLORS.coral,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 2,
  },

  /* SAVE */
  saveWrapper: {
    marginTop: 26,
  },
  reassuranceText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    textAlign: 'center',
    marginTop: 14,
    marginBottom: 10,
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.88,
  },
});
