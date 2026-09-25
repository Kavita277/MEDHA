import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  Platform,
  Pressable,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

import { RADIUS, SHADOW } from '../constants/theme';

export default function VoiceScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    mood?: string;
    moodComparison?: string;
    topic?: string;
    adaptiveQuestion?: string;
    adaptiveAnswer?: string;
  }>();

  const [recording, setRecording] = useState(false);
  const [seconds, setSeconds] = useState(0);

  // 5 Staggered smooth breathing animated scale values
  const pulse1 = useRef(new Animated.Value(1)).current;
  const pulse2 = useRef(new Animated.Value(1)).current;
  const pulse3 = useRef(new Animated.Value(1)).current;
  const pulse4 = useRef(new Animated.Value(1)).current;
  const pulse5 = useRef(new Animated.Value(1)).current;

  // Continuous organic breathing wave across all 5 concentric layers
  useEffect(() => {
    const timeoutIds: ReturnType<typeof setTimeout>[] = [];
    const loops: Animated.CompositeAnimation[] = [];

    const createBreath = (
      val: Animated.Value,
      toScale: number,
      halfDuration: number,
    ) => {
      return Animated.loop(
        Animated.sequence([
          Animated.timing(val, {
            toValue: toScale,
            duration: halfDuration,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(val, {
            toValue: 1,
            duration: halfDuration,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ]),
      );
    };

    if (recording) {
      // 5 staggered breathing layers creating a smooth outward ripple wave
      const configs = [
        { anim: pulse1, toScale: 1.05, halfDuration: 1100, delay: 0 },   // ~2200ms
        { anim: pulse2, toScale: 1.07, halfDuration: 1250, delay: 180 }, // ~2500ms
        { anim: pulse3, toScale: 1.09, halfDuration: 1400, delay: 360 }, // ~2800ms
        { anim: pulse4, toScale: 1.11, halfDuration: 1550, delay: 540 }, // ~3100ms
        { anim: pulse5, toScale: 1.13, halfDuration: 1700, delay: 720 }, // ~3400ms
      ];

      configs.forEach(({ anim, toScale, halfDuration, delay }) => {
        const loop = createBreath(anim, toScale, halfDuration);
        loops.push(loop);
        if (delay === 0) {
          loop.start();
        } else {
          const id = setTimeout(() => {
            loop.start();
          }, delay);
          timeoutIds.push(id);
        }
      });
    } else {
      // Gracefully ease back to resting scale when recording stops
      Animated.parallel([
        Animated.timing(pulse1, { toValue: 1, duration: 600, easing: Easing.out(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse2, { toValue: 1, duration: 600, easing: Easing.out(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse3, { toValue: 1, duration: 600, easing: Easing.out(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse4, { toValue: 1, duration: 600, easing: Easing.out(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse5, { toValue: 1, duration: 600, easing: Easing.out(Easing.ease), useNativeDriver: true }),
      ]).start();
    }

    return () => {
      timeoutIds.forEach(clearTimeout);
      loops.forEach((l) => l.stop());
    };
  }, [recording, pulse1, pulse2, pulse3, pulse4, pulse5]);

  // Continuous live recording timer (MM:SS / 02:00)
  useEffect(() => {
    if (!recording) {
      setSeconds(0);
      return;
    }

    const interval = setInterval(() => {
      setSeconds((prev) => {
        if (prev >= 120) {
          return 120;
        }
        return prev + 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [recording]);

  const formatTimer = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')} / 02:00`;
  };

  const handlePrimaryPress = () => {
    if (recording) {
      setRecording(false);
      router.push({
        pathname: '/chat',
        params: {
          fromVoice: 'true',
          mood: params.mood ?? '',
          topic: params.topic ?? '',
          adaptiveAnswer: params.adaptiveAnswer ?? '',
        },
      });
    } else {
      setRecording(true);
    }
  };

  const eyebrowText = params.topic
    ? `VOICE CHECK-IN · ${params.topic.toUpperCase()}`
    : 'VOICE CHECK-IN';

  return (
    <View style={styles.container}>
      {/* ATMOSPHERIC DEEP TWILIGHT GRADIENT */}
      <LinearGradient
        colors={['#080C14', '#101625', '#1A2135', '#0A0E18']}
        locations={[0, 0.35, 0.75, 1]}
        style={StyleSheet.absoluteFill}
      />

      <SafeAreaView style={styles.safe}>
        <View style={styles.content}>
          {/* TOP BAR: BACK & HOME CONTROLS */}
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
              <Ionicons
                name="arrow-back"
                size={20}
                color="rgba(255, 255, 255, 0.9)"
              />
            </Pressable>

            <Pressable
              onPress={() => router.replace('/home')}
              style={({ pressed }) => [
                styles.iconButton,
                pressed && styles.pressed,
              ]}
              hitSlop={12}
              accessibilityRole="button"
              accessibilityLabel="Go to home"
            >
              <Ionicons
                name="home-outline"
                size={18}
                color="rgba(255, 255, 255, 0.9)"
              />
            </Pressable>
          </View>

          {/* HEADER */}
          <View style={styles.header}>
            <Text style={styles.eyebrow}>{eyebrowText}</Text>
            <Text style={styles.title}>I’m listening.</Text>
            <Text style={styles.subtitle}>
              {params.adaptiveAnswer
                ? `You noted: "${params.adaptiveAnswer}". Speak freely about what is on your mind.`
                : 'Speak freely about how you’re feeling today.'}
            </Text>
          </View>

          {/* CENTER ATMOSPHERIC FOCAL ORB (5 CONTINUOUS BREATHING TRANSLUCENT PORCELAIN/CREAM LAYERS) */}
          <View style={styles.centerSection}>
            <View style={styles.orbWrapper}>
              {/* Layer 5: Largest / Outermost / Faintest (~0.045) */}
              <Animated.View
                style={[
                  styles.layer5,
                  recording && styles.layer5Active,
                  { transform: [{ scale: pulse5 }] },
                ]}
              />

              {/* Layer 4: Large / Soft (~0.075) */}
              <Animated.View
                style={[
                  styles.layer4,
                  recording && styles.layer4Active,
                  { transform: [{ scale: pulse4 }] },
                ]}
              />

              {/* Layer 3: Medium (~0.11) */}
              <Animated.View
                style={[
                  styles.layer3,
                  recording && styles.layer3Active,
                  { transform: [{ scale: pulse3 }] },
                ]}
              />

              {/* Layer 2: Smaller (~0.14) */}
              <Animated.View
                style={[
                  styles.layer2,
                  recording && styles.layer2Active,
                  { transform: [{ scale: pulse2 }] },
                ]}
              />

              {/* Layer 1: Core closest to microphone (~0.18 porcelain over twilight capsule) */}
              <Animated.View
                style={[
                  styles.layer1,
                  recording && styles.layer1Active,
                  { transform: [{ scale: pulse1 }] },
                ]}
              >
                <Ionicons
                  name={recording ? 'mic' : 'mic-outline'}
                  size={38}
                  color={recording ? '#FAF9F6' : 'rgba(255, 255, 255, 0.92)'}
                />
              </Animated.View>
            </View>

            {/* LIVE CONTINUOUS TIMER & GENTLE STATUS */}
            <Text style={styles.timer}>
              {formatTimer(seconds)}
            </Text>

            <Text style={styles.status}>
              {recording ? 'Listening gently...' : 'Tap when you’re ready'}
            </Text>

            <Text style={styles.hint}>
              You can stop whenever you want.
            </Text>
          </View>

          {/* BOTTOM ACTIONS */}
          <View style={styles.bottomSection}>
            <Pressable
              onPress={handlePrimaryPress}
              style={({ pressed }) => [
                styles.primaryButton,
                recording && styles.primaryButtonActive,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel={recording ? 'Finish and talk with MEDHA' : 'Tap to speak'}
            >
              <Ionicons
                name={recording ? 'stop' : 'mic'}
                size={20}
                color={recording ? '#181E2C' : '#FFFFFF'}
              />
              <Text
                style={[
                  styles.primaryButtonText,
                  recording && styles.primaryButtonTextActive,
                ]}
              >
                {recording ? 'Finish & talk with MEDHA' : 'Tap to speak'}
              </Text>
            </Pressable>

            {!recording && (
              <Pressable
                onPress={() => router.push('/chat')}
                style={({ pressed }) => [
                  styles.skipButton,
                  pressed && styles.pressed,
                ]}
                hitSlop={12}
                accessibilityRole="button"
                accessibilityLabel="Skip voice and continue to Talk with MEDHA"
              >
                <Text style={styles.skipButtonText}>
                  Skip voice · continue to Talk with MEDHA
                </Text>
              </Pressable>
            )}
          </View>
        </View>
      </SafeAreaView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080C14',
  },
  safe: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 22,
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) + 12 : 20,
    paddingBottom: 28,
    justifyContent: 'space-between',
  },

  /* TOP BAR */
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  iconButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },

  /* HEADER */
  header: {
    marginTop: 6,
    marginBottom: 10,
  },
  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.5,
    color: '#FFA07A',
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 28,
    lineHeight: 34,
    color: '#FFFFFF',
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 20,
    color: 'rgba(255, 255, 255, 0.72)',
    marginTop: 4,
  },

  /* CENTER ATMOSPHERIC FOCAL ORB (5 CONTINUOUS BREATHING TRANSLUCENT PORCELAIN LAYERS - NO OUTLINES) */
  centerSection: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 6,
  },
  orbWrapper: {
    width: 280,
    height: 280,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },

  /* Layer 5: Outermost / Faintest (280px) */
  layer5: {
    position: 'absolute',
    width: 280,
    height: 280,
    borderRadius: 140,
    backgroundColor: 'rgba(250, 249, 246, 0.025)',
  },
  layer5Active: {
    backgroundColor: 'rgba(250, 249, 246, 0.045)',
  },

  /* Layer 4: Large / Soft (236px) */
  layer4: {
    position: 'absolute',
    width: 236,
    height: 236,
    borderRadius: 118,
    backgroundColor: 'rgba(250, 249, 246, 0.04)',
  },
  layer4Active: {
    backgroundColor: 'rgba(250, 249, 246, 0.075)',
  },

  /* Layer 3: Medium (194px) */
  layer3: {
    position: 'absolute',
    width: 194,
    height: 194,
    borderRadius: 97,
    backgroundColor: 'rgba(250, 249, 246, 0.06)',
  },
  layer3Active: {
    backgroundColor: 'rgba(250, 249, 246, 0.11)',
  },

  /* Layer 2: Smaller (152px) */
  layer2: {
    position: 'absolute',
    width: 152,
    height: 152,
    borderRadius: 76,
    backgroundColor: 'rgba(250, 249, 246, 0.08)',
  },
  layer2Active: {
    backgroundColor: 'rgba(250, 249, 246, 0.14)',
  },

  /* Layer 1: Core closest to microphone (112px) */
  layer1: {
    width: 112,
    height: 112,
    borderRadius: 56,
    backgroundColor: 'rgba(26, 33, 53, 0.88)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },
  layer1Active: {
    backgroundColor: 'rgba(24, 30, 48, 0.96)',
  },

  /* STATUS & TYPOGRAPHY */
  timer: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    letterSpacing: 1.2,
    color: 'rgba(255, 255, 255, 0.55)',
    marginTop: 18,
  },
  status: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 22,
    color: '#FFFFFF',
    marginTop: 6,
  },
  hint: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.6)',
    marginTop: 4,
  },

  /* BOTTOM ACTIONS */
  bottomSection: {
    width: '100%',
    paddingBottom: 4,
  },
  primaryButton: {
    height: 54,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.14)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.22)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    ...SHADOW.subtle,
  },
  primaryButtonActive: {
    backgroundColor: '#FAF9F6',
    borderWidth: 0,
  },
  primaryButtonText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: '#FFFFFF',
  },
  primaryButtonTextActive: {
    color: '#181E2C',
  },
  skipButton: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 14,
    marginTop: 4,
  },
  skipButtonText: {
    fontFamily: 'Nunito-Medium',
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.58)',
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.88,
  },
});
