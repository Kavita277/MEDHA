import React, { useState } from 'react';
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

export default function ConnectedDevicesScreen() {
  const router = useRouter();
  const [isConnected, setIsConnected] = useState(true);
  const [lastSync, setLastSync] = useState('2 minutes ago');

  const handleManage = () => {
    router.push('/settings');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* TOP BAR */}
          <View style={styles.topBar}>
            <Pressable
              onPress={() => router.back()}
              style={({ pressed }) => [
                styles.iconButton,
                pressed && styles.pressed,
              ]}
              hitSlop={12}
              accessibilityRole="button"
              accessibilityLabel="Back"
            >
              <Ionicons name="arrow-back" size={20} color={COLORS.navy} />
            </Pressable>

            <View style={styles.statusBadge}>
              <View
                style={[
                  styles.statusDot,
                  { backgroundColor: isConnected ? '#2D8A4E' : COLORS.subtleText },
                ]}
              />
              <Text style={styles.statusBadgeText}>
                {isConnected ? 'Bluetooth Active' : 'Disconnected'}
              </Text>
            </View>
          </View>

          {/* SCREEN HEADER */}
          <View style={styles.header}>
            <Text style={styles.title}>Connected Devices</Text>
            <Text style={styles.subtitle}>
              Pair personal wearables to support gentle, unobtrusive wellbeing insights.
            </Text>
          </View>

          {/* SMARTWATCH DEVICE CARD MATCHING REFERENCE SCREEN 23 */}
          <View style={styles.deviceCard}>
            <View style={styles.deviceCardTop}>
              <View style={styles.watchIconWrap}>
                <Ionicons name="watch-outline" size={24} color={COLORS.white} />
              </View>

              <View style={styles.deviceDetails}>
                <Text style={styles.deviceName}>Smartwatch</Text>
                <Text
                  style={[
                    styles.deviceStatus,
                    { color: isConnected ? '#2D8A4E' : COLORS.navyMuted },
                  ]}
                >
                  {isConnected ? 'Connected' : 'Paused'}
                </Text>
                <Text style={styles.deviceMetrics}>
                  Heart rate • Sleep • Activity
                </Text>
              </View>

              {/* Toggle Switch */}
              <Switch
                value={isConnected}
                onValueChange={(val) => {
                  setIsConnected(val);
                  if (val) setLastSync('Just now');
                }}
                trackColor={{ false: '#D9DFE8', true: '#7856D6' }}
                thumbColor={COLORS.white}
              />
            </View>

            {isConnected && (
              <View style={styles.deviceCardFooter}>
                <Ionicons name="time-outline" size={13} color={COLORS.navyMuted} />
                <Text style={styles.lastSyncText}>Last synced {lastSync}</Text>
              </View>
            )}
          </View>

          {/* DATA USAGE BULLETS CARD MATCHING REFERENCE SCREEN 23 */}
          <View style={styles.usageCard}>
            <Text style={styles.usageTitle}>Use this data to:</Text>

            <View style={styles.bulletsList}>
              <View style={styles.bulletItem}>
                <View style={[styles.bulletDot, { backgroundColor: '#7856D6' }]} />
                <Text style={styles.bulletText}>Track sleep patterns & sleep quality</Text>
              </View>

              <View style={styles.bulletItem}>
                <View style={[styles.bulletDot, { backgroundColor: '#2D8A4E' }]} />
                <Text style={styles.bulletText}>Understand daily physical activity levels</Text>
              </View>

              <View style={styles.bulletItem}>
                <View style={[styles.bulletDot, { backgroundColor: '#E66A35' }]} />
                <Text style={styles.bulletText}>Detect physical stress indicators</Text>
              </View>

              <View style={styles.bulletItem}>
                <View style={[styles.bulletDot, { backgroundColor: '#2B7CB0' }]} />
                <Text style={styles.bulletText}>Personalize reflection & grounding recommendations</Text>
              </View>
            </View>
          </View>

          {/* PRIVACY REASSURANCE */}
          <View style={styles.privacyCard}>
            <Ionicons name="shield-checkmark-outline" size={16} color={COLORS.sage} />
            <Text style={styles.privacyText}>
              Device signals are processed locally on your device for personal reflection and are never sold or shared.
            </Text>
          </View>

          {/* MANAGE BUTTON MATCHING REFERENCE SCREEN 23 */}
          <View style={styles.actionWrapper}>
            <Pressable
              onPress={handleManage}
              style={({ pressed }) => [
                styles.manageButton,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Manage Device"
            >
              <Text style={styles.manageButtonText}>Manage</Text>
              <Ionicons name="settings-outline" size={16} color={COLORS.white} />
            </Pressable>
          </View>
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.porcelain,
  },
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 36,
  },

  /* TOP BAR */
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
  },
  statusBadgeText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 11,
    color: COLORS.navy,
  },

  /* HEADER */
  header: {
    marginTop: 12,
    marginBottom: 20,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 26,
    lineHeight: 32,
    color: COLORS.navy,
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 18,
    color: COLORS.navyMuted,
    marginTop: 4,
  },

  /* DEVICE CARD */
  deviceCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 18,
    ...SHADOW.subtle,
  },
  deviceCardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
  },
  watchIconWrap: {
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: COLORS.navy,
    alignItems: 'center',
    justifyContent: 'center',
  },
  deviceDetails: {
    flex: 1,
  },
  deviceName: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 17,
    color: COLORS.navy,
  },
  deviceStatus: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    marginTop: 2,
  },
  deviceMetrics: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  deviceCardFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.04)',
  },
  lastSyncText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
  },

  /* USAGE CARD */
  usageCard: {
    marginTop: 16,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 18,
    ...SHADOW.subtle,
  },
  usageTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.navy,
    marginBottom: 12,
  },
  bulletsList: {
    gap: 12,
  },
  bulletItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  bulletDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  bulletText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 18,
    color: COLORS.navy,
  },

  /* PRIVACY */
  privacyCard: {
    marginTop: 16,
    backgroundColor: 'rgba(0, 0, 0, 0.02)',
    borderRadius: RADIUS.card,
    padding: 14,
    flexDirection: 'row',
    gap: 10,
    alignItems: 'flex-start',
  },
  privacyText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
  },

  /* ACTION */
  actionWrapper: {
    marginTop: 24,
  },
  manageButton: {
    height: 52,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.navy,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    ...SHADOW.dock,
  },
  manageButtonText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.white,
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.88,
  },
});
