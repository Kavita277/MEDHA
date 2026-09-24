import React, { useEffect, useRef, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';
import {
  ApiError,
  createSession,
  getAccessToken,
  getHistory,
  sendMessage,
} from '../services/api';

type Message = {
  id: string;
  from: 'medha' | 'you';
  text: string;
  timestamp?: string;
};

const formatTimestamp = (isoOrText?: string): string => {
  if (!isoOrText) return 'Just now';
  if (isoOrText === 'Just now') return 'Just now';
  try {
    const d = new Date(isoOrText);
    if (isNaN(d.getTime())) return isoOrText;
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return isoOrText;
  }
};

const INITIAL_MESSAGES: Message[] = [
  {
    id: 'welcome',
    from: 'medha',
    text: "Hi! I'm Medha. I'm here to listen and support you. How are you feeling right now?",
    timestamp: 'Just now',
  },
];

const QUICK_SUGGESTIONS = [
  'I feel anxious',
  'I need motivation',
  'Can you give me a coping tip?',
  'Today felt overwhelming',
];

export default function ChatScreen() {
  const router = useRouter();
  const scrollViewRef = useRef<ScrollView>(null);
  const [text, setText] = useState('');
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [errorState, setErrorState] = useState<{ message: string; retryText?: string } | null>(null);
  const [safetyTriggered, setSafetyTriggered] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const init = async () => {
      const token = getAccessToken();
      if (!token) {
        // Unauthenticated: preserve initial welcome UI
        return;
      }

      try {
        const session = await createSession();
        if (!isMounted) return;
        setSessionId(session.id);

        try {
          const history = await getHistory(session.id);
          if (!isMounted) return;
          if (history.messages && history.messages.length > 0) {
            const mapped: Message[] = history.messages.map((m) => ({
              id: m.id,
              from: m.role === 'user' ? 'you' : 'medha',
              text: m.content,
              timestamp: formatTimestamp(m.timestamp),
            }));
            setMessages(mapped);
          }
        } catch {
          // If history fetch fails on fresh session, preserve initial greeting
        }
      } catch (err: unknown) {
        if (!isMounted) return;
        // Session initialization failure handled on demand when user sends
      }
    };

    init();
    return () => {
      isMounted = false;
    };
  }, []);

  const send = async (overrideText?: string) => {
    const value = (overrideText || text).trim();
    if (!value) return;

    setErrorState(null);

    const userMsg: Message = {
      id: `${Date.now()}-you`,
      from: 'you',
      text: value,
      timestamp: 'Just now',
    };

    setMessages((current) => [...current, userMsg]);
    setText('');
    setIsTyping(true);

    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);

    const token = getAccessToken();
    if (!token) {
      setIsTyping(false);
      setErrorState({
        message: 'Sign in is required to connect to MEDHA chat.',
        retryText: value,
      });
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
      return;
    }

    try {
      let activeSessionId = sessionId;
      if (!activeSessionId) {
        const newSession = await createSession();
        activeSessionId = newSession.id;
        setSessionId(newSession.id);
      }

      const result = await sendMessage(activeSessionId, value, {
        language: 'en',
        behaviour_data: null,
        metadata: null,
      });

      setIsTyping(false);

      const botMsg: Message = {
        id: `${Date.now()}-medha`,
        from: 'medha',
        text: result.assistant_response,
        timestamp: formatTimestamp(result.timestamp),
      };

      setMessages((current) => [...current, botMsg]);

      if (result.safety_triggered) {
        setSafetyTriggered(true);
      }

      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    } catch (err: unknown) {
      setIsTyping(false);
      const message =
        err instanceof ApiError
          ? err.message
          : 'Unable to reach MEDHA care services. Please check your connection and try again.';
      setErrorState({
        message,
        retryText: value,
      });
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.keyboard}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* TOP BAR WITH MEDHA IDENTITY */}
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

          {/* Center Medha Header */}
          <View style={styles.headerTitleWrap}>
            <View style={styles.avatarWrap}>
              <Ionicons name="sparkles" size={14} color={COLORS.coralDark} />
            </View>
            <View style={styles.headerTextGroup}>
              <Text style={styles.headerName}>Chat with Medha</Text>
              <Text style={styles.headerSub}>Always here to listen</Text>
            </View>
          </View>

          {/* Voice Assistant Shortcut */}
          <Pressable
            onPress={() => router.push('/voice-assistant')}
            style={({ pressed }) => [
              styles.iconButton,
              pressed && styles.pressed,
            ]}
            hitSlop={12}
            accessibilityRole="button"
            accessibilityLabel="Switch to Voice Assistant"
          >
            <Ionicons name="mic-outline" size={20} color={COLORS.navy} />
          </Pressable>
        </View>

        {/* MESSAGE STREAM */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messageList}
          contentContainerStyle={styles.messageContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Subtle Private Badge */}
          <View style={styles.privatePill}>
            <Ionicons name="shield-checkmark-outline" size={12} color={COLORS.sage} />
            <Text style={styles.privateText}>
              Private & confidential • Support always within reach
            </Text>
          </View>

          {messages.map((message) => {
            const isUser = message.from === 'you';

            return (
              <View
                key={message.id}
                style={[
                  styles.bubbleContainer,
                  isUser ? styles.userContainer : styles.botContainer,
                ]}
              >
                {!isUser && (
                  <View style={styles.botSenderRow}>
                    <View style={styles.miniAvatar}>
                      <Ionicons name="sparkles" size={10} color={COLORS.coralDark} />
                    </View>
                    <Text style={styles.senderLabel}>MEDHA</Text>
                  </View>
                )}

                <View
                  style={[
                    styles.bubble,
                    isUser ? styles.userBubble : styles.medhaBubble,
                  ]}
                >
                  <Text
                    style={[
                      styles.bubbleText,
                      isUser ? styles.userText : styles.medhaText,
                    ]}
                  >
                    {message.text}
                  </Text>
                </View>

                {message.timestamp && (
                  <Text
                    style={[
                      styles.timestampText,
                      isUser ? styles.userTimestamp : styles.botTimestamp,
                    ]}
                  >
                    {message.timestamp}
                  </Text>
                )}
              </View>
            );
          })}

          {/* TYPING INDICATOR */}
          {isTyping && (
            <View style={[styles.bubbleContainer, styles.botContainer]}>
              <View style={styles.botSenderRow}>
                <View style={styles.miniAvatar}>
                  <Ionicons name="sparkles" size={10} color={COLORS.coralDark} />
                </View>
                <Text style={styles.senderLabel}>MEDHA is listening...</Text>
              </View>
              <View style={[styles.bubble, styles.medhaBubble, styles.typingBubble]}>
                <View style={styles.typingDot} />
                <View style={[styles.typingDot, styles.typingDotDelay1]} />
                <View style={[styles.typingDot, styles.typingDotDelay2]} />
              </View>
            </View>
          )}

          {/* CALM INLINE ERROR / RETRY STATE */}
          {errorState && (
            <View style={styles.errorCard}>
              <View style={styles.errorHeaderRow}>
                <Ionicons name="information-circle-outline" size={16} color="#B8564D" />
                <Text style={styles.errorText}>{errorState.message}</Text>
              </View>
              {errorState.retryText && (
                <Pressable
                  onPress={() => send(errorState.retryText)}
                  style={({ pressed }) => [
                    styles.retryButton,
                    pressed && styles.pressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel="Retry sending message"
                >
                  <Ionicons name="refresh-outline" size={13} color={COLORS.navy} />
                  <Text style={styles.retryButtonText}>Retry</Text>
                </Pressable>
              )}
            </View>
          )}

          {/* SAFETY PATHWAY BANNER (SURFACED WHEN safety_triggered === true) */}
          {safetyTriggered && (
            <View style={styles.safetyCard}>
              <View style={styles.safetyHeaderRow}>
                <View style={styles.safetyIconBadge}>
                  <Ionicons name="heart" size={14} color={COLORS.coralDark} />
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.safetyTitle}>We care about your safety</Text>
                  <Text style={styles.safetySub}>
                    Support and someone to talk to are available right now. Free, confidential, and 24/7.
                  </Text>
                </View>
              </View>
              <Pressable
                onPress={() => router.push('/support')}
                style={({ pressed }) => [
                  styles.safetyActionBtn,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Open Support Services"
              >
                <Text style={styles.safetyActionText}>View Free Support Helplines</Text>
                <Ionicons name="arrow-forward" size={14} color={COLORS.white} />
              </Pressable>
            </View>
          )}

          {/* QUICK SUGGESTIONS SECTION MATCHING REFERENCE SCREEN 19 */}
          <View style={styles.suggestionsContainer}>
            <Text style={styles.suggestionsHeading}>Not sure what to say?</Text>
            <View style={styles.suggestionsRow}>
              {QUICK_SUGGESTIONS.map((item) => (
                <Pressable
                  key={item}
                  onPress={() => send(item)}
                  style={({ pressed }) => [
                    styles.suggestionChip,
                    pressed && styles.pressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel={item}
                >
                  <Text style={styles.suggestionText}>{item}</Text>
                </Pressable>
              ))}
            </View>
          </View>
        </ScrollView>

        {/* CLEAN COMPOSER DOCK (No mic inside input) */}
        <View style={styles.composerWrapper}>
          <View style={styles.composer}>
            <TextInput
              value={text}
              onChangeText={setText}
              placeholder="Type a message..."
              placeholderTextColor={COLORS.navyMuted}
              multiline
              style={styles.textInput}
              accessibilityLabel="Type your message"
            />

            <Pressable
              onPress={() => send()}
              disabled={!text.trim()}
              style={({ pressed }) => [
                styles.sendButton,
                !text.trim() && styles.sendButtonDisabled,
                pressed && text.trim() && styles.pressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel="Send message"
            >
              <Ionicons
                name="arrow-up"
                size={19}
                color={COLORS.white}
              />
            </Pressable>
          </View>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.porcelain,
  },
  keyboard: {
    flex: 1,
  },

  /* TOP BAR */
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0, 0, 0, 0.04)',
    backgroundColor: COLORS.porcelain,
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
  headerTitleWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  avatarWrap: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: COLORS.pinkSoft,
    borderWidth: 1,
    borderColor: COLORS.pink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTextGroup: {
    alignItems: 'flex-start',
  },
  headerName: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 16,
    color: COLORS.navy,
  },
  headerSub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
  },

  /* MESSAGES */
  messageList: {
    flex: 1,
  },
  messageContent: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 16,
    gap: 14,
  },
  privatePill: {
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: COLORS.white,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.04)',
    marginBottom: 4,
    ...SHADOW.subtle,
  },
  privateText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 11,
    color: COLORS.navyMuted,
  },

  /* BUBBLES */
  bubbleContainer: {
    maxWidth: '85%',
  },
  botContainer: {
    alignSelf: 'flex-start',
  },
  userContainer: {
    alignSelf: 'flex-end',
  },
  botSenderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
    marginLeft: 4,
  },
  miniAvatar: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: COLORS.creamSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  senderLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 0.8,
    color: COLORS.coralDark,
  },
  bubble: {
    paddingHorizontal: 16,
    paddingVertical: 13,
    borderRadius: 20,
    ...SHADOW.subtle,
  },
  medhaBubble: {
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    borderTopLeftRadius: 6,
  },
  userBubble: {
    backgroundColor: COLORS.navy,
    borderTopRightRadius: 6,
  },
  bubbleText: {
    fontSize: 14,
    lineHeight: 21,
  },
  medhaText: {
    fontFamily: 'Nunito-Regular',
    color: COLORS.navy,
  },
  userText: {
    fontFamily: 'Nunito-SemiBold',
    color: COLORS.white,
  },
  timestampText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 10,
    marginTop: 4,
    marginHorizontal: 4,
  },
  botTimestamp: {
    color: COLORS.navyMuted,
    alignSelf: 'flex-start',
  },
  userTimestamp: {
    color: COLORS.subtleText,
    alignSelf: 'flex-end',
  },

  /* TYPING */
  typingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  typingDot: {
    width: 7,
    height: 7,
    borderRadius: 3.5,
    backgroundColor: COLORS.coral,
    opacity: 0.4,
  },
  typingDotDelay1: {
    opacity: 0.7,
  },
  typingDotDelay2: {
    opacity: 1,
  },

  /* QUICK SUGGESTIONS */
  suggestionsContainer: {
    marginTop: 10,
  },
  suggestionsHeading: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    letterSpacing: 0.8,
    color: COLORS.coralDark,
    marginBottom: 8,
    marginLeft: 4,
  },
  suggestionsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  suggestionChip: {
    backgroundColor: COLORS.white,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: RADIUS.pill,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  suggestionText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navy,
  },

  /* COMPOSER */
  composerWrapper: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: COLORS.porcelain,
  },
  composer: {
    minHeight: 52,
    maxHeight: 120,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.06)',
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: 18,
    paddingRight: 6,
    paddingVertical: 4,
    ...SHADOW.subtle,
  },
  textInput: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    color: COLORS.navy,
    paddingVertical: 6,
    paddingRight: 8,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.navy,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#D3D8E2',
    opacity: 0.7,
  },

  pressed: {
    transform: [{ scale: 0.96 }],
    opacity: 0.88,
  },

  /* CALM ERROR CARD */
  errorCard: {
    backgroundColor: '#FFF5F4',
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: '#F6D2CF',
    padding: 14,
    alignSelf: 'center',
    width: '100%',
    ...SHADOW.subtle,
  },
  errorHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  errorText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: '#8B3832',
    lineHeight: 17,
  },
  retryButton: {
    marginTop: 10,
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.08)',
  },
  retryButtonText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navy,
  },

  /* SAFETY CARD */
  safetyCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(235, 114, 88, 0.25)',
    padding: 16,
    width: '100%',
    ...SHADOW.subtle,
  },
  safetyHeaderRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
  },
  safetyIconBadge: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#FFEFEB',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  safetyTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.navy,
  },
  safetySub: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    lineHeight: 17,
    marginTop: 4,
  },
  safetyActionBtn: {
    marginTop: 12,
    height: 40,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.navy,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingHorizontal: 16,
  },
  safetyActionText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
});
