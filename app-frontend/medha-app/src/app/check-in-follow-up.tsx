import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';

import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';
import { checkinService } from '../services/api';

const DEFAULT_TOPICS = [
  'Work / Studies',
  'Relationships',
  'Health',
  'Self-doubt',
  'Loneliness',
  'Something else',
];

const moodScoreMap: Record<string, number> = {
  'Great': 5,
  'Good': 4,
  'Okay': 3,
  'Low': 2,
  'Anxious': 2,
  'Overwhelmed': 1,
};

export default function CheckInFollowUpScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ mood?: string }>();

  const [loading, setLoading] = useState(true);
  const [checkinData, setCheckinData] = useState<any>(null);
  const [currentQuestion, setCurrentQuestion] = useState<any>(null);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  // Initialize or fetch the active Question Engine session
  useEffect(() => {
    let mounted = true;
    checkinService.startCheckin()
      .then((chk) => {
        if (mounted && chk) {
          setCheckinData(chk);
          // Find the active question to display
          const activeQ = (chk.questions || []).find(
            (q: any) => q.question_id === chk.current_question_id || q.answer_status === 'pending'
          );
          if (activeQ) {
            setCurrentQuestion(activeQ);
          } else if (chk.questions && chk.questions.length > 0) {
            setCurrentQuestion(chk.questions[0]);
          }
          setLoading(false);
        }
      })
      .catch((err) => {
        console.warn('Could not fetch adaptive check-in question:', err);
        if (mounted) setLoading(false);
      });
    return () => { mounted = false; };
  }, []);

  const handleContinue = async () => {
    if (!selectedOption || submitting) return;
    setSubmitting(true);

    try {
      const moodVal = params.mood || 'Okay';
      const numericMood = moodScoreMap[moodVal] || 3;

      if (checkinData && checkinData.id && currentQuestion) {
        // Submit response to Question Engine
        const answerPayload: Record<string, any> = {
          value: selectedOption,
          mood: moodVal,
          mood_score: numericMood,
        };

        const res = await checkinService.submitAnswer(checkinData.id, answerPayload);

        if (res && res.next_question) {
          // Present next adaptive question in sequence
          setCurrentQuestion(res.next_question);
          setSelectedOption(null);
          setSubmitting(false);
          return;
        } else {
          // All questions answered, check-in completed! Progress to Voice
          setSubmitting(false);
          router.push({
            pathname: '/voice' as any,
            params: {
              mood: params.mood ?? '',
              topic: selectedOption ?? '',
            },
          });
          return;
        }
      }
    } catch (err) {
      console.warn('Check-in answer sync error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // Determine display options: prefer question options from Question Engine, fallback to default topics
  const displayOptions = currentQuestion?.options && currentQuestion.options.length > 0
    ? currentQuestion.options
    : DEFAULT_TOPICS;

  const displayTitle = currentQuestion?.question_text || "What’s been taking up most of your mind?";
  const displayDomain = currentQuestion?.domain || "CLINICAL ADAPTIVE CHECK-IN";

  return (
    <MedhaScreen
      eyebrow={displayDomain}
      title={displayTitle}
      subtitle={
        params.mood
          ? `You noted feeling ${params.mood.toLowerCase()}. Your answers help tailor support.`
          : 'Choose the option that feels closest to your experience right now.'
      }
      onBack={() => router.back()}
    >
      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator color={COLORS.forest} size="large" />
          <Text style={styles.loadingText}>Fetching your personalized check-in question...</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {displayOptions.map((opt: string) => {
            const active = selectedOption === opt;

            return (
              <Pressable
                key={opt}
                onPress={() => setSelectedOption(opt)}
                style={({ pressed }) => [
                  styles.topic,
                  active && styles.topicActive,
                  pressed && styles.topicPressed,
                ]}
              >
                <View style={styles.topicContent}>
                  <View
                    style={[
                      styles.radio,
                      active && styles.radioActive,
                    ]}
                  >
                    {active && <View style={styles.radioDot} />}
                  </View>

                  <Text
                    style={[
                      styles.topicText,
                      active && styles.topicTextActive,
                    ]}
                  >
                    {opt}
                  </Text>
                </View>

                <Ionicons
                  name={active ? 'checkmark-circle' : 'chevron-forward'}
                  size={18}
                  color={active ? COLORS.forest : COLORS.mutedText}
                />
              </Pressable>
            );
          })}
        </View>
      )}

      <Pressable
        disabled={!selectedOption || submitting}
        onPress={handleContinue}
        style={({ pressed }) => [
          styles.next,
          (!selectedOption || submitting) && styles.nextDisabled,
          pressed && selectedOption && styles.nextPressed,
        ]}
      >
        {submitting ? (
          <ActivityIndicator color={COLORS.white} size="small" />
        ) : (
          <>
            <Text style={styles.nextText}>
              {currentQuestion ? 'Submit & Continue' : 'Continue'}
            </Text>
            <Ionicons
              name="mic-outline"
              size={18}
              color={COLORS.white}
            />
          </>
        )}
      </Pressable>

      <Text style={styles.hint}>
        Next, MEDHA will listen. You can speak freely for a moment.
      </Text>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    paddingVertical: 50,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 14,
  },

  loadingText: {
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.mutedText,
    textAlign: 'center',
  },

  list: {
    gap: 9,
    marginTop: 8,
  },

  topic: {
    minHeight: 56,
    paddingHorizontal: 16,
    borderRadius: 17,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  topicActive: {
    borderColor: COLORS.forest,
    backgroundColor: COLORS.surfaceWarm,
  },

  topicPressed: {
    opacity: 0.82,
    transform: [{ scale: 0.99 }],
  },

  topicContent: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },

  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },

  radioActive: {
    borderColor: COLORS.forest,
  },

  radioDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: COLORS.forest,
  },

  topicText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.text,
  },

  topicTextActive: {
    fontFamily: 'Inter-Medium',
    color: COLORS.deepForest,
  },

  next: {
    marginTop: 22,
    height: 54,
    borderRadius: 27,
    backgroundColor: COLORS.forest,
    flexDirection: 'row',
    gap: 9,
    alignItems: 'center',
    justifyContent: 'center',
  },

  nextDisabled: {
    backgroundColor: COLORS.lichen,
  },

  nextPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.98 }],
  },

  nextText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },

  hint: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    lineHeight: 15,
    textAlign: 'center',
    color: COLORS.mutedText,
    marginTop: 13,
  },
});
