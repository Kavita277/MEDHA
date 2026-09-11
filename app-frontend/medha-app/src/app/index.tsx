import { useEffect } from 'react';
import {
  ImageBackground,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';

import { MedhaLogo } from '../components/medha-logo';
import { COLORS } from '../constants/colors';

const FOREST_IMAGE =
  'https://images.unsplash.com/photo-1511497584788-876760111969?q=90&w=1400&auto=format&fit=crop';

export default function SplashScreen() {
  useEffect(() => {
    const timer = setTimeout(() => {
      router.replace('/onboarding');
    }, 2800);

    return () => clearTimeout(timer);
  }, []);

  return (
    <View style={styles.container}>
      <ImageBackground
        source={{ uri: FOREST_IMAGE }}
        style={styles.background}
      >
        <LinearGradient
          colors={[
            'rgba(25,37,29,0.04)',
            'rgba(25,37,29,0.12)',
            'rgba(25,37,29,0.78)',
          ]}
          locations={[0, 0.45, 1]}
          style={StyleSheet.absoluteFill}
        />

        {/* subtle warm veil */}
        <View style={styles.warmVeil} />

        <View style={styles.content}>

          <View style={styles.center}>
            <MedhaLogo light />

            <Text style={styles.philosophy}>
              A calmer tomorrow.
            </Text>
          </View>

          <View style={styles.bottom}>
            <Text style={styles.navigationText}>
              LISTEN   ·   UNDERSTAND   ·   SUPPORT
            </Text>

            <View style={styles.progress}>
              <View style={styles.progressFill} />
            </View>

            <View style={styles.homeIndicator} />
          </View>

        </View>
      </ImageBackground>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.deepForest,
  },

  background: {
    flex: 1,
  },

  warmVeil: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(171,157,123,0.08)',
  },

  content: {
    flex: 1,
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 250,
    paddingBottom: 25,
  },

  center: {
    alignItems: 'center',
  },

  philosophy: {
    fontFamily: 'CormorantGaramond-Regular',
    color: COLORS.white,
    fontSize: 18,
    marginTop: 18,
    letterSpacing: 0.3,
  },

  bottom: {
    width: '100%',
    alignItems: 'center',
  },

  navigationText: {
    fontFamily: 'Inter-Regular',
    color: 'rgba(255,255,255,0.82)',
    fontSize: 8,
    letterSpacing: 1.6,
  },

  progress: {
    width: 65,
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.35)',
    marginTop: 16,
  },

  progressFill: {
    width: '35%',
    height: 1,
    backgroundColor: COLORS.white,
  },

  homeIndicator: {
    width: 100,
    height: 3,
    borderRadius: 3,
    backgroundColor: COLORS.white,
    marginTop: 18,
  },
});