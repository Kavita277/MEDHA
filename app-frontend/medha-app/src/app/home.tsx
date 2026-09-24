import React from 'react';
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';
import { MedhaBackground } from '../components/medha-background';
import { MedhaBottomNav } from '../components/medha-bottom-nav';
import { MedhaFloatingChat } from '../components/medha-floating-chat';

export default function HomeScreen() {
  const router = useRouter();

  return (
    <MedhaBackground variant="home">
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
                <Text style={styles.greetingTitle}>
                  Good morning, Kavita 🌤️
                </Text>
                <Text style={styles.greetingSub}>
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
                    size={20}
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

            {/* HERO CHECK-IN CARD (Blue Gradient from HTML benchmark) */}
            <View style={styles.heroWrap}>
              <LinearGradient
                colors={[COLORS.blueDark, '#6FC3E8']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.heroCard}
              >
                <View style={styles.heroBadge}>
                  <Ionicons name="sparkles" size={12} color="#FFFFFF" />
                  <Text style={styles.heroBadgeText}>A QUIET MOMENT</Text>
                </View>

                <Text style={styles.heroTitle}>
                  How are you feeling today?
                </Text>

                <Text style={styles.heroSub}>
                  Take a moment to check in. Nothing needs to be solved all at once.
                </Text>

                <Pressable
                  onPress={() => router.push('/check-in')}
                  style={({ pressed }) => [
                    styles.heroPill,
                    pressed && styles.pressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel="Quick Check-in"
                >
                  <Text style={styles.heroPillText}>Quick Check-in →</Text>
                </Pressable>
              </LinearGradient>
            </View>

            {/* ARRIVE SECTION */}
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionEyebrow}>ARRIVE</Text>
              <Text style={styles.sectionTitle}>
                How would you like to arrive?
              </Text>
            </View>

            <View style={styles.arriveGrid}>
              {/* Quick Check-in Card */}
              <Pressable
                onPress={() => router.push('/check-in')}
                style={({ pressed }) => [
                  styles.arriveCard,
                  styles.arriveCardPeach,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Check in with gentle questions"
              >
                <View style={[styles.arriveIconCircle, { backgroundColor: COLORS.peach }]}>
                  <Ionicons name="sparkles" size={20} color={COLORS.coralDark} />
                </View>
                <Text style={styles.arriveCardTitle}>Check in</Text>
                <Text style={styles.arriveCardSub}>A few gentle questions</Text>
              </Pressable>

              {/* Speak / Voice Check-in Card */}
              <Pressable
                onPress={() => router.push('/voice')}
                style={({ pressed }) => [
                  styles.arriveCard,
                  styles.arriveCardBlue,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Speak what you are feeling"
              >
                <View style={[styles.arriveIconCircle, { backgroundColor: COLORS.blue }]}>
                  <Ionicons name="mic" size={20} color={COLORS.blueDark} />
                </View>
                <Text style={styles.arriveCardTitle}>Speak</Text>
                <Text style={styles.arriveCardSub}>Say what you’re feeling</Text>
              </Pressable>
            </View>

            {/* YOUR SPACE SECTION (2x2 Pastel Action Cards from HTML) */}
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
                  styles.actionCardPink,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Journal"
              >
                <View style={styles.actionTopRow}>
                  <View style={[styles.emojiWrap, { backgroundColor: COLORS.pink }]}>
                    <Text style={styles.emojiText}>📝</Text>
                  </View>
                  <Ionicons name="arrow-forward" size={16} color={COLORS.pinkDark} />
                </View>
                <Text style={styles.actionTitle}>Journal</Text>
                <Text style={styles.actionSub}>Write freely, just for you</Text>
              </Pressable>

              {/* 2. Find Centre / Grounding */}
              <Pressable
                onPress={() => router.push('/grounding')}
                style={({ pressed }) => [
                  styles.actionCard,
                  styles.actionCardGreen,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Find centre and grounding pause"
              >
                <View style={styles.actionTopRow}>
                  <View style={[styles.emojiWrap, { backgroundColor: COLORS.green }]}>
                    <Text style={styles.emojiText}>🧘</Text>
                  </View>
                  <Ionicons name="arrow-forward" size={16} color={COLORS.greenDark} />
                </View>
                <Text style={styles.actionTitle}>Find centre</Text>
                <Text style={styles.actionSub}>Breathe & ground pause</Text>
              </Pressable>

              {/* 3. Talk with MEDHA */}
              <Pressable
                onPress={() => router.push('/chat')}
                style={({ pressed }) => [
                  styles.actionCard,
                  styles.actionCardLavender,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Talk with MEDHA"
              >
                <View style={styles.actionTopRow}>
                  <View style={[styles.emojiWrap, { backgroundColor: COLORS.lavender }]}>
                    <Text style={styles.emojiText}>💬</Text>
                  </View>
                  <Ionicons name="arrow-forward" size={16} color={COLORS.lavenderDark} />
                </View>
                <Text style={styles.actionTitle}>Talk with MEDHA</Text>
                <Text style={styles.actionSub}>Always here to listen</Text>
              </Pressable>

              {/* 4. Insights */}
              <Pressable
                onPress={() => router.push('/insights')}
                style={({ pressed }) => [
                  styles.actionCard,
                  styles.actionCardYellow,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Insights"
              >
                <View style={styles.actionTopRow}>
                  <View style={[styles.emojiWrap, { backgroundColor: COLORS.yellow }]}>
                    <Text style={styles.emojiText}>🌱</Text>
                  </View>
                  <Ionicons name="arrow-forward" size={16} color={COLORS.yellowDark} />
                </View>
                <Text style={styles.actionTitle}>Insights</Text>
                <Text style={styles.actionSub}>Awareness of patterns</Text>
              </Pressable>
            </View>

            {/* SELF-HELP FEATURE CARD */}
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
                <View style={styles.selfHelpEyebrowWrap}>
                  <Text style={styles.selfHelpEyebrow}>A LITTLE SUPPORT</Text>
                </View>
                <Text style={styles.selfHelpTitle}>
                  Small steps.{'\n'}A calmer moment.
                </Text>
                <Text style={styles.selfHelpText}>
                  Explore gentle, evidence-informed guides for stress, anxiety, low mood and everyday wellbeing.
                </Text>

                <View style={styles.selfHelpButtonRow}>
                  <Text style={styles.selfHelpBtnText}>Explore Self Help</Text>
                  <Ionicons name="arrow-forward" size={15} color={COLORS.coralDark} />
                </View>
              </View>

              <View style={styles.selfHelpArt}>
                <View style={styles.artCircleOuter}>
                  <View style={styles.artCircleInner}>
                    <Ionicons name="leaf" size={32} color={COLORS.sage} />
                  </View>
                </View>
              </View>
            </Pressable>

            {/* Space before bottom navbar */}
            <View style={{ height: 90 }} />
          </ScrollView>

          {/* FLOATING ACTION CHAT BUTTON */}
          <MedhaFloatingChat />

          {/* BOTTOM GLASS NAVIGATION BAR */}
          <View style={styles.bottomNavContainer}>
            <MedhaBottomNav activeTab="home" />
          </View>
        </View>
      </SafeAreaView>
    </MedhaBackground>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
  },
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 24,
  },

  /* HEADER */
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
    marginTop: 6,
  },
  greetingWrap: {
    flex: 1,
    paddingRight: 12,
  },
  greetingTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 24,
    lineHeight: 30,
    color: COLORS.navy,
  },
  greetingSub: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    lineHeight: 18,
    color: COLORS.navyMuted,
    marginTop: 3,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  headerIconBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.95)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.card,
  },
  notificationDot: {
    position: 'absolute',
    top: 10,
    right: 11,
    width: 7,
    height: 7,
    borderRadius: 4,
    backgroundColor: COLORS.coral,
  },
  profileAvatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.coral,
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.glow,
  },
  avatarLetter: {
    fontFamily: 'Fredoka-Bold',
    fontSize: 18,
    color: COLORS.white,
  },

  /* HERO CARD */
  heroWrap: {
    marginBottom: 26,
    ...SHADOW.soft,
  },
  heroCard: {
    borderRadius: RADIUS.card + 6,
    padding: 22,
    overflow: 'hidden',
  },
  heroBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(255, 255, 255, 0.22)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginBottom: 12,
  },
  heroBadgeText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 10,
    letterSpacing: 1.2,
    color: COLORS.white,
  },
  heroTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 22,
    lineHeight: 28,
    color: COLORS.white,
    marginBottom: 6,
  },
  heroSub: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    lineHeight: 18,
    color: 'rgba(255, 255, 255, 0.92)',
    marginBottom: 16,
    maxWidth: 290,
  },
  heroPill: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.white,
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 16,
    ...SHADOW.card,
  },
  heroPillText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 13,
    color: COLORS.blueDark,
  },

  /* SECTION HEADERS */
  sectionHeader: {
    marginBottom: 12,
  },
  sectionEyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.5,
    color: COLORS.coralDark,
    textTransform: 'uppercase',
  },
  sectionTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 17,
    color: COLORS.navy,
    marginTop: 2,
  },

  /* ARRIVE ROW */
  arriveGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 26,
  },
  arriveCard: {
    flex: 1,
    borderRadius: RADIUS.card,
    padding: 16,
    borderWidth: 1.5,
    ...SHADOW.card,
  },
  arriveCardPeach: {
    backgroundColor: COLORS.creamSecondary,
    borderColor: COLORS.peach,
  },
  arriveCardBlue: {
    backgroundColor: COLORS.blueSoft,
    borderColor: COLORS.blue,
  },
  arriveIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  arriveCardTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.navy,
    marginBottom: 2,
  },
  arriveCardSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
  },

  /* ACTION 2X2 GRID (HTML benchmark) */
  actionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 26,
  },
  actionCard: {
    width: '48%',
    borderRadius: RADIUS.card,
    padding: 14,
    borderWidth: 1.5,
    ...SHADOW.card,
  },
  actionCardPink: {
    backgroundColor: COLORS.pinkSoft,
    borderColor: COLORS.pink,
  },
  actionCardGreen: {
    backgroundColor: COLORS.greenSoft,
    borderColor: COLORS.green,
  },
  actionCardLavender: {
    backgroundColor: '#F3EFFF',
    borderColor: COLORS.lavender,
  },
  actionCardYellow: {
    backgroundColor: COLORS.yellowSoft,
    borderColor: COLORS.yellow,
  },
  actionTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  emojiWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emojiText: {
    fontSize: 18,
  },
  actionTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 14,
    color: COLORS.navy,
    marginBottom: 2,
  },
  actionSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 10,
    lineHeight: 14,
    color: COLORS.navyMuted,
  },

  /* SELF HELP FEATURE CARD */
  selfHelpCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.sageSoft,
    borderWidth: 1.5,
    borderColor: COLORS.sage,
    borderRadius: RADIUS.card + 4,
    padding: 18,
    marginBottom: 14,
    ...SHADOW.card,
  },
  selfHelpCopy: {
    flex: 1,
    paddingRight: 10,
  },
  selfHelpEyebrowWrap: {
    alignSelf: 'flex-start',
    backgroundColor: 'rgba(127, 168, 138, 0.22)',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    marginBottom: 8,
  },
  selfHelpEyebrow: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 9,
    letterSpacing: 1.2,
    color: COLORS.forestClassic,
  },
  selfHelpTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 17,
    lineHeight: 22,
    color: COLORS.navy,
    marginBottom: 6,
  },
  selfHelpText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
    marginBottom: 12,
  },
  selfHelpButtonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  selfHelpBtnText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 12,
    color: COLORS.coralDark,
  },
  selfHelpArt: {
    alignItems: 'center',
    justifyContent: 'center',
    width: 76,
  },
  artCircleOuter: {
    width: 68,
    height: 68,
    borderRadius: 34,
    backgroundColor: 'rgba(255, 255, 255, 0.65)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  artCircleInner: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: COLORS.white,
    alignItems: 'center',
    justifyContent: 'center',
  },

  /* BOTTOM NAV CONTAINER */
  bottomNavContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.9,
  },
});
