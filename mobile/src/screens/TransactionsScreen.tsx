/**
 * Transactions Screen - 2025 Modern Design
 * Clean list with edit/delete functionality
 */

import React, { useState, useEffect, useLayoutEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Modal,
  TouchableOpacity,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { IconButton } from '../components/IconButton';
import { Input } from '../components/Input';
import { BottomSheet } from '../components/BottomSheet';
import { CategoryPicker } from '../components/CategoryPicker';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import type { Transaction, Category, TransactionSpecialType } from '../types';
import { format } from 'date-fns';
import * as Haptics from 'expo-haptics';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import { formatCurrency as formatCurrencyUtil } from '../utils/currency';

import { ScreenContainer } from '../components/ScreenContainer';

export const TransactionsScreen: React.FC = () => {
  const navigation = useNavigation();
  const { preferences } = useUserPreferences();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [categoryPickerVisible, setCategoryPickerVisible] = useState(false);
  const [editingTransaction, setEditingTransaction] = useState<Transaction | null>(null);
  const [formData, setFormData] = useState({
    type: 'expense' as 'income' | 'expense' | 'lending' | 'borrowing',
    special_type: undefined as TransactionSpecialType | undefined,
    amount: '',
    category: '',
    categoryPath: '',
    description: '',
  });
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

  useLayoutEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <TouchableOpacity
          onPress={openAddModal}
          style={{ marginRight: 8 }}
        >
          <Ionicons name="add" size={28} color={colors.primary[500]} />
        </TouchableOpacity>
      ),
    });
  }, [navigation]);

  const onRefresh = () => {
    setRefreshing(true);
    loadTransactions();
  };

  const openAddModal = () => {
    setEditingTransaction(null);
    setFormData({ type: 'expense', special_type: undefined, amount: '', category: '', categoryPath: '', description: '' });
    setModalVisible(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const openEditModal = (transaction: Transaction) => {
    setEditingTransaction(transaction);
    setFormData({
      type: transaction.type || 'expense',
      special_type: transaction.special_type,
      amount: transaction.amount?.toString() || '0',
      category: transaction.category || '',
      categoryPath: transaction.category || '',
      description: transaction.description || '',
    });
    setModalVisible(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const handleDeleteTransaction = (transaction: Transaction) => {
    Alert.alert(
      'Delete Transaction',
      'Are you sure you want to delete this transaction?',
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

  const handleSubmit = async () => {
    if (!formData.amount || !formData.category || !formData.description) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setSubmitting(true);
    try {
      if (editingTransaction) {
        await financialService.updateTransaction(editingTransaction.id, {
          type: formData.type,
          special_type: formData.special_type,
          amount: parseFloat(formData.amount),
          category: formData.category,
          description: formData.description,
        });
      } else {
        await financialService.addTransaction({
          type: formData.type,
          special_type: formData.special_type,
          amount: parseFloat(formData.amount),
          category: formData.category,
          description: formData.description,
        });
      }

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setModalVisible(false);
      setFormData({ type: 'expense', special_type: undefined, amount: '', category: '', categoryPath: '', description: '' });
      setEditingTransaction(null);
      loadTransactions();
    } catch (error) {
      Alert.alert('Error', `Failed to ${editingTransaction ? 'update' : 'add'} transaction`);
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return formatCurrencyUtil(amount, preferences.currency);
  };

  const renderTransaction = ({ item }: { item: Transaction }) => (
    <Card variant="elevated" style={styles.transactionCard}>
      <View style={styles.transactionRow}>
        <View style={[
          styles.iconContainer,
          { backgroundColor: item.type === 'income' ? colors.income.light : colors.expense.light }
        ]}>
          <Ionicons
            name={item.type === 'income' ? 'arrow-down-circle' : 'arrow-up-circle'}
            size={24}
            color={item.type === 'income' ? colors.income.primary : colors.expense.primary}
          />
        </View>

        <View style={styles.transactionInfo}>
          <Text style={styles.transactionDescription}>{item.description}</Text>
          <View style={styles.transactionMeta}>
            <Text style={styles.transactionCategory}>{item.category}</Text>
            <Text style={styles.transactionDot}>•</Text>
            <Text style={styles.transactionDate}>
              {format(new Date(item.date), 'MMM dd, yyyy')}
            </Text>
          </View>
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
              onPress={() => openEditModal(item)}
              style={styles.actionButton}
            >
              <Ionicons name="create-outline" size={18} color={colors.text.tertiary} />
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => handleDeleteTransaction(item)}
              style={styles.actionButton}
            >
              <Ionicons name="trash-outline" size={18} color={colors.text.tertiary} />
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Card>
  );

  if (loading) {
    return (
      <ScreenContainer>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary[500]} />
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scrollable={false} contentContainerStyle={{ paddingHorizontal: 0 }}>
      {/* Transaction List */}
      {transactions.length === 0 ? (
        <View style={styles.emptyState}>
          <Card variant="elevated">
            <View style={styles.emptyContent}>
              <View style={styles.emptyIconContainer}>
                <Ionicons name="receipt-outline" size={48} color={colors.primary[500]} />
              </View>
              <Text style={styles.emptyTitle}>No Transactions Yet</Text>
              <Text style={styles.emptyText}>
                Tap the + button to add your first transaction
              </Text>
            </View>
          </Card>
        </View>
      ) : (
        <FlatList
          data={transactions}
          renderItem={renderTransaction}
          keyExtractor={(item) => item.id}
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

      {/* Category Picker Modal */}
      <Modal
        visible={categoryPickerVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setCategoryPickerVisible(false)}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity
              onPress={() => setCategoryPickerVisible(false)}
              style={styles.modalCloseButton}
            >
              <Ionicons name="close" size={28} color={colors.text.primary} />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Select Category</Text>
            <View style={styles.modalSpacer} />
          </View>
          <CategoryPicker
            onSelect={(category: Category, fullPath: string) => {
              setFormData({
                ...formData,
                category: category.name,
                categoryPath: fullPath,
              });
              setCategoryPickerVisible(false);
              Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
            }}
            selectedCategory={formData.category}
            showPath={true}
          />
        </View>
      </Modal>

      {/* Add/Edit Modal */}
      <BottomSheet
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        title={editingTransaction ? 'Edit Transaction' : 'Add Transaction'}
        subtitle="Fill in the details below"
      >

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
              color={formData.type === 'expense' ? colors.expense.primary : colors.gray[400]}
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
              color={formData.type === 'income' ? colors.income.primary : colors.gray[400]}
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

        {/* Category Selector */}
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>Category</Text>
          <TouchableOpacity
            style={styles.categoryButton}
            onPress={() => setCategoryPickerVisible(true)}
          >
            <View style={styles.categoryButtonContent}>
              <Ionicons name="pricetag-outline" size={20} color={colors.text.secondary} />
              <Text style={[
                styles.categoryButtonText,
                !formData.categoryPath && styles.categoryButtonPlaceholder
              ]}>
                {formData.categoryPath || 'Select category'}
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.text.tertiary} />
          </TouchableOpacity>
        </View>

        <Input
          label="Description"
          value={formData.description}
          onChangeText={(text) => setFormData({ ...formData, description: text })}
          placeholder="What was this for?"
          multiline
        />

        <Button
          title={editingTransaction ? 'Update Transaction' : 'Add Transaction'}
          onPress={handleSubmit}
          loading={submitting}
          variant="primary"
          style={styles.submitButton}
        />
      </BottomSheet>
    </ScreenContainer>
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
    gap: theme.spacing.md,
    paddingBottom: theme.spacing.xxl,
  },
  transactionCard: {
    padding: theme.spacing.md,
  },
  transactionRow: {
    flexDirection: 'row',
    alignItems: 'center',
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
  transactionDescription: {
    ...theme.typography.body,
    color: colors.text.primary,
    fontWeight: '600',
    marginBottom: 4,
  },
  transactionMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  transactionCategory: {
    ...theme.typography.caption,
    color: colors.text.secondary,
    textTransform: 'uppercase',
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  transactionDot: {
    ...theme.typography.caption,
    color: colors.text.tertiary,
  },
  transactionDate: {
    ...theme.typography.caption,
    color: colors.text.tertiary,
  },
  transactionRight: {
    alignItems: 'flex-end',
    gap: theme.spacing.sm,
  },
  transactionAmount: {
    ...theme.typography.h4,
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
  emptyIconContainer: {
    width: 96,
    height: 96,
    borderRadius: theme.radius.full,
    backgroundColor: colors.primary[50],
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.lg,
  },
  emptyTitle: {
    ...theme.typography.h3,
    color: colors.text.primary,
    marginBottom: theme.spacing.sm,
    fontWeight: '600',
  },
  emptyText: {
    ...theme.typography.body,
    color: colors.text.secondary,
    textAlign: 'center',
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
    borderWidth: 2,
    borderColor: colors.border.medium,
    backgroundColor: colors.background.secondary,
  },
  typeButtonExpenseActive: {
    backgroundColor: colors.expense.light,
    borderColor: colors.expense.primary,
  },
  typeButtonIncomeActive: {
    backgroundColor: colors.income.light,
    borderColor: colors.income.primary,
  },
  typeButtonText: {
    ...theme.typography.body,
    color: colors.gray[400],
    fontWeight: '600',
  },
  typeButtonExpenseTextActive: {
    color: colors.expense.primary,
  },
  typeButtonIncomeTextActive: {
    color: colors.income.primary,
  },
  submitButton: {
    marginTop: theme.spacing.md,
  },
  inputGroup: {
    marginBottom: theme.spacing.md,
  },
  inputLabel: {
    ...theme.typography.caption,
    color: colors.text.secondary,
    fontWeight: '600',
    marginBottom: theme.spacing.sm,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  categoryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: theme.spacing.md,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: colors.border.medium,
    backgroundColor: colors.background.secondary,
  },
  categoryButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    flex: 1,
  },
  categoryButtonText: {
    ...theme.typography.body,
    color: colors.text.primary,
  },
  categoryButtonPlaceholder: {
    color: colors.text.tertiary,
  },
  modalContainer: {
    flex: 1,
    backgroundColor: colors.background.primary,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.xxl,
    paddingBottom: theme.spacing.lg,
    borderBottomWidth: 1,
    borderBottomColor: colors.border.light,
  },
  modalCloseButton: {
    padding: theme.spacing.sm,
  },
  modalTitle: {
    ...theme.typography.h3,
    color: colors.text.primary,
    fontWeight: '700',
  },
  modalSpacer: {
    width: 44,
  },
});
