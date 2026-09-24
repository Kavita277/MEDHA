import React, { useState } from 'react';
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
import Svg, { Circle, Path } from 'react-native-svg';

import { MedhaBottomNav } from '../components/medha-bottom-nav';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

export type MoodType = 'happy' | 'calm' | 'thoughtful' | 'stressed' | 'tired';

export interface DayMoodRecord {
  day: number;
  mood?: MoodType;
  note?: string;
}

// Local mock data model for September 2025 (designed for future API swap)
const SEPTEMBER_MOODS: Record<number, DayMoodRecord> = {
  1: { day: 1, mood: 'calm', note: 'Took a morning walk in the park.' },
  2: { day: 2, mood: 'happy', note: 'Had lunch with a close friend.' },
  3: { day: 3, mood: 'stressed', note: 'Busy workday with deadlines.' },
  4: { day: 4, mood: 'thoughtful', note: 'Reflected in the journal.' },
  5: { day: 5, mood: 'happy', note: 'Productive and feeling light.' },
  6: { day: 6, mood: 'calm', note: 'Slow Saturday morning.' },
  7: { day: 7, mood: 'happy', note: 'Felt very grateful today.' },
  8: { day: 8, mood: 'calm', note: 'Quiet evening reading.' },
  9: { day: 9, mood: 'stressed', note: 'Felt a bit overwhelmed.' },
  10: { day: 10, mood: 'tired', note: 'Long hours, went to bed early.' },
  11: { day: 11, mood: 'happy', note: 'Good conversation with mom.' },
  12: { day: 12, mood: 'calm', note: 'Practiced 4-2-6 breathing.' },
  13: { day: 13, mood: 'happy', note: 'Relaxing weekend walk.' },
  14: { day: 14, mood: 'calm', note: 'Peaceful afternoon.' },
  15: { day: 15, mood: 'thoughtful', note: 'Thinking about next steps.' },
  16: { day: 16, mood: 'happy', note: 'Felt energised and focused.' },
  17: { day: 17, mood: 'happy', note: 'Celebrated a small milestone.' },
  18: { day: 18, mood: 'calm', note: 'Gentle check-in completed.' },
  19: { day: 19, mood: 'tired', note: 'Needed some extra rest.' },
  20: { day: 20, mood: 'happy', note: 'Lovely sunny afternoon.' },
  21: { day: 21, mood: 'happy', note: 'Feeling centered and well.' },
  22: { day: 22, mood: 'calm', note: 'Deep breathing grounding.' },
  23: { day: 23, mood: 'stressed', note: 'Tight schedule today.' },
  24: { day: 24, mood: 'happy', note: 'Arriving with calm joy.' },
};

function MoodFace({ mood, size = 32 }: { mood: MoodType; size?: number }) {
  const getColors = () => {
    switch (mood) {
      case 'happy':
        return { bg: COLORS.moodYellow, stroke: '#8F6B12' };
      case 'calm':
        return { bg: COLORS.moodGreen, stroke: '#2D7344' };
      case 'thoughtful':
        return { bg: COLORS.moodPurple, stroke: '#564299' };
      case 'stressed':
        return { bg: COLORS.moodCoral, stroke: '#A83B24' };
      case 'tired':
        return { bg: COLORS.moodBlue, stroke: '#2A6B99' };
    }
  };

  const { bg, stroke } = getColors();

  return (
    <Svg width={size} height={size} viewBox="0 0 32 32">
      {/* Face circle */}
      <Circle cx="16" cy="16" r="14" fill={bg} />

      {/* Eyes */}
      {mood === 'happy' && (
        <>
          <Path d="M10 13 Q12 11 14 13" stroke={stroke} strokeWidth="1.8" fill="none" strokeLinecap="round" />
          <Path d="M18 13 Q20 11 22 13" stroke={stroke} strokeWidth="1.8" fill="none" strokeLinecap="round" />
          <Path d="M11 18 Q16 23 21 18" stroke={stroke} strokeWidth="1.8" fill="none" strokeLinecap="round" />
        </>
      )}

      {mood === 'calm' && (
        <>
          <Circle cx="11" cy="13" r="1.5" fill={stroke} />
          <Circle cx="21" cy="13" r="1.5" fill={stroke} />
          <Path d="M12 19 Q16 22 20 19" stroke={stroke} strokeWidth="1.6" fill="none" strokeLinecap="round" />
        </>
      )}

      {mood === 'thoughtful' && (
        <>
          <Circle cx="11" cy="13" r="1.5" fill={stroke} />
          <Circle cx="21" cy="13" r="1.5" fill={stroke} />
          <Path d="M12 20 Q16 18 20 20" stroke={stroke} strokeWidth="1.6" fill="none" strokeLinecap="round" />
        </>
      )}

      {mood === 'stressed' && (
        <>
          <Circle cx="11" cy="14" r="1.5" fill={stroke} />
          <Circle cx="21" cy="14" r="1.5" fill={stroke} />
          <Path d="M12 21 Q16 17 20 21" stroke={stroke} strokeWidth="1.8" fill="none" strokeLinecap="round" />
        </>
      )}

      {mood === 'tired' && (
        <>
          <Path d="M9 14 L14 14" stroke={stroke} strokeWidth="1.6" strokeLinecap="round" />
          <Path d="M18 14 L23 14" stroke={stroke} strokeWidth="1.6" strokeLinecap="round" />
          <Circle cx="16" cy="20" r="2" fill={stroke} />
        </>
      )}
    </Svg>
  );
}

const WEEKDAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function MoodCalendarScreen() {
  const router = useRouter();
  const [selectedDay, setSelectedDay] = useState<number>(24);
  const [currentMonth, setCurrentMonth] = useState('September 2025');

  // September 2025 starts on Monday (offset 1) and has 30 days
  const startDayOffset = 1;
  const daysInMonth = 30;

  const calendarCells = [];
  for (let i = 0; i < startDayOffset; i++) {
    calendarCells.push(null);
  }
  for (let day = 1; day <= daysInMonth; day++) {
    calendarCells.push(day);
  }

  const selectedRecord = SEPTEMBER_MOODS[selectedDay];

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

            <View style={styles.monthSelector}>
              <Pressable
                onPress={() => setCurrentMonth('August 2025')}
                hitSlop={8}
                style={({ pressed }) => [pressed && styles.pressed]}
              >
                <Ionicons name="chevron-back" size={16} color={COLORS.navy} />
              </Pressable>
              <Text style={styles.monthTitle}>{currentMonth}</Text>
              <Pressable
                onPress={() => setCurrentMonth('October 2025')}
                hitSlop={8}
                style={({ pressed }) => [pressed && styles.pressed]}
              >
                <Ionicons name="chevron-forward" size={16} color={COLORS.navy} />
              </Pressable>
            </View>

            <Pressable
              onPress={() => router.push('/journal')}
              style={({ pressed }) => [
                styles.iconButton,
                pressed && styles.pressed,
              ]}
              hitSlop={12}
              accessibilityRole="button"
              accessibilityLabel="Open Journal"
            >
              <Ionicons name="book-outline" size={20} color={COLORS.navy} />
            </Pressable>
          </View>

          {/* SCREEN TITLE */}
          <View style={styles.header}>
            <Text style={styles.title}>Mood Calendar</Text>
            <Text style={styles.subtitle}>
              See the emotional rhythm of your past days.
            </Text>
          </View>

          {/* CALENDAR CARD CONTAINER */}
          <View style={styles.calendarCard}>
            {/* WEEKDAYS HEADER */}
            <View style={styles.weekdaysRow}>
              {WEEKDAYS.map((wd) => (
                <Text key={wd} style={styles.weekdayLabel}>
                  {wd}
                </Text>
              ))}
            </View>

            {/* DAYS GRID */}
            <View style={styles.daysGrid}>
              {calendarCells.map((day, index) => {
                if (day === null) {
                  return <View key={`empty-${index}`} style={styles.dayCell} />;
                }

                const record = SEPTEMBER_MOODS[day];
                const isSelected = selectedDay === day;

                return (
                  <Pressable
                    key={`day-${day}`}
                    onPress={() => setSelectedDay(day)}
                    style={({ pressed }) => [
                      styles.dayCell,
                      isSelected && styles.dayCellSelected,
                      pressed && styles.pressed,
                    ]}
                    accessibilityRole="button"
                    accessibilityLabel={`Day ${day}`}
                  >
                    {record?.mood ? (
                      <MoodFace mood={record.mood} size={28} />
                    ) : (
                      <View style={styles.emptyDayDot} />
                    )}
                    <Text
                      style={[
                        styles.dayNumber,
                        isSelected && styles.dayNumberSelected,
                      ]}
                    >
                      {day}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>

          {/* SELECTED DAY DETAIL SNIPPET */}
          {selectedRecord && (
            <View style={styles.detailCard}>
              <View style={styles.detailLeft}>
                {selectedRecord.mood && <MoodFace mood={selectedRecord.mood} size={32} />}
                <View>
                  <Text style={styles.detailDate}>September {selectedRecord.day}, 2025</Text>
                  <Text style={styles.detailMoodText}>
                    Logged as {selectedRecord.mood}
                  </Text>
                </View>
              </View>
              {selectedRecord.note && (
                <Text style={styles.detailNote}>"{selectedRecord.note}"</Text>
              )}
            </View>
          )}

          {/* MONTHLY SUMMARY CARD MATCHING REFERENCE SCREEN 17 */}
          <View style={styles.summaryCard}>
            <View style={styles.summaryTextWrap}>
              <Text style={styles.summaryEyebrow}>MONTHLY SUMMARY</Text>
              <Text style={styles.summaryTitle}>More good days this month!</Text>
              <Text style={styles.summaryDescription}>
                You completed 18 calm & joyful check-ins across September.
              </Text>
            </View>

            {/* Friendly Green Mascot Blob */}
            <View style={styles.mascotWrap}>
              <MoodFace mood="happy" size={48} />
            </View>
          </View>
        </ScrollView>

        {/* BOTTOM NAVIGATION DOCK */}
        <MedhaBottomNav activeTab="explore" />
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
    paddingBottom: 24,
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
  monthSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  monthTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
  },

  /* HEADER */
  header: {
    marginTop: 12,
    marginBottom: 16,
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
    color: COLORS.navyMuted,
    marginTop: 4,
  },

  /* CALENDAR CARD */
  calendarCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    paddingVertical: 18,
    paddingHorizontal: 12,
    ...SHADOW.subtle,
  },
  weekdaysRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 0, 0, 0.04)',
  },
  weekdayLabel: {
    width: 40,
    textAlign: 'center',
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    color: COLORS.subtleText,
  },
  daysGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingTop: 10,
  },
  dayCell: {
    width: '14.28%',
    height: 52,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 14,
    marginVertical: 2,
  },
  dayCellSelected: {
    backgroundColor: 'rgba(24, 30, 44, 0.06)',
    borderWidth: 1.5,
    borderColor: COLORS.navy,
  },
  emptyDayDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    marginVertical: 11,
  },
  dayNumber: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 10,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  dayNumberSelected: {
    fontFamily: 'Nunito-Bold',
    color: COLORS.navy,
  },

  /* DETAIL CARD */
  detailCard: {
    marginTop: 14,
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 14,
    ...SHADOW.subtle,
  },
  detailLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  detailDate: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
    color: COLORS.navy,
  },
  detailMoodText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.coralDark,
    textTransform: 'capitalize',
  },
  detailNote: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.navyMuted,
    fontStyle: 'italic',
    marginTop: 8,
  },

  /* SUMMARY CARD */
  summaryCard: {
    marginTop: 16,
    backgroundColor: COLORS.greenSoft,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: COLORS.green,
    padding: 18,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    ...SHADOW.subtle,
  },
  summaryTextWrap: {
    flex: 1,
    paddingRight: 10,
  },
  summaryEyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 9,
    letterSpacing: 1.2,
    color: COLORS.greenDark,
    marginBottom: 4,
  },
  summaryTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 16,
    color: COLORS.navy,
  },
  summaryDescription: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 17,
    color: COLORS.navyMuted,
    marginTop: 4,
  },
  mascotWrap: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.white,
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },

  pressed: {
    transform: [{ scale: 0.96 }],
    opacity: 0.88,
  },
});
