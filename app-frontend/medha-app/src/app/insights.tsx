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

type TrendStatus = 'Improving' | 'Stable' | 'Needs Attention';

interface TrendData {
  status: TrendStatus;
  message: string;
  period: string;
  contributors: string[];
  explanation: string;
}

/*
 * MOCK BACKEND RESPONSE
 *
 * Later this entire object will come from the backend
 * explainability / insights module.
 *
 * The frontend does NOT calculate the trend.
 */
const mockTrend: TrendData = {
  status: 'Improving',
  message:
    'Your recent moments show a little more steadiness.',
  period: 'Compared with your recent activity',
  contributors: [
    'You checked in more consistently.',
    'You spent some time writing your thoughts down.',
    'Your recent conversations with MEDHA have been more regular.',
  ],
  explanation:
    'This reflection is based on changes in your recent activity over time. It looks at the moments you chose to check in, write, or talk — rather than trying to label how you feel.',
};

export default function InsightsScreen() {
  const router = useRouter();

  const [showContributors, setShowContributors] =
    useState(false);

  const [showWhy, setShowWhy] =
    useState(false);

  const trend = mockTrend;

  const getTrendIcon = () => {
    if (trend.status === 'Improving') {
      return 'leaf-outline';
    }

    if (trend.status === 'Needs Attention') {
      return 'alert-circle-outline';
    }

    return 'remove-outline';
  };

  return (
    <MedhaScreen
      eyebrow="Your patterns"
      title="A little more awareness."
      subtitle="Gentle reflections from your recent moments — not labels or diagnoses."
      onBack={() => router.back()}
    >

      {/* TREND CARD */}

      <View style={styles.trendCard}>

        <View style={styles.trendTop}>

          <View style={styles.trendIcon}>
            <Ionicons
              name={getTrendIcon()}
              size={23}
              color={COLORS.forest}
            />
          </View>

          <View style={styles.trendLabelContainer}>
            <Text style={styles.trendEyebrow}>
              YOUR WELL-BEING TREND
            </Text>

            <Text style={styles.trendStatus}>
              {trend.status}
            </Text>
          </View>

        </View>

        <Text style={styles.trendMessage}>
          {trend.message}
        </Text>

        <Text style={styles.trendPeriod}>
          {trend.period}
        </Text>

        {/* VIEW CONTRIBUTION */}

        <Pressable
          onPress={() =>
            setShowContributors(!showContributors)
          }
          style={styles.contributorButton}
        >
          <Text style={styles.contributorText}>
            View what contributed to this trend
          </Text>

          <Ionicons
            name={
              showContributors
                ? 'chevron-up'
                : 'arrow-forward'
            }
            size={16}
            color={COLORS.forest}
          />
        </Pressable>

        {showContributors && (
          <View style={styles.contributors}>

            {trend.contributors.map(
              (contributor, index) => (
                <View
                  key={index}
                  style={styles.contributorRow}
                >
                  <View style={styles.contributorDot} />

                  <Text style={styles.contributorBody}>
                    {contributor}
                  </Text>
                </View>
              )
            )}

          </View>
        )}

      </View>


      {/* WHY THIS INSIGHT */}

      <Pressable
        onPress={() => setShowWhy(!showWhy)}
        style={styles.whyCard}
      >

        <View style={styles.whyIcon}>
          <Ionicons
            name="help-circle-outline"
            size={19}
            color={COLORS.forest}
          />
        </View>

        <View style={styles.whyCopy}>
          <Text style={styles.whyTitle}>
            Why this insight?
          </Text>

          {!showWhy && (
            <Text style={styles.whyHint}>
              Understand what influenced this reflection
            </Text>
          )}
        </View>

        <Ionicons
          name={
            showWhy
              ? 'chevron-up'
              : 'chevron-down'
          }
          size={17}
          color={COLORS.mutedText}
        />

      </Pressable>

      {showWhy && (
        <View style={styles.explanation}>

          <Text style={styles.explanationTitle}>
            What influenced this?
          </Text>

          <Text style={styles.explanationBody}>
            {trend.explanation}
          </Text>

          <View style={styles.activityList}>

            <View style={styles.activity}>
              <Ionicons
                name="checkmark-circle-outline"
                size={17}
                color={COLORS.forest}
              />

              <Text style={styles.activityText}>
                Recent check-ins
              </Text>
            </View>

            <View style={styles.activity}>
              <Ionicons
                name="book-outline"
                size={17}
                color={COLORS.forest}
              />

              <Text style={styles.activityText}>
                Journal activity
              </Text>
            </View>

            <View style={styles.activity}>
              <Ionicons
                name="chatbubble-outline"
                size={17}
                color={COLORS.forest}
              />

              <Text style={styles.activityText}>
                Voice and text conversations
              </Text>
            </View>

          </View>

        </View>
      )}


      {/* WEEKLY VISUAL */}

      <Text style={styles.section}>
        THE WEEK IN GENTLE SHAPES
      </Text>

      <View style={styles.week}>

        {[
          ['M', 0.35],
          ['T', 0.55],
          ['W', 0.72],
          ['T', 0.48],
          ['F', 0.82],
          ['S', 0.62],
          ['S', 0.42],
        ].map(([day, height], index) => (

          <View
            key={`${day}-${index}`}
            style={styles.day}
          >

            <View style={styles.barTrack}>

              <View
                style={[
                  styles.bar,
                  {
                    height: `${Number(height) * 100}%`,
                  },
                ]}
              />

            </View>

            <Text style={styles.dayText}>
              {day}
            </Text>

          </View>

        ))}

      </View>


      {/* REFLECTION */}

      <View style={styles.reflection}>

        <View style={styles.reflectionIcon}>
          <Ionicons
            name="sparkles-outline"
            size={18}
            color={COLORS.forest}
          />
        </View>

        <View style={styles.reflectionCopy}>

          <Text style={styles.reflectionTitle}>
            Something worth noticing
          </Text>

          <Text style={styles.reflectionBody}>
            Your check-ins seem to happen more often
            when your days feel full.
          </Text>

        </View>

      </View>

    </MedhaScreen>
  );
}


