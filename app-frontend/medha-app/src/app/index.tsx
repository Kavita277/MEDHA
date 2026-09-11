import { router } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Easing,
  Image,
  StyleSheet,
  Text,
  View,
} from 'react-native';

const MEDHA_LOGO = require('../../assets/images/medha-logo.png');

export default function Index() {
  const logoOpacity = useRef(new Animated.Value(0)).current;
  const logoScale = useRef(new Animated.Value(0.88)).current;
  const textOpacity = useRef(new Animated.Value(0)).current;
  const loaderOpacity = useRef(new Animated.Value(0)).current;
  const rotation = useRef(new Animated.Value(0)).current;

  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;

    Animated.parallel([
      Animated.timing(logoOpacity, {
        toValue: 1,
        duration: 900,
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
      if (!mounted) return;

      Animated.timing(textOpacity, {
        toValue: 1,
        duration: 650,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start();
    }, 650);

    const loadingTimer = setTimeout(() => {
      if (!mounted) return;

      setLoading(true);

      Animated.timing(loaderOpacity, {
        toValue: 1,
        duration: 500,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start();

      Animated.loop(
        Animated.timing(rotation, {
          toValue: 1,
          duration: 1300,
          easing: Easing.linear,
          useNativeDriver: true,
        }),
      ).start();
    }, 1750);

    const navigationTimer = setTimeout(() => {
      if (!mounted) return;

      router.replace('/onboarding');
    }, 3900);

    return () => {
      mounted = false;
      clearTimeout(textTimer);
      clearTimeout(loadingTimer);
      clearTimeout(navigationTimer);
    };
  }, [
    loaderOpacity,
    logoOpacity,
    logoScale,
    rotation,
    textOpacity,
  ]);

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
            styles.logoContainer,
            {
              opacity: logoOpacity,
              transform: [{ scale: logoScale }],
            },
          ]}
        >
          <Image
            source={MEDHA_LOGO}
            style={styles.logo}
            resizeMode="contain"
          />
        </Animated.View>

        <Animated.View
          style={[
            styles.messageContainer,
            {
              opacity: textOpacity,
            },
          ]}
        >
          <Text style={styles.title}>MEDHA</Text>

          <Text style={styles.subtitle}>
            A calmer mind.
          </Text>

          <Text style={styles.tagline}>
            A kinder tomorrow.
          </Text>
        </Animated.View>

        {loading && (
          <Animated.View
            style={[
              styles.loaderContainer,
              {
                opacity: loaderOpacity,
              },
            ]}
          >
            <Animated.View
              style={[
                styles.loaderRing,
                {
                  transform: [{ rotate: spin }],
                },
              ]}
            />

            <Text style={styles.loadingText}>
              Preparing your space...
            </Text>
          </Animated.View>
        )}
      </View>

      <View style={styles.bottom}>
        <Text style={styles.bottomText}>
          LISTEN  ·  UNDERSTAND  ·  SUPPORT
        </Text>

        <View style={styles.indicator} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F3EFE4',
  },

  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
  },

  logoContainer: {
    width: 180,
    height: 180,
    alignItems: 'center',
    justifyContent: 'center',
  },

  logo: {
    width: 175,
    height: 175,
  },

  messageContainer: {
    alignItems: 'center',
    marginTop: 12,
  },

  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 30,
    letterSpacing: 8,
    color: '#24372C',
    marginLeft: 8,
  },

  subtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: '#5F6F63',
    marginTop: 10,
    letterSpacing: 0.5,
  },

  tagline: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 20,
    fontStyle: 'italic',
    color: '#53665A',
    marginTop: 3,
  },

  loaderContainer: {
    alignItems: 'center',
    marginTop: 42,
  },

  loaderRing: {
    width: 38,
    height: 38,
    borderRadius: 19,
    borderWidth: 2,
    borderColor: '#D8DED2',
    borderTopColor: '#526B5B',
  },

  loadingText: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: '#7B857D',
    marginTop: 14,
    letterSpacing: 0.3,
  },

  bottom: {
    alignItems: 'center',
    paddingBottom: 28,
  },

  bottomText: {
    fontFamily: 'Inter-Regular',
    fontSize: 8,
    letterSpacing: 1.4,
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