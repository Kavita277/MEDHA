import React, { useRef, useState } from 'react';
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
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { MedhaCard } from '../components/medha-card';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

type Message = {
  id: string;
  from: 'medha' | 'you';
  text: string;
  timestamp?: string;
};

const INITIAL_MESSAGES: Message[] = [
  {
    id: 'welcome',
    from: 'medha',
    text: 'Hi. I’m here with you. You can tell me what’s on your mind, in your own words.',
    timestamp: 'Just now',
  },
];

const QUICK_SUGGESTIONS = [
  'I’m feeling anxious.',
  'Help me sleep better.',
  'I just want to talk.',
  'Today felt overwhelming.',
];

export default function ChatScreen() {
  const router = useRouter();
  const scrollViewRef = useRef<ScrollView>(null);
  const [text, setText] = useState('');
  const [messages, setMessages] = useState<Message[]>(INITIAL_MESSAGES);
  const [isTyping, setIsTyping] = useState(false);

  const send = (overrideText?: string) => {
    const value = (overrideText || text).trim();
    if (!value) return;

    const userMsg: Message = {
      id: `${Date.now()}-you`,
      from: 'you',
      text: value,
      timestamp: 'Just now',
    };

    setMessages((current) => [...current, userMsg]);
    setText('');
    setIsTyping(true);

    // Scroll to bottom after user message
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);

    // Simulated supportive response
    setTimeout(() => {
      setIsTyping(false);
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-medha`,
          from: 'medha',
          text: 'I’m listening. Take your time — you don’t have to explain everything at once. What feels heaviest right now?',
          timestamp: 'Just now',
        },
      ]);
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }, 1200);
  };

  return (
    <MedhaScreen
      eyebrow="Talk with MEDHA"
      title="You can start anywhere."
      subtitle="Type what you’re feeling, or switch to voice when speaking feels easier."
      onBack={() => router.back()}
      rightIcon="mic-outline"
      onRightPress={() => router.push('/voice-assistant')}
      scroll={false}
      withBackground={true}
    >
      <KeyboardAvoidingView
        style={styles.keyboard}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        {/* Messages Stream */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messages}
          contentContainerStyle={styles.messageContent}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Subtle Private Badge */}
          <View style={styles.privatePill}>
            <Ionicons name="shield-checkmark" size={13} color={COLORS.sage} />
            <Text style={styles.privateText}>
              Private & confidential • Human support always available
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
                  <View style={styles.botHeader}>
                    <View style={styles.botAvatar}>
                      <Ionicons name="sparkles" size={12} color={COLORS.coral} />
                    </View>
                    <Text style={styles.sender}>MEDHA</Text>
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
                      styles.timestamp,
                      isUser ? styles.userTimestamp : styles.botTimestamp,
                    ]}
                  >
                    {message.timestamp}
                  </Text>
                )}
              </View>
            );
          })}

          {/* Typing Indicator */}
          {isTyping && (
            <View style={[styles.bubbleContainer, styles.botContainer]}>
              <View style={styles.botHeader}>
                <View style={styles.botAvatar}>
                  <Ionicons name="sparkles" size={12} color={COLORS.coral} />
                </View>
                <Text style={styles.sender}>MEDHA is listening...</Text>
              </View>
              <View style={[styles.bubble, styles.medhaBubble, styles.typingBubble]}>
                <View style={styles.typingDot} />
                <View style={[styles.typingDot, styles.typingDotDelay1]} />
                <View style={[styles.typingDot, styles.typingDotDelay2]} />
              </View>
            </View>
          )}

          {/* Quick suggestions */}
          <View style={styles.quickSection}>
            <Text style={styles.quickSectionTitle}>Not sure where to begin?</Text>
            <View style={styles.quickRow}>
              {QUICK_SUGGESTIONS.map((item) => (
                <Pressable
                  key={item}
                  onPress={() => send(item)}
                  style={({ pressed }) => [
                    styles.quickChip,
                    pressed && styles.quickChipPressed,
                  ]}
                  accessibilityRole="button"
                >
                  <Text style={styles.quickText}>{item}</Text>
                </Pressable>
              ))}
            </View>
          </View>

          {/* Voice Switch Card */}
          <MedhaCard
            variant="peach"
            style={styles.voiceCard}
            onPress={() => router.push('/voice-assistant')}
            accessibilityLabel="Switch to Voice Assistant"
          >
            <View style={styles.voiceRow}>
              <View style={styles.voiceIconWrap}>
                <Ionicons name="mic" size={20} color={COLORS.coralDark} />
              </View>
              <View style={styles.voiceTextWrap}>
                <Text style={styles.voiceTitle}>Prefer to speak?</Text>
                <Text style={styles.voiceSubtitle}>
                  Have a natural voice conversation with MEDHA.
                </Text>
              </View>
              <View style={styles.voiceArrow}>
                <Ionicons name="arrow-forward" size={16} color={COLORS.white} />
              </View>
            </View>
          </MedhaCard>
        </ScrollView>

        {/* Clean Composer Bar (No mic inside input) */}
        <View style={styles.composerWrapper}>
          <View style={styles.composer}>
            <TextInput
              value={text}
              onChangeText={setText}
              placeholder="Type what’s on your mind..."
              placeholderTextColor={COLORS.navyMuted}
              multiline
              style={styles.input}
              textAlignVertical="center"
              accessibilityLabel="Type your message"
            />
            <Pressable
              onPress={() => send()}
              style={({ pressed }) => [
                styles.sendButton,
                !text.trim() && styles.sendDisabled,
                pressed && text.trim() && styles.sendPressed,
              ]}
              disabled={!text.trim()}
              accessibilityRole="button"
              accessibilityLabel="Send message"
            >
              <Ionicons name="arrow-up" size={20} color={COLORS.white} />
            </Pressable>
          </View>
        </View>
      </KeyboardAvoidingView>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  keyboard: {
    flex: 1,
  },
  messages: {
    flex: 1,
  },
  messageContent: {
    paddingVertical: 12,
    gap: 14,
    paddingBottom: 16,
  },
  privatePill: {
    alignSelf: 'center',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: 'rgba(255, 255, 255, 0.75)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    borderWidth: 1,
    borderColor: 'rgba(127, 168, 138, 0.3)',
    marginBottom: 4,
  },
  privateText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 11,
    color: COLORS.navyMuted,
  },
  bubbleContainer: {
    maxWidth: '85%',
  },
  botContainer: {
    alignSelf: 'flex-start',
  },
  userContainer: {
    alignSelf: 'flex-end',
  },
  botHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
    marginLeft: 4,
  },
  botAvatar: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: COLORS.pinkSoft,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: COLORS.pink,
  },
  sender: {
    fontFamily: 'Nunito-Bold',
    fontSize: 11,
    letterSpacing: 0.6,
    color: COLORS.coralDark,
  },
  bubble: {
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderRadius: 22,
    ...SHADOW.card,
  },
  medhaBubble: {
    backgroundColor: 'rgba(255, 255, 255, 0.90)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.95)',
    borderTopLeftRadius: 6,
  },
  userBubble: {
    backgroundColor: COLORS.coral,
    borderTopRightRadius: 6,
    ...SHADOW.soft,
  },
  bubbleText: {
    fontSize: 15,
    lineHeight: 22,
  },
  medhaText: {
    fontFamily: 'Nunito-Regular',
    color: COLORS.navy,
  },
  userText: {
    fontFamily: 'Nunito-SemiBold',
    color: COLORS.white,
  },
  timestamp: {
    fontFamily: 'Nunito-Regular',
    fontSize: 10,
    marginTop: 4,
    marginHorizontal: 6,
  },
  botTimestamp: {
    color: COLORS.navyMuted,
    alignSelf: 'flex-start',
  },
  userTimestamp: {
    color: COLORS.navyMuted,
    alignSelf: 'flex-end',
  },
  typingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
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
  quickSection: {
    marginTop: 10,
    marginBottom: 4,
  },
  quickSectionTitle: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginBottom: 8,
    marginLeft: 4,
  },
  quickRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  quickChip: {
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderRadius: RADIUS.pill,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1.5,
    borderColor: 'rgba(255, 201, 172, 0.5)',
    ...SHADOW.card,
  },
  quickChipPressed: {
    backgroundColor: COLORS.creamSecondary,
    transform: [{ scale: 0.97 }],
  },
  quickText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 13,
    color: COLORS.navy,
  },
  voiceCard: {
    marginTop: 12,
    padding: 14,
  },
  voiceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  voiceIconWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.pinkSoft,
    borderWidth: 1,
    borderColor: COLORS.pink,
    alignItems: 'center',
    justifyContent: 'center',
  },
  voiceTextWrap: {
    flex: 1,
  },
  voiceTitle: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 15,
    color: COLORS.navy,
  },
  voiceSubtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  voiceArrow: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: COLORS.coral,
    alignItems: 'center',
    justifyContent: 'center',
  },
  composerWrapper: {
    paddingVertical: 8,
    backgroundColor: 'transparent',
  },
  composer: {
    minHeight: 56,
    borderRadius: 28,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 201, 172, 0.65)',
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: 18,
    paddingRight: 6,
    paddingVertical: 4,
    ...SHADOW.card,
  },
  input: {
    flex: 1,
    maxHeight: 100,
    fontFamily: 'Nunito-Regular',
    fontSize: 15,
    color: COLORS.navy,
    paddingVertical: 8,
    paddingRight: 8,
  },
  sendButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: COLORS.coral,
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.glow,
  },
  sendDisabled: {
    backgroundColor: '#F0D5C9',
    opacity: 0.6,
  },
  sendPressed: {
    transform: [{ scale: 0.92 }],
  },
});
