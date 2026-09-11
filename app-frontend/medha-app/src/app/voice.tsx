import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { Animated, Pressable, StyleSheet, Text, View } from 'react-native';

import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

export default function VoiceScreen() {
  const router = useRouter();
  const [recording, setRecording] = useState(false);
  const pulse = useRef(new Animated.Value(1)).current;

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
          duration: 1800,
          useNativeDriver: true,
        }),
      ]),
    );

    animation.start();

    return () => animation.stop();
  }, []);

  return (
    <MedhaScreen
      eyebrow="Voice check-in"
      title="I’m listening."
      subtitle="Speak freely about how you’re feeling today."
      onBack={() => router.back()}
    >
      {/* HOME BUTTON */}

      <View style={styles.homeRow}>
        <Pressable
          onPress={() => router.replace('/home')}
          style={({ pressed }) => [
            styles.homeButton,
            pressed && styles.homeButtonPressed,
          ]}
          accessibilityRole="button"
          accessibilityLabel="Go to home"
        >
          <Ionicons
            name="home-outline"
            size={17}
            color={COLORS.forest}
          />
        </Pressable>
      </View>

      <View style={styles.center}>
        <Animated.View
          style={[
            styles.outer,
            { transform: [{ scale: pulse }] },
          ]}
        >
          <View style={styles.middle}>
            <View
              style={[
                styles.inner,
                recording && styles.recording,
              ]}
            >
              <Ionicons
                name={recording ? 'mic' : 'mic-outline'}
                size={35}
                color={COLORS.deepForest}
              />
            </View>
          </View>
        </Animated.View>

        <Text style={styles.timer}>
          {recording ? '00:12 / 02:00' : '00:00 / 02:00'}
        </Text>

        <Text style={styles.status}>
          {recording
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
            setRecording(false);
            router.push('/chat');
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

      {!recording && (
        <Pressable
          onPress={() => router.push('/chat')}
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
  homeRow: {
    alignItems: 'flex-end',
    marginTop: -4,
    marginBottom: -8,
  },

  homeButton: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },

  homeButtonPressed: {
    opacity: 0.7,
    transform: [{ scale: 0.94 }],
  },

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