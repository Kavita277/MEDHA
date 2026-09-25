import React from 'react';
import {
  Platform,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW, TOP_HOME_PADDING } from '../constants/theme';
import { MedhaBottomNav } from '../components/medha-bottom-nav';
import { MedhaFloatingChat } from '../components/medha-floating-chat';
import { MedhaScreenBackground } from '../components/medha-screen-background';

export default function HomeScreen() {
  const router = useRouter();

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safe}>
        <View style={styles.container}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          {/* HEADER */}
          <View style={styles.header}>
            <View style={styles.greetingWrap}>
              <Text style={styles.greetingTitle} numberOfLines={1}>
                Good morning, Kavita 🌤️
              </Text>
              <Text style={styles.greetingSub} numberOfLines={1}>
                Take a moment for yourself.
              </Text>
            </View>

            <View style={styles.headerActions}>
              {/* Notifications button */}
              <Pressable
                onPress={() => router.push('/notifications')}
                style={({ pressed }) => [
                  styles.headerIconBtn,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Notifications"
              >
                <Ionicons
                  name="notifications-outline"
                  size={19}
                  color={COLORS.navy}
                />
                <View style={styles.notificationDot} />
              </Pressable>

              {/* Profile Avatar button */}
              <Pressable
                onPress={() => router.push('/profile')}
                style={({ pressed }) => [
                  styles.profileAvatar,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Profile"
              >
                <Text style={styles.avatarLetter}>K</Text>
              </Pressable>
            </View>
          </View>

          {/* EXACTLY ONE DOMINANT CHECK-IN HERO CARD (LIGHT DAYTIME PATIENT DESIGN - COMPACT) */}
          <View style={styles.heroWrap}>
            <View style={styles.heroCard}>
              <View style={styles.heroTopRow}>
                <View style={styles.heroBadge}>
                  <Ionicons name="sparkles" size={12} color={COLORS.coralDark} />
                  <Text style={styles.heroBadgeText}>DAILY CHECK-IN</Text>
                </View>

                <View style={styles.streakBadge}>
                  <Ionicons name="heart" size={13} color="#0284C7" />
                  <Text style={styles.streakText}>7 day streak</Text>
                </View>
              </View>

              <Text style={styles.heroTitle}>
                How is your mind today?
              </Text>

              <Text style={styles.heroSub}>
                Take 2 minutes to notice your thoughts and feelings. One quiet moment is enough.
              </Text>

              {/* GENTLE MOTIVATION */}
              <View style={styles.motivationRow}>
                <Ionicons name="sparkles-outline" size={13} color="#CCA01A" />
                <Text style={styles.motivationText}>
                  You showed up today. That’s a good step.
                </Text>
              </View>

              <Pressable
                onPress={() => router.push('/check-in')}
                style={({ pressed }) => [
                  styles.heroPill,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Start Daily Check-in"
              >
                <Text style={styles.heroPillText}>Quick Check-in</Text>
                <Ionicons name="arrow-forward" size={15} color={COLORS.white} />
              </Pressable>
            </View>
          </View>

          {/* YOUR SPACE SECTION (2x2 Balanced Action Cards) */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionEyebrow}>YOUR SPACE</Text>
            <Text style={styles.sectionTitle}>Daily reflections & support</Text>
          </View>

          <View style={styles.actionGrid}>
            {/* 1. Journal */}
            <Pressable
              onPress={() => router.push('/journal')}
              style={({ pressed }) => [
                styles.actionCard,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Journal"
            >
              <View style={styles.actionTopRow}>
                <View style={[styles.badgeWrap, { backgroundColor: '#FFEBF1' }]}>
                  <Ionicons name="create-outline" size={18} color="#E05375" />
                </View>
                <Ionicons name="arrow-forward" size={15} color={COLORS.navyMuted} />
              </View>
              <Text style={styles.actionTitle}>Journal</Text>
              <Text style={styles.actionSub}>Write freely, just for you</Text>
            </Pressable>

            {/* 2. Find Centre / Grounding */}
            <Pressable
              onPress={() => router.push('/grounding')}
              style={({ pressed }) => [
                styles.actionCard,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Find centre and grounding pause"
            >
              <View style={styles.actionTopRow}>
                <View style={[styles.badgeWrap, { backgroundColor: '#E2F5E8' }]}>
                  <Ionicons name="leaf-outline" size={18} color="#2D8A4E" />
                </View>
                <Ionicons name="arrow-forward" size={15} color={COLORS.navyMuted} />
              </View>
              <Text style={styles.actionTitle}>Find centre</Text>
              <Text style={styles.actionSub}>Breathe & ground pause</Text>
            </Pressable>

            {/* 3. Speak / Voice Check-in */}
            <Pressable
              onPress={() => router.push('/voice')}
              style={({ pressed }) => [
                styles.actionCard,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Speak voice check-in"
            >
              <View style={styles.actionTopRow}>
                <View style={[styles.badgeWrap, { backgroundColor: '#E1F2FE' }]}>
                  <Ionicons name="mic-outline" size={18} color="#0284C7" />
                </View>
                <Ionicons name="arrow-forward" size={15} color={COLORS.navyMuted} />
              </View>
              <Text style={styles.actionTitle}>Speak</Text>
              <Text style={styles.actionSub}>Say what you’re feeling</Text>
            </Pressable>

            {/* 4. Insights */}
            <Pressable
              onPress={() => router.push('/insights')}
              style={({ pressed }) => [
                styles.actionCard,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Insights"
            >
              <View style={styles.actionTopRow}>
                <View style={[styles.badgeWrap, { backgroundColor: '#FFF4D9' }]}>
                  <Ionicons name="analytics-outline" size={18} color="#CCA01A" />
                </View>
                <Ionicons name="arrow-forward" size={15} color={COLORS.navyMuted} />
              </View>
              <Text style={styles.actionTitle}>Insights</Text>
              <Text style={styles.actionSub}>Awareness of patterns</Text>
            </Pressable>
          </View>

          {/* SECONDARY SMALL STEPS CARD (PRESERVING ORIGINAL #DDE8D2 COLOR & ARTWORK) */}
          <Pressable
            onPress={() => router.push('/self-help')}
            style={({ pressed }) => [
              styles.selfHelpCard,
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Explore Self Help"
          >
            <View style={styles.selfHelpCopy}>
              <Text style={styles.selfHelpEyebrow}>A LITTLE SUPPORT</Text>
              <Text style={styles.selfHelpTitle}>
                Small steps.{'\n'}A calmer moment.
              </Text>
              <Text style={styles.selfHelpText}>
                Explore gentle, evidence-informed guides for stress, anxiety, low mood and everyday wellbeing.
              </Text>

              <View style={styles.selfHelpButton}>
                <Text style={styles.selfHelpButtonText}>Explore Self Help</Text>
                <Ionicons name="arrow-forward" size={14} color="#1B3122" />
              </View>
            </View>

            <View style={styles.selfHelpIllustration}>
              <View style={styles.illustrationCircleLarge} />
              <View style={styles.illustrationCircleSmall} />
              <Ionicons name="leaf-outline" size={40} color="#3B5D45" />
            </View>
          </Pressable>
        </ScrollView>

        {/* FLOATING ACTION CHAT BUTTON */}
        <MedhaFloatingChat />

        {/* FLOATING BOTTOM NAVIGATION */}
        <View style={styles.bottomNavContainer}>
          <MedhaBottomNav activeTab="home" />
        </View>
      </View>
    </SafeAreaView>
  </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: COLORS.porcelain,
  },
  safe: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  container: {
    flex: 1,
    position: 'relative',
  },
  scrollContent: {
    paddingHorizontal: 22,
    paddingTop: TOP_HOME_PADDING,
    paddingBottom: 110,
  },

  /* HEADER */
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 22,
  },
  greetingWrap: {
    flex: 1,
    paddingRight: 12,
  },
  greetingTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 19,
    lineHeight: 25,
    color: COLORS.navy,
  },
  greetingSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 18,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerIconBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
    ...SHADOW.subtle,
  },
  notificationDot: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: COLORS.coralDark,
  },
  profileAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },
  avatarLetter: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.navy,
  },

  /* STANDALONE HERO CHECK-IN CARD (LIGHT DAYTIME PATIENT PALETTE - 12-15% COMPACT) */
  heroWrap: {
    marginBottom: 20,
  },
  heroCard: {
    borderRadius: RADIUS.card,
    paddingVertical: 18,
    paddingHorizontal: 20,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  heroTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  heroBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    backgroundColor: '#FFEADB',
    paddingHorizontal: 10,
    paddingVertical: 3.5,
    borderRadius: RADIUS.pill,
  },
  heroBadgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.2,
    color: COLORS.coralDark,
  },
  heroCalmBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#E1F2FE',
    alignItems: 'center',
    justifyContent: 'center',
  },
  streakBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: '#E1F2FE',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: RADIUS.pill,
  },
  streakText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11.5,
    color: '#0284C7',
  },
  motivationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: '#FFF9ED',
    borderWidth: 1,
    borderColor: '#FFE8B8',
    paddingVertical: 5,
    paddingHorizontal: 10,
    borderRadius: RADIUS.pill,
    alignSelf: 'flex-start',
    marginBottom: 14,
  },
  motivationText: {
    fontFamily: 'Nunito-Medium',
    fontSize: 12,
    color: '#8A6814',
  },
  heroTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 21,
    lineHeight: 26,
    color: COLORS.navy,
    marginBottom: 4,
  },
  heroSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 18,
    color: COLORS.navyMuted,
    marginBottom: 14,
    maxWidth: 320,
  },
  heroPill: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: COLORS.navy,
    paddingHorizontal: 18,
    height: 40,
    borderRadius: RADIUS.pill,
    ...SHADOW.subtle,
  },
  heroPillText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 13,
    color: COLORS.white,
  },

  /* SECTION HEADERS */
  sectionHeader: {
    marginBottom: 12,
  },
  sectionEyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.4,
    color: COLORS.coralDark,
    textTransform: 'uppercase',
  },
  sectionTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 17,
    color: COLORS.navy,
    marginTop: 2,
  },

  /* ACTION 2X2 GRID */
  actionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  actionCard: {
    width: '48%',
    borderRadius: RADIUS.card,
    padding: 16,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  actionTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  badgeWrap: {
    width: 38,
    height: 38,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.navy,
    marginBottom: 3,
  },
  actionSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 15,
    color: COLORS.navyMuted,
  },

  /* PRESERVED SMALL STEPS CARD (ORIGINAL #DDE8D2, ARTWORK, BALANCED SECONDARY PROPORTIONS) */
  selfHelpCard: {
    borderRadius: RADIUS.card,
    backgroundColor: '#DDE8D2',
    padding: 18,
    overflow: 'hidden',
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.04)',
    ...SHADOW.subtle,
  },
  selfHelpCopy: {
    flex: 1,
    zIndex: 2,
    paddingRight: 6,
  },
  selfHelpEyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 9,
    letterSpacing: 1.6,
    color: '#496B52',
    textTransform: 'uppercase',
    marginBottom: 5,
  },
  selfHelpTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 18,
    lineHeight: 22,
    color: '#1B3122',
  },
  selfHelpText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: '#3D5443',
    marginTop: 6,
    maxWidth: 190,
  },
  selfHelpButton: {
    alignSelf: 'flex-start',
    marginTop: 12,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    ...SHADOW.subtle,
  },
  selfHelpButtonText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 11,
    color: '#1B3122',
  },
  selfHelpIllustration: {
    width: 90,
    height: 120,
    marginLeft: -4,
    alignItems: 'center',
    justifyContent: 'center',
  },
  illustrationCircleLarge: {
    position: 'absolute',
    width: 104,
    height: 104,
    borderRadius: 52,
    backgroundColor: 'rgba(255, 255, 255, 0.42)',
  },
  illustrationCircleSmall: {
    position: 'absolute',
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: 'rgba(255, 255, 255, 0.52)',
  },

  /* BOTTOM NAV CONTAINER */
  bottomNavContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.88,
  },
});
