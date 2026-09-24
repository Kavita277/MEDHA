import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';

import { MedhaScreen } from '../components/medha-screen';
import { MedhaButton } from '../components/medha-button';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

const AMBIENT = require('../../assets/medha-grounding-ambient.wav');

export default function GroundingScreen() {
  const router = useRouter();

  // Configure expo-audio without passing invalid options to hook
  const player = useAudioPlayer(AMBIENT);
  const status = useAudioPlayerStatus(player);

  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState('Ready');
  const scale = useRef(new Animated.Value(0.75)).current;

  // Set loop on player instance correctly
  useEffect(() => {
    if (player) {
      player.loop = true;
    }
  }, [player]);

  useEffect(() => {
    if (!running) {
      scale.stopAnimation();
      scale.setValue(0.75);
      setPhase('Ready');
      if (status.playing) {
        player.pause();
      }
      return;
    }

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
      withBackground={true}
    >
      <View style={styles.center}>
        {/* CONCENTRIC ANIMATED BREATHING CIRCLES */}
        <Animated.View style={[styles.outerField, { transform: [{ scale }] }]}>
          <View style={styles.middleField}>
            <View style={styles.core}>
              <Text style={styles.phase}>{phase}</Text>
              {running ? (
                <View style={styles.countBadge}>
                  <Text style={styles.count}>4  ·  2  ·  6</Text>
                </View>
              ) : (
                <View style={styles.idleBadge}>
                  <Ionicons name="leaf" size={16} color={COLORS.sage} />
                </View>
              )}
            </View>
          </View>
        </Animated.View>

        <Text style={styles.instruction}>
          {running
            ? 'Let your breathing become unhurried and soft.'
            : 'When you’re ready, tap begin to settle your space.'}
        </Text>
      </View>

      {/* CONTROLS */}
      <View style={styles.controls}>
        <View style={styles.buttonWrapper}>
          <MedhaButton
            title={running ? 'Pause' : 'Begin'}
            variant={running ? 'primary' : 'coral'}
            size="lg"
            icon={running ? 'pause' : 'leaf'}
            iconPosition="left"
            onPress={() => setRunning((value) => !value)}
          />
        </View>

        <Pressable
          onPress={() => setRunning(false)}
          style={({ pressed }) => [
            styles.musicButton,
            pressed && styles.pressed,
          ]}
          accessibilityRole="button"
          accessibilityLabel="Music plays while grounding is active"
        >
          <Ionicons
            name={status.playing ? 'musical-notes' : 'musical-notes-outline'}
            size={20}
            color={status.playing ? COLORS.coralDark : COLORS.navyMuted}
          />
        </Pressable>
      </View>

      {/* COMPLETION / RETURN */}
      <Pressable
        onPress={() => router.push('/home')}
        style={({ pressed }) => [styles.done, pressed && styles.pressed]}
        accessibilityRole="button"
        accessibilityLabel="I'm feeling ready, return to home"
      >
        <Text style={styles.doneText}>I’m feeling ready →</Text>
      </Pressable>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
  },

  outerField: {
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: 'rgba(211, 236, 214, 0.45)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(127, 168, 138, 0.35)',
  },

  middleField: {
    width: 220,
    height: 220,
    borderRadius: 110,
    backgroundColor: 'rgba(191, 227, 245, 0.55)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.85)',
  },

  core: {
    width: 156,
    height: 156,
    borderRadius: 78,
    backgroundColor: COLORS.white,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.95)',
    ...SHADOW.card,
  },

  phase: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 24,
    color: COLORS.navy,
    textAlign: 'center',
  },

  countBadge: {
    marginTop: 6,
    backgroundColor: COLORS.creamSecondary,
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: RADIUS.pill,
  },

  count: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    color: COLORS.coralDark,
    letterSpacing: 1.5,
  },

  idleBadge: {
    marginTop: 8,
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: COLORS.greenSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },

  instruction: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    lineHeight: 19,
    color: COLORS.navyMuted,
    marginTop: 28,
    textAlign: 'center',
    maxWidth: 280,
  },

  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginTop: 10,
  },

  buttonWrapper: {
    flex: 1,
  },

  musicButton: {
    width: 54,
    height: 54,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.95)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.card,
  },

  done: {
    alignItems: 'center',
    paddingVertical: 18,
    marginTop: 4,
  },

  doneText: {
    fontFamily: 'Fredoka-Medium',
    color: COLORS.navyMuted,
    fontSize: 13,
  },

  pressed: {
    transform: [{ scale: 0.96 }],
    opacity: 0.88,
  },
});
