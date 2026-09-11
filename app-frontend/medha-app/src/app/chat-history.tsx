import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';
import { useAuth } from '../context/AuthContext';
import { useSession } from '../context/SessionContext';
import { getSessions, deleteSession } from '../services/session';
import { SessionResponse } from '../types/auth';

export default function ChatHistoryScreen() {
  const router = useRouter();
  const { token } = useAuth();
  const { restoreSession } = useSession();

  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSessions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const loadSessions = async () => {
    if (!token) return;
    setIsLoading(true);
    try {
      const data = await getSessions(token);
      setSessions(data);
    } catch (err) {
      Alert.alert('Error', 'Could not load chat history.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenSession = (session: SessionResponse) => {
    restoreSession(session.id);
    router.push('/chat');
  };

  const handleDeleteSession = async (session: SessionResponse) => {
    if (!token) return;
    Alert.alert('Delete Chat', 'Are you sure you want to delete this conversation?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteSession(session.id, token);
            setSessions((curr) => curr.filter((s) => s.id !== session.id));
          } catch (err) {
            Alert.alert('Error', 'Could not delete chat session.');
          }
        },
      },
    ]);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  };

  return (
    <MedhaScreen
      eyebrow="Past Conversations"
      title="Chat History"
      subtitle="Revisit your previous conversations with MEDHA or clear them out."
      onBack={() => router.back()}
      scroll={true}
    >
      <View style={styles.container}>
        {isLoading ? (
          <ActivityIndicator color={COLORS.forest} style={{ marginTop: 40 }} />
        ) : sessions.length === 0 ? (
          <Text style={styles.emptyText}>No chat history found.</Text>
        ) : (
          sessions.map((session) => (
            <View key={session.id} style={styles.card}>
              <Pressable
                style={styles.cardContent}
                onPress={() => handleOpenSession(session)}
              >
                <Text style={styles.date}>{formatDate(session.created_at)}</Text>
                {session.state_summary?.latest_assistant_response ? (
                  <Text style={styles.preview} numberOfLines={2}>
                    {session.state_summary.latest_assistant_response}
                  </Text>
                ) : (
                  <Text style={styles.preview}>No messages yet</Text>
                )}
                <View style={styles.metaRow}>
                  <Text style={styles.metaText}>
                    {session.state_summary?.turn_count || 0} messages
                  </Text>
                </View>
              </Pressable>
              
              <Pressable
                style={styles.deleteButton}
                onPress={() => handleDeleteSession(session)}
              >
                <Ionicons name="trash-outline" size={20} color={'#CC0000'} />
              </Pressable>
            </View>
          ))
        )}
      </View>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 10,
    gap: 12,
  },
  emptyText: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    color: COLORS.mutedText,
    textAlign: 'center',
    marginTop: 40,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    alignItems: 'center',
    overflow: 'hidden',
  },
  cardContent: {
    flex: 1,
    padding: 16,
  },
  date: {
    fontFamily: 'Inter-Medium',
    fontSize: 12,
    color: COLORS.deepForest,
    marginBottom: 4,
  },
  preview: {
    fontFamily: 'Inter-Regular',
    fontSize: 13,
    color: COLORS.text,
    lineHeight: 18,
    marginBottom: 8,
  },
  metaRow: {
    flexDirection: 'row',
  },
  metaText: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.subtleText,
  },
  deleteButton: {
    padding: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
