import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

const moods = [
  { label: 'Overwhelmed', icon: 'sad-outline' as const, tone: COLORS.support },
  { label: 'Anxious', icon: 'remove-circle-outline' as const, tone: COLORS.elevated },
  { label: 'Low', icon: 'cloud-outline' as const, tone: COLORS.water },
  { label: 'Okay', icon: 'ellipse-outline' as const, tone: COLORS.okay },
  { label: 'Good', icon: 'sunny-outline' as const, tone: COLORS.sand },
  { label: 'Great', icon: 'leaf-outline' as const, tone: COLORS.forest },
];

export default function CheckInScreen() {
  const [selected, setSelected] = useState<string | null>(null);

  return (
    <MedhaScreen
      eyebrow="Quick check-in"
      title={'How are you feeling\ntoday?'}
      subtitle="It’s okay to feel whatever you feel."
      onBack={() => router.back()}
    >
      <View style={styles.grid}>
        {moods.map((mood) => {
          const active = selected === mood.label;
          return (
            <Pressable
              key={mood.label}
              onPress={() => setSelected(mood.label)}
              style={[styles.moodCard, active && styles.moodCardActive]}
            >
              <View
                style={[
                  styles.moodIcon,
                  { backgroundColor: mood.tone + '35' },
                  active && { backgroundColor: COLORS.forest },
                ]}
              >
                <Ionicons
                  name={mood.icon}
                  size={22}
                  color={active ? COLORS.white : COLORS.deepForest}
                />
              </View>
              <Text style={[styles.moodText, active && styles.activeText]}>
                {mood.label}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <View style={styles.note}>
        <Ionicons name="sparkles-outline" size={18} color={COLORS.forest} />
        <Text style={styles.noteText}>
          You don’t need to explain everything. One small check-in is enough.
        </Text>
      </View>

      <Pressable
        disabled={!selected}
        onPress={() => router.push({ pathname: '/check-in-follow-up', params: { mood: selected ?? '' } })}
        style={({ pressed }) => [
          styles.button,
          !selected && styles.buttonDisabled,
          pressed && selected && styles.buttonPressed,
        ]}
      >
        <Text style={styles.buttonText}>Next</Text>
        <Ionicons name="arrow-forward" size={18} color={COLORS.white} />
      </Pressable>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 12,
  },
  moodCard: {
    width: '31%',
    minHeight: 126,
    borderRadius: 22,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 8,
  },
  moodCardActive: {
    borderColor: COLORS.forest,
    backgroundColor: COLORS.surfaceWarm,
  },
  moodIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 11,
  },
  moodText: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.mutedText,
    textAlign: 'center',
  },
  activeText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
  note: {
    marginTop: 20,
    padding: 16,
    borderRadius: 18,
    backgroundColor: COLORS.surfaceWarm,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    gap: 11,
    alignItems: 'flex-start',
  },
  noteText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    lineHeight: 17,
    color: COLORS.mutedText,
  },
  button: {
    height: 52,
    borderRadius: 26,
    marginTop: 22,
    backgroundColor: COLORS.forest,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
  },
  buttonDisabled: {
    backgroundColor: COLORS.lichen,
  },
  buttonPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.98 }],
  },
  buttonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
});
