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

export default function OfflineScreen() {
  const router = useRouter();
  const [retrying, setRetrying] = useState(false);

  const handleRetry = () => {
    setRetrying(true);
    setTimeout(() => {
      setRetrying(false);
      router.replace('/home');
    }, 800);
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
          <View style={styles.offlinePill}>
            <Ionicons name="cloud-offline-outline" size={14} color="rgba(255, 255, 255, 0.7)" />
            <Text style={styles.offlinePillText}>Offline Mode</Text>
          </View>
        </View>

        {/* CENTER ATMOSPHERIC MOUNTAIN & CONTENT */}
        <View style={styles.centerContent}>
          {/* CINEMATIC MOUNTAIN PEAK SILHOUETTE SVG */}
          <View style={styles.mountainWrapper}>
            <Svg width={280} height={160} viewBox="0 0 280 160">
              <Defs>
                <SvgGradient id="mountainGrad" x1="0" y1="0" x2="0" y2="1">
                  <Stop offset="0%" stopColor="#FFA4B0" stopOpacity="0.85" />
                  <Stop offset="40%" stopColor="#8A66D6" stopOpacity="0.4" />
                  <Stop offset="100%" stopColor="#121726" stopOpacity="0" />
                </SvgGradient>
                <SvgGradient id="duskGlow" x1="0" y1="0" x2="1" y2="1">
                  <Stop offset="0%" stopColor="#FFE0E6" stopOpacity="0.5" />
                  <Stop offset="100%" stopColor="#1A2135" stopOpacity="0" />
                </SvgGradient>
              </Defs>

              {/* Distant mountain glow */}
              <Path
                d="M10 150 L80 80 L130 110 L190 60 L270 150 Z"
                fill="url(#duskGlow)"
                opacity={0.35}
              />

              {/* Main silhouette peak */}
              <Path
                d="M40 160 L140 30 L160 55 L240 160 Z"
                fill="url(#mountainGrad)"
              />

              {/* Subtle mountain ridge line */}
              <Path
                d="M140 30 Q145 90 120 160"
                stroke="rgba(255, 255, 255, 0.25)"
                strokeWidth="1.5"
                fill="none"
              />
            </Svg>
          </View>

          {/* REASSURING TYPOGRAPHY MATCHING REFERENCE SCREEN 28 */}
          <Text style={styles.title}>You're still safe</Text>
          <Text style={styles.subtitle}>
            No internet connection. Some online features may be limited, but your private data is safe on this device.
          </Text>

          {/* ACTION BUTTONS */}
          <View style={styles.actionsGroup}>
            {/* Primary: Retry */}
            <Pressable
              onPress={handleRetry}
              disabled={retrying}
              style={({ pressed }) => [
                styles.retryButton,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Retry connection"
            >
              {retrying ? (
                <ActivityIndicator size="small" color={COLORS.white} />
              ) : (
                <>
                  <Text style={styles.retryButtonText}>Retry</Text>
                  <Ionicons name="refresh-outline" size={17} color={COLORS.white} />
                </>
              )}
            </Pressable>

            {/* Secondary: Continue Offline */}
            <Pressable
              onPress={() => router.replace('/home')}
              style={({ pressed }) => [
                styles.offlineButton,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Continue offline"
            >
              <Text style={styles.offlineButtonText}>Continue Offline</Text>
              <Ionicons name="arrow-forward" size={15} color="rgba(255, 255, 255, 0.75)" />
            </Pressable>
          </View>
        </View>

        {/* BOTTOM REASSURANCE */}
        <View style={styles.bottomFooter}>
          <Text style={styles.footerNote}>
            Breathing, grounding exercises, and saved journal entries remain fully accessible offline.
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
  offlinePill: {
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
  offlinePillText: {
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
    width: 280,
    height: 160,
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
  retryButton: {
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
  retryButtonText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.white,
  },
  offlineButton: {
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
  offlineButtonText: {
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
