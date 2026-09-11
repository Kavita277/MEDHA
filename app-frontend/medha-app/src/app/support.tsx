import React, { useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

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
}

/*
 * MOCK RECOMMENDATION ENGINE RESPONSE
 *
 * Eventually the backend Recommendation Engine
 * will return this structure.
 *
 * The frontend only renders what it receives.
 */
const mockRecommendations: Recommendation[] = [
  {
    id: '1',
    type: 'counselling',
    priority: 'Recommended',
    title: 'Talk to a counsellor',
    description:
      'A trained person can give you space to talk through what has been happening.',
    cta: 'Talk to a Counsellor',
  },

  {
    id: '2',
    type: 'coping',
    priority: 'Recommended',
    title: 'Take a grounding pause',
    description:
      'Try a short guided exercise to bring your attention back to the present moment.',
    cta: 'Start Exercise',
    route: '/grounding',
  },

  {
    id: '3',
    type: 'self-help',
    priority: 'Recommended',
    title: 'A quieter conversation',
    description:
      'If speaking to someone feels difficult right now, you can start by talking with MEDHA.',
    cta: 'Talk with MEDHA',
    route: '/chat',
  },

  {
    id: '4',
    type: 'safety',
    priority: 'Important',
    title: 'Safety support',
    description:
      'If something around you feels unsafe, consider moving somewhere safer and reaching someone you trust.',
    cta: 'View Safety Support',
  },

  {
    id: '5',
    type: 'crisis',
    priority: 'Immediate',
    title: 'Immediate help',
    description:
      'If you are in immediate danger or feel unable to keep yourself safe, seek emergency support now.',
    cta: 'Get Emergency Help',
  },
];

export default function SupportScreen() {
  const router = useRouter();

  const [recommendations] =
    useState<Recommendation[]>(
      mockRecommendations
    );

  const getIcon = (
    type: RecommendationType
  ): keyof typeof Ionicons.glyphMap => {
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

  const getIconBackground = (
    priority: RecommendationPriority
  ) => {
    if (priority === 'Immediate') {
      return '#EBD6CC';
    }

    if (priority === 'Important') {
      return COLORS.sand;
    }

    return COLORS.mist;
  };

  const handleRecommendation = (
    recommendation: Recommendation
  ) => {
    if (recommendation.route) {
      router.push(recommendation.route as any);
    }
  };

  return (
    <MedhaScreen
      eyebrow="Support"
      title="You deserve real support, too."
      subtitle="MEDHA can accompany you, but it should never replace people or professional care."
      onBack={() => router.back()}
    >

      {/* DYNAMIC RESOURCES */}

      <View style={styles.list}>

        {recommendations.map(
          (recommendation) => (

            <View
              key={recommendation.id}
              style={[
                styles.card,
                recommendation.priority ===
                  'Immediate' &&
                  styles.immediateCard,
              ]}
            >

              <View style={styles.cardTop}>

                <View
                  style={[
                    styles.icon,
                    {
                      backgroundColor:
                        getIconBackground(
                          recommendation.priority
                        ),
                    },
                  ]}
                >
                  <Ionicons
                    name={getIcon(
                      recommendation.type
                    )}
                    size={21}
                    color={COLORS.forest}
                  />
                </View>

                <View style={styles.heading}>

                  <Text
                    style={[
                      styles.priority,
                      recommendation.priority ===
                        'Immediate' &&
                        styles.immediatePriority,
                    ]}
                  >
                    {recommendation.priority.toUpperCase()}
                  </Text>

                  <Text style={styles.title}>
                    {recommendation.title}
                  </Text>

                </View>

              </View>


              <Text style={styles.description}>
                {recommendation.description}
              </Text>


              <Pressable
                onPress={() =>
                  handleRecommendation(
                    recommendation
                  )
                }
                style={[
                  styles.cta,
                  recommendation.priority ===
                    'Immediate' &&
                    styles.immediateCta,
                ]}
              >

                <Text
                  style={[
                    styles.ctaText,
                    recommendation.priority ===
                      'Immediate' &&
                      styles.immediateCtaText,
                  ]}
                >
                  {recommendation.cta}
                </Text>

                <Ionicons
                  name="arrow-forward"
                  size={15}
                  color={
                    recommendation.priority ===
                    'Immediate'
                      ? COLORS.white
                      : COLORS.forest
                  }
                />

              </Pressable>

            </View>

          )
        )}

      </View>


      {/* SUPPORT NOTE */}

      <View style={styles.note}>

        <Ionicons
          name="heart-outline"
          size={17}
          color={COLORS.forest}
        />

        <Text style={styles.noteText}>
          Recommendations are shown based on
          information provided by connected MEDHA
          services. They are intended to help you
          find appropriate support.
        </Text>

      </View>

    </MedhaScreen>
  );
}


const styles = StyleSheet.create({

  list: {
    gap: 12,
  },

  card: {
    padding: 19,
    borderRadius: 23,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  immediateCard: {
    backgroundColor: '#F6EDE7',
    borderColor: COLORS.clay,
  },

  cardTop: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  icon: {
    width: 47,
    height: 47,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },

  heading: {
    flex: 1,
    marginLeft: 13,
  },

  priority: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.5,
    color: COLORS.moss,
  },

  immediatePriority: {
    color: COLORS.clay,
  },

  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 23,
    color: COLORS.deepForest,
    marginTop: 1,
  },

  description: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    lineHeight: 18,
    color: COLORS.mutedText,
    marginTop: 16,
  },

  cta: {
    marginTop: 17,
    minHeight: 45,
    borderRadius: 23,
    backgroundColor: COLORS.mist,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },

  immediateCta: {
    backgroundColor: COLORS.clay,
  },

  ctaText: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.forest,
  },

  immediateCtaText: {
    color: COLORS.white,
  },

  note: {
    marginTop: 27,
    padding: 17,
    borderRadius: 20,
    backgroundColor: COLORS.surfaceWarm,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },

  noteText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 15,
    color: COLORS.mutedText,
  },

});