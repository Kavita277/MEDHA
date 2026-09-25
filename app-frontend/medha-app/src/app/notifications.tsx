import React, { useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';

import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW, TOP_HEADER_PADDING } from '../constants/theme';
import { MedhaScreenBackground } from '../components/medha-screen-background';

type NotificationCategory = 'all' | 'check-in' | 'reminder';
type NotificationPriority = 'Informational' | 'Attention' | 'Urgent';

interface NotificationItem {
  id: string;
  category: 'check-in' | 'reminder';
  priority: NotificationPriority;
  title: string;
  message: string;
  timestamp: string;
  action?: string;
  actionRoute?: string;
  icon: keyof typeof Ionicons.glyphMap;
  iconBg: string;
  iconColor: string;
  read: boolean;
}

const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: '1',
    category: 'check-in',
    priority: 'Informational',
    title: 'Keep going!',
    message: "You've completed 3 check-ins this week. Showing up is powerful.",
    timestamp: '2m ago',
    action: 'View Progress',
    actionRoute: '/mood-calendar',
    icon: 'sparkles',
    iconBg: '#EDE7FB',
    iconColor: '#7856D6',
    read: false,
  },
  {
    id: '2',
    category: 'check-in',
    priority: 'Informational',
    title: 'Time for a check-in',
    message: 'How are you feeling today? Take a moment to check in with yourself.',
    timestamp: '1h ago',
    action: 'Check In',
    actionRoute: '/check-in',
    icon: 'sunny',
    iconBg: '#FFEADB',
    iconColor: '#E66A35',
    read: false,
  },
  {
    id: '3',
    category: 'reminder',
    priority: 'Informational',
    title: 'New resource for you',
    message: 'Try a gentle 4-2-6 breathing exercise to settle your morning space.',
    timestamp: '3h ago',
    action: 'Start Breathing',
    actionRoute: '/grounding',
    icon: 'leaf',
    iconBg: '#FFF4D6',
    iconColor: '#CCA01A',
    read: false,
  },
  {
    id: '4',
    category: 'reminder',
    priority: 'Attention',
    title: 'Quiet reflection time',
    message: 'A space for your thoughts is always open in your private journal.',
    timestamp: 'Yesterday',
    action: 'Open Journal',
    actionRoute: '/journal',
    icon: 'book',
    iconBg: '#EDE7FB',
    iconColor: '#7856D6',
    read: true,
  },
  {
    id: '5',
    category: 'reminder',
    priority: 'Urgent',
    title: 'Support is always available',
    message: 'If feelings ever become overwhelming, professional and helpline support is ready 24/7.',
    timestamp: '2d ago',
    action: 'View Support Directory',
    actionRoute: '/support',
    icon: 'heart',
    iconBg: '#FFEBEA',
    iconColor: '#E03E3E',
    read: true,
  },
];

