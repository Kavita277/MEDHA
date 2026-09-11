import { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  Image,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useAuth } from '../context/AuthContext';

const MEDHA_LOGO = require('../../assets/images/medha-logo.png');

export default function Index() {
  const { isAuthenticated, user } = useAuth();
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const logoScale = useRef(new Animated.Value(0.84)).current;
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
          duration: 1250,
          easing: Easing.linear,
          useNativeDriver: true,
        }),
      ).start();
    }, 1450);

    const navigationTimer = setTimeout(() => {
      if (isAuthenticated && user) {
        if (user.role?.toUpperCase() === 'THERAPIST' || user.role?.toUpperCase() === 'ADMIN') {
          router.replace('/therapist');
        } else {
          router.replace('/home');
        }
      } else {
        router.replace('/onboarding');
      }
    }, 3200);

    return () => {
      clearTimeout(textTimer);
      clearTimeout(loadingTimer);
      clearTimeout(navigationTimer);
    };
  }, [isAuthenticated, user]);

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
  container: { flex: 1, backgroundColor: '#F3EFE4' },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 36,
  },
  logoWrap: {
    width: 235,
    height: 235,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logo: { width: 225, height: 225 },
  copy: { alignItems: 'center', marginTop: 2 },
  brand: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 28,
    letterSpacing: 7,
    color: '#24372C',
    marginLeft: 7,
  },
  subtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: '#5F6F63',
    marginTop: 9,
  },
  tagline: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 19,
    fontStyle: 'italic',
    color: '#53665A',
    marginTop: 2,
  },
  loader: { alignItems: 'center', marginTop: 38 },
  ring: {
    width: 42,
    height: 42,
    borderRadius: 21,
    borderWidth: 2,
    borderColor: '#D8DED2',
    borderTopColor: '#526B5B',
  },
  loadingText: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: '#7B857D',
    marginTop: 13,
  },
  bottom: { alignItems: 'center', paddingBottom: 28 },
  bottomText: {
    fontFamily: 'Inter-Regular',
    fontSize: 8,
    letterSpacing: 1.3,
    color: '#7C877E',
  },
  indicator: {
    width: 78,
    height: 3,
    borderRadius: 3,
    backgroundColor: '#536B5B',
    marginTop: 18,
  },
});
