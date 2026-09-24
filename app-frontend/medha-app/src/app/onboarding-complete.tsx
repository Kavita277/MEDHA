import React, { useEffect, useRef } from 'react';
import {
  Animated,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Circle, Defs, LinearGradient as SvgGradient, Path, Stop } from 'react-native-svg';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

export default function OnboardingCompleteScreen() {
  const router = useRouter();
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 900,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 900,
        useNativeDriver: true,
      }),
    ]).start();
  }, [fadeAnim, slideAnim]);

  return (
    <LinearGradient
      colors={['#0A0D16', '#141A2B', '#22263D', '#121624']}
      locations={[0, 0.35, 0.72, 1]}
      style={styles.gradientContainer}
    >
      <SafeAreaView style={styles.safeArea}>
        {/* CENTER CONTENT MATCHING REFERENCE SCREEN 29 */}
        <Animated.View
          style={[
            styles.centerContent,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
          {/* SUNSET MOUNTAIN HORIZON SVG */}
          <View style={styles.horizonWrapper}>
            <Svg width={300} height={180} viewBox="0 0 300 180">
              <Defs>
                <SvgGradient id="sunsetSkyGlow" x1="0" y1="0" x2="0" y2="1">
                  <Stop offset="0%" stopColor="#FFA4B0" stopOpacity="0.9" />
                  <Stop offset="45%" stopColor="#FFC899" stopOpacity="0.6" />
                  <Stop offset="100%" stopColor="#22263D" stopOpacity="0" />
                </SvgGradient>

                <SvgGradient id="mountainRidge1" x1="0" y1="0" x2="0" y2="1">
                  <Stop offset="0%" stopColor="#FF9B8A" stopOpacity="0.75" />
                  <Stop offset="70%" stopColor="#1C2136" stopOpacity="0.95" />
                  <Stop offset="100%" stopColor="#121624" stopOpacity="1" />
                </SvgGradient>

                <SvgGradient id="mountainRidge2" x1="0" y1="0" x2="0" y2="1">
                  <Stop offset="0%" stopColor="#8A66D6" stopOpacity="0.5" />
                  <Stop offset="100%" stopColor="#0E121E" stopOpacity="1" />
                </SvgGradient>
              </Defs>

              {/* Gentle dusk sun glow behind mountains */}
              <Circle cx="150" cy="90" r="50" fill="url(#sunsetSkyGlow)" />

              {/* Distant mountains layer */}
              <Path
                d="M0 170 L50 90 L110 130 L180 75 L250 125 L300 170 Z"
                fill="url(#mountainRidge2)"
                opacity={0.6}
              />

              {/* Foreground dramatic mountain peaks */}
              <Path
                d="M20 180 L110 65 L170 120 L220 50 L300 180 Z"
                fill="url(#mountainRidge1)"
              />

              {/* Warm dusk horizon light rim */}
              <Path
                d="M110 65 L170 120 L220 50"
                stroke="rgba(255, 200, 153, 0.45)"
                strokeWidth="1.5"
                fill="none"
              />
            </Svg>
          </View>

          {/* EMOTIONAL REASSURANCE TEXT */}
          <View style={styles.textGroup}>
            <Text style={styles.title}>You showed up.{'\n'}And that's powerful.</Text>
            <Text style={styles.subtitle}>Small steps lead to brighter days.</Text>
          </View>

          {/* PRIMARY ENTER ACTION */}
          <View style={styles.actionWrapper}>
            <Pressable
              onPress={() => router.replace('/home')}
              style={({ pressed }) => [
                styles.enterButton,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Enter MEDHA"
            >
              <Text style={styles.enterButtonText}>Enter MEDHA</Text>
              <Ionicons name="arrow-forward" size={17} color={COLORS.white} />
            </Pressable>
          </View>
        </Animated.View>

        {/* BOTTOM NOTE */}
        <View style={styles.bottomFooter}>
          <Text style={styles.footerNote}>
            Your safe space is ready whenever you need it.
          </Text>
        </View>
      </SafeAreaView>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  safeArea: {
    flex: 1,
    paddingHorizontal: 24,
    justifyContent: 'space-between',
  },

  /* CENTER */
  centerContent: {
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 'auto',
    paddingVertical: 20,
  },
  horizonWrapper: {
    width: 300,
    height: 180,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 28,
  },
  textGroup: {
    alignItems: 'center',
    paddingHorizontal: 12,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 32,
    lineHeight: 40,
    color: COLORS.white,
    textAlign: 'center',
    letterSpacing: 0.3,
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 15,
    lineHeight: 22,
    color: 'rgba(255, 255, 255, 0.75)',
    textAlign: 'center',
    marginTop: 12,
  },

  /* ACTION */
  actionWrapper: {
    width: '100%',
    maxWidth: 280,
    marginTop: 36,
  },
  enterButton: {
    height: 52,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.18)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.35)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    ...SHADOW.dock,
  },
  enterButtonText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.white,
    letterSpacing: 0.3,
  },

  /* FOOTER */
  bottomFooter: {
    alignItems: 'center',
    paddingBottom: 28,
  },
  footerNote: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.45)',
    textAlign: 'center',
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.85,
  },
});
