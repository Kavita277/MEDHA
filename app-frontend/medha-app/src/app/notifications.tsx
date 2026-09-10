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
import { COLORS } from '../constants/colors';

type NotificationPriority =
  | 'Informational'
  | 'Attention'
  | 'Urgent';

interface NotificationItem {
  id: string;
  type: 'app' | 'support' | 'risk';
  priority: NotificationPriority;
  title: string;
  message: string;
  action?: string;
  actionRoute?: string;
}

/*
 * MOCK BACKEND RESPONSE
 *
 * IMPORTANT:
 * The frontend does NOT calculate risk,
 * priority or alert type.
 *
 * Eventually this array will come from
 * the backend notification / recommendation system.
 */
const mockNotifications: NotificationItem[] = [
  {
    id: '1',
    type: 'app',
    priority: 'Informational',
    title: 'A small moment for yourself',
    message:
      'You have not checked in today. If you feel like it, take a quiet moment.',
    action: 'Check in',
    actionRoute: '/check-in',
  },

  {
    id: '2',
    type: 'support',
    priority: 'Attention',
    title: 'Support is available',
    message:
      'Some recent moments suggest that talking with someone could be helpful.',
    action: 'View Support',
    actionRoute: '/support',
  },

  {
    id: '3',
    type: 'support',
    priority: 'Urgent',
    title: 'Please reach out for support',
    message:
      'If you feel unsafe or believe you may be in immediate danger, please seek real-world help now.',
    action: 'Get Emergency Help',
    actionRoute: '/support',
  },
];

export default function NotificationsScreen() {
  const router = useRouter();

  const [notifications] =
    useState<NotificationItem[]>(
      mockNotifications
    );

  const getPriorityIcon = (
    priority: NotificationPriority
  ): keyof typeof Ionicons.glyphMap => {
    switch (priority) {
      case 'Urgent':
        return 'alert-circle-outline';

      case 'Attention':
        return 'information-circle-outline';

      default:
        return 'leaf-outline';
    }
  };

  const getPriorityContainer = (
    priority: NotificationPriority
  ) => {
    switch (priority) {
      case 'Urgent':
        return styles.urgentIcon;

      case 'Attention':
        return styles.attentionIcon;

      default:
        return styles.infoIcon;
    }
  };

  const getPriorityText = (
    priority: NotificationPriority
  ) => {
    switch (priority) {
      case 'Urgent':
        return styles.urgentText;

      case 'Attention':
        return styles.attentionText;

      default:
        return styles.infoText;
    }
  };

  const handleAction = (
    notification: NotificationItem
  ) => {
    if (notification.actionRoute) {
      router.push(notification.actionRoute as any);
    }
  };

  return (
    <MedhaScreen
      eyebrow="Notifications"
      title="A quiet place for things that matter."
      subtitle="MEDHA keeps notifications intentional. Some may simply inform you; others may suggest reaching out for support."
      onBack={() => router.back()}
    >

      <View style={styles.list}>

        {notifications.map((notification) => (

          <View
            key={notification.id}
            style={[
              styles.notification,
              notification.priority === 'Urgent' &&
                styles.urgentNotification,
            ]}
          >

            {/* HEADER */}

            <View style={styles.notificationHeader}>

              <View
                style={[
                  styles.priorityIcon,
                  getPriorityContainer(
                    notification.priority
                  ),
                ]}
              >
                <Ionicons
                  name={getPriorityIcon(
                    notification.priority
                  )}
                  size={20}
                  color={COLORS.forest}
                />
              </View>

              <View style={styles.headerCopy}>

                <Text
                  style={[
                    styles.priority,
                    getPriorityText(
                      notification.priority
                    ),
                  ]}
                >
                  {notification.priority.toUpperCase()}
                </Text>

                <Text style={styles.title}>
                  {notification.title}
                </Text>

              </View>

            </View>


            {/* MESSAGE */}

            <Text style={styles.message}>
              {notification.message}
            </Text>


            {/* CTA */}

            {notification.action && (
              <Pressable
                onPress={() =>
                  handleAction(notification)
                }
                style={[
                  styles.action,
                  notification.priority ===
                    'Urgent' &&
                    styles.urgentAction,
                ]}
              >

                <Text
                  style={[
                    styles.actionText,
                    notification.priority ===
                      'Urgent' &&
                      styles.urgentActionText,
                  ]}
                >
                  {notification.action}
                </Text>

                <Ionicons
                  name="arrow-forward"
                  size={15}
                  color={
                    notification.priority ===
                    'Urgent'
                      ? COLORS.white
                      : COLORS.forest
                  }
                />

              </Pressable>
            )}

          </View>

        ))}

      </View>


      <View style={styles.footer}>

        <Ionicons
          name="shield-checkmark-outline"
          size={17}
          color={COLORS.moss}
        />

        <Text style={styles.footerText}>
          Support alerts are provided by the
          services connected to MEDHA. They are
          not diagnoses.
        </Text>

      </View>

    </MedhaScreen>
  );
}


const styles = StyleSheet.create({

  list: {
    gap: 12,
  },

  notification: {
    padding: 19,
    borderRadius: 23,
    backgroundColor: COLORS.surface,
    borderWidth: 1,
    borderColor: COLORS.border,
  },

  urgentNotification: {
    borderColor: COLORS.clay,
    backgroundColor: '#F6EDE7',
  },

  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
  },

  priorityIcon: {
    width: 45,
    height: 45,
    borderRadius: 23,
    alignItems: 'center',
    justifyContent: 'center',
  },

  infoIcon: {
    backgroundColor: COLORS.mist,
  },

  attentionIcon: {
    backgroundColor: COLORS.sand,
  },

  urgentIcon: {
    backgroundColor: '#EBD6CC',
  },

  headerCopy: {
    flex: 1,
    marginLeft: 13,
  },

  priority: {
    fontFamily: 'Inter-Medium',
    fontSize: 8,
    letterSpacing: 1.5,
  },

  infoText: {
    color: COLORS.forest,
  },

  attentionText: {
    color: COLORS.wood,
  },

  urgentText: {
    color: COLORS.clay,
  },

  title: {
    fontFamily: 'CormorantGaramond-Regular',
    fontSize: 22,
    color: COLORS.deepForest,
    marginTop: 1,
  },

  message: {
    fontFamily: 'Inter-Regular',
    fontSize: 11,
    lineHeight: 18,
    color: COLORS.mutedText,
    marginTop: 17,
  },

  action: {
    marginTop: 17,
    minHeight: 44,
    paddingHorizontal: 16,
    borderRadius: 22,
    backgroundColor: COLORS.mist,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },

  urgentAction: {
    backgroundColor: COLORS.clay,
  },

  actionText: {
    fontFamily: 'Inter-Medium',
    fontSize: 11,
    color: COLORS.forest,
  },

  urgentActionText: {
    color: COLORS.white,
  },

  footer: {
    marginTop: 28,
    padding: 17,
    borderRadius: 20,
    backgroundColor: COLORS.surfaceWarm,
    flexDirection: 'row',
    gap: 10,
    alignItems: 'flex-start',
  },

  footerText: {
    flex: 1,
    fontFamily: 'Inter-Regular',
    fontSize: 9,
    lineHeight: 15,
    color: COLORS.mutedText,
  },

});