import React, { useState } from 'react';
import {
  Linking,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { MedhaCard, CardVariant } from '../components/medha-card';
import { MedhaButton } from '../components/medha-button';
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

export default function SupportScreen() {
  const router = useRouter();
  const [recommendations] = useState<Recommendation[]>(mockRecommendations);
  const [safetyPlanOpen, setSafetyPlanOpen] = useState(false);

  const dialNumber = (phone: string) => {
    Linking.openURL(`tel:${phone}`).catch(() => {
      // Graceful fallback for web/devices without phone handler
    });
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

  const getIcon = (type: RecommendationType): keyof typeof Ionicons.glyphMap => {
    switch (type) {
      case 'counselling':
        return 'people-outline';
      case 'safety':
        return 'shield-checkmark-outline';
      case 'financial':
        return 'wallet-outline';
      case 'rehabilitation':
        return 'fitness-outline';
      case 'legal':
        return 'document-text-outline';
      case 'coping':
        return 'leaf-outline';
      case 'crisis':
        return 'alert-circle-outline';
      default:
        return 'book-outline';
    }
  };

  const getCardVariant = (type: RecommendationType, priority: RecommendationPriority): CardVariant => {
    if (priority === 'Immediate') return 'pink';
    if (priority === 'Important') return 'yellow';
    if (type === 'coping') return 'sage';
    if (type === 'self-help') return 'peach';
    return 'glass';
  };

  return (
    <MedhaScreen
      eyebrow="Human Support"
      title="You deserve real support, too."
      subtitle="MEDHA can accompany you, but it should never replace people or professional care."
      onBack={() => router.back()}
      withBackground={true}
    >
      <View style={styles.container}>
        {/* 1. IMMEDIATE EMERGENCY BANNER */}
        <View style={styles.emergencyCard}>
          <View style={styles.emergencyHeader}>
            <View style={styles.emergencyBadge}>
              <Ionicons name="call" size={14} color={COLORS.white} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.emergencyEyebrow}>IMMEDIATE DANGER & MEDICAL HELP</Text>
              <Text style={styles.emergencyTitle}>National Emergency Services</Text>
            </View>
          </View>
          <Text style={styles.emergencyDescription}>
            If you or someone around you is in immediate danger or facing an acute medical crisis, contact national emergency responders.
          </Text>
          <Pressable
            onPress={() => dialNumber('112')}
            style={({ pressed }) => [
              styles.emergencyButton,
              pressed && styles.emergencyButtonPressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Call 112 National Emergency"
          >
            <Ionicons name="call" size={16} color={COLORS.white} />
            <Text style={styles.emergencyButtonText}>Call 112 (Emergency Hotline)</Text>
          </Pressable>
        </View>

        {/* 2. 24/7 CRISIS & MENTAL HEALTH HELPLINES */}
        <View style={styles.sectionHeader}>
          <Ionicons name="heart" size={16} color={COLORS.coralDark} />
          <Text style={styles.sectionTitle}>Free & Confidential Helplines</Text>
        </View>

        <View style={styles.helplineList}>
          {/* Tele-MANAS */}
          <MedhaCard variant="peach" style={styles.helplineCard}>
            <View style={styles.helplineTop}>
              <View style={styles.helplineIconWrap}>
                <Ionicons name="chatbubbles" size={20} color={COLORS.coralDark} />
              </View>
              <View style={{ flex: 1 }}>
                <View style={styles.helplineBadgeRow}>
                  <Text style={styles.helplineBadge}>GOVT. OF INDIA • 24/7 FREE</Text>
                </View>
                <Text style={styles.helplineName}>Tele-MANAS</Text>
                <Text style={styles.helplineSub}>
                  National Tele-Mental Health Programme. Available in 20+ regional languages.
                </Text>
              </View>
            </View>
            <Pressable
              onPress={() => dialNumber('14416')}
              style={({ pressed }) => [
                styles.helplineCallBtn,
                pressed && styles.helplineCallBtnPressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Call Tele-MANAS at 14416"
            >
              <Ionicons name="call-outline" size={16} color={COLORS.navy} />
              <Text style={styles.helplineCallText}>Call 14416 (Toll-Free)</Text>
            </Pressable>
          </MedhaCard>

          {/* KIRAN Helpline */}
          <MedhaCard variant="glass" style={styles.helplineCard}>
            <View style={styles.helplineTop}>
              <View style={[styles.helplineIconWrap, { backgroundColor: COLORS.yellowSoft, borderColor: COLORS.yellow }]}>
                <Ionicons name="shield-checkmark" size={20} color={COLORS.yellowDark} />
              </View>
              <View style={{ flex: 1 }}>
                <View style={styles.helplineBadgeRow}>
                  <Text style={[styles.helplineBadge, { color: COLORS.yellowDark }]}>
                    MINISTRY OF SOCIAL JUSTICE • 24/7
                  </Text>
                </View>
                <Text style={styles.helplineName}>KIRAN Helpline</Text>
                <Text style={styles.helplineSub}>
                  Mental health rehabilitation, crisis resolution, and anxiety support.
                </Text>
              </View>
            </View>
            <Pressable
              onPress={() => dialNumber('18005990019')}
              style={({ pressed }) => [
                styles.helplineCallBtn,
                pressed && styles.helplineCallBtnPressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Call KIRAN Helpline at 1800-599-0019"
            >
              <Ionicons name="call-outline" size={16} color={COLORS.navy} />
              <Text style={styles.helplineCallText}>Call 1800-599-0019</Text>
            </Pressable>
          </MedhaCard>
        </View>

        {/* 3. SAFETY PLAN (Expandable Card) */}
        <MedhaCard
          variant={safetyPlanOpen ? 'sage' : 'glass'}
          style={styles.safetyCard}
          onPress={() => setSafetyPlanOpen(!safetyPlanOpen)}
          accessibilityLabel="Toggle Safety Plan details"
        >
          <View style={styles.safetyHeader}>
            <View style={styles.safetyIcon}>
              <Ionicons name="shield-checkmark-outline" size={22} color={COLORS.sage} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.safetyEyebrow}>PERSONAL GROUNDING</Text>
              <Text style={styles.safetyTitle}>Personal Safety Plan</Text>
              <Text style={styles.safetySubtitle}>
                Clear, proactive steps to take when distress feels intense.
              </Text>
            </View>
            <Ionicons
              name={safetyPlanOpen ? 'chevron-up' : 'chevron-down'}
              size={20}
              color={COLORS.navy}
            />
          </View>

          {safetyPlanOpen && (
            <View style={styles.safetyDetails}>
              <View style={styles.safetyStep}>
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

              <View style={styles.safetyStep}>
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

              <View style={styles.safetyStep}>
                <View style={styles.stepNumberBadge}>
                  <Text style={styles.stepNumberText}>3</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.stepTitle}>Reach out to a trusted contact</Text>
                  <Text style={styles.stepDesc}>
                    Send a short message to a friend, family member, or trusted mentor: "Can we talk for a minute?"
                  </Text>
                </View>
              </View>

              <View style={styles.safetyStep}>
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
        </MedhaCard>

        {/* 4. DYNAMIC RECOMMENDATIONS */}
        <View style={styles.sectionHeader}>
          <Ionicons name="compass" size={16} color={COLORS.coralDark} />
          <Text style={styles.sectionTitle}>Recommended For You</Text>
        </View>

        <View style={styles.list}>
          {recommendations.map((recommendation) => (
            <MedhaCard
              key={recommendation.id}
              variant={getCardVariant(recommendation.type, recommendation.priority)}
              style={styles.card}
            >
              <View style={styles.cardTop}>
                <View style={styles.iconCircle}>
                  <Ionicons
                    name={getIcon(recommendation.type)}
                    size={22}
                    color={COLORS.navy}
                  />
                </View>

                <View style={styles.heading}>
                  <View style={styles.priorityRow}>
                    <Text
                      style={[
                        styles.priority,
                        recommendation.priority === 'Immediate' && styles.immediatePriority,
                        recommendation.priority === 'Important' && styles.importantPriority,
                      ]}
                    >
                      {recommendation.priority.toUpperCase()}
                    </Text>
                  </View>
                  <Text style={styles.cardTitle}>{recommendation.title}</Text>
                </View>
              </View>

              <Text style={styles.description}>{recommendation.description}</Text>

              <MedhaButton
                title={recommendation.cta}
                onPress={() => handleRecommendation(recommendation)}
                variant={recommendation.priority === 'Immediate' ? 'coral' : 'pill'}
                size="md"
                icon="arrow-forward"
                style={styles.cardButton}
              />
            </MedhaCard>
          ))}
        </View>

        {/* 5. SUPPORT NOTE & DISCLAIMER */}
        <View style={styles.note}>
          <Ionicons name="shield-checkmark" size={18} color={COLORS.sage} />
          <Text style={styles.noteText}>
            Recommendations are shown based on information provided by connected MEDHA services.
            They are intended to help you find appropriate human support. They are not medical diagnoses.
          </Text>
        </View>
      </View>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
    paddingBottom: 20,
  },
  emergencyCard: {
    padding: 18,
    borderRadius: RADIUS.card,
    backgroundColor: '#FFF0F0',
    borderWidth: 1.5,
    borderColor: '#FFC7C7',
    ...SHADOW.card,
  },
  emergencyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
  },
  emergencyBadge: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: '#E53E3E',
    alignItems: 'center',
    justifyContent: 'center',
  },
  emergencyEyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.2,
    color: '#C53030',
  },
  emergencyTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 18,
    color: COLORS.navy,
  },
  emergencyDescription: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 19,
    color: COLORS.navyMuted,
    marginBottom: 14,
  },
  emergencyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#E53E3E',
    paddingVertical: 12,
    borderRadius: RADIUS.pill,
    ...SHADOW.glow,
  },
  emergencyButtonPressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.9,
  },
  emergencyButtonText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 14,
    color: COLORS.white,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 8,
    marginBottom: 2,
    paddingLeft: 4,
  },
  sectionTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 18,
    color: COLORS.navy,
  },
  helplineList: {
    gap: 12,
  },
  helplineCard: {
    padding: 16,
  },
  helplineTop: {
    flexDirection: 'row',
    gap: 12,
  },
  helplineIconWrap: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.pinkSoft,
    borderWidth: 1,
    borderColor: COLORS.pink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  helplineBadgeRow: {
    marginBottom: 4,
  },
  helplineBadge: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1,
    color: COLORS.coralDark,
  },
  helplineName: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 17,
    color: COLORS.navy,
  },
  helplineSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  helplineCallBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: RADIUS.pill,
    paddingVertical: 10,
    marginTop: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 201, 172, 0.6)',
    ...SHADOW.card,
  },
  helplineCallBtnPressed: {
    backgroundColor: COLORS.creamSecondary,
    transform: [{ scale: 0.98 }],
  },
  helplineCallText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 13,
    color: COLORS.navy,
  },
  safetyCard: {
    padding: 16,
  },
  safetyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  safetyIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.sageSoft,
    borderWidth: 1,
    borderColor: COLORS.sage,
    alignItems: 'center',
    justifyContent: 'center',
  },
  safetyEyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1,
    color: COLORS.sage,
  },
  safetyTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 17,
    color: COLORS.navy,
  },
  safetySubtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  safetyDetails: {
    marginTop: 16,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: 'rgba(127, 168, 138, 0.25)',
    gap: 14,
  },
  safetyStep: {
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
    fontSize: 14,
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
  list: {
    gap: 12,
  },
  card: {
    padding: 16,
  },
  cardTop: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconCircle: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 201, 172, 0.4)',
    ...SHADOW.card,
  },
  heading: {
    flex: 1,
  },
  priorityRow: {
    marginBottom: 2,
  },
  priority: {
    fontFamily: 'Nunito-Bold',
    fontSize: 9,
    letterSpacing: 1.2,
    color: COLORS.sage,
  },
  importantPriority: {
    color: COLORS.yellowDark,
  },
  immediatePriority: {
    color: COLORS.coralDark,
  },
  cardTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 18,
    color: COLORS.navy,
  },
  description: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 19,
    color: COLORS.navyMuted,
    marginTop: 10,
    marginBottom: 14,
  },
  cardButton: {
    marginTop: 4,
  },
  note: {
    marginTop: 10,
    padding: 16,
    borderRadius: RADIUS.card,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    borderWidth: 1,
    borderColor: 'rgba(255, 201, 172, 0.5)',
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    ...SHADOW.card,
  },
  noteText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
  },
});
