/**
 * Transactions Screen - REDESIGNED for Easy Use
 * Following 2025 ISP Best Practices
 *
 * KEY IMPROVEMENTS:
 * 1. ✅ FAB at bottom-right (thumb-friendly)
 * 2. ✅ Swipe-to-delete (no tiny buttons)
 * 3. ✅ Simplified cards (3 data points max)
 * 4. ✅ Quick-add with smart defaults
 * 5. ✅ Grouped by date
 * 6. ✅ Clear visual hierarchy
 * 7. ✅ Large touch targets (min 48px)
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
  Pressable,
  Animated,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import Swipeable from 'react-native-gesture-handler/Swipeable';
import { Card } from '../components/Card';
import { FAB } from '../components/FAB';
import { Input } from '../components/Input';
import { BottomSheet } from '../components/BottomSheet';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import type { Transaction } from '../types';
import { format, isToday, isYesterday, parseISO } from 'date-fns';
import * as Haptics from 'expo-haptics';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import { formatCurrency as formatCurrencyUtil } from '../utils/currency';

// Group transactions by date
interface TransactionGroup {
  date: string;
  displayDate: string;
  transactions: Transaction[];
  total: number;
}

export const TransactionsScreenRedesigned: React.FC = () => {
  const { preferences } = useUserPreferences();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [quickAddVisible, setQuickAddVisible] = useState(false);
  const [quickAmount, setQuickAmount] = useState('');
  const [quickDescription, setQuickDescription] = useState('');
  const [quickType, setQuickType] = useState<'income' | 'expense'>('expense');
  const [submitting, setSubmitting] = useState(false);

  const loadTransactions = async () => {
    try {
      const data = await financialService.getTransactions();
      setTransactions(data.sort((a, b) =>
        new Date(b.date).getTime() - new Date(a.date).getTime()
      ));
    } catch (error) {
      console.error('Failed to load transactions:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadTransactions();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadTransactions();
  };

  // Group transactions by date
  const groupedTransactions: TransactionGroup[] = React.useMemo(() => {
    const groups: { [key: string]: Transaction[] } = {};

    transactions.forEach((transaction) => {
      const date = format(new Date(transaction.date), 'yyyy-MM-dd');
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(transaction);
    });

    return Object.entries(groups).map(([date, txns]) => {
      const dateObj = parseISO(date);
      let displayDate = format(dateObj, 'MMM dd, yyyy');

      if (isToday(dateObj)) {
        displayDate = 'Today';
      } else if (isYesterday(dateObj)) {
        displayDate = 'Yesterday';
      }

      const total = txns.reduce((sum, t) =>
        sum + (t.type === 'income' ? t.amount : -t.amount), 0
      );

      return { date, displayDate, transactions: txns, total };
    });
  }, [transactions]);

  const formatCurrency = (amount: number) => {
    return formatCurrencyUtil(amount, preferences.currency);
  };

  // Quick add with smart defaults
  const handleQuickAdd = async () => {
    if (!quickAmount) {
      Alert.alert('Error', 'Please enter an amount');
      return;
    }

    setSubmitting(true);
    try {
      await financialService.addTransaction({
        type: quickType,
        amount: parseFloat(quickAmount),
        category: quickType === 'expense' ? 'General' : 'Income',
        description: quickDescription || `${quickType === 'expense' ? 'Expense' : 'Income'} - ${format(new Date(), 'MMM dd')}`,
      });

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setQuickAddVisible(false);
      setQuickAmount('');
      setQuickDescription('');
      loadTransactions();
    } catch (error) {
      Alert.alert('Error', 'Failed to add transaction');
    } finally {
      setSubmitting(false);
    }
  };

  // Swipe to delete
  const handleDelete = async (transaction: Transaction) => {
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);

    Alert.alert(
      'Delete Transaction',
      'Are you sure?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await financialService.deleteTransaction(transaction.id);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              loadTransactions();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete transaction');
            }
          },
        },
      ]
    );
  };

  // Render swipe actions
  const renderRightActions = (
    progress: Animated.AnimatedInterpolation<number>,
    transaction: Transaction
  ) => {
    const translateX = progress.interpolate({
      inputRange: [0, 1],
      outputRange: [80, 0],
    });

    return (
      <Animated.View style={[styles.swipeAction, { transform: [{ translateX }] }]}>
        <Pressable
          style={styles.deleteButton}
          onPress={() => handleDelete(transaction)}
        >
          <Ionicons name="trash" size={24} color={colors.white} />
          <Text style={styles.deleteText}>Delete</Text>
        </Pressable>
      </Animated.View>
    );
  };

  // SIMPLIFIED transaction card - only 3 data points
  const renderTransaction = ({ item }: { item: Transaction }) => (
    <Swipeable renderRightActions={(progress) => renderRightActions(progress, item)}>
      <Pressable
        style={styles.transactionCard}
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          // Navigate to details or edit
        }}
      >
        {/* Icon + Description (LEFT) */}
        <View style={styles.transactionLeft}>
          <View style={[
            styles.iconContainer,
            { backgroundColor: item.type === 'income' ? colors.income.light : colors.expense.light }
          ]}>
            <Ionicons
              name={item.type === 'income' ? 'arrow-down' : 'arrow-up'}
              size={24}
              color={item.type === 'income' ? colors.income.primary : colors.expense.primary}
            />
          </View>

          <View style={styles.transactionInfo}>
            {/* PRIMARY: Description (biggest) */}
            <Text style={styles.transactionDescription} numberOfLines={1}>
              {item.description}
            </Text>
            {/* SECONDARY: Category (smaller) */}
            <Text style={styles.transactionCategory} numberOfLines={1}>
              {item.category}
            </Text>
          </View>
        </View>

        {/* Amount (RIGHT) - BIGGEST element */}
        <Text style={[
          styles.transactionAmount,
          { color: item.type === 'income' ? colors.income.primary : colors.text.primary }
        ]}>
          {item.type === 'income' ? '+' : '-'}{formatCurrency(item.amount)}
        </Text>
      </Pressable>
    </Swipeable>
  );

  // Date section header
  const renderSectionHeader = (group: TransactionGroup) => (
    <View style={styles.sectionHeader}>
      <Text style={styles.sectionDate}>{group.displayDate}</Text>
      <Text style={[
        styles.sectionTotal,
        { color: group.total >= 0 ? colors.income.primary : colors.expense.primary }
      ]}>
        {group.total >= 0 ? '+' : ''}{formatCurrency(group.total)}
      </Text>
    </View>
  );

  if (loading) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary[500]} />
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Transaction List */}
      {transactions.length === 0 ? (
        <View style={styles.emptyState}>
          <View style={styles.emptyIconContainer}>
            <Ionicons name="receipt-outline" size={64} color={colors.primary[500]} />
          </View>
          <Text style={styles.emptyTitle}>No Transactions Yet</Text>
          <Text style={styles.emptyText}>
            Tap the + button below to add your first transaction
          </Text>
        </View>
      ) : (
        <FlatList
          data={groupedTransactions}
          renderItem={({ item: group }) => (
            <View>
              {renderSectionHeader(group)}
              {group.transactions.map((transaction) => (
                <View key={transaction.id}>
                  {renderTransaction({ item: transaction })}
                </View>
              ))}
            </View>
          )}
          keyExtractor={(item) => item.date}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={colors.primary[500]}
            />
          }
          contentContainerStyle={styles.listContent}
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* FAB - BOTTOM RIGHT (Thumb-friendly) */}
      <FAB
        icon="add"
        onPress={() => {
          setQuickAddVisible(true);
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
        }}
      />

      {/* QUICK ADD Modal - Minimal friction */}
      <BottomSheet
        visible={quickAddVisible}
        onClose={() => setQuickAddVisible(false)}
        title="Quick Add"
        subtitle="Add a transaction in seconds"
      >
        {/* Type Toggle - BIG buttons */}
        <View style={styles.typeToggle}>
          <Pressable
            style={[
              styles.typeButton,
              quickType === 'expense' && styles.typeButtonExpense,
            ]}
            onPress={() => {
              setQuickType('expense');
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            }}
          >
            <Ionicons
              name="arrow-up"
              size={28}
              color={quickType === 'expense' ? colors.white : colors.expense.primary}
            />
            <Text style={[
              styles.typeButtonText,
              quickType === 'expense' && styles.typeButtonTextActive,
            ]}>
              Expense
            </Text>
          </Pressable>

          <Pressable
            style={[
              styles.typeButton,
              quickType === 'income' && styles.typeButtonIncome,
            ]}
            onPress={() => {
              setQuickType('income');
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            }}
          >
            <Ionicons
              name="arrow-down"
              size={28}
              color={quickType === 'income' ? colors.white : colors.income.primary}
            />
            <Text style={[
              styles.typeButtonText,
              quickType === 'income' && styles.typeButtonTextActive,
            ]}>
              Income
            </Text>
          </Pressable>
        </View>

        {/* Amount - ONLY required field */}
        <Input
          label="Amount *"
          value={quickAmount}
          onChangeText={setQuickAmount}
          keyboardType="decimal-pad"
          placeholder="0.00"
          autoFocus
          style={styles.amountInput}
        />

        {/* Description - Optional with smart default */}
        <Input
          label="Description (optional)"
          value={quickDescription}
          onChangeText={setQuickDescription}
          placeholder={`${quickType === 'expense' ? 'Coffee' : 'Salary'}`}
        />

        {/* BIG submit button */}
        <Pressable
          style={[
            styles.submitButton,
            quickType === 'expense' ? styles.submitButtonExpense : styles.submitButtonIncome,
          ]}
          onPress={handleQuickAdd}
          disabled={submitting}
        >
          {submitting ? (
            <ActivityIndicator color={colors.white} />
          ) : (
            <>
              <Ionicons name="checkmark-circle" size={24} color={colors.white} />
              <Text style={styles.submitButtonText}>
                Add {quickType === 'expense' ? 'Expense' : 'Income'}
              </Text>
            </>
          )}
        </Pressable>
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
  },
  listContent: {
    padding: theme.spacing.lg,
    paddingBottom: 100, // Space for FAB
  },

  // Date section header
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.xs,
    marginTop: theme.spacing.md,
  },
  sectionDate: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionTotal: {
    fontSize: 16,
    fontWeight: '700',
  },

  // SIMPLIFIED transaction card
  transactionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: colors.background.primary,
    padding: theme.spacing.lg,
    borderRadius: theme.radius.lg,
    marginBottom: theme.spacing.sm,
    minHeight: 72, // Ensure 48px+ touch target
    ...theme.shadows.sm,
  },
  transactionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: theme.spacing.md,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  transactionInfo: {
    flex: 1,
  },
  // PRIMARY info - biggest
  transactionDescription: {
    fontSize: 17, // Readable size
    fontWeight: '600',
    color: colors.text.primary,
    marginBottom: 4,
  },
  // SECONDARY info - smaller
  transactionCategory: {
    fontSize: 14,
    color: colors.text.secondary,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  // Amount - BIGGEST (most important)
  transactionAmount: {
    fontSize: 20, // Large, easy to scan
    fontWeight: '700',
    marginLeft: theme.spacing.md,
  },

  // Swipe actions
  swipeAction: {
    justifyContent: 'center',
    marginBottom: theme.spacing.sm,
  },
  deleteButton: {
    backgroundColor: colors.error.primary,
    justifyContent: 'center',
    alignItems: 'center',
    width: 80,
    height: '100%',
    borderRadius: theme.radius.lg,
    gap: 4,
  },
  deleteText: {
    color: colors.white,
    fontSize: 12,
    fontWeight: '600',
  },

  // Empty state
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.xxxl,
  },
  emptyIconContainer: {
    width: 120,
    height: 120,
    borderRadius: theme.radius.full,
    backgroundColor: colors.primary[50],
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.xl,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.text.primary,
    marginBottom: theme.spacing.sm,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: colors.text.secondary,
    textAlign: 'center',
    lineHeight: 24,
  },

  // Quick add modal
  typeToggle: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.xl,
  },
  typeButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: 64, // BIG touch target
    paddingVertical: theme.spacing.lg,
    paddingHorizontal: theme.spacing.md,
    borderRadius: theme.radius.lg,
    borderWidth: 2,
    borderColor: colors.border.medium,
    backgroundColor: colors.background.secondary,
  },
  typeButtonExpense: {
    backgroundColor: colors.expense.primary,
    borderColor: colors.expense.primary,
  },
  typeButtonIncome: {
    backgroundColor: colors.income.primary,
    borderColor: colors.income.primary,
  },
  typeButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text.secondary,
  },
  typeButtonTextActive: {
    color: colors.white,
  },
  amountInput: {
    fontSize: 24, // BIG for primary input
    fontWeight: '700',
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: 56, // BIG button
    paddingVertical: theme.spacing.lg,
    borderRadius: theme.radius.lg,
    marginTop: theme.spacing.xl,
  },
  submitButtonExpense: {
    backgroundColor: colors.expense.primary,
  },
  submitButtonIncome: {
    backgroundColor: colors.income.primary,
  },
  submitButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.white,
  },
});
