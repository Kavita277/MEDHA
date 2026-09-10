import React from 'react';
import {
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';

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
}: MedhaScreenProps) {
  const content = (
    <View style={styles.inner}>
      {(back || rightIcon) && (
        <View style={styles.topBar}>
          {back ? (
            <Pressable
              onPress={onBack}
              style={styles.iconButton}
              hitSlop={12}
            >
              <Ionicons
                name="arrow-back"
                size={19}
                color={COLORS.deepForest}
              />
            </Pressable>
          ) : (
            <View />
          )}

          {rightIcon && (
            <Pressable
              onPress={onRightPress}
              style={styles.iconButton}
              hitSlop={12}
            >
              <Ionicons
                name={rightIcon}
                size={19}
                color={COLORS.deepForest}
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

  return (
    <SafeAreaView style={styles.safe}>
      {scroll ? (
        <ScrollView
          contentContainerStyle={styles.scroll}
          showsVerticalScrollIndicator={false}
        >
          {content}
        </ScrollView>
      ) : (
        content
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: COLORS.background,
  },

  scroll: {
    flexGrow: 1,
    paddingBottom: 40,
  },

  inner: {
    flex: 1,
    paddingHorizontal: 24,
  },

  topBar: {
    height: 62,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },

  iconButton: {
    width: 42,
    height: 42,
    borderRadius: 21,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    justifyContent: 'center',
  },

  heading: {
    marginTop: 18,
    marginBottom: 28,
  },

  eyebrow: {
    fontFamily: 'Inter-Medium',
    fontSize: 9,
    letterSpacing: 2,
    color: COLORS.forest,
    textTransform: 'uppercase',
    marginBottom: 12,
  },

  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 38,
    lineHeight: 41,
    color: COLORS.deepForest,
  },

  subtitle: {
    fontFamily: 'Inter-Regular',
    fontSize: 14,
    lineHeight: 21,
    color: COLORS.mutedText,
    marginTop: 12,
    maxWidth: 340,
  },
});