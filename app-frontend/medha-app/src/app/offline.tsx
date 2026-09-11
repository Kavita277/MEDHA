import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';

export default function OfflineScreen() {
  return (
    <View style={styles.container}>
      <View style={styles.art}>
        <Ionicons name="cloud-offline-outline" size={56} color={COLORS.forest} />
      </View>
      <Text style={styles.title}>You’re offline</Text>
      <Text style={styles.subtitle}>
        Some features need a connection. Your space will be here when you’re back online.
      </Text>
      <Pressable onPress={() => router.back()} style={styles.button}>
        <Text style={styles.buttonText}>Try again</Text>
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
  art: {
    width: 118,
    height: 118,
    borderRadius: 59,
    backgroundColor: COLORS.mist,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 28,
  },
  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 39,
    color: COLORS.deepForest,
    textAlign: 'center',
  },
  subtitle: {
    marginTop: 10,
    maxWidth: 300,
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
    marginTop: 28,
  },
  buttonText: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
    color: COLORS.white,
  },
});
