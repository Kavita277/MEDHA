import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';

export default function ErrorStateScreen() {
  return (
    <View style={styles.container}>
      <View style={styles.leaf}>
        <Ionicons name="leaf-outline" size={54} color={COLORS.forest} />
      </View>
      <Text style={styles.title}>Something went wrong</Text>
      <Text style={styles.subtitle}>
        But it’s not you. We couldn’t complete that moment. Please try again.
      </Text>
      <Pressable onPress={() => router.back()} style={styles.button}>
        <Text style={styles.buttonText}>Try again</Text>
        <Ionicons name="refresh-outline" size={18} color={COLORS.white} />
      </Pressable>
      <Pressable onPress={() => router.replace('/home')} style={styles.home}>
        <Text style={styles.homeText}>Return to MEDHA</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    paddingHorizontal: 28,
    alignItems: 'center',
    justifyContent: 'center',
  },
  leaf: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 28,
  },
  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 38,
    color: COLORS.deepForest,
    textAlign: 'center',
  },
  subtitle: {
    maxWidth: 300,
    marginTop: 10,
    fontFamily: 'Inter-Regular',
    fontSize: 12,
    lineHeight: 19,
    color: COLORS.mutedText,
    textAlign: 'center',
  },
  button: {
    width: '100%',
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.forest,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 9,
    marginTop: 28,
  },
  buttonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
  home: {
    paddingVertical: 18,
  },
  homeText: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.mutedText,
  },
});
