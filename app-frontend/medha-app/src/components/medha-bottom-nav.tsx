import React from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

export type NavTab = 'home' | 'ambient' | 'support' | 'profile';

interface MedhaBottomNavProps {
  activeTab?: NavTab;
}

export function MedhaBottomNav({ activeTab = 'home' }: MedhaBottomNavProps) {
  const router = useRouter();

  const tabs = [
    {
      id: 'home' as NavTab,
      label: 'Home',
      iconActive: 'home' as const,
      iconInactive: 'home-outline' as const,
      emoji: '🏠',
      onPress: () => router.replace('/home'),
    },
    {
      id: 'ambient' as NavTab,
      label: 'Ambient',
      iconActive: 'musical-notes' as const,
      iconInactive: 'musical-notes-outline' as const,
      emoji: '🎵',
      onPress: () => router.push('/ambient'),
    },
    {
      id: 'support' as NavTab,
      label: 'Support',
      iconActive: 'heart' as const,
      iconInactive: 'heart-outline' as const,
      emoji: '💖',
      onPress: () => router.push('/support'),
    },
    {
      id: 'profile' as NavTab,
      label: 'Profile',
      iconActive: 'person' as const,
      iconInactive: 'person-outline' as const,
      emoji: '👤',
      onPress: () => router.push('/profile'),
    },
  ];

  return (
    <View style={styles.wrapper}>
      <View style={styles.glassBar}>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;

          return (
            <Pressable
              key={tab.id}
              onPress={tab.onPress}
              style={({ pressed }) => [
                styles.tabItem,
                isActive && styles.tabItemActive,
                pressed && styles.tabItemPressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel={tab.label}
              accessibilityState={{ selected: isActive }}
            >
              <View style={[styles.iconWrapper, isActive && styles.iconWrapperActive]}>
                <Ionicons
                  name={isActive ? tab.iconActive : tab.iconInactive}
                  size={20}
                  color={isActive ? COLORS.coralDark : COLORS.navyMuted}
                />
              </View>
              <Text
                style={[
                  styles.tabLabel,
                  isActive && styles.tabLabelActive,
                ]}
              >
                {tab.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    paddingHorizontal: 20,
    paddingBottom: 16,
    paddingTop: 8,
  },
  glassBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    backgroundColor: 'rgba(255, 255, 255, 0.78)',
    borderWidth: 1.5,
    borderColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: RADIUS.large,
    paddingVertical: 8,
    paddingHorizontal: 8,
    ...SHADOW.soft,
  },
  tabItem: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: RADIUS.medium,
  },
  tabItemActive: {
    backgroundColor: COLORS.creamSecondary,
  },
  tabItemPressed: {
    transform: [{ scale: 0.94 }],
  },
  iconWrapper: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
  },
  iconWrapperActive: {
    backgroundColor: 'rgba(255, 122, 89, 0.12)',
  },
  tabLabel: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  tabLabelActive: {
    color: COLORS.coralDark,
    fontFamily: 'Fredoka-Medium',
  },
});
