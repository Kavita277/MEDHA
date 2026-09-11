import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';

import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';
import { voiceService } from '../services/api';

export default function VoiceScreen() {
  const router = useRouter();
  const [recording, setRecording] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [seconds, setSeconds] = useState(0);
  const pulse = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    let interval: any;
    if (recording) {
      interval = setInterval(() => {
        setSeconds((prev) => {
          if (prev >= 120) {
            handleFinishRecording();
            return prev;
          }
          return prev + 1;
        });
      }, 1000);
    } else {
      setSeconds(0);
    }
    return () => clearInterval(interval);
  }, [recording]);

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, {
          toValue: 1.1,
          duration: 1800,
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 1,
          duration: recording ? 1000 : 1800,
          useNativeDriver: true,
        }),
      ]),
    );

    animation.start();
    return () => animation.stop();
  }, [recording]);

  const formatTimer = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const remainingSecs = sec % 60;
    return `${String(mins).padStart(2, '0')}:${String(remainingSecs).padStart(2, '0')} / 02:00`;
  };

  const handleFinishRecording = async () => {
    setRecording(false);
    setSubmitting(true);
    setStatusMessage('Analyzing acoustic prosody & features...');
    try {
      await voiceService.uploadCheckin();
      setStatusMessage('Voice check-in processed successfully!');
      setTimeout(() => {
        router.push('/chat' as any);
      }, 1000);
    } catch (err: any) {
      console.warn('Voice upload error:', err);
      setStatusMessage('Voice recorded! Continuing to talk with MEDHA...');
      setTimeout(() => {
        router.push('/chat' as any);
      }, 1200);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <MedhaScreen
      eyebrow="Voice check-in"
      title="I’m listening."
      subtitle="Speak freely about how you’re feeling today."
      onBack={() => router.back()}
    >
      <View style={styles.center}>
        <Animated.View style={[styles.outer, { transform: [{ scale: pulse }] }]}>
          <View style={styles.middle}>
            <View style={[styles.inner, recording && styles.recording]}>
              <Ionicons
                name="mic"
                size={36}
                color={recording ? COLORS.forest : COLORS.mutedText}
              />
            </View>
          </View>
        </Animated.View>

        <Text style={styles.timer}>
          {recording ? formatTimer(seconds) : '00:00 / 02:00'}
        </Text>

        <Text style={styles.status}>
          {submitting
            ? 'Processing voice...'
            : recording
            ? 'Listening gently...'
            : 'Tap when you’re ready'}
        </Text>

        <Text style={styles.hint}>
          You can stop whenever you want.
        </Text>
      </View>

      <Pressable
        onPress={() => {
          if (recording) {
            handleFinishRecording();
          } else {
            setRecording(true);
          }
        }}
        style={[
          styles.button,
          recording && styles.stop,
        ]}
      >
        <Ionicons
          name={recording ? 'stop' : 'mic'}
          size={20}
          color={COLORS.white}
        />

        <Text style={styles.buttonText}>
          {recording
            ? 'Finish & talk with MEDHA'
            : 'Tap to speak'}
        </Text>
      </Pressable>

      {!recording && !submitting && (
        <Pressable
          onPress={() => router.push('/chat' as any)}
          style={styles.skip}
        >
          <Text style={styles.skipText}>
            Skip voice · continue to Talk with MEDHA
          </Text>
        </Pressable>
      )}
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    minHeight: 390,
    alignItems: 'center',
    justifyContent: 'center',
  },

  outer: {
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: 'rgba(166,170,145,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  middle: {
    width: 205,
    height: 205,
    borderRadius: 103,
    backgroundColor: 'rgba(170,188,180,0.32)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  inner: {
    width: 125,
    height: 125,
    borderRadius: 63,
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  recording: {
    backgroundColor: COLORS.mist,
    borderColor: COLORS.forest,
  },

  timer: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.mutedText,
    marginTop: 23,
    letterSpacing: 1,
  },

  status: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 25,
    color: COLORS.deepForest,
    marginTop: 8,
  },

  hint: {
    fontFamily: 'Inter-Regular',
    fontSize: 10,
    color: COLORS.mutedText,
    marginTop: 7,
  },

  button: {
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
  },

  stop: {
    backgroundColor: COLORS.wood,
  },

  buttonText: {
    color: COLORS.white,
    fontFamily: 'Inter-Medium',
    fontSize: 12,
  },

  skip: {
    alignItems: 'center',
    paddingVertical: 17,
  },

  skipText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.mutedText,
    fontSize: 10,
  },
});