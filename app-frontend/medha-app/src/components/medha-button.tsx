import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';

interface MedhaButtonProps {
  title: string;
  onPress: () => void;
  icon?: keyof typeof Ionicons.glyphMap;
  variant?: 'primary' | 'soft';
}

export function MedhaButton({
  title,
  onPress,
  icon,
  variant = 'primary',
}: MedhaButtonProps) {
  const isSoft = variant === 'soft';

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        isSoft ? styles.softButton : styles.primaryButton,
        pressed && styles.pressed,
      ]}
    >
      <Text
        style={[
          styles.text,
          isSoft ? styles.softText : styles.primaryText,
        ]}
      >
        {title}
      </Text>

      {icon && (
        <View
          style={[
            styles.icon,
            isSoft ? styles.softIcon : styles.primaryIcon,
          ]}
        >
          <Ionicons
            name={icon}
            size={17}
            color={
              isSoft
                ? COLORS.deepForest
                : COLORS.white
            }
          />
        </View>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    height: 52,
    borderRadius: 26,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 7,
  },

  primaryButton: {
    backgroundColor: COLORS.forest,
  },

  softButton: {
    backgroundColor: COLORS.surfaceWarm,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  text: {
    fontFamily: 'Inter-Medium',
    fontSize: 13,
  },

  primaryText: {
    color: COLORS.white,
  },

  softText: {
    color: COLORS.deepForest,
  },

  icon: {
    position: 'absolute',
    right: 7,
    width: 38,
    height: 38,
    borderRadius: 19,
    alignItems: 'center',
    justifyContent: 'center',
  },

  primaryIcon: {
    backgroundColor: 'rgba(255,255,255,0.15)',
  },

  softIcon: {
    backgroundColor: COLORS.mist,
  },

  pressed: {
    transform: [{ scale: 0.98 }],
    opacity: 0.82,
  },
});