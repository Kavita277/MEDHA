import React, { useState } from 'react';
import {
  ImageBackground,
  Platform,
  Pressable,
  SafeAreaView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { SHADOW } from '../constants/theme';

const slides = [
  {
    eyebrow: 'WELCOME',
    title: 'You are\nnot alone',
    body: 'A quiet place to check in, reflect, and find support whenever you need it.',
    image:
      'https://images.unsplash.com/photo-1500534623283-312aade485b7?q=85&w=1200&auto=format&fit=crop',
  },
  {
    eyebrow: 'PERSPECTIVE',
    title: 'Small steps create\nbig change',
    body: 'Talk, reflect, breathe, and feel better — at your own gentle pace.',
    image:
      'https://images.unsplash.com/photo-1448375240586-882707db888b?q=85&w=1200&auto=format&fit=crop',
  },
  {
    eyebrow: 'GROWTH',
    title: 'A brighter you,\nalways',
    body: 'MEDHA gently brings together voice, text, and everyday patterns to understand you better.',
    image:
      'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=85&w=1200&auto=format&fit=crop',
  },
];

export default function OnboardingScreen() {
  const router = useRouter();
  const [current, setCurrent] = useState(0);

  const slide = slides[current];

  function next() {
    if (current < slides.length - 1) {
      setCurrent(current + 1);
    } else {
      router.replace('/signup');
    }
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />
      <ImageBackground
        source={{ uri: slide.image }}
        style={styles.background}
        resizeMode="cover"
      >
        {/* ATMOSPHERIC CINEMATIC OVERLAY */}
        <LinearGradient
          colors={[
            'rgba(8, 12, 20, 0.35)',
            'rgba(8, 12, 20, 0.55)',
            'rgba(8, 12, 20, 0.88)',
            '#080C14',
          ]}
          locations={[0, 0.38, 0.72, 1]}
          style={StyleSheet.absoluteFill}
        />

        <SafeAreaView style={styles.safe}>
          <View style={styles.layout}>
            {/* TOP BAR: LOGO & SKIP ACTION */}
            <View style={styles.top}>
              <Text style={styles.logo}>MEDHA</Text>

              <Pressable
                onPress={() => router.replace('/signup')}
                style={({ pressed }) => [
                  styles.skipButton,
                  pressed && styles.pressed,
                ]}
                hitSlop={15}
                accessibilityRole="button"
                accessibilityLabel="Skip onboarding"
              >
                <Text style={styles.skip}>Skip</Text>
              </Pressable>
            </View>

            {/* LOWER-MIDDLE CENTERED COPY */}
            <View style={styles.content}>
              <Text style={styles.eyebrow}>{slide.eyebrow}</Text>
              <Text style={styles.title}>{slide.title}</Text>
              <Text style={styles.body}>{slide.body}</Text>
            </View>

            {/* BOTTOM CONTROLS: DOTS & CIRCULAR NEXT BUTTON */}
            <View style={styles.controls}>
              <View style={styles.dots}>
                {slides.map((_, index) => (
                  <View
                    key={index}
                    style={[
                      styles.dot,
                      index === current && styles.activeDot,
                    ]}
                  />
                ))}
              </View>

              <Pressable
                onPress={next}
                style={({ pressed }) => [
                  styles.nextButton,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel={
                  current < slides.length - 1 ? 'Next slide' : 'Get started'
                }
              >
                <Ionicons
                  name="arrow-forward"
                  size={22}
                  color="#181E2C"
                />
              </Pressable>
            </View>
          </View>
        </SafeAreaView>
      </ImageBackground>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080C14',
  },
  background: {
    flex: 1,
  },
  safe: {
    flex: 1,
  },
  layout: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: Platform.OS === 'android' ? (StatusBar.currentHeight ?? 24) + 12 : 12,
    paddingBottom: Platform.OS === 'android' ? 24 : 16,
    justifyContent: 'space-between',
  },

  /* TOP */
  top: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  logo: {
    fontFamily: 'Nunito-Bold',
    color: '#FAF9F6',
    fontSize: 13,
    letterSpacing: 3.5,
  },
  skipButton: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
  },
  skip: {
    fontFamily: 'Nunito-SemiBold',
    color: '#FAF9F6',
    fontSize: 12,
    letterSpacing: 0.5,
  },

  /* LOWER-MIDDLE CONTENT */
  content: {
    alignItems: 'center',
    paddingHorizontal: 12,
    marginTop: 'auto',
    marginBottom: 44,
  },
  eyebrow: {
    fontFamily: 'Nunito-Bold',
    color: '#FFA07A',
    fontSize: 11,
    letterSpacing: 2,
    textTransform: 'uppercase',
    marginBottom: 10,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    color: '#FFFFFF',
    fontSize: 32,
    lineHeight: 38,
    textAlign: 'center',
    letterSpacing: -0.3,
    marginBottom: 14,
  },
  body: {
    fontFamily: 'Nunito-Regular',
    color: 'rgba(255, 255, 255, 0.82)',
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    maxWidth: 320,
  },

  /* BOTTOM CONTROLS */
  controls: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingBottom: 8,
  },
  dots: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(255, 255, 255, 0.35)',
  },
  activeDot: {
    width: 22,
    backgroundColor: '#FAF9F6',
  },
  nextButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: '#FAF9F6',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },

  pressed: {
    transform: [{ scale: 0.94 }],
    opacity: 0.85,
  },
});