import React, { useState } from 'react';
import {
  Linking,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

type RecommendationType =
  | 'counselling'
  | 'safety'
  | 'financial'
  | 'rehabilitation'
  | 'legal'
  | 'coping'
  | 'crisis'
  | 'self-help';

type RecommendationPriority =
  | 'Recommended'
  | 'Important'
  | 'Immediate';

interface Recommendation {
  id: string;
  type: RecommendationType;
  priority: RecommendationPriority;
  title: string;
  description: string;
  cta: string;
  route?: string;
  phone?: string;
}

const mockRecommendations: Recommendation[] = [
  {
    id: '1',
    type: 'counselling',
    priority: 'Recommended',
    title: 'Talk to a counsellor',
    description:
      'A trained person can give you space to talk through what has been happening in a safe environment.',
    cta: 'Connect with Tele-MANAS',
    phone: '14416',
  },
  {
    id: '2',
    type: 'coping',
    priority: 'Recommended',
    title: 'Take a grounding pause',
    description:
      'Try a short 4-2-6 guided breathing exercise to bring your attention back to the present moment.',
    cta: 'Start Exercise',
    route: '/grounding',
  },
  {
    id: '3',
    type: 'self-help',
    priority: 'Recommended',
    title: 'A quieter conversation',
    description:
      'If speaking to someone feels difficult right now, you can start by typing with MEDHA.',
    cta: 'Talk with MEDHA',
    route: '/chat',
  },
  {
    id: '4',
    type: 'safety',
    priority: 'Important',
    title: 'Safety support',
    description:
      'If something around you feels unsafe, consider moving somewhere quiet and reaching someone you trust.',
    cta: 'View Safety Plan',
  },
  {
    id: '5',
    type: 'crisis',
    priority: 'Immediate',
    title: 'Immediate help',
    description:
      'If you are in immediate danger or feel unable to keep yourself safe, seek emergency support now.',
    cta: 'Call Emergency (112)',
    phone: '112',
  },
];

interface HelplineItem {
  id: string;
  title: string;
  number: string;
  subtitle?: string;
  icon: keyof typeof Ionicons.glyphMap;
  iconBg: string;
  iconColor: string;
  phone?: string;
  link?: string;
}

const HELPLINES: HelplineItem[] = [
  {
    id: 'emergency',
    title: 'Emergency (India)',
    number: '112',
    subtitle: 'National emergency services & medical response',
    icon: 'call',
    iconBg: '#FFEAE8',
    iconColor: '#E03E3E',
    phone: '112',
  },
  {
    id: 'women',
    title: 'Women Helpline',
    number: '181',
    subtitle: '24/7 dedicated support & safety assistance',
    icon: 'shield-checkmark',
    iconBg: '#FFEBF3',
    iconColor: '#DE4A82',
    phone: '181',
  },
  {
    id: 'mental-health',
    title: 'Mental Health Helpline',
    number: '1800-599-0019',
    subtitle: 'KIRAN rehabilitation & Tele-MANAS (14416)',
    icon: 'heart',
    iconBg: '#E4F6EB',
    iconColor: '#2D8A4E',
    phone: '18005990019',
  },
  {
    id: 'local',
    title: 'Find Local Support',
    number: 'View resources',
    subtitle: 'District health centres & community care directory',
    icon: 'search',
    iconBg: '#E8F2FA',
    iconColor: '#2B7CB0',
    link: 'https://www.dghs.mohfw.gov.in/national-mental-health-programme.php',
  },
];

export default function SupportScreen() {
  const router = useRouter();
  const [recommendations] = useState<Recommendation[]>(mockRecommendations);
  const [safetyPlanOpen, setSafetyPlanOpen] = useState(false);

  const dialNumber = (phone: string) => {
    Linking.openURL(`tel:${phone}`).catch(() => {
      // Graceful fallback for environments without a phone dialer
    });
  };

  const handleHelplinePress = (item: HelplineItem) => {
    if (item.phone) {
      dialNumber(item.phone);
    } else if (item.link) {
      Linking.openURL(item.link);
    }
  };

  const handleRecommendation = (recommendation: Recommendation) => {
    if (recommendation.phone) {
      dialNumber(recommendation.phone);
      return;
    }
    if (recommendation.route) {
      router.push(recommendation.route as any);
      return;
    }
    if (recommendation.type === 'safety') {
      setSafetyPlanOpen(true);
    }
  };

  const getRecIcon = (type: RecommendationType): keyof typeof Ionicons.glyphMap => {
    switch (type) {
      case 'counselling':
        return 'people-outline';
      case 'safety':
        return 'shield-checkmark-outline';
      case 'coping':
        return 'leaf-outline';
      case 'crisis':
        return 'alert-circle-outline';
      default:
        return 'chatbubble-ellipses-outline';
    }
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

            <View style={styles.badgeWrap}>
              <Ionicons name="shield-checkmark" size={13} color={COLORS.sage} />
              <Text style={styles.badgeText}>Confidential & 24/7</Text>
            </View>
          </View>

          {/* SCREEN TITLE MATCHING REFERENCE SCREEN 20 */}
          <View style={styles.header}>
            <Text style={styles.title}>You're not alone</Text>
            <Text style={styles.subtitle}>
              If you're in immediate danger, please reach out for help.
            </Text>
          </View>

          {/* HELPLINE CARDS LIST MATCHING REFERENCE SCREEN 20 */}
          <View style={styles.helplineList}>
            {HELPLINES.map((item) => (
              <Pressable
                key={item.id}
                onPress={() => handleHelplinePress(item)}
                style={({ pressed }) => [
                  styles.helplineCard,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel={`${item.title}, ${item.number}`}
              >
                {/* Pastel Squircle Icon Badge */}
                <View style={[styles.helplineIconBadge, { backgroundColor: item.iconBg }]}>
                  <Ionicons name={item.icon} size={20} color={item.iconColor} />
                </View>

                {/* Content */}
                <View style={styles.helplineInfo}>
                  <Text style={styles.helplineTitle}>{item.title}</Text>
                  <Text style={styles.helplineNumber}>{item.number}</Text>
                  {item.subtitle && (
                    <Text style={styles.helplineSub}>{item.subtitle}</Text>
                  )}
                </View>

                {/* Chevron */}
                <View style={styles.chevronWrap}>
                  <Ionicons name="chevron-forward" size={18} color={COLORS.navyMuted} />
                </View>
              </Pressable>
            ))}
          </View>

          {/* EXPANDABLE PERSONAL SAFETY PLAN */}
          <View style={styles.safetyCard}>
            <Pressable
              onPress={() => setSafetyPlanOpen(!safetyPlanOpen)}
              style={styles.safetyHeaderPressable}
              accessibilityRole="button"
              accessibilityLabel="Toggle safety plan"
            >
              <View style={styles.safetyIconWrap}>
                <Ionicons name="shield-checkmark-outline" size={20} color={COLORS.sage} />
              </View>
              <View style={styles.safetyTitleWrap}>
                <Text style={styles.safetyEyebrow}>PERSONAL GROUNDING</Text>
                <Text style={styles.safetyTitle}>Personal Safety Plan</Text>
                <Text style={styles.safetySub}>
                  Clear, proactive steps to take when distress feels intense.
                </Text>
              </View>
              <Ionicons
                name={safetyPlanOpen ? 'chevron-up' : 'chevron-down'}
                size={20}
                color={COLORS.navy}
              />
            </Pressable>

            {safetyPlanOpen && (
              <View style={styles.safetyStepsList}>
                <View style={styles.safetyStepItem}>
                  <View style={styles.stepNumberBadge}>
                    <Text style={styles.stepNumberText}>1</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.stepTitle}>Recognize warning signs</Text>
                    <Text style={styles.stepDesc}>
                      Notice physical cues: rapid heartbeat, muscle tension, or sudden racing thoughts.
                    </Text>
                  </View>
                </View>

                <View style={styles.safetyStepItem}>
                  <View style={styles.stepNumberBadge}>
                    <Text style={styles.stepNumberText}>2</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.stepTitle}>Use internal coping tools</Text>
                    <Text style={styles.stepDesc}>
                      Pause for 4-2-6 breathing, drink cold water, or practice the 5-4-3-2-1 sensory method.
                    </Text>
                    <Pressable
                      onPress={() => router.push('/grounding')}
                      style={styles.stepLink}
                    >
                      <Ionicons name="leaf-outline" size={13} color={COLORS.coralDark} />
                      <Text style={styles.stepLinkText}>Open Grounding Pause</Text>
                    </Pressable>
                  </View>
                </View>

                <View style={styles.safetyStepItem}>
                  <View style={styles.stepNumberBadge}>
                    <Text style={styles.stepNumberText}>3</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.stepTitle}>Reach out to a trusted contact</Text>
                    <Text style={styles.stepDesc}>
                      Send a short message to a friend, family member, or mentor: "Can we talk for a minute?"
                    </Text>
                  </View>
                </View>

                <View style={styles.safetyStepItem}>
                  <View style={styles.stepNumberBadge}>
                    <Text style={styles.stepNumberText}>4</Text>
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.stepTitle}>Make your environment safe</Text>
                    <Text style={styles.stepDesc}>
                      Step away from noise and crowds. Move to a comfortable, well-lit, private room.
                    </Text>
                  </View>
                </View>
              </View>
            )}
          </View>

          {/* DYNAMIC RECOMMENDATIONS LIST */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Recommended For You</Text>
          </View>

          <View style={styles.recommendationsList}>
            {recommendations.map((rec) => (
              <View key={rec.id} style={styles.recCard}>
                <View style={styles.recHeaderRow}>
                  <View style={styles.recIconWrap}>
                    <Ionicons name={getRecIcon(rec.type)} size={18} color={COLORS.navy} />
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text
                      style={[
                        styles.recPriorityTag,
                        rec.priority === 'Immediate' && styles.recPriorityImmediate,
                        rec.priority === 'Important' && styles.recPriorityImportant,
                      ]}
                    >
                      {rec.priority.toUpperCase()}
                    </Text>
                    <Text style={styles.recTitle}>{rec.title}</Text>
                  </View>
                </View>

                <Text style={styles.recDesc}>{rec.description}</Text>

                <Pressable
                  onPress={() => handleRecommendation(rec)}
                  style={({ pressed }) => [
                    styles.recButton,
                    rec.priority === 'Immediate' ? styles.recButtonCoral : styles.recButtonNavy,
                    pressed && styles.pressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel={rec.cta}
                >
                  <Text style={styles.recButtonText}>{rec.cta}</Text>
                  <Ionicons name="arrow-forward" size={15} color={COLORS.white} />
                </Pressable>
              </View>
            ))}
          </View>

          {/* DISCLAIMER FOOTER */}
          <View style={styles.disclaimerCard}>
            <Ionicons name="information-circle-outline" size={18} color={COLORS.navyMuted} />
            <Text style={styles.disclaimerText}>
              MEDHA is a supportive companion and does not replace medical treatment. In emergencies, call 112 or visit your nearest hospital.
            </Text>
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
  badgeWrap: {
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
  badgeText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 11,
    color: COLORS.navyMuted,
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

  /* HELPLINES */
  helplineList: {
    gap: 12,
  },
  helplineCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    ...SHADOW.subtle,
  },
  helplineIconBadge: {
    width: 46,
    height: 46,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  helplineInfo: {
    flex: 1,
  },
  helplineTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.navy,
  },
  helplineNumber: {
    fontFamily: 'Nunito-Bold',
    fontSize: 13,
    color: COLORS.navy,
    marginTop: 2,
  },
  helplineSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  chevronWrap: {
    width: 28,
    height: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },

  /* SAFETY PLAN */
  safetyCard: {
    marginTop: 22,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 16,
    ...SHADOW.subtle,
  },
  safetyHeaderPressable: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  safetyIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.sageSoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  safetyTitleWrap: {
    flex: 1,
  },
  safetyEyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 9,
    letterSpacing: 1.1,
    color: COLORS.sage,
  },
  safetyTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 16,
    color: COLORS.navy,
    marginTop: 1,
  },
  safetySub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  safetyStepsList: {
    marginTop: 16,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.05)',
    gap: 14,
  },
  safetyStepItem: {
    flexDirection: 'row',
    gap: 10,
    alignItems: 'flex-start',
  },
  stepNumberBadge: {
    width: 22,
    height: 22,
    borderRadius: 11,
    backgroundColor: COLORS.sage,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  stepNumberText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 12,
    color: COLORS.white,
  },
  stepTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 13,
    color: COLORS.navy,
  },
  stepDesc: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  stepLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 6,
  },
  stepLinkText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: COLORS.coralDark,
  },

  /* RECOMMENDATIONS */
  sectionHeader: {
    marginTop: 24,
    marginBottom: 12,
  },
  sectionTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 17,
    color: COLORS.navy,
  },
  recommendationsList: {
    gap: 12,
  },
  recCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 16,
    ...SHADOW.subtle,
  },
  recHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  recIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.creamSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  recPriorityTag: {
    fontFamily: 'Nunito-Bold',
    fontSize: 9,
    letterSpacing: 1.1,
    color: COLORS.sage,
  },
  recPriorityImportant: {
    color: COLORS.yellowDark,
  },
  recPriorityImmediate: {
    color: COLORS.coralDark,
  },
  recTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 16,
    color: COLORS.navy,
    marginTop: 1,
  },
  recDesc: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.navyMuted,
    marginTop: 8,
    marginBottom: 12,
  },
  recButton: {
    height: 44,
    borderRadius: RADIUS.pill,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingHorizontal: 18,
    alignSelf: 'flex-start',
  },
  recButtonNavy: {
    backgroundColor: COLORS.navy,
  },
  recButtonCoral: {
    backgroundColor: COLORS.coral,
  },
  recButtonText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 13,
    color: COLORS.white,
  },

  /* DISCLAIMER */
  disclaimerCard: {
    marginTop: 24,
    backgroundColor: 'rgba(0, 0, 0, 0.02)',
    borderRadius: RADIUS.card,
    padding: 14,
    flexDirection: 'row',
    gap: 10,
    alignItems: 'flex-start',
  },
  disclaimerText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.88,
  },
});
