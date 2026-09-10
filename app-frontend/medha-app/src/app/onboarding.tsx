import { useState } from 'react';
import {
  ImageBackground,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';

import { COLORS } from '../constants/colors';

const slides = [
  {
    eyebrow: 'WELCOME',
    title: 'A safe space\nfor your mind.',
    body: 'Talk, reflect, breathe and feel better — at your own pace.',
    image:
      'https://images.unsplash.com/photo-1448375240586-882707db888b?q=85&w=1200&auto=format&fit=crop',
  },

  {
    eyebrow: 'UNDERSTANDING',
    title: 'More than\njust an app.',
    body: 'MEDHA gently brings together voice, text and everyday patterns to understand you better.',
    image:
      'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=85&w=1200&auto=format&fit=crop',
  },

  {
    eyebrow: 'TOGETHER',
    title: 'You are\nnot alone.',
    body: 'A quiet place to check in, reflect and find support whenever you need it.',
    image:
      'https://images.unsplash.com/photo-1500534623283-312aade485b7?q=85&w=1200&auto=format&fit=crop',
  },
];

export default function OnboardingScreen() {
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
      <ImageBackground
        source={{ uri: slide.image }}
        style={styles.background}
      >
        <LinearGradient
          colors={[
            'rgba(247,243,234,0.04)',
            'rgba(247,243,234,0.08)',
            'rgba(247,243,234,0.98)',
          ]}
          locations={[0, 0.46, 0.9]}
          style={StyleSheet.absoluteFill}
        />

        {/* TOP */}
        <View style={styles.top}>
          <Text style={styles.logo}>MEDHA</Text>

          <Pressable
            onPress={() => router.replace('/signup')}
            hitSlop={15}
          >
            <Text style={styles.skip}>Skip</Text>
          </Pressable>
        </View>

        {/* CONTENT */}
        <View style={styles.content}>

          <Text style={styles.eyebrow}>
            {slide.eyebrow}
          </Text>

          <Text style={styles.title}>
            {slide.title}
          </Text>

          <Text style={styles.body}>
            {slide.body}
          </Text>

          {/* BOTTOM CONTROLS */}
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
            >
              <Ionicons
                name="arrow-forward"
                size={20}
                color="#F8F4EA"
              />
            </Pressable>

          </View>

          <View style={styles.bottomLine} />
        </View>
      </ImageBackground>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },

  background: {
    flex: 1,
  },

  top: {
    paddingTop: 58,
    paddingHorizontal: 24,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  logo: {
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
    fontSize: 12,
    letterSpacing: 3.5,
  },

  skip: {
    fontFamily: 'Inter-Regular',
    color: COLORS.deepForest,
    fontSize: 12,
  },

  content: {
    position: 'absolute',
    left: 24,
    right: 24,
    bottom: 28,
  },

  eyebrow: {
    fontFamily: 'Inter-Medium',
    color: COLORS.forest,
    fontSize: 9,
    letterSpacing: 2,
    marginBottom: 13,
  },

  title: {
    fontFamily: 'CormorantGaramond-Light',
    color: COLORS.deepForest,
    fontSize: 43,
    lineHeight: 42,
    letterSpacing: -0.8,
  },

  body: {
    fontFamily: 'Inter-Regular',
    color: '#52584F',
    fontSize: 14,
    lineHeight: 21,
    marginTop: 15,
    width: '84%',
  },

  controls: {
    marginTop: 28,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  dots: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },

  dot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: '#B9B7AB',
  },

  activeDot: {
    width: 22,
    backgroundColor: COLORS.forest,
  },

  nextButton: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },

  pressed: {
    transform: [{ scale: 0.94 }],
    opacity: 0.8,
  },

  bottomLine: {
    height: 1,
    backgroundColor: '#D5D0C2',
    marginTop: 22,
  },
});