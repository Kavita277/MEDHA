import React, { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW, TOP_HEADER_PADDING } from '../constants/theme';
import { MedhaScreenBackground } from '../components/medha-screen-background';

const moods = [
  { label: 'Calm', emoji: '🌿', color: COLORS.greenSoft, border: COLORS.green },
  { label: 'Grateful', emoji: '🌸', color: COLORS.pinkSoft, border: COLORS.pink },
  { label: 'Stressed', emoji: '⚡', color: COLORS.yellowSoft, border: COLORS.yellow },
  { label: 'Hopeful', emoji: '☀️', color: COLORS.blueSoft, border: COLORS.blue },
  { label: 'Tired', emoji: '🌙', color: '#F3EFFF', border: COLORS.lavender },
  { label: 'Unsure', emoji: '💭', color: COLORS.creamSecondary, border: COLORS.peach },
];

export default function JournalScreen() {
  const router = useRouter();
  const [text, setText] = useState('');
  const [mood, setMood] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  // Dynamic formatted date
  const today = new Date();
  const dateString = today.toLocaleDateString('en-US', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => {
      router.push('/home');
    }, 600);
  };

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safeArea}>
        <KeyboardAvoidingView
        style={styles.keyboard}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
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

            <Pressable
              onPress={() => router.push('/mood-calendar')}
              style={({ pressed }) => [
                styles.dateBadge,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="View Mood Calendar"
            >
              <Ionicons name="calendar-outline" size={13} color={COLORS.coralDark} />
              <Text style={styles.dateText}>{dateString}</Text>
            </Pressable>
          </View>

          {/* SCREEN HEADER */}
          <View style={styles.header}>
            <Text style={styles.title}>A space for your thoughts</Text>
            <Text style={styles.subtitle}>
              Write freely. This journal is private to you.
            </Text>
          </View>

          {/* WRITING CARD CONTAINER */}
          <View style={styles.paperCard}>
            {/* PROMPT BUBBLE */}
            <View style={styles.promptRow}>
              <View style={styles.sparkleCircle}>
                <Ionicons name="sparkles" size={14} color={COLORS.coralDark} />
              </View>
              <Text style={styles.promptText}>What’s on your mind today?</Text>
            </View>

            {/* TEXT INPUT AREA */}
            <TextInput
              value={text}
              onChangeText={setText}
              multiline
              placeholder="I felt a bit overwhelmed but I'm proud that I reached out for support..."
              placeholderTextColor={COLORS.subtleText}
              style={styles.input}
              textAlignVertical="top"
              accessibilityLabel="Journal entry text input"
            />

            {/* FOOTER BAR WITH PRIVACY STATUS */}
            <View style={styles.paperFooter}>
              <View style={styles.privateTag}>
                <Ionicons name="shield-checkmark-outline" size={12} color={COLORS.sage} />
                <Text style={styles.privateText}>End-to-end encrypted & local</Text>
              </View>
              {text.trim().length > 0 && (
                <Text style={styles.charCount}>{text.trim().split(/\s+/).length} words</Text>
              )}
            </View>
          </View>

          {/* MOOD SELECTION SECTION */}
          <View style={styles.moodSection}>
            <Text style={styles.sectionHeading}>HOW ARE YOU FEELING RIGHT NOW?</Text>

            <View style={styles.moodGrid}>
              {moods.map((item) => {
                const active = mood === item.label;

                return (
                  <Pressable
                    key={item.label}
                    onPress={() => setMood(active ? null : item.label)}
                    style={({ pressed }) => [
                      styles.moodChip,
                      { backgroundColor: item.color, borderColor: item.border },
                      active && styles.moodChipActive,
                      pressed && styles.pressed,
                    ]}
                    accessibilityRole="button"
                    accessibilityLabel={`Select mood ${item.label}`}
                    accessibilityState={{ selected: active }}
                  >
                    <Text style={styles.moodEmoji}>{item.emoji}</Text>
                    <Text
                      style={[
                        styles.moodLabel,
                        active && styles.moodLabelActive,
                      ]}
                    >
                      {item.label}
                    </Text>
                    {active && (
                      <View style={styles.activeDot}>
                        <Ionicons name="checkmark" size={11} color={COLORS.white} />
                      </View>
                    )}
                  </Pressable>
                );
              })}
            </View>
          </View>

          {/* SAVE BUTTON */}
          <View style={styles.saveWrapper}>
            <Pressable
              onPress={handleSave}
              disabled={saved}
              style={({ pressed }) => [
                styles.saveButton,
                saved && styles.saveButtonSuccess,
                pressed && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Save entry"
            >
              <Text style={styles.saveButtonText}>
                {saved ? 'Saved to Your Space' : 'Save Entry'}
              </Text>
              <Ionicons
                name={saved ? 'checkmark-circle' : 'arrow-forward'}
                size={18}
                color={COLORS.white}
              />
            </Pressable>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: COLORS.porcelain,
  },
  safeArea: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  keyboard: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: TOP_HEADER_PADDING,
    paddingBottom: 40,
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
  dateBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  dateText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navy,
  },

  /* HEADER */
  header: {
    marginTop: 14,
    marginBottom: 18,
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

  /* WRITING PAPER CARD */
  paperCard: {
    minHeight: 250,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 18,
    ...SHADOW.subtle,
  },
  promptRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingBottom: 12,
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 0, 0, 0.04)',
  },
  sparkleCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: COLORS.creamSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  promptText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 15,
    color: COLORS.navy,
  },
  input: {
    minHeight: 160,
    fontFamily: 'Nunito-Regular',
    fontSize: 15,
    lineHeight: 23,
    color: COLORS.navy,
    paddingTop: 4,
  },
  paperFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0, 0, 0, 0.04)',
    marginTop: 8,
  },
  privateTag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  privateText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 11,
    color: COLORS.navyMuted,
  },
  charCount: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.subtleText,
  },

  /* MOOD SECTION */
  moodSection: {
    marginTop: 22,
  },
  sectionHeading: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.2,
    color: COLORS.coralDark,
    marginBottom: 12,
  },
  moodGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  moodChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: RADIUS.pill,
    borderWidth: 1,
    gap: 7,
    ...SHADOW.subtle,
  },
  moodChipActive: {
    backgroundColor: COLORS.navy,
    borderColor: COLORS.navy,
  },
  moodEmoji: {
    fontSize: 14,
  },
  moodLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: COLORS.navy,
  },
  moodLabelActive: {
    color: COLORS.white,
    fontFamily: 'Fredoka-Medium',
  },
  activeDot: {
    width: 15,
    height: 15,
    borderRadius: 7.5,
    backgroundColor: COLORS.coral,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 2,
  },

  /* SAVE BUTTON */
  saveWrapper: {
    marginTop: 26,
  },
  saveButton: {
    height: 52,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.navy,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    ...SHADOW.dock,
  },
  saveButtonSuccess: {
    backgroundColor: '#3E9257',
  },
  saveButtonText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.white,
    letterSpacing: 0.3,
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.88,
  },
});
