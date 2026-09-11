import React, { useEffect, useRef, useState } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

const suggestions = [
  'How can you help me today?',
  'I’m feeling anxious.',
  'Help me sleep better.',
  'Just listening...',
];

export default function VoiceAssistantScreen() {
  const [listening, setListening] = useState(false);
  const wave = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(wave, {
          toValue: 1,
          duration: 1100,
          useNativeDriver: true,
        }),
        Animated.timing(wave, {
          toValue: 0,
          duration: 1100,
          useNativeDriver: true,
        }),
      ])
    );

    animation.start();
    return () => animation.stop();
  }, [wave]);

  const scale = wave.interpolate({
    inputRange: [0, 1],
    outputRange: [0.96, 1.04],
  });

  return (
    <MedhaScreen
      eyebrow="Voice assistant"
      title="Speak with MEDHA"
      subtitle="Natural conversation. Meaningful support."
      onBack={() => router.back()}
    >
      <View style={styles.center}>
        <Animated.View style={[styles.waveOrb, { transform: [{ scale }] }]}>
          <View style={styles.waveLine} />
          <View style={[styles.waveLine, styles.waveLineLarge]} />
          <View style={styles.waveLine} />
          <View style={styles.micCircle}>
            <Ionicons
              name={listening ? 'mic' : 'mic-outline'}
              size={28}
              color={COLORS.white}
            />
          </View>
        </Animated.View>

        <Text style={styles.status}>
          {listening ? 'I’m listening.' : 'Whenever you’re ready.'}
        </Text>
        <Text style={styles.hint}>
          You can speak naturally. There’s no right way to begin.
        </Text>
      </View>

      <View style={styles.suggestions}>
        {suggestions.map((suggestion) => (
          <Pressable key={suggestion} style={styles.suggestion}>
            <Text style={styles.suggestionText}>{suggestion}</Text>
            <Ionicons name="chevron-forward" size={16} color={COLORS.mutedText} />
          </Pressable>
        ))}
      </View>

      <Pressable
        onPress={() => setListening((value) => !value)}
        style={[styles.button, listening && styles.buttonListening]}
      >
        <Ionicons
          name={listening ? 'stop' : 'mic'}
          size={20}
          color={COLORS.white}
        />
        <Text style={styles.buttonText}>
          {listening ? 'Stop listening' : 'Start talking'}
        </Text>
      </Pressable>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  center: {
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 300,
  },
  waveOrb: {
    width: 230,
    height: 230,
    borderRadius: 115,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  waveLine: {
    position: 'absolute',
    width: 155,
    height: 1,
    backgroundColor: COLORS.water,
    transform: [{ rotate: '-10deg' }],
  },
  waveLineLarge: {
    width: 205,
    backgroundColor: COLORS.lichen,
  },
  micCircle: {
    width: 88,
    height: 88,
    borderRadius: 44,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  status: {
    marginTop: 25,
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 26,
    color: COLORS.deepForest,
  },
  hint: {
    marginTop: 7,
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    lineHeight: 17,
    color: COLORS.mutedText,
    textAlign: 'center',
    maxWidth: 290,
  },
  suggestions: {
    gap: 9,
    marginBottom: 17,
  },
  suggestion: {
    minHeight: 48,
    paddingHorizontal: 15,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    backgroundColor: COLORS.surface,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  suggestionText: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.text,
  },
  button: {
    height: 54,
    borderRadius: 27,
    backgroundColor: COLORS.forest,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 9,
  },
  buttonListening: {
    backgroundColor: COLORS.wood,
  },
  buttonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
});
