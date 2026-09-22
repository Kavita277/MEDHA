import React, { useEffect, useRef } from 'react';
import { Animated, Image, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';

import { COLORS } from '../constants/colors';

const MEDHA_LOGO = require('../../assets/images/medha-logo.png');

export default function LoadingScreen() {
  const opacity = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(0.88)).current;
  const ring = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const intro = Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: 650,
        useNativeDriver: true,
      }),
      Animated.spring(scale, {
        toValue: 1,
        damping: 14,
        stiffness: 100,
        mass: 0.8,
        useNativeDriver: true,
      }),
    ]);

    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(ring, {
          toValue: 1,
          duration: 1400,
          useNativeDriver: true,
        }),
        Animated.timing(ring, {
          toValue: 0,
          duration: 1400,
          useNativeDriver: true,
        }),
      ])
    );

    intro.start();
    pulse.start();

    const timer = setTimeout(() => {
      router.replace('/home');
    }, 2400);

    return () => {
      pulse.stop();
      clearTimeout(timer);
    };
  }, [opacity, ring, scale]);

  const ringScale = ring.interpolate({
    inputRange: [0, 1],
    outputRange: [0.9, 1.15],
  });

  const ringOpacity = ring.interpolate({
    inputRange: [0, 1],
    outputRange: [0.35, 0],
  });

  return (
    <View style={styles.container}>
      <Animated.View
        style={[
          styles.ring,
          {
            opacity: ringOpacity,
            transform: [{ scale: ringScale }],
          },
        ]}
      />

      <Animated.View
        style={[
          styles.content,
          {
            opacity,
            transform: [{ scale }],
          },
        ]}
      >
        <Image source={MEDHA_LOGO} style={styles.logo} resizeMode="contain" />
        <Text style={styles.message}>Preparing your space...</Text>
        <View style={styles.loader}>
          <View style={styles.loaderDot} />
          <View style={[styles.loaderDot, styles.loaderDotMiddle]} />
          <View style={styles.loaderDot} />
        </View>
      </Animated.View>

      <View style={styles.bottom}>
        <Text style={styles.bottomText}>A calmer moment is waiting.</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    alignItems: 'center',
  },
  logo: {
    width: 170,
    height: 170,
    borderRadius: 24,
  },
  message: {
    marginTop: 22,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.mutedText,
  },
  loader: {
    marginTop: 24,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  loaderDot: {
    width: 5,
    height: 5,
    borderRadius: 3,
    backgroundColor: COLORS.lichen,
  },
  loaderDotMiddle: {
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: COLORS.forest,
  },
  ring: {
    position: 'absolute',
    width: 245,
    height: 245,
    borderRadius: 123,
    borderWidth: 1,
    borderColor: COLORS.lichen,
  },
  bottom: {
    position: 'absolute',
    bottom: 45,
  },
  bottomText: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 16,
    color: COLORS.moss,
  },
});
