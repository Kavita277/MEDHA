import React, { useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { COLORS } from '../constants/colors';

const sounds = [
  { name: 'Forest', icon: 'leaf-outline' as const },
  { name: 'Rain', icon: 'rainy-outline' as const },
  { name: 'Ocean', icon: 'water-outline' as const },
  { name: 'Wind', icon: 'cloud-outline' as const },
  { name: 'Fireplace', icon: 'flame-outline' as const },
  { name: 'Silence', icon: 'moon-outline' as const },
];

export default function AmbientScreen() {
  const router = useRouter();
  const [selected, setSelected] = useState('Forest');

  return (
    <MedhaScreen
      eyebrow="Ambient"
      title="Choose your atmosphere."
      subtitle="A little background sound, if you want it. Nothing plays unless you choose it."
      onBack={() => router.back()}
    >
      <View style={styles.visual}>
        <View style={styles.visualCore}>
          <Ionicons
            name="leaf"
            size={30}
            color={COLORS.forest}
          />
        </View>
      </View>

      <View style={styles.grid}>
        {sounds.map((sound) => {
          const active = selected === sound.name;

          return (
            <Pressable
              key={sound.name}
              onPress={() => setSelected(sound.name)}
              style={[
                styles.sound,
                active && styles.active,
              ]}
            >
              <Ionicons
                name={sound.icon}
                size={22}
                color={active ? COLORS.white : COLORS.forest}
              />

              <Text
                style={[
                  styles.soundText,
                  active && styles.activeText,
                ]}
              >
                {sound.name}
              </Text>
            </Pressable>
          );
        })}
      </View>

      <View style={styles.player}>
        <View>
          <Text style={styles.nowPlaying}>
            SELECTED ATMOSPHERE
          </Text>

          <Text style={styles.current}>
            {selected}
          </Text>
        </View>

        <Pressable style={styles.play}>
          <Ionicons
            name="play"
            size={18}
            color={COLORS.white}
          />
        </Pressable>
      </View>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  visual: {
    height: 190,
    borderRadius: 30,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },

  visualCore: {
    width: 110,
    height: 110,
    borderRadius: 55,
    backgroundColor: COLORS.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },

  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },

  sound: {
    width: '31.8%',
    aspectRatio: 1,
    borderRadius: 20,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },

  active: {
    backgroundColor: COLORS.forest,
    borderColor: COLORS.forest,
  },

  soundText: {
    fontFamily: 'Inter-Medium',
    fontSize: 10,
    color: COLORS.deepForest,
  },

  activeText: {
    color: COLORS.white,
  },

  player: {
    marginTop: 24,
    padding: 17,
    borderRadius: 22,
    backgroundColor: COLORS.surfaceWarm,
    flexDirection: 'row',
    alignItems: 'center',
  },

  nowPlaying: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.5,
    color: COLORS.moss,
  },

  current: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 23,
    color: COLORS.deepForest,
    marginTop: 2,
  },

  play: {
    marginLeft: 'auto',
    width: 46,
    height: 46,
    borderRadius: 23,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
  },
});