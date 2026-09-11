import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';

function ResultCard({
  icon,
  title,
  value,
  description,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  value: string;
  description: string;
}) {
  return (
    <View style={styles.resultCard}>
      <View style={styles.resultIcon}>
        <Ionicons name={icon} size={18} color={COLORS.forest} />
      </View>
      <View style={styles.resultCopy}>
        <Text style={styles.resultTitle}>{title}</Text>
        <Text style={styles.resultValue}>{value}</Text>
        <Text style={styles.resultDescription}>{description}</Text>
      </View>
    </View>
  );
}

export default function TherapistCaseScreen() {
  const { caseId } = useLocalSearchParams<{ caseId?: string }>();

  return (
    <View style={styles.screen}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.content}
      >
        <View style={styles.top}>
          <Pressable onPress={() => router.back()} style={styles.back}>
            <Ionicons name="arrow-back" size={19} color={COLORS.deepForest} />
          </Pressable>
          <Text style={styles.topLabel}>CASE REVIEW</Text>
          <View style={styles.backPlaceholder} />
        </View>

        <View style={styles.heading}>
          <Text style={styles.eyebrow}>{caseId ?? 'MEDHA CASE'}</Text>
          <View style={styles.titleRow}>
            <Text style={styles.title}>Case review</Text>
            <View style={styles.reviewPill}>
              <Text style={styles.reviewPillText}>Human review</Text>
            </View>
          </View>
          <Text style={styles.subtitle}>
            AI-assisted context for a therapist. Final interpretation remains human.
          </Text>
        </View>

        <View style={styles.banner}>
          <Ionicons name="time-outline" size={19} color={COLORS.forest} />
          <View style={styles.bannerCopy}>
            <Text style={styles.bannerTitle}>Results availability</Text>
            <Text style={styles.bannerText}>
              Some model outputs may be unavailable until the case has enough observations.
            </Text>
          </View>
        </View>

        <Text style={styles.sectionEyebrow}>CLINICAL SUMMARY</Text>

        <ResultCard
          icon="pulse-outline"
          title="Distress"
          value="Unavailable"
          description="No validated result is available to display yet."
        />

        <ResultCard
          icon="trending-up-outline"
          title="Trend"
          value="Unavailable"
          description="Longitudinal trend requires sufficient timepoints."
        />

        <ResultCard
          icon="shield-outline"
          title="Safety"
          value="Review separately"
          description="Distress is not the same as immediate safety risk."
        />

        <View style={styles.whyCard}>
          <Text style={styles.whyEyebrow}>WHY / CONTRIBUTING FACTORS</Text>
          <Text style={styles.whyTitle}>Awaiting model evidence</Text>
          <Text style={styles.whyText}>
            This section will be populated from specialist, temporal and fusion outputs.
            It intentionally does not invent explanations when predictions are null.
          </Text>
        </View>

        <Text style={styles.sectionEyebrow}>RECENT INTERACTIONS</Text>

        <View style={styles.interactionCard}>
          <Interaction icon="chatbubble-outline" title="Chat session" value="Result unavailable" />
          <Interaction icon="mic-outline" title="Voice check-in" value="Result unavailable" />
          <Interaction icon="book-outline" title="Journal entry" value="Available when connected" />
        </View>

        <Pressable
          onPress={() => router.replace('/therapist')}
          style={styles.button}
        >
          <Text style={styles.buttonText}>Back to cases</Text>
        </Pressable>
      </ScrollView>
    </View>
  );
}

function Interaction({
  icon,
  title,
  value,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  value: string;
}) {
  return (
    <View style={styles.interactionRow}>
      <View style={styles.interactionIcon}>
        <Ionicons name={icon} size={17} color={COLORS.forest} />
      </View>
      <View style={styles.interactionCopy}>
        <Text style={styles.interactionTitle}>{title}</Text>
        <Text style={styles.interactionValue}>{value}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    paddingHorizontal: 22,
    paddingTop: 52,
    paddingBottom: 42,
  },
  top: {
    height: 42,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  back: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backPlaceholder: {
    width: 42,
  },
  topLabel: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.7,
    color: COLORS.forest,
  },
  heading: {
    marginTop: 27,
  },
  eyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.7,
    color: COLORS.forest,
  },
  titleRow: {
    marginTop: 7,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
  },
  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 35,
    color: COLORS.deepForest,
  },
  reviewPill: {
    paddingHorizontal: 9,
    paddingVertical: 5,
    borderRadius: 10,
    backgroundColor: COLORS.mist,
  },
  reviewPillText: {
    fontFamily: 'Inter-Medium',
    fontSize: 7,
    color: COLORS.forest,
  },
  subtitle: {
    marginTop: 7,
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 15,
    color: COLORS.mutedText,
  },
  banner: {
    marginTop: 20,
    padding: 15,
    borderRadius: 18,
    backgroundColor: COLORS.surfaceWarm,
    flexDirection: 'row',
    gap: 10,
    alignItems: 'flex-start',
  },
  bannerCopy: {
    flex: 1,
  },
  bannerTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.deepForest,
  },
  bannerText: {
    marginTop: 3,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 14,
    color: COLORS.mutedText,
  },
  sectionEyebrow: {
    marginTop: 27,
    marginBottom: 10,
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.7,
    color: COLORS.forest,
  },
  resultCard: {
    minHeight: 95,
    marginBottom: 9,
    padding: 15,
    borderRadius: 18,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    gap: 12,
  },
  resultIcon: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },
  resultCopy: {
    flex: 1,
  },
  resultTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.mutedText,
  },
  resultValue: {
    marginTop: 2,
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 21,
    color: COLORS.deepForest,
  },
  resultDescription: {
    marginTop: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 8,
    lineHeight: 13,
    color: COLORS.subtleText,
  },
  whyCard: {
    marginTop: 8,
    padding: 18,
    borderRadius: 20,
    backgroundColor: COLORS.deepForest,
  },
  whyEyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.6,
    color: COLORS.lichen,
  },
  whyTitle: {
    marginTop: 8,
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 25,
    color: COLORS.white,
  },
  whyText: {
    marginTop: 6,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 15,
    color: COLORS.stone,
  },
  interactionCard: {
    borderRadius: 19,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    overflow: 'hidden',
  },
  interactionRow: {
    minHeight: 62,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  interactionIcon: {
    width: 34,
    height: 34,
    borderRadius: 17,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
  },
  interactionCopy: {
    marginLeft: 11,
  },
  interactionTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.deepForest,
  },
  interactionValue: {
    marginTop: 3,
    fontFamily: 'Inter-Regular',
    fontSize: 8,
    color: COLORS.subtleText,
  },
  button: {
    marginTop: 22,
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
});
