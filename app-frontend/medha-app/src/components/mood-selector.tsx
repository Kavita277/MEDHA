import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { COLORS } from '../constants/colors';

interface Mood {
  label: string;
  symbol: string;
}

const moods: Mood[] = [
  { label: 'Heavy', symbol: '●' },
  { label: 'Low', symbol: '◐' },
  { label: 'Okay', symbol: '○' },
  { label: 'Good', symbol: '◒' },
  { label: 'Light', symbol: '◉' },
];

interface MoodSelectorProps {
  selected: string | null;
  onSelect: (mood: string) => void;
}

export function MoodSelector({
  selected,
  onSelect,
}: MoodSelectorProps) {
  return (
    <View style={styles.container}>
      {moods.map((mood) => {
        const active = selected === mood.label;

        return (
          <Pressable
            key={mood.label}
            onPress={() => onSelect(mood.label)}
            style={[styles.item, active && styles.active]}
          >
            <View style={[styles.orb, active && styles.activeOrb]}>
              <Text style={[styles.symbol, active && styles.activeSymbol]}>
                {mood.symbol}
              </Text>
            </View>

            <Text style={[styles.label, active && styles.activeLabel]}>
              {mood.label}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 18,
  },

  item: {
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 4,
    borderRadius: 20,
  },

  active: {
    backgroundColor: COLORS.surfaceWarm,
  },

  orb: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },

  activeOrb: {
    backgroundColor: COLORS.forest,
  },

  symbol: {
    fontSize: 17,
    color: COLORS.moss,
  },

  activeSymbol: {
    color: COLORS.white,
  },

  label: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.mutedText,
  },

  activeLabel: {
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },
});