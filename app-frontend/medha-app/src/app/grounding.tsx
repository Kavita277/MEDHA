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

export default function GroundingScreen() {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState('Ready');

  const scale = useRef(new Animated.Value(0.75)).current;

  useEffect(() => {
    if (!running) {
      scale.stopAnimation();
      scale.setValue(0.75);
      setPhase('Ready');
      return;
    }

    const run = () => {
      setPhase('Breathe in');

      Animated.timing(scale, {
        toValue: 1,
        duration: 4000,
        useNativeDriver: true,
      }).start(() => {
        setPhase('Hold');

        setTimeout(() => {
          setPhase('Breathe out');

          Animated.timing(scale, {
            toValue: 0.75,
            duration: 6000,
            useNativeDriver: true,
          }).start(() => {
            if (running) run();
          });
        }, 2000);
      });
    };

    run();

    return () => scale.stopAnimation();
  }, [running]);

  return (
    <MedhaScreen
      eyebrow="Grounding"
      title="Come back to this moment."
      subtitle="Nothing to fix. Just follow the rhythm for a little while."
      onBack={() => router.back()}
      scroll={false}
    >
      <View style={styles.center}>
        <Animated.View
          style={[
            styles.field,
            { transform: [{ scale }] },
          ]}
        >
          <View style={styles.core}>
            <Text style={styles.phase}>{phase}</Text>
          </View>
        </Animated.View>

        <Text style={styles.instruction}>
          {running
            ? 'Let your breathing become unhurried.'
            : 'When you’re ready, begin.'}
        </Text>
      </View>

      <Pressable
        onPress={() => setRunning(!running)}
        style={styles.button}
      >
        <Ionicons
          name={running ? 'pause' : 'leaf-outline'}
          size={18}
          color={COLORS.white}
        />

        <Text style={styles.buttonText}>
          {running ? 'Pause' : 'Begin'}
        </Text>
      </Pressable>

      <Pressable
        onPress={() => router.push('/home')}
        style={styles.done}
      >
        <Text style={styles.doneText}>I’m feeling ready</Text>
      </Pressable>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },

  field: {
    width: 260,
    height: 260,
    borderRadius: 130,
    backgroundColor: 'rgba(170,188,180,0.28)',
    alignItems: 'center',
    justifyContent: 'center',
  },

  core: {
    width: 160,
    height: 160,
    borderRadius: 80,
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },

  phase: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 27,
    color: COLORS.forest,
  },

  instruction: {
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    color: COLORS.mutedText,
    marginTop: 30,
    textAlign: 'center',
  },

  button: {
    height: 54,
    borderRadius: 27,
    backgroundColor: COLORS.forest,
    flexDirection: 'row',
    gap: 9,
    alignItems: 'center',
    justifyContent: 'center',
  },

  buttonText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.white,
    fontSize: 13,
  },

  done: {
    alignItems: 'center',
    paddingVertical: 18,
  },

  doneText: {
    fontFamily: 'Inter-Medium',
    color: COLORS.mutedText,
    fontSize: 12,
  },
});