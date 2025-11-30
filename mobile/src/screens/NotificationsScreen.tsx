/**
 * Notifications Screen - Financial Alerts & Reminders
 * Glassmorphic Finance Theme - TIER 1 Feature
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  Alert,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../components/GlassCard';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import type { Notification } from '../types';
import { format } from 'date-fns';
import * as Haptics from 'expo-haptics';

export const NotificationsScreen: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');

  const loadNotifications = async () => {
    try {
      const response = await financialService.getNotifications();
      const sorted = (response.notifications || []).sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setNotifications(sorted);
    } catch (error) {
      console.error('Failed to load notifications:', error);
      Alert.alert('Error', 'Failed to load notifications.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadNotifications();
  };

  const handleMarkAsRead = async (notification: Notification) => {
    try {
      await financialService.markNotificationAsRead(notification.id);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      loadNotifications();
    } catch (error) {
      Alert.alert('Error', 'Failed to update notification');
    }
  };

  const handleDelete = (notification: Notification) => {
    Alert.alert(
      'Delete Notification',
      'Are you sure you want to delete this notification?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await financialService.deleteNotification(notification.id);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              loadNotifications();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete notification');
            }
          },
        },
      ]
    );
  };

  const getNotificationIcon = (type: string): keyof typeof Ionicons.glyphMap => {
    const icons: Record<string, keyof typeof Ionicons.glyphMap> = {
      bill_reminder: 'calendar',
      budget_alert: 'wallet',
      goal_milestone: 'flag',
      unusual_spending: 'alert-circle',
      low_balance: 'trending-down',
      info: 'information-circle',
    };
    return icons[type] || 'notifications';
  };

  const getNotificationColor = (type: string) => {
    const colorMap: Record<string, string> = {
      bill_reminder: colors.warning.primary,
      budget_alert: colors.expense.primary,
      goal_milestone: colors.income.primary,
      unusual_spending: colors.warning.primary,
      low_balance: colors.expense.primary,
      info: colors.info.primary,
    };
    return colorMap[type] || colors.info.primary;
  };

  const getPriorityBadgeColor = (priority: string) => {
    const colorMap: Record<string, string> = {
      high: colors.expense.primary,
      medium: colors.warning.primary,
      low: colors.info.primary,
    };
    return colorMap[priority] || colors.info.primary;
  };

  const filteredNotifications = filter === 'unread'
    ? notifications.filter(n => !n.is_read)
    : notifications;

  const renderNotification = ({ item }: { item: Notification }) => {
    const iconColor = getNotificationColor(item.type);
    const priorityColor = getPriorityBadgeColor(item.priority);

    return (
      <GlassCard
        variant={item.is_read ? 'light' : 'medium'}
        style={[styles.notificationCard, !item.is_read && styles.unreadCard]}
      >
        <TouchableOpacity
          onPress={() => !item.is_read && handleMarkAsRead(item)}
          activeOpacity={item.is_read ? 1 : 0.7}
        >
          <View style={styles.notificationRow}>
            <View style={[styles.iconContainer, { backgroundColor: `${iconColor}20` }]}>
              <Ionicons
                name={getNotificationIcon(item.type)}
                size={24}
                color={iconColor}
              />
            </View>

            <View style={styles.notificationContent}>
              <View style={styles.notificationHeader}>
                <Text style={[
                  styles.notificationTitle,
                  !item.is_read && styles.unreadTitle
                ]}>
                  {item.title}
                </Text>
                {!item.is_read && (
                  <View style={styles.unreadDot} />
                )}
              </View>

              <Text style={styles.notificationMessage}>{item.message}</Text>

              <View style={styles.notificationFooter}>
                <View style={styles.metaBadges}>
                  <View style={[styles.priorityBadge, { borderColor: priorityColor }]}>
                    <Text style={[styles.priorityText, { color: priorityColor }]}>
                      {item.priority.toUpperCase()}
                    </Text>
                  </View>
                  <View style={styles.typeBadge}>
                    <Text style={styles.typeText}>
                      {item.type.replace(/_/g, ' ').toUpperCase()}
                    </Text>
                  </View>
                </View>
                <Text style={styles.notificationTime}>
                  {format(new Date(item.created_at), 'MMM dd, h:mm a')}
                </Text>
              </View>

              {item.action_required && (
                <View style={styles.actionRequiredBanner}>
                  <Ionicons name="hand-right" size={14} color={colors.warning.primary} />
                  <Text style={styles.actionRequiredText}>Action Required</Text>
                </View>
              )}
            </View>

            <View style={styles.notificationActions}>
              <TouchableOpacity
                onPress={() => handleDelete(item)}
                style={styles.deleteButton}
              >
                <Ionicons name="trash-outline" size={20} color={colors.text.secondary} />
              </TouchableOpacity>
            </View>
          </View>
        </TouchableOpacity>
      </GlassCard>
    );
  };

  const unreadCount = notifications.filter(n => !n.is_read).length;

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.info.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Filter Tabs */}
      <View style={styles.filterContainer}>
        <TouchableOpacity
          style={[styles.filterTab, filter === 'all' && styles.filterTabActive]}
          onPress={() => setFilter('all')}
        >
          <Text style={[
            styles.filterTabText,
            filter === 'all' && styles.filterTabTextActive
          ]}>
            All ({notifications.length})
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.filterTab, filter === 'unread' && styles.filterTabActive]}
          onPress={() => setFilter('unread')}
        >
          <Text style={[
            styles.filterTabText,
            filter === 'unread' && styles.filterTabTextActive
          ]}>
            Unread ({unreadCount})
          </Text>
        </TouchableOpacity>
      </View>

      {/* Notification List */}
      {filteredNotifications.length === 0 ? (
        <View style={styles.emptyState}>
          <GlassCard variant="medium">
            <View style={styles.emptyContent}>
              <Ionicons
                name={filter === 'unread' ? 'checkmark-circle-outline' : 'notifications-outline'}
                size={64}
                color={colors.info.primary}
              />
              <Text style={styles.emptyTitle}>
                {filter === 'unread' ? 'All Caught Up!' : 'No Notifications'}
              </Text>
              <Text style={styles.emptyText}>
                {filter === 'unread'
                  ? 'You have no unread notifications'
                  : 'You\'ll see alerts and reminders here'}
              </Text>
            </View>
          </GlassCard>
        </View>
      ) : (
        <FlatList
          data={filteredNotifications}
          renderItem={renderNotification}
          keyExtractor={(item) => item.id}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={colors.white}
            />
          }
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.secondary,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background.secondary,
  },
  filterContainer: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.lg,
  },
  filterTab: {
    flex: 1,
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.md,
    borderRadius: theme.radius.md,
    backgroundColor: colors.background.secondary,
    borderWidth: 1,
    borderColor: colors.border.light,
    alignItems: 'center',
  },
  filterTabActive: {
    backgroundColor: colors.info.glass,
    borderColor: colors.info.primary,
  },
  filterTabText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text.secondary,
  },
  filterTabTextActive: {
    color: colors.info.primary,
  },
  listContent: {
    padding: theme.spacing.lg,
    paddingTop: 0,
    gap: theme.spacing.md,
    paddingBottom: theme.spacing.xxl,
  },
  notificationCard: {
    marginBottom: 0,
  },
  unreadCard: {
    borderWidth: 1.5,
    borderColor: colors.info.primary,
  },
  notificationRow: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  notificationContent: {
    flex: 1,
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.xs,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text.primary,
    flex: 1,
  },
  unreadTitle: {
    fontWeight: '700',
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.info.primary,
  },
  notificationMessage: {
    fontSize: 14,
    color: colors.text.secondary,
    marginBottom: theme.spacing.sm,
    lineHeight: 20,
  },
  notificationFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: theme.spacing.xs,
  },
  metaBadges: {
    flexDirection: 'row',
    gap: theme.spacing.xs,
    flex: 1,
  },
  priorityBadge: {
    paddingHorizontal: theme.spacing.xs,
    paddingVertical: 2,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: '700',
  },
  typeBadge: {
    paddingHorizontal: theme.spacing.xs,
    paddingVertical: 2,
    borderRadius: theme.radius.sm,
    backgroundColor: colors.glass.light,
  },
  typeText: {
    fontSize: 10,
    fontWeight: '600',
    color: colors.text.tertiary,
  },
  notificationTime: {
    fontSize: 12,
    color: colors.text.tertiary,
  },
  actionRequiredBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    backgroundColor: colors.warning.glass,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 4,
    borderRadius: theme.radius.sm,
    marginTop: theme.spacing.sm,
    borderWidth: 1,
    borderColor: colors.warning.primary,
  },
  actionRequiredText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.warning.primary,
  },
  notificationActions: {
    justifyContent: 'center',
  },
  deleteButton: {
    padding: theme.spacing.xs,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    padding: theme.spacing.lg,
  },
  emptyContent: {
    alignItems: 'center',
    padding: theme.spacing.xl,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.text.primary,
    marginTop: theme.spacing.lg,
    marginBottom: theme.spacing.sm,
  },
  emptyText: {
    fontSize: 14,
    color: colors.text.secondary,
    textAlign: 'center',
  },
});
