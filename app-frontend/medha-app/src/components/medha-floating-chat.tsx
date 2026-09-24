import React from 'react';
import {
  Pressable,
  StyleSheet,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SHADOW } from '../constants/theme';

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
        <Ionicons name="chatbubble-ellipses" size={22} color={COLORS.white} />
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
    backgroundColor: COLORS.charcoal,
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.fab,
  },
  pressed: {
    transform: [{ scale: 0.92 }],
    opacity: 0.9,
  },
});
