import React from 'react';
import {
  Image,
  Pressable,
  StyleSheet,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { COLORS } from '../constants/colors';
import { SHADOW } from '../constants/theme';

const MEDHA_LOGO = require('../../assets/images/medha-logo.png');

export function MedhaFloatingChat() {
  const router = useRouter();

  return (
    <View style={styles.container} pointerEvents="box-none">
      <Pressable
        onPress={() => router.push('/chat')}
        style={({ pressed }) => [
          styles.fab,
          pressed && styles.pressed,
        ]}
        accessibilityRole="button"
        accessibilityLabel="Chat with MEDHA"
      >
        <Image
          source={MEDHA_LOGO}
          style={styles.logo}
          resizeMode="contain"
        />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    right: 22,
    bottom: 84,
    zIndex: 99,
  },
  fab: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.white,
    borderWidth: 1.5,
    borderColor: 'rgba(0, 0, 0, 0.08)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.dock,
  },
  logo: {
    width: 32,
    height: 32,
  },
  pressed: {
    transform: [{ scale: 0.92 }],
    opacity: 0.9,
  },
});
