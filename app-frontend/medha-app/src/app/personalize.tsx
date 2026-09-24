import React, { useState } from 'react';
import {
  ImageBackground,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

const options = [
  {
    title: 'Nature',
    image:
      'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?q=85&w=600&auto=format&fit=crop',
  },
  {
    title: 'Music',
    image:
      'https://images.unsplash.com/photo-1511379938547-c1f69419868d?q=85&w=600&auto=format&fit=crop',
  },
  {
    title: 'Warm Spaces',
    image:
      'https://images.unsplash.com/photo-1600607687920-4e2a09cf159d?q=85&w=600&auto=format&fit=crop',
  },
  {
    title: 'Minimal',
    image:
      'https://images.unsplash.com/photo-1494438639946-1ebd1d20bf85?q=85&w=600&auto=format&fit=crop',
  },
  {
    title: 'Animals',
    image:
      'https://images.unsplash.com/photo-1552053831-71594a27632d?q=85&w=600&auto=format&fit=crop',
  },
  {
    title: 'Art',
    image:
      'https://images.unsplash.com/photo-1549490349-8643362247b5?q=85&w=600&auto=format&fit=crop',
  },
];

export default function PersonalizeScreen() {
  const router = useRouter();
  const [selected, setSelected] = useState<string[]>([]);

  function toggle(title: string) {
    setSelected((current) =>
      current.includes(title)
        ? current.filter((item) => item !== title)
        : [...current, title]
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.content}
        >
          {/* TOP BAR / BACK */}
          <View style={styles.topBar}>
            <Pressable
              onPress={() => router.back()}
              style={({ pressed }) => [
                styles.iconButton,
                pressed && styles.pressed,
              ]}
              hitSlop={12}
              accessibilityRole="button"
              accessibilityLabel="Back"
            >
              <Ionicons
                name="arrow-back"
                size={20}
                color={COLORS.navy}
              />
            </Pressable>
          </View>

          {/* HEADINGS */}
          <Text style={styles.eyebrow}>PREFERENCES</Text>
          <Text style={styles.title}>
            What soothes you{'\n'}the most?
          </Text>

          <Text style={styles.subtitle}>
            Select a few to personalise your space.
          </Text>

          {/* 2-COLUMN OPTIONS GRID */}
          <View style={styles.grid}>
            {options.map((option) => {
              const active = selected.includes(option.title);

              return (
                <Pressable
                  key={option.title}
                  onPress={() => toggle(option.title)}
                  style={({ pressed }) => [
                    styles.card,
                    active && styles.cardActive,
                    pressed && styles.pressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel={option.title}
                >
                  <ImageBackground
                    source={{ uri: option.image }}
                    style={styles.image}
                    imageStyle={styles.imageRadius}
                  >
                    <View style={styles.overlay} />

                    <View style={styles.cardBottom}>
                      <Text style={styles.cardTitle}>
                        {option.title}
                      </Text>
                    </View>

                    {active && (
                      <View style={styles.check}>
                        <Ionicons
                          name="checkmark"
                          size={15}
                          color={COLORS.white}
                        />
                      </View>
                    )}
                  </ImageBackground>
                </Pressable>
              );
            })}
          </View>

          {/* CONTINUATION BUTTON ROUTING TO ONBOARDING-COMPLETE (SCREEN 29) */}
          <Pressable
            onPress={() => router.replace('/onboarding-complete')}
            style={({ pressed }) => [
              styles.button,
              pressed && styles.pressed,
            ]}
            accessibilityRole="button"
            accessibilityLabel="Continue to completion"
          >
            <Text style={styles.buttonText}>
              Continue
            </Text>
            <Ionicons name="arrow-forward" size={17} color={COLORS.white} />
          </Pressable>
        </ScrollView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: COLORS.porcelain,
  },
  container: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 20,
    paddingTop: 8,
    paddingBottom: 36,
  },

  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.subtle,
  },

  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.4,
    color: COLORS.coralDark,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 30,
    lineHeight: 36,
    color: COLORS.navy,
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 20,
    color: COLORS.navyMuted,
    marginTop: 8,
    marginBottom: 24,
  },

  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    rowGap: 14,
  },

  card: {
    width: '48%',
    height: 145,
    borderRadius: RADIUS.card,
    overflow: 'hidden',
    backgroundColor: COLORS.white,
    borderWidth: 1.5,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  cardActive: {
    borderWidth: 2.5,
    borderColor: COLORS.navy,
  },

  image: {
    flex: 1,
  },
  imageRadius: {
    borderRadius: RADIUS.card - 2,
  },
  overlay: {
    ...StyleSheet.absoluteFill,
    backgroundColor: 'rgba(24, 30, 44, 0.38)',
  },

  cardBottom: {
    position: 'absolute',
    left: 14,
    bottom: 12,
    right: 14,
  },
  cardTitle: {
    color: COLORS.white,
    fontFamily: 'Fredoka-Medium',
    fontSize: 14,
  },

  check: {
    position: 'absolute',
    top: 10,
    right: 10,
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: COLORS.navy,
    alignItems: 'center',
    justifyContent: 'center',
  },

  button: {
    height: 52,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.navy,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 28,
    ...SHADOW.subtle,
  },
  buttonText: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.white,
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.88,
  },
});
