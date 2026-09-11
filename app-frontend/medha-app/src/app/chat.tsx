import React, { useEffect, useRef, useState } from 'react';
import {
  Animated,
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
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
          toValue: 1.12,
          duration: 1800,
          useNativeDriver: true,
        }),
        Animated.timing(pulse, {
          toValue: 1,
          duration: 1800,
          useNativeDriver: true,
        }),
      ])
    );

    animation.start();

    return () => animation.stop();
  }, []);

  return (
    <MedhaScreen
      eyebrow="Voice check-in"
      title="I'm listening."
      subtitle="You don't need to organise your thoughts first. Just speak."
      onBack={() => router.back()}
    >
      <View style={styles.center}>
        <Animated.View
          style={[
            styles.outerOrb,
            {
              transform: [{ scale: pulse }],
            },
          ]}
        >
          <View style={styles.middleOrb}>
            <View
              style={[
                styles.innerOrb,
                recording && styles.recordingOrb,
              ]}
            >
              <Ionicons
                name={recording ? 'mic' : 'mic-outline'}
                size={34}
                color={COLORS.deepForest}
              />
            </View>
          </View>
        </Animated.View>

        <Text style={styles.status}>
          {recording
            ? 'Listening gently...'
            : 'Tap when you’re ready'}
        </Text>

        <Text style={styles.hint}>
          You can pause whenever you want.
        </Text>
      </View>

      <Pressable
        onPress={() => setRecording(!recording)}
        style={[
          styles.recordButton,
          recording && styles.stopButton,
        ]}
      >
        <Ionicons
          name={recording ? 'stop' : 'mic'}
          size={21}
          color={COLORS.white}
        />

        <Text style={styles.recordText}>
          {recording ? 'Finish' : 'Start speaking'}
        </Text>
      </Pressable>

      {!recording && (
        <Pressable
          onPress={() => router.push('/home')}
          style={styles.skip}
        >
          <Text style={styles.skipText}>
            Maybe later
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

  outerOrb: {
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: 'rgba(166,170,145,0.18)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  middleOrb: {
    width: 205,
    height: 205,
    borderRadius: 103,
    backgroundColor: 'rgba(170,188,180,0.32)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  innerOrb: {
    width: 125,
    height: 125,
    borderRadius: 63,
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  recordingOrb: {
    backgroundColor: COLORS.mist,
    borderColor: COLORS.forest,
  },

  status: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 24,
    color: COLORS.deepForest,
    marginTop: 32,
  },

  hint: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    color: COLORS.mutedText,
    marginTop: 8,
  },

  recordButton: {
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
  },

  stopButton: {
    backgroundColor: COLORS.wood,
  },

  recordText: {
    color: COLORS.white,
    fontFamily: 'Inter-Medium',
    fontSize: 13,
  },

  skip: {
    alignItems: 'center',
    paddingVertical: 18,
  },

  skipText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.mutedText,
    fontSize: 12,
  },
});