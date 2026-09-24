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

export type NavTab =
  | 'home'
  | 'check-in'
  | 'explore'
  | 'profile'
  | 'ambient'
  | 'support'
  | 'mood-calendar';

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
      onPress: () => router.replace('/home'),
    },
    {
      id: 'check-in' as NavTab,
      label: 'Check-in',
      iconActive: 'add-circle' as const,
      iconInactive: 'add-circle-outline' as const,
      onPress: () => router.push('/check-in'),
    },
    {
      id: 'explore' as NavTab,
      label: 'Explore',
      iconActive: 'compass' as const,
      iconInactive: 'compass-outline' as const,
      onPress: () => router.push('/self-help'),
    },
    {
      id: 'profile' as NavTab,
      label: 'Profile',
      iconActive: 'person' as const,
      iconInactive: 'person-outline' as const,
      onPress: () => router.push('/profile'),
    },
  ];

  return (
    <View style={styles.wrapper}>
      <View style={styles.dock}>
        {tabs.map((tab) => {
          const isActive =
            activeTab === tab.id ||
            (tab.id === 'explore' && activeTab === 'mood-calendar');

          return (
            <Pressable
              key={tab.id}
              onPress={tab.onPress}
              style={({ pressed }) => [
                styles.tabItem,
                pressed && styles.tabItemPressed,
              ]}
              accessibilityRole="button"
              accessibilityLabel={tab.label}
              accessibilityState={{ selected: isActive }}
            >
              <View
                style={[
                  styles.iconWrapper,
                  isActive && styles.iconWrapperActive,
                ]}
              >
                <Ionicons
                  name={isActive ? tab.iconActive : tab.iconInactive}
                  size={21}
                  color={isActive ? COLORS.navy : COLORS.subtleText}
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
    paddingBottom: 14,
    paddingTop: 6,
    backgroundColor: 'transparent',
  },
  dock: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    borderRadius: RADIUS.modal,
    paddingVertical: 8,
    paddingHorizontal: 12,
    ...SHADOW.dock,
  },
  tabItem: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
    paddingHorizontal: 14,
  },
  tabItemPressed: {
    transform: [{ scale: 0.94 }],
    opacity: 0.85,
  },
  iconWrapper: {
    width: 32,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
  },
  iconWrapperActive: {
    backgroundColor: 'rgba(24, 30, 44, 0.06)',
  },
  tabLabel: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 10,
    color: COLORS.subtleText,
    marginTop: 2,
  },
  tabLabelActive: {
    color: COLORS.navy,
    fontFamily: 'Fredoka-Medium',
  },
});
