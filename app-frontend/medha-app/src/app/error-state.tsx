import React, { useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  SafeAreaView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { Defs, LinearGradient as SvgGradient, Path, Stop } from 'react-native-svg';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

export default function ErrorStateScreen() {
  const router = useRouter();
  const [retrying, setRetrying] = useState(false);

  const handleRetry = () => {
    setRetrying(true);
    setTimeout(() => {
      setRetrying(false);
      router.back();
    }, 700);
  };

  return (
    <LinearGradient
      colors={['#080C14', '#111726', '#1A2135', '#0E1320']}
      locations={[0, 0.35, 0.75, 1]}
      style={styles.gradientContainer}
    >
      <SafeAreaView style={styles.safeArea}>
        {/* TOP STATUS BAR */}
        <View style={styles.topBar}>
          <View style={styles.statusPill}>
            <Ionicons name="sparkles" size={13} color="rgba(255, 255, 255, 0.7)" />
            <Text style={styles.statusPillText}>Safe Space Protected</Text>
          </View>
        </View>

        {/* CENTER CONTENT */}
        <View style={styles.centerContent}>
          {/* CINEMATIC MOUNTAIN SVG WITH SOFT TWILIGHT GLOW */}
          <View style={styles.mountainWrapper}>
            <Svg width={260} height={150} viewBox="0 0 260 150">
              <Defs>
                <SvgGradient id="errorMountainGrad" x1="0" y1="0" x2="0" y2="1">
                  <Stop offset="0%" stopColor="#FFA4B0" stopOpacity="0.8" />
                  <Stop offset="50%" stopColor="#8A66D6" stopOpacity="0.35" />
                  <Stop offset="100%" stopColor="#121726" stopOpacity="0" />
                </SvgGradient>
                <SvgGradient id="softAura" x1="0" y1="0" x2="1" y2="1">
                  <Stop offset="0%" stopColor="#FFE0E6" stopOpacity="0.4" />
                  <Stop offset="100%" stopColor="#1A2135" stopOpacity="0" />
                </SvgGradient>
              </Defs>

              <Path
                d="M10 140 L75 75 L120 100 L180 50 L250 140 Z"
                fill="url(#softAura)"
                opacity={0.35}
              />

              <Path
                d="M35 150 L130 25 L150 50 L225 150 Z"
                fill="url(#errorMountainGrad)"
              />

              <Path
                d="M130 25 Q135 85 110 150"
                stroke="rgba(255, 255, 255, 0.25)"
                strokeWidth="1.5"
                fill="none"
              />
            </Svg>
          </View>

          {/* CALM REASSURANCE TYPOGRAPHY */}
          <Text style={styles.title}>Take a calm breath</Text>
          <Text style={styles.subtitle}>
            Something didn't quite go as expected. It's not you, and your space is safe. Let's try that moment again.
          </Text>

          {/* ACTION BUTTONS */}
          <View style={styles.actionsGroup}>
            {/* Try Again */}
            <Pressable
              onPress={handleRetry}
              disabled={retrying}
              style={({ pressed }) => [
                styles.primaryButton,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Try again"
            >
              {retrying ? (
                <ActivityIndicator size="small" color={COLORS.white} />
              ) : (
                <>
                  <Text style={styles.primaryButtonText}>Try Again</Text>
                  <Ionicons name="refresh-outline" size={17} color={COLORS.white} />
                </>
              )}
            </Pressable>

            {/* Return to Home */}
            <Pressable
              onPress={() => router.replace('/home')}
              style={({ pressed }) => [
                styles.secondaryButton,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Return to MEDHA Home"
            >
              <Text style={styles.secondaryButtonText}>Return to Home</Text>
              <Ionicons name="home-outline" size={15} color="rgba(255, 255, 255, 0.75)" />
            </Pressable>
          </View>
        </View>

        {/* BOTTOM REASSURANCE */}
        <View style={styles.bottomFooter}>
          <Text style={styles.footerNote}>
            Your entries and recorded check-ins are saved and never lost.
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

  /* TOP BAR */
  topBar: {
    alignItems: 'center',
    paddingTop: 16,
  },
  statusPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
  },
  statusPillText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.75)',
  },

  /* CENTER */
  centerContent: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  mountainWrapper: {
    width: 260,
    height: 150,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 32,
    lineHeight: 38,
    color: COLORS.white,
    textAlign: 'center',
    letterSpacing: 0.3,
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 22,
    color: 'rgba(255, 255, 255, 0.7)',
    textAlign: 'center',
    marginTop: 10,
    maxWidth: 300,
  },

  /* ACTIONS */
  actionsGroup: {
    width: '100%',
    maxWidth: 300,
    gap: 12,
    marginTop: 32,
  },
  primaryButton: {
    height: 52,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.16)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.35)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    ...SHADOW.dock,
  },
  primaryButtonText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.white,
  },
  secondaryButton: {
    height: 48,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  secondaryButtonText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.85)',
  },

  /* FOOTER */
  bottomFooter: {
    alignItems: 'center',
    paddingBottom: 24,
  },
  footerNote: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: 'rgba(255, 255, 255, 0.45)',
    textAlign: 'center',
    maxWidth: 280,
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.85,
  },
});
