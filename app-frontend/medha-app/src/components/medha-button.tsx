import React from 'react';
import {
  Pressable,
  StyleProp,
  StyleSheet,
  Text,
  TextStyle,
  View,
  ViewStyle,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

export type ButtonVariant =
  | 'primary'
  | 'coral'
  | 'pill'
  | 'soft'
  | 'glass';

interface MedhaButtonProps {
  title: string;
  onPress: () => void;
  icon?: keyof typeof Ionicons.glyphMap;
  iconPosition?: 'left' | 'right';
  variant?: ButtonVariant;
  size?: 'sm' | 'md' | 'lg';
  style?: StyleProp<ViewStyle>;
  textStyle?: StyleProp<TextStyle>;
  disabled?: boolean;
}

export function MedhaButton({
  title,
  onPress,
  icon,
  iconPosition = 'right',
  variant = 'primary',
  size = 'md',
  style,
  textStyle,
  disabled = false,
}: MedhaButtonProps) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.button,
        styles[variant],
        styles[`size_${size}`],
        disabled && styles.disabled,
        pressed && !disabled && styles.pressed,
        style,
      ]}
      accessibilityRole="button"
    >
      {icon && iconPosition === 'left' && (
        <Ionicons
          name={icon}
          size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16}
          color={getIconColor(variant)}
          style={styles.iconLeft}
        />
      )}

      <Text
        style={[
          styles.text,
          styles[`text_${variant}`],
          styles[`textSize_${size}`],
          textStyle,
        ]}
      >
        {title}
      </Text>

      {icon && iconPosition === 'right' && (
        <Ionicons
          name={icon}
          size={size === 'sm' ? 14 : size === 'lg' ? 20 : 16}
          color={getIconColor(variant)}
          style={styles.iconRight}
        />
      )}
    </Pressable>
  );
}

function getIconColor(variant: ButtonVariant): string {
  switch (variant) {
    case 'primary':
    case 'coral':
      return COLORS.white;
    case 'pill':
      return COLORS.blueDark;
    case 'soft':
    case 'glass':
    default:
      return COLORS.navy;
  }
}

const styles = StyleSheet.create({
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: RADIUS.pill,
  },

  // Variants
  primary: {
    backgroundColor: COLORS.charcoal,
    ...SHADOW.fab,
  },
  coral: {
    backgroundColor: COLORS.coral,
    ...SHADOW.glow,
  },
  pill: {
    backgroundColor: COLORS.white,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 14,
    ...SHADOW.card,
  },
  soft: {
    backgroundColor: COLORS.creamSecondary,
    borderWidth: 1,
    borderColor: COLORS.peach,
  },
  glass: {
    backgroundColor: COLORS.glass,
    borderWidth: 1.5,
    borderColor: COLORS.glassBorder,
  },

  // Sizes
  size_sm: {
    height: 36,
    paddingHorizontal: 14,
    borderRadius: 12,
  },
  size_md: {
    height: 48,
    paddingHorizontal: 20,
    borderRadius: 16,
  },
  size_lg: {
    height: 54,
    paddingHorizontal: 24,
    borderRadius: 20,
  },

  // Typography
  text: {
    fontFamily: 'Fredoka-SemiBold',
    letterSpacing: 0.3,
  },
  text_primary: {
    color: COLORS.white,
  },
  text_coral: {
    color: COLORS.white,
  },
  text_pill: {
    color: COLORS.blueDark,
    fontFamily: 'Fredoka-Medium',
  },
  text_soft: {
    color: COLORS.navy,
  },
  text_glass: {
    color: COLORS.navy,
  },

  textSize_sm: {
    fontSize: 12,
  },
  textSize_md: {
    fontSize: 14,
  },
  textSize_lg: {
    fontSize: 16,
  },

  iconLeft: {
    marginRight: 8,
  },
  iconRight: {
    marginLeft: 8,
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.88,
  },
  disabled: {
    opacity: 0.5,
  },
});