const styles = StyleSheet.create({

  trendCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 28,
    padding: 22,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  trendTop: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  trendIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },

  trendLabelContainer: {
    marginLeft: 14,
  },

  trendEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.6,
    color: COLORS.moss,
  },

  trendStatus: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 27,
    color: COLORS.deepForest,
    marginTop: 1,
  },

  trendMessage: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 23,
    lineHeight: 28,
    color: COLORS.deepForest,
    marginTop: 20,
  },

  trendPeriod: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.mutedText,
    marginTop: 7,
  },

  contributorButton: {
    marginTop: 20,
    paddingTop: 17,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
    flexDirection: 'row',
    alignItems: 'center',
  },

  contributorText: {
    flex: 1,
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.forest,
  },

  contributors: {
    marginTop: 15,
    gap: 12,
  },

  contributorRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },

  contributorDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.moss,
    marginTop: 6,
  },

  contributorBody: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    lineHeight: 17,
    color: COLORS.mutedText,
  },

  whyCard: {
    marginTop: 14,
    minHeight: 65,
    paddingHorizontal: 16,
    paddingVertical: 13,
    backgroundColor: COLORS.surfaceWarm,
    borderRadius: 20,
    flexDirection: 'row',
    alignItems: 'center',
  },

  whyIcon: {
    width: 37,
    height: 37,
    borderRadius: 19,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },

  whyCopy: {
    flex: 1,
    marginLeft: 12,
  },

  whyTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 12,
    color: COLORS.deepForest,
  },

  whyHint: {
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    color: COLORS.mutedText,
    marginTop: 3,
  },

  explanation: {
    marginTop: 8,
    padding: 19,
    borderRadius: 20,
    backgroundColor: COLORS.mist,
  },

  explanationTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 22,
    color: COLORS.deepForest,
  },

  explanationBody: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    lineHeight: 18,
    color: COLORS.mutedText,
    marginTop: 6,
  },

  activityList: {
    marginTop: 14,
    gap: 10,
  },

  activity: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
  },

  activityText: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.text,
  },

  section: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 1.8,
    color: COLORS.forest,
    marginTop: 32,
    marginBottom: 16,
  },

  week: {
    height: 150,
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    paddingHorizontal: 8,
  },

  day: {
    alignItems: 'center',
    gap: 8,
  },

  barTrack: {
    height: 115,
    width: 24,
    borderRadius: 12,
    backgroundColor: COLORS.stone,
    justifyContent: 'flex-end',
    overflow: 'hidden',
  },

  bar: {
    width: '100%',
    backgroundColor: COLORS.forest,
    borderRadius: 12,
  },

  dayText: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    color: COLORS.mutedText,
  },

  reflection: {
    marginTop: 30,
    padding: 20,
    backgroundColor: COLORS.surfaceWarm,
    borderRadius: 22,
    flexDirection: 'row',
    gap: 13,
  },

  reflectionIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },

  reflectionCopy: {
    flex: 1,
  },

  reflectionTitle: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 21,
    color: COLORS.deepForest,
  },

  reflectionBody: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    lineHeight: 17,
    color: COLORS.mutedText,
    marginTop: 5,
  },

});