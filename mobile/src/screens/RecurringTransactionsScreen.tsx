/**
 * Recurring Transactions Screen - Manage Scheduled Bills & Income
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
  Pressable,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../components/GlassCard';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { BottomSheet } from '../components/BottomSheet';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import type { RecurringTransaction } from '../types';
import { format } from 'date-fns';
import * as Haptics from 'expo-haptics';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import { formatCurrency as formatCurrencyUtil } from '../utils/currency';

export const RecurringTransactionsScreen: React.FC = () => {
  const { preferences } = useUserPreferences();
  const [recurringTransactions, setRecurringTransactions] = useState<RecurringTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<RecurringTransaction | null>(null);
  const [formData, setFormData] = useState({
    type: 'expense' as 'income' | 'expense',
    amount: '',
    category: '',
    description: '',
    frequency: 'monthly' as 'daily' | 'weekly' | 'bi_weekly' | 'monthly' | 'quarterly' | 'yearly',
    next_date: '',
    reminder_days_before: '3',
  });
  const [submitting, setSubmitting] = useState(false);

  const loadRecurringTransactions = async () => {
    try {
      const response = await financialService.getRecurringTransactions();
      const sorted = (response.recurring_transactions || []).sort((a, b) =>
        new Date(a.next_date).getTime() - new Date(b.next_date).getTime()
      );
      setRecurringTransactions(sorted);
    } catch (error) {
      console.error('Failed to load recurring transactions:', error);
      Alert.alert('Error', 'Failed to load recurring transactions.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadRecurringTransactions();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadRecurringTransactions();
  };

  const openAddModal = () => {
    setEditingTransaction(null);
    const today = new Date().toISOString().split('T')[0];
    setFormData({
      type: 'expense',
      amount: '',
      category: '',
      description: '',
      frequency: 'monthly',
      next_date: today,
      reminder_days_before: '3',
    });
    setModalVisible(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const openEditModal = (transaction: RecurringTransaction) => {
    setEditingTransaction(transaction);
    setFormData({
      type: transaction.type || 'expense',
      amount: transaction.amount?.toString() || '0',
      category: transaction.category || '',
      description: transaction.description || '',
      frequency: transaction.frequency || 'monthly',
      next_date: transaction.next_date ? transaction.next_date.split('T')[0] : new Date().toISOString().split('T')[0],
      reminder_days_before: transaction.reminder_days_before?.toString() || '3',
    });
    setModalVisible(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const handleDelete = (transaction: RecurringTransaction) => {
    Alert.alert(
      'Delete Recurring Transaction',
      `Are you sure you want to delete this ${transaction.type}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await financialService.deleteRecurringTransaction(transaction.id);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              loadRecurringTransactions();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete transaction');
            }
          },
        },
      ]
    );
  };

  const toggleActive = async (transaction: RecurringTransaction) => {
    try {
      await financialService.updateRecurringTransaction(transaction.id, {
        is_active: !transaction.is_active,
      });
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      loadRecurringTransactions();
    } catch (error) {
      Alert.alert('Error', 'Failed to update transaction');
    }
  };

  const handleSubmit = async () => {
    if (!formData.amount || !formData.category || !formData.description) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    try {
      const data = {
        type: formData.type,
        amount: parseFloat(formData.amount),
        category: formData.category,
        description: formData.description,
        frequency: formData.frequency,
        next_date: formData.next_date,
        reminder_days_before: parseInt(formData.reminder_days_before),
      };

      if (editingTransaction) {
        await financialService.updateRecurringTransaction(editingTransaction.id, data);
      } else {
        await financialService.createRecurringTransaction(data);
      }

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setModalVisible(false);
      loadRecurringTransactions();
    } catch (error) {
      Alert.alert('Error', `Failed to ${editingTransaction ? 'update' : 'create'} transaction`);
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return formatCurrencyUtil(amount, preferences.currency);
  };

  const getFrequencyLabel = (frequency: string) => {
    const labels: Record<string, string> = {
      daily: 'Daily',
      weekly: 'Weekly',
      bi_weekly: 'Bi-Weekly',
      monthly: 'Monthly',
      quarterly: 'Quarterly',
      yearly: 'Yearly',
    };
    return labels[frequency] || frequency;
  };

  const getDaysUntil = (dateString: string) => {
    const nextDate = new Date(dateString);
    const today = new Date();
    const diffTime = nextDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const renderTransaction = ({ item }: { item: RecurringTransaction }) => {
    const daysUntil = getDaysUntil(item.next_date);
    const isDueSoon = daysUntil <= item.reminder_days_before && daysUntil >= 0;

    return (
      <GlassCard variant="medium" style={styles.transactionCard}>
        <View style={styles.transactionRow}>
          <View style={styles.transactionLeft}>
            <View style={styles.transactionHeader}>
              <View style={styles.transactionTitleRow}>
                <Ionicons
                  name={item.type === 'income' ? 'arrow-down-circle' : 'arrow-up-circle'}
                  size={24}
                  color={item.type === 'income' ? colors.income.primary : colors.expense.primary}
                />
                <View style={styles.transactionInfo}>
                  <Text style={styles.transactionCategory}>{item.category.toUpperCase()}</Text>
                  <Text style={styles.transactionDescription}>{item.description}</Text>
                </View>
              </View>
            </View>

            <View style={styles.transactionMeta}>
              <View style={styles.frequencyBadge}>
                <Ionicons name="repeat" size={14} color={colors.info.primary} />
                <Text style={styles.frequencyText}>{getFrequencyLabel(item.frequency)}</Text>
              </View>
              <View style={styles.dateBadge}>
                <Ionicons name="calendar-outline" size={14} color={colors.text.secondary} />
                <Text style={styles.dateText}>
                  {format(new Date(item.next_date), 'MMM dd')} ({daysUntil} days)
                </Text>
              </View>
            </View>

            {isDueSoon && item.is_active && (
              <View style={styles.reminderBanner}>
                <Ionicons name="notifications" size={14} color={colors.warning.primary} />
                <Text style={styles.reminderText}>Due soon!</Text>
              </View>
            )}

            {!item.is_active && (
              <View style={[styles.reminderBanner, { backgroundColor: colors.glass.light }]}>
                <Ionicons name="pause-circle" size={14} color={colors.text.secondary} />
                <Text style={[styles.reminderText, { color: colors.text.secondary }]}>Paused</Text>
              </View>
            )}
          </View>

          <View style={styles.transactionRight}>
            <Text style={[
              styles.transactionAmount,
              { color: item.type === 'income' ? colors.income.primary : colors.expense.primary }
            ]}>
              {item.type === 'income' ? '+' : '-'}{formatCurrency(item.amount)}
            </Text>

            <View style={styles.actionButtons}>
              <TouchableOpacity
                onPress={() => toggleActive(item)}
                style={styles.actionButton}
              >
                <Ionicons
                  name={item.is_active ? 'pause' : 'play'}
                  size={20}
                  color={colors.text.secondary}
                />
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => openEditModal(item)}
                style={styles.actionButton}
              >
                <Ionicons name="create-outline" size={20} color={colors.text.secondary} />
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => handleDelete(item)}
                style={styles.actionButton}
              >
                <Ionicons name="trash-outline" size={20} color={colors.text.secondary} />
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </GlassCard>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.info.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Transaction List */}
      {recurringTransactions.length === 0 ? (
        <View style={styles.emptyState}>
          <GlassCard variant="medium">
            <View style={styles.emptyContent}>
              <Ionicons name="repeat-outline" size={64} color={colors.info.primary} />
              <Text style={styles.emptyTitle}>No Recurring Transactions</Text>
              <Text style={styles.emptyText}>
                Set up bills, subscriptions, and recurring income
              </Text>
              <Button
                title="Add Recurring Transaction"
                onPress={openAddModal}
                variant="primary"
                icon="add-circle"
                style={styles.emptyButton}
              />
            </View>
          </GlassCard>
        </View>
      ) : (
        <FlatList
          data={recurringTransactions}
          renderItem={renderTransaction}
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

      {/* Add/Edit Modal */}
      <BottomSheet
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        title={editingTransaction ? 'Edit Recurring' : 'Add Recurring'}
        subtitle="Set up automatic transactions"
      >
        <ScrollView showsVerticalScrollIndicator={false}>
              {/* Type Selector */}
              <View style={styles.typeSelector}>
                <Pressable
                  style={[
                    styles.typeButton,
                    formData.type === 'expense' && styles.typeButtonExpenseActive,
                  ]}
                  onPress={() => setFormData({ ...formData, type: 'expense' })}
                >
                  <Ionicons
                    name="arrow-up-circle"
                    size={24}
                    color={formData.type === 'expense' ? colors.expense.primary : colors.gray[600]}
                  />
                  <Text style={[
                    styles.typeButtonText,
                    formData.type === 'expense' && styles.typeButtonExpenseTextActive,
                  ]}>
                    Expense
                  </Text>
                </Pressable>

                <Pressable
                  style={[
                    styles.typeButton,
                    formData.type === 'income' && styles.typeButtonIncomeActive,
                  ]}
                  onPress={() => setFormData({ ...formData, type: 'income' })}
                >
                  <Ionicons
                    name="arrow-down-circle"
                    size={24}
                    color={formData.type === 'income' ? colors.income.primary : colors.gray[600]}
                  />
                  <Text style={[
                    styles.typeButtonText,
                    formData.type === 'income' && styles.typeButtonIncomeTextActive,
                  ]}>
                    Income
                  </Text>
                </Pressable>
              </View>

              <Input
                label="Amount"
                value={formData.amount}
                onChangeText={(text) => setFormData({ ...formData, amount: text })}
                keyboardType="decimal-pad"
                placeholder="0.00"
              />

              <Input
                label="Category"
                value={formData.category}
                onChangeText={(text) => setFormData({ ...formData, category: text })}
                placeholder="e.g., Netflix, Rent, Salary"
              />

              <Input
                label="Description"
                value={formData.description}
                onChangeText={(text) => setFormData({ ...formData, description: text })}
                placeholder="What is this for?"
              />

              {/* Frequency Selector */}
              <Text style={styles.selectorLabel}>Frequency</Text>
              <View style={styles.frequencySelector}>
                {['daily', 'weekly', 'bi_weekly', 'monthly', 'quarterly', 'yearly'].map((freq) => (
                  <Pressable
                    key={freq}
                    style={[
                      styles.frequencyButton,
                      formData.frequency === freq && styles.frequencyButtonActive,
                    ]}
                    onPress={() => setFormData({ ...formData, frequency: freq as any })}
                  >
                    <Text style={[
                      styles.frequencyButtonText,
                      formData.frequency === freq && styles.frequencyButtonTextActive,
                    ]}>
                      {getFrequencyLabel(freq)}
                    </Text>
                  </Pressable>
                ))}
              </View>

              <Input
                label="Next Date (YYYY-MM-DD)"
                value={formData.next_date}
                onChangeText={(text) => setFormData({ ...formData, next_date: text })}
                placeholder="2025-01-15"
              />

              <Input
                label="Reminder Days Before"
                value={formData.reminder_days_before}
                onChangeText={(text) => setFormData({ ...formData, reminder_days_before: text })}
                keyboardType="number-pad"
                placeholder="3"
              />

              <Button
                title={editingTransaction ? 'Update' : 'Create'}
                onPress={handleSubmit}
                loading={submitting}
                variant="primary"
                style={styles.submitButton}
              />
        </ScrollView>
      </BottomSheet>
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
  listContent: {
    padding: theme.spacing.lg,
    paddingTop: 0,
    gap: theme.spacing.md,
    paddingBottom: theme.spacing.xxl,
  },
  transactionCard: {
    marginBottom: 0,
  },
  transactionRow: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  transactionLeft: {
    flex: 1,
  },
  transactionHeader: {
    marginBottom: theme.spacing.sm,
  },
  transactionTitleRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.sm,
  },
  transactionInfo: {
    flex: 1,
  },
  transactionCategory: {
    fontSize: 12,
    fontWeight: '700',
    color: colors.text.secondary,
    letterSpacing: 1,
    marginBottom: 4,
  },
  transactionDescription: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text.primary,
  },
  transactionMeta: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.sm,
  },
  frequencyBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.info.glass,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 4,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
    borderColor: colors.info.primary,
  },
  frequencyText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.info.primary,
  },
  dateBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  dateText: {
    fontSize: 12,
    color: colors.text.secondary,
  },
  reminderBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.warning.glass,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 4,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
    borderColor: colors.warning.primary,
  },
  reminderText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.warning.primary,
  },
  transactionRight: {
    alignItems: 'flex-end',
    gap: theme.spacing.sm,
  },
  transactionAmount: {
    fontSize: 18,
    fontWeight: '700',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: theme.spacing.xs,
  },
  actionButton: {
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
    marginBottom: theme.spacing.lg,
  },
  emptyButton: {
    marginTop: theme.spacing.md,
  },
  typeSelector: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.lg,
  },
  typeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    padding: theme.spacing.md,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: colors.border.light,
    backgroundColor: colors.background.secondary,
  },
  typeButtonExpenseActive: {
    backgroundColor: colors.expense.glass,
    borderColor: colors.expense.primary,
  },
  typeButtonIncomeActive: {
    backgroundColor: colors.income.glass,
    borderColor: colors.income.primary,
  },
  typeButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.gray[600],
  },
  typeButtonExpenseTextActive: {
    color: colors.expense.primary,
  },
  typeButtonIncomeTextActive: {
    color: colors.income.primary,
  },
  selectorLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text.secondary,
    marginBottom: theme.spacing.sm,
  },
  frequencySelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.md,
  },
  frequencyButton: {
    minWidth: '30%',
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: theme.spacing.sm,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: colors.border.light,
    backgroundColor: colors.background.secondary,
    alignItems: 'center',
  },
  frequencyButtonActive: {
    backgroundColor: colors.info.glass,
    borderColor: colors.info.primary,
  },
  frequencyButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text.secondary,
  },
  frequencyButtonTextActive: {
    color: colors.info.primary,
  },
  submitButton: {
    marginTop: theme.spacing.lg,
  },
});
