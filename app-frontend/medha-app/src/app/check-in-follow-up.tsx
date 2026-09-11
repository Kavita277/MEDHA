import { Ionicons } from '@expo/vector-icons';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

const topics = [
  'Work / Studies',
  'Relationships',
  'Health',
  'Self-doubt',
  'Loneliness',
  'Something else',
];

export default function CheckInFollowUpScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ mood?: string }>();

  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);

  const handleContinue = () => {
    if (!selectedTopic) return;

    router.push({
      pathname: '/voice',
      params: {
        mood: params.mood ?? '',
        topic: selectedTopic,
      },
    });
  };

  return (
    <MedhaScreen
      eyebrow="Check-in"
      title="What’s been taking up most of your mind?"
      subtitle={
        params.mood
          ? `You chose ${params.mood.toLowerCase()}. You can tell me a little more.`
          : 'Choose what feels closest right now.'
      }
      onBack={() => router.back()}
    >
      <View style={styles.list}>
        {topics.map((topic) => {
          const active = selectedTopic === topic;

          return (
            <Pressable
              key={topic}
              onPress={() => setSelectedTopic(topic)}
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
                  {topic}
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

      <Pressable
        disabled={!selectedTopic}
        onPress={handleContinue}
        style={({ pressed }) => [
          styles.next,
          !selectedTopic && styles.nextDisabled,
          pressed && selectedTopic && styles.nextPressed,
        ]}
      >
        <Text style={styles.nextText}>Continue</Text>

        <Ionicons
          name="mic-outline"
          size={18}
          color={COLORS.white}
        />
      </Pressable>

      <Text style={styles.hint}>
        Next, MEDHA will listen. You can speak freely for a moment.
      </Text>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  list: {
    gap: 9,
    marginTop: 8,
  },

  topic: {
    minHeight: 58,
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
    marginTop: 18,
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