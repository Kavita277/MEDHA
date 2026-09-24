import React, { useEffect, useRef } from 'react';
import {
  Animated,
  Image,
  Platform,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

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
    outputRange: [0.92, 1.14],
  });

  const ringOpacity = ring.interpolate({
    inputRange: [0, 1],
    outputRange: [0.35, 0],
  });

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
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
    backgroundColor: '#FAF9F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    alignItems: 'center',
  },
  logo: {
    width: 160,
    height: 160,
  },
  message: {
    marginTop: 20,
    fontFamily: 'Nunito-SemiBold',
    fontSize: 14,
    color: '#5B6478',
  },
  loader: {
    marginTop: 18,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },
  loaderDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(24, 30, 44, 0.18)',
  },
  loaderDotMiddle: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#FF735C',
  },
  ring: {
    position: 'absolute',
    width: 230,
    height: 230,
    borderRadius: 115,
    borderWidth: 1.5,
    borderColor: '#FF735C',
  },
  bottom: {
    position: 'absolute',
    bottom: Platform.OS === 'android' ? 32 : 45,
  },
  bottomText: {
    fontFamily: 'Nunito-Medium',
    fontSize: 13,
    color: '#8E97A8',
    letterSpacing: 0.2,
  },
});
