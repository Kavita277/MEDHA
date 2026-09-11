import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

<<<<<<< HEAD
=======
import { journalService } from '../services/api';

>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c
const moods = ['Calm', 'Grateful', 'Stressed', 'Hopeful', 'Tired', 'Unsure'];

export default function JournalScreen() {
  const router = useRouter();
  const [text, setText] = useState('');
  const [mood, setMood] = useState<string | null>(null);
<<<<<<< HEAD
=======
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!text.trim()) {
      router.push('/home');
      return;
    }
    setSaving(true);
    try {
      const fullContent = mood ? `[Mood: ${mood}] ${text.trim()}` : text.trim();
      await journalService.createEntry(fullContent);
      router.push('/home');
    } catch (err) {
      console.warn("Journal save error:", err);
      router.push('/home');
    } finally {
      setSaving(false);
    }
  };
>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c

  return (
    <MedhaScreen
      eyebrow="Today’s Journal"
      title="A space just for you."
      subtitle="Write without needing to make sense of everything."
      onBack={() => router.back()}
    >
      <View style={styles.datePill}>
        <Ionicons name="calendar-outline" size={14} color={COLORS.deepForest} />
<<<<<<< HEAD
        <Text style={styles.dateText}>Mon, 1 Jun 2026</Text>
=======
        <Text style={styles.dateText}>
          {new Date().toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })}
        </Text>
>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c
      </View>

      <View style={styles.paper}>
        <TextInput
          value={text}
          onChangeText={setText}
          multiline
          placeholder="What’s on your mind today?"
          placeholderTextColor={COLORS.subtleText}
          style={styles.input}
          textAlignVertical="top"
        />
      </View>

      <Text style={styles.moodHeading}>HOW ARE YOU FEELING?</Text>
      <View style={styles.moods}>
        {moods.map((item) => {
          const active = mood === item;
          return (
            <Pressable
              key={item}
              onPress={() => setMood(active ? null : item)}
              style={[styles.mood, active && styles.moodActive]}
            >
              <Text style={[styles.moodText, active && styles.moodTextActive]}>
                {item}
              </Text>
            </Pressable>
          );
        })}
      </View>

<<<<<<< HEAD
      <Pressable style={styles.save} onPress={() => router.push('/home')}>
        <Text style={styles.saveText}>Save Entry</Text>
=======
      <Pressable style={[styles.save, saving && { opacity: 0.7 }]} onPress={handleSave} disabled={saving}>
        <Text style={styles.saveText}>{saving ? 'Saving...' : 'Save Entry'}</Text>
>>>>>>> 40e4450e4d451d2bd31862d1ee53d8149e4a204c
      </Pressable>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  datePill: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 17,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 13,
  },
  dateText: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.deepForest,
  },
  paper: {
    height: 255,
    backgroundColor: COLORS.surface,
    borderRadius: 7,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 17,
    shadowColor: '#2D3B31',
    shadowOpacity: 0.05,
    shadowRadius: 12,
    elevation: 1,
  },
  input: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    lineHeight: 21,
    color: COLORS.text,
  },
  moodHeading: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.6,
    color: COLORS.moss,
    marginTop: 19,
    marginBottom: 10,
  },
  moods: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  mood: {
    paddingHorizontal: 14,
    paddingVertical: 9,
    borderRadius: 17,
    backgroundColor: COLORS.surfaceWarm,
  },
  moodActive: { backgroundColor: COLORS.forest },
  moodText: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.deepForest,
  },
  moodTextActive: { color: COLORS.white },
  save: {
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
  },
  saveText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
});
