import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Circle, Defs, Ellipse, RadialGradient, Stop } from 'react-native-svg';
import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';

import { COLORS } from '../constants/colors';
import { RADIUS } from '../constants/theme';

const AMBIENT = require('../../assets/medha-grounding-ambient.wav');

export default function GroundingScreen() {
  const router = useRouter();

  // Configure expo-audio
  const player = useAudioPlayer(AMBIENT);
  const status = useAudioPlayerStatus(player);

  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState('Breathe in');
  const [durationSecs, setDurationSecs] = useState('4 seconds');

  // Animation values for glowing lotus and pulse
  const scale = useRef(new Animated.Value(0.85)).current;
  const glowOpacity = useRef(new Animated.Value(0.6)).current;

  // Set looping behavior on player
  useEffect(() => {
    if (player) {
      player.loop = true;
    }
  }, [player]);

  useEffect(() => {
    if (!running) {
      scale.stopAnimation();
      glowOpacity.stopAnimation();
      scale.setValue(0.85);
      glowOpacity.setValue(0.5);
      setPhase('Ready');
      setDurationSecs('Tap play to begin');
      if (status.playing) {
        player.pause();
      }
      return;
    }

    player.play();

    let isMounted = true;

    const cycle = () => {
      if (!isMounted) return;

      // Inhale: 4 seconds
      setPhase('Breathe in');
      setDurationSecs('4 seconds');

      Animated.parallel([
        Animated.timing(scale, {
          toValue: 1.15,
          duration: 4000,
          useNativeDriver: true,
        }),
        Animated.timing(glowOpacity, {
          toValue: 0.95,
          duration: 4000,
          useNativeDriver: true,
        }),
      ]).start(({ finished }) => {
        if (!finished || !isMounted) return;

        // Hold: 2 seconds
        setPhase('Hold');
        setDurationSecs('2 seconds');

        setTimeout(() => {
          if (!isMounted) return;

          // Exhale: 6 seconds
          setPhase('Breathe out');
          setDurationSecs('6 seconds');

          Animated.parallel([
            Animated.timing(scale, {
              toValue: 0.85,
              duration: 6000,
              useNativeDriver: true,
            }),
            Animated.timing(glowOpacity, {
              toValue: 0.45,
              duration: 6000,
              useNativeDriver: true,
            }),
          ]).start(({ finished: exhaleFinished }) => {
            if (exhaleFinished && isMounted) {
              cycle();
            }
          });
        }, 2000);
      });
    };

    cycle();

    return () => {
      isMounted = false;
      scale.stopAnimation();
      glowOpacity.stopAnimation();
    };
  }, [running]);

  useEffect(() => {
    return () => {
      player.pause();
    };
  }, [player]);

  return (
    <LinearGradient
      colors={['#0A0D14', '#121726', '#1A2135', '#0E1320']}
      locations={[0, 0.35, 0.75, 1]}
      style={styles.gradientContainer}
    >
      <SafeAreaView style={styles.safeArea}>
        {/* TOP BAR WITH CLOSE AND SOUND INDICATOR */}
        <View style={styles.topBar}>
          <Pressable
            onPress={() => router.back()}
            style={({ pressed }) => [
              styles.iconButton,
              pressed && styles.pressed,
            ]}
            hitSlop={12}
            accessibilityRole="button"
            accessibilityLabel="Close grounding"
          >
            <Ionicons name="close" size={22} color="rgba(255, 255, 255, 0.85)" />
          </Pressable>

          <View style={styles.audioBadge}>
            <Ionicons
              name={status.playing ? 'musical-notes' : 'musical-notes-outline'}
              size={13}
              color={status.playing ? COLORS.lotusGlow : 'rgba(255, 255, 255, 0.4)'}
            />
            <Text style={styles.audioBadgeText}>
              {status.playing ? 'Ambient sound on' : 'Ambient sound paused'}
            </Text>
          </View>
        </View>

        {/* CENTER BREATHING LOTUS & TYPOGRAPHY */}
        <View style={styles.centerContainer}>
          {/* GLOWING LOTUS GRAPHIC WITH ANIMATED SCALE */}
          <Animated.View
            style={[
              styles.lotusWrapper,
              {
                transform: [{ scale }],
              },
            ]}
          >
            {/* Ambient Radial Aura */}
            <Animated.View
              style={[
                styles.ambientAura,
                {
                  opacity: glowOpacity,
                },
              ]}
            />

            {/* Botanical Ethereal Lotus SVG */}
            <Svg width={240} height={240} viewBox="0 0 240 240">
              <Defs>
                <RadialGradient id="coreGlow" cx="50%" cy="50%" rx="50%" ry="50%">
                  <Stop offset="0%" stopColor="#FFF1D6" stopOpacity="0.95" />
                  <Stop offset="40%" stopColor="#FFA4B0" stopOpacity="0.7" />
                  <Stop offset="80%" stopColor="#C487F5" stopOpacity="0.25" />
                  <Stop offset="100%" stopColor="#1A2135" stopOpacity="0" />
                </RadialGradient>
                <RadialGradient id="petalGlow1" cx="50%" cy="20%" rx="60%" ry="60%">
                  <Stop offset="0%" stopColor="#FFE0E6" stopOpacity="0.85" />
                  <Stop offset="70%" stopColor="#FF9AA8" stopOpacity="0.45" />
                  <Stop offset="100%" stopColor="#9C77E8" stopOpacity="0.1" />
                </RadialGradient>
              </Defs>

              {/* Background soft glow circle */}
              <Circle cx="120" cy="120" r="95" fill="url(#coreGlow)" />

              {/* Outer radiating lotus petals */}
              <Ellipse cx="120" cy="55" rx="26" ry="50" fill="url(#petalGlow1)" opacity={0.75} />
              <Ellipse cx="120" cy="185" rx="26" ry="50" fill="url(#petalGlow1)" opacity={0.75} />
              <Ellipse cx="55" cy="120" rx="50" ry="26" fill="url(#petalGlow1)" opacity={0.75} />
              <Ellipse cx="185" cy="120" rx="50" ry="26" fill="url(#petalGlow1)" opacity={0.75} />

              {/* Diagonal petals */}
              <Ellipse
                cx="74"
                cy="74"
                rx="28"
                ry="48"
                transform="rotate(-45 74 74)"
                fill="url(#petalGlow1)"
                opacity={0.8}
              />
              <Ellipse
                cx="166"
                cy="74"
                rx="28"
                ry="48"
                transform="rotate(45 166 74)"
                fill="url(#petalGlow1)"
                opacity={0.8}
              />
              <Ellipse
                cx="74"
                cy="166"
                rx="28"
                ry="48"
                transform="rotate(45 74 166)"
                fill="url(#petalGlow1)"
                opacity={0.8}
              />
              <Ellipse
                cx="166"
                cy="166"
                rx="28"
                ry="48"
                transform="rotate(-45 166 166)"
                fill="url(#petalGlow1)"
                opacity={0.8}
              />

              {/* Inner delicate blossom layer */}
              <Circle cx="120" cy="120" r="38" fill="#FFC9D2" opacity={0.65} />
              <Circle cx="120" cy="120" r="22" fill="#FFF2CE" opacity={0.9} />
              <Circle cx="120" cy="120" r="10" fill="#FFFFFF" opacity={0.95} />
            </Svg>
          </Animated.View>

          {/* PHASE INSTRUCTION & DURATION */}
          <View style={styles.textContainer}>
            <Text style={styles.phaseTitle}>{phase}</Text>
            <Text style={styles.durationSubtitle}>{durationSecs}</Text>
          </View>
        </View>

        {/* BOTTOM CONTROLS BAR MATCHING REFERENCE SCREEN 15 */}
        <View style={styles.bottomControls}>
          {/* Restart / Reset */}
          <Pressable
            onPress={() => {
              setRunning(false);
              setTimeout(() => setRunning(true), 150);
            }}
            style={({ pressed }) => [
              styles.controlAuxButton,
              pressed && styles.pressed,
            ]}
            hitSlop={12}
            accessibilityRole="button"
            accessibilityLabel="Reset breathing"
          >
            <Ionicons name="refresh" size={20} color="rgba(255, 255, 255, 0.7)" />
          </Pressable>

          {/* Primary Play / Pause Pill */}
          <Pressable
            onPress={() => setRunning((prev) => !prev)}
            style={({ pressed }) => [
              styles.mainPlayButton,
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel={running ? 'Pause exercise' : 'Begin exercise'}
          >
            <Ionicons
              name={running ? 'pause' : 'play'}
              size={24}
              color="#FFFFFF"
            />
          </Pressable>

          {/* Skip / Complete to Home */}
          <Pressable
            onPress={() => router.push('/home')}
            style={({ pressed }) => [
              styles.controlAuxButton,
              pressed && styles.pressed,
            ]}
            hitSlop={12}
            accessibilityRole="button"
            accessibilityLabel="Done, return home"
          >
            <Ionicons name="arrow-forward" size={20} color="rgba(255, 255, 255, 0.7)" />
          </Pressable>
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
    paddingHorizontal: 20,
    justifyContent: 'space-between',
  },

  /* TOP BAR */
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 12,
    paddingBottom: 8,
  },
  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  audioBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
  },
  audioBadgeText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.65)',
  },

  /* CENTER */
  centerContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 'auto',
  },
  lotusWrapper: {
    width: 260,
    height: 260,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 36,
  },
  ambientAura: {
    position: 'absolute',
    width: 240,
    height: 240,
    borderRadius: 120,
    backgroundColor: 'rgba(255, 164, 176, 0.22)',
  },
  textContainer: {
    alignItems: 'center',
  },
  phaseTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 34,
    lineHeight: 40,
    color: '#FFFFFF',
    textAlign: 'center',
    letterSpacing: 0.4,
  },
  durationSubtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 16,
    lineHeight: 22,
    color: 'rgba(255, 255, 255, 0.6)',
    marginTop: 8,
    textAlign: 'center',
  },

  /* CONTROLS */
  bottomControls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 28,
    paddingBottom: 28,
  },
  controlAuxButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mainPlayButton: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: 'rgba(255, 255, 255, 0.16)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  pressed: {
    transform: [{ scale: 0.93 }],
    opacity: 0.85,
  },
});
