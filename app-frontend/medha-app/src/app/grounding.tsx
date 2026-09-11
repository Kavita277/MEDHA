import React, { useEffect, useRef, useState } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

const AMBIENT = require('../../assets/medha-grounding-ambient.wav');

export default function GroundingScreen() {
  const router = useRouter();
  const player = useAudioPlayer(AMBIENT);
  const status = useAudioPlayerStatus(player);
  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState('Ready');
  const scale = useRef(new Animated.Value(0.75)).current;

  useEffect(() => {
    if (!running) {
      scale.stopAnimation();
      scale.setValue(0.75);
      setPhase('Ready');
      if (status.playing) player.pause();
      return;
    }

    player.loop = true;
    player.play();

    const run = () => {
      setPhase('Breathe in');
      Animated.timing(scale, {
        toValue: 1,
        duration: 4000,
        useNativeDriver: true,
      }).start(({ finished }) => {
        if (!finished) return;
        setPhase('Hold');
        setTimeout(() => {
          if (!running) return;
          setPhase('Breathe out');
          Animated.timing(scale, {
            toValue: 0.75,
            duration: 6000,
            useNativeDriver: true,
          }).start(() => {
            if (running) run();
          });
        }, 2000);
      });
    };

    run();
    return () => scale.stopAnimation();
  }, [running]);

  useEffect(() => {
    return () => {
      player.pause();
    };
  }, [player]);

  return (
    <MedhaScreen
      eyebrow="Find your centre"
      title="Breathe with me."
      subtitle="A calmer mind is just a few deep breaths away."
      onBack={() => router.back()}
      scroll={false}
    >
      <View style={styles.center}>
        <Animated.View style={[styles.field, { transform: [{ scale }] }]}>
          <View style={styles.core}>
            <Text style={styles.phase}>{phase}</Text>
            {running && <Text style={styles.count}>4  ·  4  ·  6</Text>}
          </View>
        </Animated.View>

        <Text style={styles.instruction}>
          {running
            ? 'Let your breathing become unhurried.'
            : 'When you’re ready, begin.'}
        </Text>
      </View>

      <View style={styles.controls}>
        <Pressable
          onPress={() => setRunning((value) => !value)}
          style={styles.button}
          accessibilityRole="button"
          accessibilityLabel={running ? 'Pause breathing and music' : 'Begin breathing and play music'}
        >
          <Ionicons
            name={running ? 'pause' : 'leaf-outline'}
            size={18}
            color={COLORS.white}
          />
          <Text style={styles.buttonText}>{running ? 'Pause' : 'Begin'}</Text>
        </Pressable>

        <Pressable
          onPress={() => setRunning(false)}
          style={styles.music}
          accessibilityRole="button"
          accessibilityLabel="Music plays while grounding is active"
        >
          <Ionicons name="musical-notes-outline" size={18} color={COLORS.forest} />
        </Pressable>
      </View>

      <Pressable onPress={() => router.push('/home' as any)} style={styles.done}>
        <Text style={styles.doneText}>I’m feeling ready</Text>
      </Pressable>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  field: {
    width: 270,
    height: 270,
    borderRadius: 135,
    backgroundColor: 'rgba(170,188,180,0.28)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  core: {
    width: 165,
    height: 165,
    borderRadius: 83,
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  phase: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 27,
    color: COLORS.forest,
  },
  count: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.mutedText,
    marginTop: 7,
    letterSpacing: 1.2,
  },
  instruction: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.mutedText,
    marginTop: 28,
    textAlign: 'center',
  },
  controls: {
    flexDirection: 'row',
    gap: 10,
  },
  button: {
    flex: 1,
    height: 54,
    borderRadius: 27,
    backgroundColor: COLORS.forest,
    flexDirection: 'row',
    gap: 9,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.white,
    fontSize: 13,
  },
  music: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  done: { alignItems: 'center', paddingVertical: 17 },
  doneText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.mutedText,
    fontSize: 11,
  },
});
