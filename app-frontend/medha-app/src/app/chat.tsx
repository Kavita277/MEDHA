import React, { useState } from 'react';
import React, { useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TextInput,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

type Message = { id: string; from: 'medha' | 'you'; text: string };

export default function ChatScreen() {
import { chatService, sessionService } from '../services/api';

type Message = { id: string; from: 'medha' | 'you'; text: string };

export default function ChatScreen() {
  const router = useRouter();
  const [text, setText] = useState('');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      from: 'medha',
      text: 'Hi. I’m here with you. You can tell me what’s on your mind, in your own words.',
    },
  ]);

  React.useEffect(() => {
    sessionService.createSession().then((sess) => {
      setSessionId(sess.id);
    }).catch(err => {
      console.warn("Session init error:", err);
    });
  }, []);

  const send = async () => {
    const value = text.trim();
    if (!value || sending) return;
    
    const userMsgId = `${Date.now()}`;
    setMessages((current) => [
      ...current,
      { id: userMsgId, from: 'you', text: value },
    ]);
    setText('');
    setSending(true);

    try {
      let activeSid = sessionId;
      if (!activeSid) {
        const newSess = await sessionService.createSession();
        activeSid = newSess.id;
        setSessionId(activeSid);
      }
      const res = await chatService.sendMessage(activeSid, value);
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-reply`,
          from: 'medha',
          text: res.assistant_response || 'I am here with you. Take a gentle breath.',
        },
      ]);
    } catch (e: any) {
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-reply`,
          from: 'medha',
          text: 'I hear you. Take your time — I am listening and supporting you.',
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <MedhaScreen
      eyebrow="Talk with MEDHA"
      title="You can start anywhere."
      subtitle="Type what you’re feeling, or switch to voice when speaking feels easier."
      onBack={() => router.back()}
      scroll={false}
    >
      <KeyboardAvoidingView
        style={styles.keyboard}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          style={styles.messages}
          contentContainerStyle={styles.messageContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {messages.map((message) => (
            <View
              key={message.id}
              style={[
                styles.bubble,
                message.from === 'you' ? styles.youBubble : styles.medhaBubble,
              ]}
            >
              {message.from === 'medha' && (
                <Text style={styles.sender}>MEDHA</Text>
              )}
              <Text
                style={[
                  styles.bubbleText,
                  message.from === 'you' && styles.youText,
                ]}
              >
                {message.text}
              </Text>
            </View>
          ))}

          <View style={styles.quickRow}>
            {[
              'I’m feeling anxious.',
              'Help me sleep better.',
              'I just want to talk.',
            ].map((item) => (
              <Pressable
                key={item}
                onPress={() => setText(item)}
                style={styles.quickChip}
              >
                <Text style={styles.quickText}>{item}</Text>
              </Pressable>
            ))}
          </View>
        </ScrollView>

        <View style={styles.voiceEntry}>
          <View style={styles.voiceCopy}>
            <View style={styles.voiceIcon}>
              <Ionicons name="mic-outline" size={17} color={COLORS.forest} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.voiceTitle}>Prefer to speak?</Text>
              <Text style={styles.voiceSubtitle}>
                Have a natural voice conversation with MEDHA.
              </Text>
            </View>
          </View>
          <Pressable
            style={styles.voiceButton}
            onPress={() => router.push('/voice-assistant' as any)}
            accessibilityRole="button"
            accessibilityLabel="Start voice chat with MEDHA"
          >
            <Ionicons name="arrow-forward" size={18} color={COLORS.white} />
          </Pressable>
        </View>

        <View style={styles.composer}>
          <TextInput
            value={text}
            onChangeText={setText}
            placeholder="Type a message..."
            placeholderTextColor={COLORS.subtleText}
            multiline
            style={styles.input}
            textAlignVertical="center"
          />
          <Pressable
            onPress={() => router.push('/voice-assistant' as any)}
            style={styles.micButton}
            accessibilityRole="button"
            accessibilityLabel="Open voice chat"
          >
            <Ionicons name="mic-outline" size={20} color={COLORS.forest} />
          </Pressable>
          <Pressable
            onPress={send}
            style={[styles.sendButton, !text.trim() && styles.sendDisabled]}
            disabled={!text.trim()}
          >
            <Ionicons name="arrow-up" size={19} color={COLORS.white} />
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  keyboard: { flex: 1 },
  messages: { flex: 1 },
  messageContent: { paddingVertical: 10, gap: 10 },
  bubble: {
    maxWidth: '88%',
    paddingHorizontal: 16,
    paddingVertical: 13,
    borderRadius: 20,
  },
  medhaBubble: {
    alignSelf: 'flex-start',
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderBottomLeftRadius: 6,
  },
  youBubble: {
    alignSelf: 'flex-end',
    backgroundColor: COLORS.forest,
    borderBottomRightRadius: 6,
  },
  sender: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.5,
    color: COLORS.moss,
    marginBottom: 6,
  },
  bubbleText: {
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.text,
  },
  youText: { color: COLORS.white },
  quickRow: { gap: 8, paddingVertical: 8 },
  quickChip: {
    alignSelf: 'flex-start',
    borderRadius: 18,
    backgroundColor: COLORS.surfaceWarm,
    paddingHorizontal: 14,
    paddingVertical: 9,
  },
  quickText: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.deepForest,
  },
  voiceEntry: {
    marginTop: 8,
    padding: 13,
    borderRadius: 20,
    backgroundColor: COLORS.mist,
    flexDirection: 'row',
    alignItems: 'center',
  },
  voiceCopy: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 10 },
  voiceIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  voiceTitle: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.deepForest,
  },
  voiceSubtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 13,
    color: COLORS.mutedText,
    marginTop: 2,
  },
  voiceButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  composer: {
    minHeight: 56,
    borderRadius: 28,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: 17,
    paddingRight: 6,
    marginTop: 10,
    marginBottom: 4,
  },
  input: {
    flex: 1,
    maxHeight: 80,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.text,
    paddingVertical: 10,
  },
  micButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendDisabled: { opacity: 0.35 },
});
