import React, { useState, useEffect } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View, ScrollView, ActivityIndicator } from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';
import { journalService } from '../services/journal';
import { useAuth } from '../context/AuthContext';
import { JournalEntryResponse } from '../types/journal';

const moods = ['Calm', 'Grateful', 'Stressed', 'Hopeful', 'Tired', 'Unsure'];

export default function JournalScreen() {
  const router = useRouter();
  const { token, isAuthenticated, isLoading } = useAuth();
  
  const [entries, setEntries] = useState<JournalEntryResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Editor State
  const [activeEntry, setActiveEntry] = useState<JournalEntryResponse | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  
  const [text, setText] = useState('');
  const [mood, setMood] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated || !token) {
      router.replace('/login' as any);
      return;
    }
    loadEntries();
  }, [isLoading, isAuthenticated, token]);

  const loadEntries = async () => {
    if (!token) return;
    try {
      setLoading(true);
      setError(null);
      const res = await journalService.listEntries(token);
      setEntries(res.entries || []);
    } catch (err: any) {
      setError(err.message || 'Unable to load your journal. Try again.');
    } finally {
      setLoading(false);
    }
  };

  const openEditor = (entry?: JournalEntryResponse) => {
    if (entry) {
      setActiveEntry(entry);
      // Simple mood extraction if it starts with [Mood: X]
      let content = entry.content;
      const moodMatch = content.match(/^\[Mood:\s([^\]]+)\]\s*(.*)$/s);
      if (moodMatch) {
        setMood(moodMatch[1]);
        setText(moodMatch[2]);
      } else {
        setMood(null);
        setText(content);
      }
    } else {
      setActiveEntry(null);
      setMood(null);
      setText('');
    }
    setIsEditing(true);
  };

  const handleSave = async () => {
    if (!token) return;
    if (!text.trim()) {
      setIsEditing(false);
      return;
    }
    setSaving(true);
    try {
      const fullContent = mood ? `[Mood: ${mood}] ${text.trim()}` : text.trim();
      if (activeEntry) {
        await journalService.updateEntry(token, activeEntry.id, { content: fullContent });
      } else {
        await journalService.createEntry(token, { content: fullContent });
      }
      setIsEditing(false);
      await loadEntries(); // refresh list
    } catch (err: any) {
      console.warn("Journal save error:", err);
      // Just alert or log for now, keep them in the editor so they don't lose work
      alert(err.message || 'Failed to save entry.');
    } finally {
      setSaving(false);
    }
  };

  if (!isAuthenticated) return null;

  if (isEditing) {
    return (
      <MedhaScreen
        eyebrow={activeEntry ? "Edit Entry" : "New Entry"}
        title="A space just for you."
        subtitle="Write without needing to make sense of everything."
        onBack={() => setIsEditing(false)}
      >
        <View style={styles.datePill}>
          <Ionicons name="calendar-outline" size={14} color={COLORS.deepForest} />
          <Text style={styles.dateText}>
            {activeEntry 
              ? new Date(activeEntry.updated_at).toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
              : new Date().toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' })
            }
          </Text>
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

        <Pressable style={[styles.save, saving && { opacity: 0.7 }]} onPress={handleSave} disabled={saving}>
          <Text style={styles.saveText}>{saving ? 'Saving...' : 'Save Entry'}</Text>
        </Pressable>
      </MedhaScreen>
    );
  }

  // LIST MODE
  return (
    <MedhaScreen
      eyebrow="Your Journal"
      title="Reflect and release."
      subtitle="A private space to capture your thoughts."
      onBack={() => router.back()}
      rightIcon="add"
      onRightPress={() => openEditor()}
      scroll={false}
    >
      {loading ? (
        <View style={styles.centerBox}>
          <ActivityIndicator size="small" color={COLORS.forest} />
          <Text style={styles.emptyText}>Loading your journal...</Text>
        </View>
      ) : error ? (
        <View style={styles.centerBox}>
          <Text style={styles.emptyText}>{error}</Text>
          <Pressable onPress={loadEntries} style={{ marginTop: 10 }}>
            <Text style={{ color: COLORS.forest, fontFamily: 'Inter-Medium', fontSize: 13 }}>Retry</Text>
          </Pressable>
        </View>
      ) : entries.length === 0 ? (
        <View style={styles.centerBox}>
          <Text style={styles.emptyText}>You don't have any journal entries yet.</Text>
          <Pressable onPress={() => openEditor()} style={styles.save}>
            <Text style={styles.saveText}>Write your first entry</Text>
          </Pressable>
        </View>
      ) : (
        <ScrollView style={{ flex: 1 }} contentContainerStyle={{ paddingBottom: 40, paddingTop: 10 }}>
          {entries.map(entry => {
            const date = new Date(entry.updated_at);
            const contentPreview = entry.content.replace(/^\[Mood:\s[^\]]+\]\s*/, '').substring(0, 100);
            return (
              <Pressable 
                key={entry.id} 
                style={styles.entryCard} 
                onPress={() => openEditor(entry)}
              >
                <View style={styles.entryHeader}>
                  <Text style={styles.entryDate}>
                    {date.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short' })}
                  </Text>
                  <Ionicons name="chevron-forward" size={14} color={COLORS.mutedText} />
                </View>
                <Text style={styles.entryPreview} numberOfLines={2}>
                  {contentPreview || "Empty entry"}
                </Text>
              </Pressable>
            );
          })}
        </ScrollView>
      )}
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
    paddingHorizontal: 20,
  },
  saveText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
  centerBox: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  emptyText: {
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    color: COLORS.mutedText,
    textAlign: 'center',
    marginTop: 12,
  },
  entryCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  entryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  entryDate: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.deepForest,
  },
  entryPreview: {
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    lineHeight: 20,
    color: COLORS.text,
  },
});
