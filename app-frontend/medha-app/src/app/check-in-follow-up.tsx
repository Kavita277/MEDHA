import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

const topics = [
  'Work / Studies',
  'Relationships',
  'Health',
  'Self-doubt',
  'Loneliness',
  'Something else',
];

export default function CheckInFollowUpScreen() {
  const { mood } = useLocalSearchParams<{ mood?: string }>();
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <MedhaScreen
      eyebrow="A little more"
      title={'What’s been taking up\nmost of your mind?'}
      subtitle={mood ? `You’re feeling ${mood.toLowerCase()}. We can stay with that.`
        : 'Choose whatever feels closest right now.'}
      onBack={() => router.back()}
    >
      <View style={styles.list}>
        {topics.map((topic) => {
          const active = selected === topic;
          return (
            <Pressable
              key={topic}
              onPress={() => setSelected(topic)}
              style={[styles.row, active && styles.rowActive]}
            >
              <Text style={[styles.rowText, active && styles.rowTextActive]}>
                {topic}
              </Text>
              <Ionicons
                name={active ? 'checkmark-circle' : 'chevron-forward'}
                size={18}
                color={active ? COLORS.forest : COLORS.mutedText}
              />
            </Pressable>
          );
        })}
      </View>

      <View style={styles.optional}>
        <Ionicons name="heart-outline" size={18} color={COLORS.forest} />
        <Text style={styles.optionalText}>
          You can skip this. MEDHA will never ask you to share more than you want.
        </Text>
      </View>

      <Pressable
        onPress={() => router.replace('/home')}
        style={styles.button}
      >
        <Text style={styles.buttonText}>Save check-in</Text>
      </Pressable>

      <Pressable onPress={() => router.replace('/home')} style={styles.skip}>
        <Text style={styles.skipText}>Maybe later</Text>
      </Pressable>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  list: {
    gap: 10,
  },
  row: {
    minHeight: 56,
    paddingHorizontal: 17,
    borderRadius: 17,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  rowActive: {
    backgroundColor: COLORS.surfaceWarm,
    borderColor: COLORS.forest,
  },
  rowText: {
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.text,
  },
  rowTextActive: {
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  optional: {
    marginTop: 18,
    padding: 15,
    borderRadius: 18,
    backgroundColor: COLORS.mist,
    flexDirection: 'row',
    gap: 10,
    alignItems: 'flex-start',
  },
  optionalText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 16,
    color: COLORS.mutedText,
  },
  button: {
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 22,
  },
  buttonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
  skip: {
    alignItems: 'center',
    paddingVertical: 18,
  },
  skipText: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.mutedText,
  },
});
