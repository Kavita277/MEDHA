import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  Image,
  Platform,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';

const MEDHA_LOGO = require('../../assets/images/medha-logo.png');

export default function Index() {
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const logoScale = useRef(new Animated.Value(0.86)).current;
  const textOpacity = useRef(new Animated.Value(0)).current;
  const loaderOpacity = useRef(new Animated.Value(0)).current;
  const rotation = useRef(new Animated.Value(0)).current;
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(logoOpacity, {
        toValue: 1,
        duration: 850,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.spring(logoScale, {
        toValue: 1,
        friction: 8,
        tension: 45,
        useNativeDriver: true,
      }),
    ]).start();

    const textTimer = setTimeout(() => {
      Animated.timing(textOpacity, {
        toValue: 1,
        duration: 600,
        useNativeDriver: true,
      }).start();
    }, 550);

    const loadingTimer = setTimeout(() => {
      setLoading(true);
      Animated.timing(loaderOpacity, {
        toValue: 1,
        duration: 450,
        useNativeDriver: true,
      }).start();

      Animated.loop(
        Animated.timing(rotation, {
          toValue: 1,
          duration: 1200,
          easing: Easing.linear,
          useNativeDriver: true,
        }),
      ).start();
    }, 1450);

    const navigationTimer = setTimeout(() => {
      router.replace('/onboarding');
    }, 3900);

    return () => {
      clearTimeout(textTimer);
      clearTimeout(loadingTimer);
      clearTimeout(navigationTimer);
    };
  }, []);

  const spin = rotation.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  return (
    <View style={styles.container}>
      <StatusBar style="dark" />
      <View style={styles.content}>
        <Animated.View
          style={[
            styles.logoWrap,
            {
              opacity: logoOpacity,
              transform: [{ scale: logoScale }],
            },
          ]}
        >
          <Image source={MEDHA_LOGO} style={styles.logo} resizeMode="contain" />
        </Animated.View>

        <Animated.View style={[styles.copy, { opacity: textOpacity }]}>
          <Text style={styles.brand}>MEDHA</Text>
          <Text style={styles.subtitle}>A calmer mind.</Text>
          <Text style={styles.tagline}>A kinder tomorrow.</Text>
        </Animated.View>

        {loading && (
          <Animated.View style={[styles.loader, { opacity: loaderOpacity }]}>
            <Animated.View
              style={[styles.ring, { transform: [{ rotate: spin }] }]}
            />
            <Text style={styles.loadingText}>Preparing your space...</Text>
          </Animated.View>
        )}
      </View>

      <View style={styles.bottom}>
        <Text style={styles.bottomText}>LISTEN  ·  UNDERSTAND  ·  SUPPORT</Text>
        <View style={styles.indicator} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FAF9F6',
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 36,
  },
  logoWrap: {
    width: 220,
    height: 220,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: {
    width: 210,
    height: 210,
  },
  copy: {
    alignItems: 'center',
    marginTop: 8,
  },
  brand: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 32,
    letterSpacing: 4,
    color: '#181E2C',
  },
  subtitle: {
    fontFamily: 'Nunito-Bold',
    fontSize: 14,
    letterSpacing: 0.5,
    color: '#FF735C',
    marginTop: 6,
  },
  tagline: {
    fontFamily: 'Nunito-Regular',
    fontSize: 15,
    color: '#5B6478',
    marginTop: 4,
  },
  loader: {
    alignItems: 'center',
    marginTop: 36,
  },
  ring: {
    width: 38,
    height: 38,
    borderRadius: 19,
    borderWidth: 2.5,
    borderColor: 'rgba(24, 30, 44, 0.08)',
    borderTopColor: '#FF735C',
  },
  loadingText: {
    fontFamily: 'Nunito-Medium',
    fontSize: 12,
    color: '#8E97A8',
    marginTop: 12,
  },
  bottom: {
    alignItems: 'center',
    paddingBottom: Platform.OS === 'android' ? 24 : 32,
  },
  bottomText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 2,
    color: '#8E97A8',
  },
  indicator: {
    width: 60,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: '#FF735C',
    marginTop: 14,
  },
});
