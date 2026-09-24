import React, { useState } from 'react';
import {
  Pressable,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { MedhaScreen } from '../components/medha-screen';
import { MedhaCard, CardVariant } from '../components/medha-card';
import { MedhaButton } from '../components/medha-button';
import { COLORS } from '../constants/colors';
import { RADIUS, SHADOW } from '../constants/theme';

type NotificationPriority = 'Informational' | 'Attention' | 'Urgent';

interface NotificationItem {
  id: string;
  type: 'app' | 'support' | 'risk';
  priority: NotificationPriority;
  title: string;
  message: string;
  timestamp: string;
  action?: string;
  actionRoute?: string;
  read: boolean;
}

const mockNotifications: NotificationItem[] = [
  {
    id: '1',
    type: 'app',
    priority: 'Informational',
    title: 'A small moment for yourself',
    message:
      'You have not checked in today. If you feel like it, take a quiet moment to reflect.',
    timestamp: 'Today • 9:30 AM',
    action: 'Check in',
    actionRoute: '/check-in',
    read: false,
  },
  {
    id: '2',
    type: 'support',
    priority: 'Attention',
    title: 'Support is available',
    message:
      'Some recent moments suggest that talking with someone could be gentle and helpful.',
    timestamp: 'Yesterday • 4:15 PM',
    action: 'View Support',
    actionRoute: '/support',
    read: false,
  },
  {
    id: '3',
    type: 'support',
    priority: 'Urgent',
    title: 'Please reach out for support',
    message:
      'If you feel unsafe or believe you may be in immediate danger, please seek real-world help now.',
    timestamp: '2 days ago',
    action: 'Get Emergency Help',
    actionRoute: '/support',
    read: false,
  },
];

type FilterType = 'all' | 'priority' | 'info';

export default function NotificationsScreen() {
  const router = useRouter();
  const [notifications, setNotifications] = useState<NotificationItem[]>(mockNotifications);
  const [activeFilter, setActiveFilter] = useState<FilterType>('all');

  const filteredNotifications = notifications.filter((item) => {
    if (activeFilter === 'priority') {
      return item.priority === 'Urgent' || item.priority === 'Attention';
    }
    if (activeFilter === 'info') {
      return item.priority === 'Informational';
    }
    return true;
  });

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const handleAction = (notification: NotificationItem) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notification.id ? { ...n, read: true } : n))
    );
    if (notification.actionRoute) {
      router.push(notification.actionRoute as any);
    }
  };

  const toggleRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: !n.read } : n))
    );
  };

  const getPriorityIcon = (priority: NotificationPriority): keyof typeof Ionicons.glyphMap => {
    switch (priority) {
      case 'Urgent':
        return 'alert-circle';
      case 'Attention':
        return 'information-circle';
      default:
        return 'leaf';
    }
  };

  const getPriorityColor = (priority: NotificationPriority): string => {
    switch (priority) {
      case 'Urgent':
        return COLORS.coralDark;
      case 'Attention':
        return COLORS.yellowDark;
      default:
        return COLORS.sage;
    }
  };

  const getCardVariant = (priority: NotificationPriority): CardVariant => {
    switch (priority) {
      case 'Urgent':
        return 'pink';
      case 'Attention':
        return 'yellow';
      default:
        return 'green';
    }
  };

  return (
    <MedhaScreen
      eyebrow="Notifications"
      title="A quiet place for things that matter."
      subtitle="MEDHA keeps notifications intentional. Some simply inform you; others suggest reaching out for support."
      onBack={() => router.back()}
      withBackground={true}
    >
      <View style={styles.container}>
        {/* Top Controls: Filter Pills & Mark All Read */}
        <View style={styles.topControlRow}>
          <View style={styles.filterPills}>
            <Pressable
              onPress={() => setActiveFilter('all')}
              style={[
                styles.filterPill,
                activeFilter === 'all' && styles.filterPillActive,
              ]}
              accessibilityRole="tab"
            >
              <Text
                style={[
                  styles.filterPillText,
                  activeFilter === 'all' && styles.filterPillTextActive,
                ]}
              >
                All ({notifications.length})
              </Text>
            </Pressable>

            <Pressable
              onPress={() => setActiveFilter('priority')}
              style={[
                styles.filterPill,
                activeFilter === 'priority' && styles.filterPillActive,
              ]}
              accessibilityRole="tab"
            >
              <Text
                style={[
                  styles.filterPillText,
                  activeFilter === 'priority' && styles.filterPillTextActive,
                ]}
              >
                Priority
              </Text>
            </Pressable>

            <Pressable
              onPress={() => setActiveFilter('info')}
              style={[
                styles.filterPill,
                activeFilter === 'info' && styles.filterPillActive,
              ]}
              accessibilityRole="tab"
            >
              <Text
                style={[
                  styles.filterPillText,
                  activeFilter === 'info' && styles.filterPillTextActive,
                ]}
              >
                Updates
              </Text>
            </Pressable>
          </View>

          {unreadCount > 0 && (
            <Pressable
              onPress={markAllRead}
              style={styles.markReadBtn}
              accessibilityRole="button"
              accessibilityLabel="Mark all notifications as read"
            >
              <Text style={styles.markReadText}>Mark read</Text>
            </Pressable>
          )}
        </View>

        {/* Notifications Feed */}
        {filteredNotifications.length === 0 ? (
          <MedhaCard variant="glass" style={styles.emptyCard}>
            <View style={styles.emptyIconWrap}>
              <Ionicons name="sparkles" size={26} color={COLORS.sage} />
            </View>
            <Text style={styles.emptyTitle}>All caught up</Text>
            <Text style={styles.emptySubtitle}>
              There are no notifications in this section. Take a quiet breath for yourself.
            </Text>
          </MedhaCard>
        ) : (
          <View style={styles.list}>
            {filteredNotifications.map((notification) => {
              const iconColor = getPriorityColor(notification.priority);
              const cardVariant = getCardVariant(notification.priority);

              return (
                <MedhaCard
                  key={notification.id}
                  variant={cardVariant}
                  style={[
                    styles.notificationCard,
                    !notification.read && styles.unreadCardBorder,
                  ]}
                  onPress={() => toggleRead(notification.id)}
                  accessibilityLabel={`Notification: ${notification.title}`}
                >
                  <View style={styles.cardHeader}>
                    <View style={styles.iconAndBadge}>
                      <View style={[styles.priorityIcon, { backgroundColor: 'rgba(255, 255, 255, 0.9)' }]}>
                        <Ionicons
                          name={getPriorityIcon(notification.priority)}
                          size={20}
                          color={iconColor}
                        />
                      </View>
                      <View>
                        <View style={styles.priorityLabelRow}>
                          <Text style={[styles.priorityTag, { color: iconColor }]}>
                            {notification.priority.toUpperCase()}
                          </Text>
                          {!notification.read && <View style={styles.unreadDot} />}
                        </View>
                        <Text style={styles.timestamp}>{notification.timestamp}</Text>
                      </View>
                    </View>
                  </View>

                  <Text style={styles.title}>{notification.title}</Text>
                  <Text style={styles.message}>{notification.message}</Text>

                  {notification.action && (
                    <View style={styles.actionWrapper}>
                      <MedhaButton
                        title={notification.action}
                        onPress={() => handleAction(notification)}
                        variant={notification.priority === 'Urgent' ? 'coral' : 'pill'}
                        size="md"
                        icon="arrow-forward"
                      />
                    </View>
                  )}
                </MedhaCard>
              );
            })}
          </View>
        )}

        {/* Footer Note */}
        <View style={styles.footer}>
          <Ionicons
            name="shield-checkmark-outline"
            size={18}
            color={COLORS.sage}
          />
          <Text style={styles.footerText}>
            Support alerts are provided by the services connected to MEDHA. They are not medical diagnoses.
          </Text>
        </View>
      </View>
    </MedhaScreen>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 16,
    paddingBottom: 24,
  },
  topControlRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  filterPills: {
    flexDirection: 'row',
    gap: 8,
  },
  filterPill: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: RADIUS.pill,
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    borderWidth: 1,
    borderColor: 'rgba(255, 201, 172, 0.4)',
  },
  filterPillActive: {
    backgroundColor: COLORS.navy,
    borderColor: COLORS.navy,
  },
  filterPillText: {
    fontFamily: 'Nunito-SemiBold',
    fontSize: 12,
    color: COLORS.navyMuted,
  },
  filterPillTextActive: {
    color: COLORS.white,
  },
  markReadBtn: {
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  markReadText: {
    fontFamily: 'Nunito-Bold',
    fontSize: 12,
    color: COLORS.coralDark,
  },
  list: {
    gap: 14,
  },
  notificationCard: {
    padding: 18,
  },
  unreadCardBorder: {
    borderLeftWidth: 4,
    borderLeftColor: COLORS.coral,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  iconAndBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  priorityIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 201, 172, 0.4)',
    ...SHADOW.card,
  },
  priorityLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  priorityTag: {
    fontFamily: 'Nunito-Bold',
    fontSize: 10,
    letterSpacing: 1.2,
  },
  unreadDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.coral,
  },
  timestamp: {
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    color: COLORS.navyMuted,
    marginTop: 2,
  },
  title: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 18,
    lineHeight: 23,
    color: COLORS.navy,
    marginBottom: 6,
  },
  message: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 19,
    color: COLORS.navyMuted,
    marginBottom: 14,
  },
  actionWrapper: {
    marginTop: 4,
  },
  emptyCard: {
    padding: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 10,
  },
  emptyIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: COLORS.sageSoft,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  emptyTitle: {
    fontFamily: 'Fredoka-SemiBold',
    fontSize: 20,
    color: COLORS.navy,
    marginBottom: 6,
  },
  emptySubtitle: {
    fontFamily: 'Nunito-Regular',
    fontSize: 13,
    lineHeight: 19,
    color: COLORS.navyMuted,
    textAlign: 'center',
    maxWidth: 280,
  },
  footer: {
    marginTop: 12,
    padding: 16,
    borderRadius: RADIUS.card,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    borderWidth: 1,
    borderColor: 'rgba(255, 201, 172, 0.5)',
    flexDirection: 'row',
    gap: 10,
    alignItems: 'flex-start',
    ...SHADOW.card,
  },
  footerText: {
    flex: 1,
    fontFamily: 'Nunito-Regular',
    fontSize: 11,
    lineHeight: 16,
    color: COLORS.navyMuted,
  },
});
