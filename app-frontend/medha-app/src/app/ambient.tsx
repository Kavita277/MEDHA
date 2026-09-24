import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Circle, Defs, Ellipse, RadialGradient, Stop } from 'react-native-svg';
import { RADIUS, SHADOW } from '../constants/theme';

const sounds = [
  { name: 'Forest', icon: 'leaf-outline' as const },
  { name: 'Rain', icon: 'rainy-outline' as const },
  { name: 'Ocean', icon: 'water-outline' as const },
  { name: 'Wind', icon: 'cloud-outline' as const },
  { name: 'Fireplace', icon: 'flame-outline' as const },
  { name: 'Silence', icon: 'moon-outline' as const },
];

export default function AmbientScreen() {
  const router = useRouter();
  const [selected, setSelected] = useState('Forest');
  const [isPlaying, setIsPlaying] = useState(false);
  const [phase, setPhase] = useState<'Breathe in' | 'Breathe out' | 'Ready'>('Ready');
  const [secondsLeft, setSecondsLeft] = useState(4);

  // Animation values for glowing blossom and pulse
  const scale = useRef(new Animated.Value(0.88)).current;
  const glowOpacity = useRef(new Animated.Value(0.45)).current;

  useEffect(() => {
    if (!isPlaying) {
      scale.stopAnimation();
      glowOpacity.stopAnimation();
      Animated.parallel([
        Animated.timing(scale, {
          toValue: 0.88,
          duration: 500,
          easing: Easing.out(Easing.ease),
          useNativeDriver: true,
        }),
        Animated.timing(glowOpacity, {
          toValue: 0.45,
          duration: 500,
          easing: Easing.out(Easing.ease),
          useNativeDriver: true,
        }),
      ]).start();
      setPhase('Ready');
      setSecondsLeft(4);
      return;
    }

    let isMounted = true;
    let currentPhase: 'Breathe in' | 'Breathe out' = 'Breathe in';
    setPhase('Breathe in');
    setSecondsLeft(4);

    let sec = 4;
    const interval = setInterval(() => {
      if (!isMounted) return;
      sec -= 1;
      if (sec <= 0) {
        currentPhase = currentPhase === 'Breathe in' ? 'Breathe out' : 'Breathe in';
        setPhase(currentPhase);
        sec = 4;
      }
      setSecondsLeft(sec);
    }, 1000);

    const runAnimationCycle = () => {
      if (!isMounted) return;

      // Inhale: 4 seconds
      Animated.parallel([
        Animated.timing(scale, {
          toValue: 1.16,
          duration: 4000,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(glowOpacity, {
          toValue: 0.88,
          duration: 4000,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]).start(({ finished }) => {
        if (!finished || !isMounted) return;

        // Exhale: 4 seconds
        Animated.parallel([
          Animated.timing(scale, {
            toValue: 0.88,
            duration: 4000,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
          Animated.timing(glowOpacity, {
            toValue: 0.45,
            duration: 4000,
            easing: Easing.inOut(Easing.sin),
            useNativeDriver: true,
          }),
        ]).start(({ finished: exhaleFinished }) => {
          if (exhaleFinished && isMounted) {
            runAnimationCycle();
          }
        });
      });
    };

    runAnimationCycle();

    return () => {
      isMounted = false;
      clearInterval(interval);
      scale.stopAnimation();
      glowOpacity.stopAnimation();
    };
  }, [isPlaying]);

  const handleReset = () => {
    setIsPlaying(false);
    setTimeout(() => {
      setIsPlaying(true);
    }, 150);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#080C14" />
      <LinearGradient
        colors={['#080C14', '#101625', '#1A2135', '#0A0E18']}
        locations={[0, 0.35, 0.75, 1]}
        style={StyleSheet.absoluteFill}
      />

      <SafeAreaView style={styles.safe}>
        <View style={styles.content}>
          {/* TOP BAR: MINIMAL BACK & ATMOSPHERE BADGE */}
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
              <Ionicons name="close" size={20} color="rgba(255, 255, 255, 0.85)" />
            </Pressable>

            <View style={styles.audioBadge}>
              <Ionicons
                name={isPlaying && selected !== 'Silence' ? 'musical-notes' : 'musical-notes-outline'}
                size={13}
                color={isPlaying && selected !== 'Silence' ? '#FFA4B0' : 'rgba(255, 255, 255, 0.45)'}
              />
              <Text style={styles.audioBadgeText}>
                {selected}
              </Text>
            </View>
          </View>

          {/* CENTER: BOTANICAL LOTUS FLOWER VISUAL & BREATHING HIERARCHY */}
          <View style={styles.centerSection}>
            <Pressable
              onPress={() => setIsPlaying((p) => !p)}
              style={styles.flowerTouchable}
              accessibilityRole="button"
              accessibilityLabel={isPlaying ? 'Pause breathing' : 'Start breathing'}
            >
              <Animated.View
                style={[
                  styles.flowerWrapper,
                  {
                    transform: [{ scale }],
                  },
                ]}
              >
                {/* Soft ambient aura */}
                <Animated.View
                  style={[
                    styles.ambientAura,
                    {
                      opacity: glowOpacity,
                    },
                  ]}
                />

                {/* Botanical Blossom SVG with Dusk Pink/Lilac/Cream gradients */}
                <Svg width={250} height={250} viewBox="0 0 240 240">
                  <Defs>
                    <RadialGradient id="coreGlowAmbient" cx="50%" cy="50%" rx="50%" ry="50%">
                      <Stop offset="0%" stopColor="#FFF1D6" stopOpacity="0.95" />
                      <Stop offset="40%" stopColor="#FFA4B0" stopOpacity="0.75" />
                      <Stop offset="80%" stopColor="#C487F5" stopOpacity="0.3" />
                      <Stop offset="100%" stopColor="#1A2135" stopOpacity="0" />
                    </RadialGradient>
                    <RadialGradient id="petalGlowAmbient" cx="50%" cy="20%" rx="60%" ry="60%">
                      <Stop offset="0%" stopColor="#FFE0E6" stopOpacity="0.88" />
                      <Stop offset="70%" stopColor="#FF9AA8" stopOpacity="0.48" />
                      <Stop offset="100%" stopColor="#9C77E8" stopOpacity="0.12" />
                    </RadialGradient>
                  </Defs>

                  {/* Soft background glow */}
                  <Circle cx="120" cy="120" r="96" fill="url(#coreGlowAmbient)" />

                  {/* Radiating petals */}
                  <Ellipse cx="120" cy="55" rx="26" ry="50" fill="url(#petalGlowAmbient)" opacity={0.78} />
                  <Ellipse cx="120" cy="185" rx="26" ry="50" fill="url(#petalGlowAmbient)" opacity={0.78} />
                  <Ellipse cx="55" cy="120" rx="50" ry="26" fill="url(#petalGlowAmbient)" opacity={0.78} />
                  <Ellipse cx="185" cy="120" rx="50" ry="26" fill="url(#petalGlowAmbient)" opacity={0.78} />

                  {/* Diagonal petals */}
                  <Ellipse
                    cx="74"
                    cy="74"
                    rx="28"
                    ry="48"
                    transform="rotate(-45 74 74)"
                    fill="url(#petalGlowAmbient)"
                    opacity={0.82}
                  />
                  <Ellipse
                    cx="166"
                    cy="74"
                    rx="28"
                    ry="48"
                    transform="rotate(45 166 74)"
                    fill="url(#petalGlowAmbient)"
                    opacity={0.82}
                  />
                  <Ellipse
                    cx="74"
                    cy="166"
                    rx="28"
                    ry="48"
                    transform="rotate(45 74 166)"
                    fill="url(#petalGlowAmbient)"
                    opacity={0.82}
                  />
                  <Ellipse
                    cx="166"
                    cy="166"
                    rx="28"
                    ry="48"
                    transform="rotate(-45 166 166)"
                    fill="url(#petalGlowAmbient)"
                    opacity={0.82}
                  />

                  {/* Inner blossom core */}
                  <Circle cx="120" cy="120" r="38" fill="#FFC9D2" opacity={0.68} />
                  <Circle cx="120" cy="120" r="22" fill="#FFF2CE" opacity={0.92} />
                  <Circle cx="120" cy="120" r="10" fill="#FFFFFF" opacity={0.98} />
                </Svg>
              </Animated.View>
            </Pressable>

            {/* BREATHING INSTRUCTION & COUNTDOWN */}
            <View style={styles.textContainer}>
              <Text style={styles.phaseTitle}>
                {phase === 'Ready' ? 'Breathe in' : phase}
              </Text>
              <Text style={styles.durationSubtitle}>
                {isPlaying ? `${secondsLeft} seconds` : '4 seconds'}
              </Text>
            </View>
          </View>

          {/* BOTTOM CONTROLS & ATMOSPHERE SELECTION */}
          <View style={styles.bottomSection}>
            {/* ATMOSPHERE SELECTION CHIPS */}
            <View style={styles.soundSelectorWrapper}>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.soundChipsContainer}
              >
                {sounds.map((sound) => {
                  const active = selected === sound.name;
                  return (
                    <Pressable
                      key={sound.name}
                      onPress={() => setSelected(sound.name)}
                      style={({ pressed }) => [
                        styles.soundChip,
                        active && styles.soundChipActive,
                        pressed && styles.pressed,
                      ]}
                      accessibilityRole="button"
                      accessibilityLabel={`${sound.name} atmosphere`}
                    >
                      <Ionicons
                        name={sound.icon}
                        size={15}
                        color={active ? '#181E2C' : 'rgba(255, 255, 255, 0.72)'}
                      />
                      <Text
                        style={[
                          styles.soundChipText,
                          active && styles.soundChipTextActive,
                        ]}
                      >
                        {sound.name}
                      </Text>
                    </Pressable>
                  );
                })}
              </ScrollView>
            </View>

            {/* PLAY / PAUSE & AUX CONTROLS */}
            <View style={styles.controlsRow}>
              <Pressable
                onPress={handleReset}
                style={({ pressed }) => [
                  styles.auxButton,
                  pressed && styles.pressed,
                ]}
                hitSlop={12}
                accessibilityRole="button"
                accessibilityLabel="Reset breathing cycle"
              >
                <Ionicons name="refresh" size={18} color="rgba(255, 255, 255, 0.7)" />
              </Pressable>

              <Pressable
                onPress={() => setIsPlaying((p) => !p)}
                style={({ pressed }) => [
                  styles.mainPlayButton,
                  isPlaying && styles.mainPlayButtonActive,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel={isPlaying ? 'Pause exercise' : 'Begin exercise'}
              >
                <Ionicons
                  name={isPlaying ? 'pause' : 'play'}
                  size={26}
                  color={isPlaying ? '#181E2C' : '#FFFFFF'}
                  style={!isPlaying ? { marginLeft: 3 } : undefined}
                />
              </Pressable>

              <Pressable
                onPress={() => router.back()}
                style={({ pressed }) => [
                  styles.auxButton,
                  pressed && styles.pressed,
                ]}
                hitSlop={12}
                accessibilityRole="button"
                accessibilityLabel="Done"
              >
                <Ionicons name="checkmark" size={18} color="rgba(255, 255, 255, 0.7)" />
              </Pressable>
            </View>
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
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) + 12 : 16,
    paddingBottom: 24,
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
  audioBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  audioBadgeText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.75)',
  },

  /* CENTER */
  centerSection: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 'auto',
  },
  flowerTouchable: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  flowerWrapper: {
    width: 260,
    height: 260,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    marginBottom: 28,
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

  /* BOTTOM SECTION */
  bottomSection: {
    width: '100%',
    gap: 20,
    paddingBottom: 4,
  },
  soundSelectorWrapper: {
    width: '100%',
  },
  soundChipsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 2,
    paddingVertical: 4,
  },
  soundChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  soundChipActive: {
    backgroundColor: '#FAF9F6',
    borderColor: '#FAF9F6',
  },
  soundChipText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.72)',
  },
  soundChipTextActive: {
    color: '#181E2C',
  },

  /* CONTROLS ROW */
  controlsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 24,
  },
  auxButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  mainPlayButton: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: 'rgba(255, 255, 255, 0.16)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },
  mainPlayButtonActive: {
    backgroundColor: '#FAF9F6',
    borderColor: '#FAF9F6',
  },

  pressed: {
    transform: [{ scale: 0.95 }],
    opacity: 0.88,
  },
});