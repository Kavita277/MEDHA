import React, { useEffect, useRef } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';

export default function OnboardingCompleteScreen() {
  const scale = useRef(new Animated.Value(0.82)).current;
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(scale, {
        toValue: 1,
        damping: 13,
        stiffness: 110,
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();
  }, [opacity, scale]);

  return (
    <View style={styles.container}>
      <Animated.View
        style={[
          styles.content,
          {
            opacity,
            transform: [{ scale }],
          },
        ]}
      >
        <View style={styles.logoMark}>
          <Ionicons name="leaf-outline" size={42} color={COLORS.deepForest} />
        </View>

        <Text style={styles.title}>You’re all set.</Text>
        <Text style={styles.subtitle}>
          Your space is ready.{'\n'}Take a deep breath — you’ve got this.
        </Text>

        <View style={styles.quote}>
          <Text style={styles.quoteText}>
            “You don’t have to have it all figured out.”
          </Text>
        </View>

        <Pressable onPress={() => router.replace('/home')} style={styles.button}>
          <Text style={styles.buttonText}>Go to Home</Text>
          <Ionicons name="arrow-forward" size={18} color={COLORS.white} />
        </Pressable>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    paddingHorizontal: 24,
    justifyContent: 'center',
  },
  content: {
    alignItems: 'center',
  },
  logoMark: {
    width: 92,
    height: 92,
    borderRadius: 46,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 30,
  },
  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 42,
    lineHeight: 45,
    color: COLORS.deepForest,
    textAlign: 'center',
  },
  subtitle: {
    marginTop: 13,
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    lineHeight: 20,
    color: COLORS.mutedText,
    textAlign: 'center',
  },
  quote: {
    marginTop: 28,
    paddingHorizontal: 22,
    paddingVertical: 17,
    borderRadius: 19,
    backgroundColor: COLORS.surfaceWarm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  quoteText: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 19,
    color: COLORS.deepForest,
    textAlign: 'center',
  },
  button: {
    width: '100%',
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.forest,
    marginTop: 30,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 10,
  },
  buttonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
});
