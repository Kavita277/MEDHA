import React from 'react';
import {
  Pressable,
  StyleProp,
  StyleSheet,
  View,
  ViewStyle,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

export type CardVariant =
  | 'glass'
  | 'blueHero'
  | 'pink'
  | 'green'
  | 'yellow'
  | 'peach'
  | 'lavender'
  | 'sage'
  | 'surface';

interface MedhaCardProps {
  children: React.ReactNode;
  variant?: CardVariant;
  style?: StyleProp<ViewStyle>;
  onPress?: () => void;
  accessibilityLabel?: string;
}

export function MedhaCard({
  children,
  variant = 'glass',
  style,
  onPress,
  accessibilityLabel,
}: MedhaCardProps) {
  const isBlueHero = variant === 'blueHero';

  const cardStyle = [
    styles.card,
    variantStyles[variant],
    style,
  ];

  if (isBlueHero) {
    const content = (
      <LinearGradient
        colors={[COLORS.blueDark, '#6FC3E8']}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={[styles.heroGradient, style]}
      >
        {children}
      </LinearGradient>
    );

    if (onPress) {
      return (
        <Pressable
          onPress={onPress}
          style={({ pressed }) => [
            styles.pressable,
            pressed && styles.pressed,
          ]}
          accessibilityRole="button"
          accessibilityLabel={accessibilityLabel}
        >
          {content}
        </Pressable>
      );
    }
    return content;
  }

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        style={({ pressed }) => [
          cardStyle,
          pressed && styles.pressed,
        ]}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel}
      >
        {children}
      </Pressable>
    );
  }

  return <View style={cardStyle}>{children}</View>;
}

const styles = StyleSheet.create({
  card: {
    borderRadius: RADIUS.card,
    padding: 16,
    ...SHADOW.card,
  },
  heroGradient: {
    borderRadius: RADIUS.card + 4,
    padding: 20,
    ...SHADOW.soft,
    overflow: 'hidden',
  },
  pressable: {
    borderRadius: RADIUS.card,
  },
  pressed: {
    transform: [{ scale: 0.985 }],
    opacity: 0.92,
  },
});

const variantStyles = StyleSheet.create<Record<CardVariant, ViewStyle>>({
  glass: {
    backgroundColor: COLORS.glass,
    borderWidth: 1.5,
    borderColor: COLORS.glassBorder,
  },
  blueHero: {},
  pink: {
    backgroundColor: COLORS.pinkSoft,
    borderWidth: 1,
    borderColor: COLORS.pink,
  },
  green: {
    backgroundColor: COLORS.greenSoft,
    borderWidth: 1,
    borderColor: COLORS.green,
  },
  yellow: {
    backgroundColor: COLORS.yellowSoft,
    borderWidth: 1,
    borderColor: COLORS.yellow,
  },
  peach: {
    backgroundColor: COLORS.creamSecondary,
    borderWidth: 1,
    borderColor: COLORS.peach,
  },
  lavender: {
    backgroundColor: '#F3EFFF',
    borderWidth: 1,
    borderColor: COLORS.lavender,
  },
  sage: {
    backgroundColor: COLORS.sageSoft,
    borderWidth: 1,
    borderColor: COLORS.sage,
  },
  surface: {
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
});