export default function NotificationsScreen() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<NotificationItem[]>(INITIAL_NOTIFICATIONS);
  const [activeFilter, setActiveFilter] = useState<NotificationCategory>('all');

  const filtered = notifications.filter((item) => {
    if (activeFilter === 'all') return true;
    return item.category === activeFilter;
  });

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const toggleRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: !n.read } : n))
    );
  };

  const handleAction = (item: NotificationItem) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === item.id ? { ...n, read: true } : n))
    );
    if (item.actionRoute) {
      router.push(item.actionRoute as any);
    }
  };

  return (
    <View style={styles.root}>
      <MedhaScreenBackground />
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.container}>
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* TOP BAR */}
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
              <Ionicons name="arrow-back" size={20} color={COLORS.navy} />
            </Pressable>

            {unreadCount > 0 && (
              <Pressable
                onPress={markAllRead}
                style={({ pressed }) => [
                  styles.markReadBtn,
                  pressed && styles.pressed,
                ]}
                accessibilityRole="button"
                accessibilityLabel="Mark all notifications as read"
              >
                <Text style={styles.markReadText}>Mark all as read</Text>
              </Pressable>
            )}
          </View>

          {/* SCREEN TITLE */}
          <View style={styles.header}>
            <Text style={styles.title}>Notifications</Text>
            <Text style={styles.subtitle}>
              Gentle check-in reminders and wellbeing updates.
            </Text>
          </View>

          {/* CATEGORY FILTER PILLS MATCHING REFERENCE SCREEN 21 */}
          <View style={styles.filtersRow}>
            {[
              { id: 'all' as NotificationCategory, label: 'All' },
              { id: 'check-in' as NotificationCategory, label: 'Check-ins' },
              { id: 'reminder' as NotificationCategory, label: 'Reminders' },
            ].map((tab) => {
              const active = activeFilter === tab.id;
              const count =
                tab.id === 'all'
                  ? notifications.length
                  : notifications.filter((n) => n.category === tab.id).length;

              return (
                <Pressable
                  key={tab.id}
                  onPress={() => setActiveFilter(tab.id)}
                  style={({ pressed }) => [
                    styles.filterChip,
                    active && styles.filterChipActive,
                    pressed && styles.pressed,
                  ]}
                  accessibilityRole="tab"
                  accessibilityState={{ selected: active }}
                >
                  <Text
                    style={[
                      styles.filterText,
                      active && styles.filterTextActive,
                    ]}
                  >
                    {tab.label}
                  </Text>
                  {count > 0 && (
                    <View
                      style={[
                        styles.filterBadge,
                        active && styles.filterBadgeActive,
                      ]}
                    >
                      <Text
                        style={[
                          styles.filterBadgeText,
                          active && styles.filterBadgeTextActive,
                        ]}
                      >
                        {count}
                      </Text>
                    </View>
                  )}
                </Pressable>
              );
            })}
          </View>

          {/* NOTIFICATION FEED */}
          {filtered.length === 0 ? (
            <View style={styles.emptyCard}>
              <View style={styles.emptyIconWrap}>
                <Ionicons name="sparkles" size={24} color={COLORS.sage} />
              </View>
              <Text style={styles.emptyTitle}>All caught up</Text>
              <Text style={styles.emptySubtitle}>
                No notifications in this section. Take a calm breath for yourself.
              </Text>
            </View>
          ) : (
            <View style={styles.notificationList}>
              {filtered.map((item) => (
                <Pressable
                  key={item.id}
                  onPress={() => toggleRead(item.id)}
                  style={({ pressed }) => [
                    styles.notificationCard,
                    !item.read && styles.notificationCardUnread,
                    pressed && styles.pressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel={`${item.title}, ${item.message}`}
                >
                  {/* Left Pastel Squircle Icon Badge */}
                  <View style={[styles.iconBadge, { backgroundColor: item.iconBg }]}>
                    <Ionicons name={item.icon} size={20} color={item.iconColor} />
                  </View>

                  {/* Body Content */}
                  <View style={styles.contentWrap}>
                    <View style={styles.titleRow}>
                      <Text style={styles.cardTitle}>{item.title}</Text>
                      <View style={styles.timeWrap}>
                        {!item.read && <View style={styles.unreadDot} />}
                        <Text style={styles.timestampText}>{item.timestamp}</Text>
                      </View>
                    </View>

                    <Text style={styles.cardMessage}>{item.message}</Text>

                    {item.action && (
                      <Pressable
                        onPress={() => handleAction(item)}
                        style={({ pressed }) => [
                          styles.actionPill,
                          pressed && styles.pressed,
                        ]}
                        accessibilityRole="button"
                        accessibilityLabel={item.action}
                      >
                        <Text style={styles.actionPillText}>{item.action}</Text>
                        <Ionicons name="arrow-forward" size={13} color={COLORS.navy} />
                      </Pressable>
                    )}
                  </View>
                </Pressable>
              ))}
            </View>
          )}

          {/* FOOTER NOTE */}
          <View style={styles.footerNote}>
            <Ionicons name="shield-checkmark-outline" size={16} color={COLORS.sage} />
            <Text style={styles.footerNoteText}>
              MEDHA notifications are intentional and designed to support your daily rhythm.
            </Text>
          </View>
        </ScrollView>
      </View>
    </SafeAreaView>
  </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: COLORS.porcelain,
  },
  safeArea: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  container: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 20,
    paddingTop: TOP_HEADER_PADDING,
    paddingBottom: 36,
  },

  /* TOP BAR */
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
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
  markReadBtn: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  markReadText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: COLORS.coralDark,
  },

  /* HEADER */
  header: {
    marginTop: 12,
    marginBottom: 16,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 26,
    lineHeight: 32,
    color: COLORS.navy,
  },
  subtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    color: COLORS.navyMuted,
    marginTop: 4,
  },

  /* FILTER PILLS */
  filtersRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: RADIUS.pill,
    backgroundColor: COLORS.white,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    ...SHADOW.subtle,
  },
  filterChipActive: {
    backgroundColor: COLORS.navy,
    borderColor: COLORS.navy,
  },
  filterText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navyMuted,
  },
  filterTextActive: {
    color: COLORS.white,
    fontFamily: 'Fredoka-Medium',
  },
  filterBadge: {
    backgroundColor: 'rgba(0, 0, 0, 0.06)',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 8,
  },
  filterBadgeActive: {
    backgroundColor: 'rgba(255, 255, 255, 0.25)',
  },
  filterBadgeText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    color: COLORS.navyMuted,
  },
  filterBadgeTextActive: {
    color: COLORS.white,
  },

  /* NOTIFICATIONS LIST */
  notificationList: {
    gap: 12,
  },
  notificationCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 16,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    ...SHADOW.subtle,
  },
  notificationCardUnread: {
    borderColor: 'rgba(255, 115, 92, 0.25)',
  },
  iconBadge: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  contentWrap: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  cardTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 15,
    color: COLORS.navy,
    flex: 1,
  },
  timeWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
  },
  unreadDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.coralDark,
  },
  timestampText: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.subtleText,
  },
  cardMessage: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.navyMuted,
  },
  actionPill: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: COLORS.porcelain,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.06)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    marginTop: 10,
  },
  actionPillText: {
    fontFamily: 'Fredoka-Medium',
    fontSize: 11,
    color: COLORS.navy,
  },

  /* EMPTY STATE */
  emptyCard: {
    backgroundColor: COLORS.white,
    borderRadius: RADIUS.card,
    borderWidth: 1,
    borderColor: 'rgba(0, 0, 0, 0.05)',
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginVertical: 16,
    ...SHADOW.subtle,
  },
  emptyIconWrap: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: COLORS.greenSoft,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  emptyTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 18,
    color: COLORS.navy,
  },
  emptySubtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 12,
    lineHeight: 18,
    color: COLORS.navyMuted,
    textAlign: 'center',
    marginTop: 4,
    maxWidth: 260,
  },

  /* FOOTER */
  footerNote: {
    marginTop: 24,
    flexDirection: 'row',
    gap: 8,
    alignItems: 'flex-start',
    paddingHorizontal: 6,
  },
  footerNoteText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.subtleText,
  },

  pressed: {
    transform: [{ scale: 0.97 }],
    opacity: 0.88,
  },
});
