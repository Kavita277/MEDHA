import React from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { SHADOW } from '../constants/theme';
import { MedhaBackground } from './medha-background';

interface MedhaScreenProps {
  children: React.ReactNode;
  title?: string;
  eyebrow?: string;
  subtitle?: string;
  back?: boolean;
  onBack?: () => void;
  scroll?: boolean;
  rightIcon?: keyof typeof Ionicons.glyphMap;
  onRightPress?: () => void;
  withBackground?: boolean;
}

export function MedhaScreen({
  children,
  title,
  eyebrow,
  subtitle,
  back = true,
  onBack,
  scroll = true,
  rightIcon,
  onRightPress,
  withBackground = false,
}: MedhaScreenProps) {
  const content = (
    <View style={styles.inner}>
      {(back || rightIcon) && (
        <View style={styles.topBar}>
          {back ? (
            <Pressable
              onPress={onBack}
              style={({ pressed }) => [
                styles.iconButton,
                pressed && styles.iconButtonPressed,
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
          ) : (
            <View />
          )}

          {rightIcon && (
            <Pressable
              onPress={onRightPress}
              style={({ pressed }) => [
                styles.iconButton,
                pressed && styles.iconButtonPressed,
              ]}
              hitSlop={12}
              accessibilityRole="button"
              accessibilityLabel="Action"
            >
              <Ionicons
                name={rightIcon}
                size={20}
                color={COLORS.navy}
              />
            </Pressable>
          )}
        </View>
      )}

      {(eyebrow || title || subtitle) && (
        <View style={styles.heading}>
          {eyebrow && <Text style={styles.eyebrow}>{eyebrow}</Text>}
          {title && <Text style={styles.title}>{title}</Text>}
          {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
        </View>
      )}

      {children}
    </View>
  );

  const body = (
    <SafeAreaView style={styles.safe}>
      {scroll ? (
        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {content}
        </ScrollView>
      ) : (
        content
      )}
    </SafeAreaView>
  );

  if (withBackground) {
    return <MedhaBackground variant="calm">{body}</MedhaBackground>;
  }

  return body;
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: COLORS.cream,
  },

  scroll: {
    flexGrow: 1,
    paddingBottom: 40,
  },

  inner: {
    flex: 1,
    paddingHorizontal: 20,
  },

  topBar: {
    height: 56,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
  },

  iconButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255, 255, 255, 0.85)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.95)',
    alignItems: 'center',
    justifyContent: 'center',
    ...SHADOW.card,
  },

  iconButtonPressed: {
    transform: [{ scale: 0.92 }],
    opacity: 0.85,
  },

  heading: {
    marginTop: 14,
    marginBottom: 22,
  },

  eyebrow: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.5,
    color: COLORS.coralDark,
    textTransform: 'uppercase',
    marginBottom: 8,
  },

  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 28,
    lineHeight: 34,
    color: COLORS.navy,
  },

  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 14,
    lineHeight: 20,
    color: COLORS.navyMuted,
    marginTop: 8,
    maxWidth: 340,
  },
});
