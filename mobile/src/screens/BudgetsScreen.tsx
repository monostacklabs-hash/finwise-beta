/**
 * Budgets Screen - Budget Management & Tracking
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
import type { Budget, BudgetStatus } from '../types';
import * as Haptics from 'expo-haptics';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import { formatCurrency as formatCurrencyUtil } from '../utils/currency';
import { ScreenContainer } from '../components/ScreenContainer';

export const BudgetsScreen: React.FC = () => {
  const { preferences } = useUserPreferences();
  const [budgets, setBudgets] = useState<Budget[]>([]);
  const [budgetStatuses, setBudgetStatuses] = useState<Map<string, BudgetStatus>>(new Map());
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingBudget, setEditingBudget] = useState<Budget | null>(null);
  const [formData, setFormData] = useState({
    category: '',
    amount: '',
    period: 'monthly' as 'weekly' | 'monthly' | 'quarterly' | 'yearly',
    alert_threshold: '0.9',
  });
  const [submitting, setSubmitting] = useState(false);
  const [showInsights, setShowInsights] = useState(false);
  const [insights, setInsights] = useState<any>(null);
  const [loadingInsights, setLoadingInsights] = useState(false);

  const loadBudgets = async () => {
    try {
      const response = await financialService.getBudgets();
      setBudgets(response.budgets || []);

      // Load status for each budget
      const statusMap = new Map();
      for (const budget of response.budgets || []) {
        try {
          const status = await financialService.getBudgetStatus(budget.id);
          statusMap.set(budget.id, status);
        } catch (error) {
          console.error(`Failed to load status for budget ${budget.id}:`, error);
        }
      }
      setBudgetStatuses(statusMap);
    } catch (error) {
      console.error('Failed to load budgets:', error);
      Alert.alert('Error', 'Failed to load budgets. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadBudgets();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    loadBudgets();
  };

  const openAddModal = () => {
    setEditingBudget(null);
    setFormData({ category: '', amount: '', period: 'monthly', alert_threshold: '0.9' });
    setModalVisible(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const openEditModal = (budget: Budget) => {
    setEditingBudget(budget);
    setFormData({
      category: budget.category || '',
      amount: budget.amount?.toString() || '0',
      period: budget.period || 'monthly',
      alert_threshold: budget.alert_threshold?.toString() || '0.9',
    });
    setModalVisible(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const handleDeleteBudget = (budget: Budget) => {
    Alert.alert(
      'Delete Budget',
      `Are you sure you want to delete the ${budget.category} budget?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await financialService.deleteBudget(budget.id);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              loadBudgets();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete budget');
            }
          },
        },
      ]
    );
  };

  const handleSubmit = async () => {
    if (!formData.category || !formData.amount) {
      Alert.alert('Error', 'Please fill in category and amount');
      return;
    }

    setSubmitting(true);
    try {
      const data = {
        category: formData.category,
        amount: parseFloat(formData.amount),
        period: formData.period,
        alert_threshold: parseFloat(formData.alert_threshold),
      };

      if (editingBudget) {
        await financialService.updateBudget(editingBudget.id, data);
      } else {
        await financialService.createBudget(data);
      }

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setModalVisible(false);
      setFormData({ category: '', amount: '', period: 'monthly', alert_threshold: '0.9' });
      setEditingBudget(null);
      loadBudgets();
    } catch (error) {
      Alert.alert('Error', `Failed to ${editingBudget ? 'update' : 'create'} budget`);
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return formatCurrencyUtil(amount, preferences.currency);
  };

  const loadAIInsights = async () => {
    if (budgets.length === 0) {
      Alert.alert('No Budgets', 'Create some budgets first to get AI insights.');
      return;
    }

    setLoadingInsights(true);
    try {
      const analysis = await financialService.analyzeBudgets();
      setInsights(analysis);
      setShowInsights(true);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    } catch (error) {
      Alert.alert('Error', 'Failed to load AI insights. Please try again.');
    } finally {
      setLoadingInsights(false);
    }
  };

  const applyAdjustments = async () => {
    if (!insights?.adjustments || insights.adjustments.length === 0) return;

    Alert.alert(
      'Apply Adjustments',
      `Apply ${insights.adjustments.length} AI-recommended budget changes?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Apply',
          onPress: async () => {
            try {
              await financialService.applyBudgetAdjustments(insights.adjustments, true);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              setShowInsights(false);
              loadBudgets();
              Alert.alert('Success', 'Budget adjustments applied!');
            } catch (error) {
              Alert.alert('Error', 'Failed to apply adjustments');
            }
          },
        },
      ]
    );
  };

  const renderBudgetCard = ({ item }: { item: Budget }) => {
    const status = budgetStatuses.get(item.id);
    const percentage = status ? status.percentage_used : 0;
    const isOverspent = status ? status.is_overspent : false;

    return (
      <GlassCard variant="medium" style={styles.budgetCard}>
        <View style={styles.budgetHeader}>
          <View style={styles.budgetTitleRow}>
            <Ionicons name="wallet" size={24} color={colors.info.primary} />
            <Text style={styles.budgetCategory}>{item.category.toUpperCase()}</Text>
          </View>
          <View style={styles.actionButtons}>
            <TouchableOpacity
              onPress={() => openEditModal(item)}
              style={styles.actionButton}
            >
              <Ionicons name="create-outline" size={20} color={colors.text.secondary} />
            </TouchableOpacity>
            <TouchableOpacity
              onPress={() => handleDeleteBudget(item)}
              style={styles.actionButton}
            >
              <Ionicons name="trash-outline" size={20} color={colors.text.secondary} />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.periodBadge}>
          <Text style={styles.periodText}>{item.period.toUpperCase()}</Text>
        </View>

        {status && (
          <>
            <View style={styles.amountsRow}>
              <View style={styles.amountColumn}>
                <Text style={styles.amountLabel}>Budget</Text>
                <Text style={styles.amountValue}>{formatCurrency(status.budgeted_amount)}</Text>
              </View>
              <View style={styles.amountColumn}>
                <Text style={styles.amountLabel}>Spent</Text>
                <Text style={[
                  styles.amountValue,
                  { color: isOverspent ? colors.expense.primary : colors.text.primary }
                ]}>
                  {formatCurrency(status.actual_spent)}
                </Text>
              </View>
              <View style={styles.amountColumn}>
                <Text style={styles.amountLabel}>Remaining</Text>
                <Text style={[
                  styles.amountValue,
                  { color: isOverspent ? colors.expense.primary : colors.income.primary }
                ]}>
                  {formatCurrency(status.remaining)}
                </Text>
              </View>
            </View>

            <View style={styles.progressContainer}>
              <View style={styles.progressBar}>
                <View
                  style={[
                    styles.progressFill,
                    {
                      width: `${Math.min(percentage, 100)}%`,
                      backgroundColor: isOverspent
                        ? colors.expense.primary
                        : percentage >= item.alert_threshold * 100
                          ? colors.warning.primary
                          : colors.income.primary
                    }
                  ]}
                />
              </View>
              <Text style={[
                styles.progressText,
                { color: isOverspent ? colors.expense.primary : colors.text.primary }
              ]}>
                {percentage.toFixed(1)}%
              </Text>
            </View>

            {isOverspent && (
              <View style={styles.alertBanner}>
                <Ionicons name="warning" size={16} color={colors.expense.primary} />
                <Text style={styles.alertText}>
                  OVERSPENT by {formatCurrency(Math.abs(status.remaining))}
                </Text>
              </View>
            )}

            {!isOverspent && percentage >= item.alert_threshold * 100 && (
              <View style={[styles.alertBanner, { backgroundColor: colors.warning.glass }]}>
                <Ionicons name="alert-circle" size={16} color={colors.warning.primary} />
                <Text style={[styles.alertText, { color: colors.warning.primary }]}>
                  {(item.alert_threshold * 100).toFixed(0)}% threshold reached
                </Text>
              </View>
            )}
          </>
        )}
      </GlassCard>
    );
  };

  if (loading) {
    return (
      <ScreenContainer>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.info.primary} />
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scrollable={false} contentContainerStyle={{ paddingHorizontal: 0 }}>
      {/* Budget List */}
      {budgets.length === 0 ? (
        <View style={styles.emptyState}>
          <GlassCard variant="medium">
            <View style={styles.emptyContent}>
              <Ionicons name="wallet-outline" size={64} color={colors.info.primary} />
              <Text style={styles.emptyTitle}>No Budgets Yet</Text>
              <Text style={styles.emptyText}>
                Create budgets to track your spending by category
              </Text>
              <Button
                title="Create Budget"
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
          data={budgets}
          renderItem={renderBudgetCard}
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

      {/* AI Insights Modal */}
      <BottomSheet
        visible={showInsights}
        onClose={() => setShowInsights(false)}
        title="AI Budget Insights"
        subtitle="Optimize your spending"
      >
        <ScrollView showsVerticalScrollIndicator={false}>
          {insights && (
            <>
              {/* Analysis Summary */}
              <GlassCard variant="medium" style={styles.insightCard}>
                <Text style={styles.insightTitle}>📊 Analysis</Text>
                <View style={styles.insightRow}>
                  <Text style={styles.insightLabel}>Total Budget:</Text>
                  <Text style={styles.insightValue}>
                    {formatCurrency(insights.analysis?.total_budget || 0)}
                  </Text>
                </View>
                <View style={styles.insightRow}>
                  <Text style={styles.insightLabel}>Total Spent:</Text>
                  <Text style={[styles.insightValue, {
                    color: (insights.analysis?.total_spent || 0) > (insights.analysis?.total_budget || 0)
                      ? colors.expense.primary
                      : colors.text.primary
                  }]}>
                    {formatCurrency(insights.analysis?.total_spent || 0)}
                  </Text>
                </View>
                <View style={styles.insightRow}>
                  <Text style={styles.insightLabel}>Overspent Categories:</Text>
                  <Text style={styles.insightValue}>
                    {insights.analysis?.overspent_categories || 0}
                  </Text>
                </View>
              </GlassCard>

              {/* Adjustments */}
              {insights.adjustments && insights.adjustments.length > 0 ? (
                <>
                  <Text style={styles.sectionTitle}>Recommended Changes</Text>
                  {insights.adjustments.map((adj: any, index: number) => (
                    <GlassCard key={index} variant="light" style={styles.adjustmentCard}>
                      <View style={styles.adjustmentHeader}>
                        <Text style={styles.adjustmentCategory}>
                          {adj.category.toUpperCase()}
                        </Text>
                        <View style={[styles.adjustmentBadge, {
                          backgroundColor: adj.change < 0 ? colors.expense.glass : colors.income.glass,
                          borderColor: adj.change < 0 ? colors.expense.primary : colors.income.primary,
                        }]}>
                          <Text style={[styles.adjustmentBadgeText, {
                            color: adj.change < 0 ? colors.expense.primary : colors.income.primary,
                          }]}>
                            {adj.change < 0 ? '📉' : '📈'} {adj.change > 0 ? '+' : ''}{formatCurrency(adj.change)}
                          </Text>
                        </View>
                      </View>
                      <View style={styles.adjustmentAmounts}>
                        <Text style={styles.adjustmentText}>
                          {formatCurrency(adj.current_amount)} → {formatCurrency(adj.new_amount)}
                        </Text>
                      </View>
                      <Text style={styles.adjustmentReason}>{adj.reason}</Text>
                    </GlassCard>
                  ))}

                  <Button
                    title="Apply All Adjustments"
                    onPress={applyAdjustments}
                    variant="primary"
                    icon="checkmark-circle"
                    style={styles.applyButton}
                  />
                </>
              ) : (
                <GlassCard variant="medium" style={styles.insightCard}>
                  <Text style={styles.insightTitle}>✅ All Good!</Text>
                  <Text style={styles.insightText}>
                    Your budgets are well-balanced. No adjustments needed right now.
                  </Text>
                </GlassCard>
              )}
            </>
          )}
        </ScrollView>
      </BottomSheet>

      {/* Add/Edit Modal */}
      <BottomSheet
        visible={modalVisible}
        onClose={() => setModalVisible(false)}
        title={editingBudget ? 'Edit Budget' : 'Create Budget'}
        subtitle="Set your spending limits"
      >
        <ScrollView showsVerticalScrollIndicator={false}>
          <Input
            label="Category"
            value={formData.category}
            onChangeText={(text) => setFormData({ ...formData, category: text })}
            placeholder="e.g., Groceries, Entertainment, Transport"
          />

          <Input
            label="Budget Amount"
            value={formData.amount}
            onChangeText={(text) => setFormData({ ...formData, amount: text })}
            keyboardType="decimal-pad"
            placeholder="0.00"
          />

          {/* Period Selector */}
          <Text style={styles.selectorLabel}>Period</Text>
          <View style={styles.periodSelector}>
            {['weekly', 'monthly', 'quarterly', 'yearly'].map((period) => (
              <Pressable
                key={period}
                style={[
                  styles.periodButton,
                  formData.period === period && styles.periodButtonActive,
                ]}
                onPress={() => setFormData({ ...formData, period: period as any })}
              >
                <Text style={[
                  styles.periodButtonText,
                  formData.period === period && styles.periodButtonTextActive,
                ]}>
                  {period}
                </Text>
              </Pressable>
            ))}
          </View>

          <Input
            label="Alert Threshold (0-1)"
            value={formData.alert_threshold}
            onChangeText={(text) => setFormData({ ...formData, alert_threshold: text })}
            keyboardType="decimal-pad"
            placeholder="0.9"
          />
          <Text style={styles.helperText}>
            Get notified when you reach this % of your budget (0.9 = 90%)
          </Text>

          <Button
            title={editingBudget ? 'Update Budget' : 'Create Budget'}
            onPress={handleSubmit}
            loading={submitting}
            variant="primary"
            style={styles.submitButton}
          />
        </ScrollView>
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
    backgroundColor: colors.background.secondary,
  },
  listContent: {
    padding: theme.spacing.lg,
    paddingTop: 0,
    gap: theme.spacing.md,
    paddingBottom: theme.spacing.xxl,
  },
  budgetCard: {
    marginBottom: 0,
  },
  budgetHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.sm,
  },
  budgetTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    flex: 1,
  },
  budgetCategory: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
    letterSpacing: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  actionButton: {
    padding: theme.spacing.xs,
  },
  periodBadge: {
    alignSelf: 'flex-start',
    backgroundColor: colors.info.glass,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 4,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
    borderColor: colors.info.primary,
    marginBottom: theme.spacing.md,
  },
  periodText: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.info.primary,
  },
  amountsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.md,
  },
  amountColumn: {
    flex: 1,
    alignItems: 'center',
  },
  amountLabel: {
    fontSize: 12,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  amountValue: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.sm,
  },
  progressBar: {
    flex: 1,
    height: 10,
    backgroundColor: colors.gray[800],
    borderRadius: theme.radius.full,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: theme.radius.full,
  },
  progressText: {
    fontSize: 14,
    fontWeight: '700',
    minWidth: 50,
    textAlign: 'right',
  },
  alertBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    backgroundColor: colors.expense.glass,
    padding: theme.spacing.sm,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
    borderColor: colors.expense.primary,
  },
  alertText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.expense.primary,
    flex: 1,
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
  selectorLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text.secondary,
    marginBottom: theme.spacing.sm,
  },
  periodSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.md,
  },
  periodButton: {
    flex: 1,
    minWidth: '45%',
    paddingVertical: theme.spacing.md,
    paddingHorizontal: theme.spacing.sm,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: colors.border.light,
    backgroundColor: colors.background.secondary,
    alignItems: 'center',
  },
  periodButtonActive: {
    backgroundColor: colors.info.glass,
    borderColor: colors.info.primary,
  },
  periodButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text.secondary,
    textTransform: 'capitalize',
  },
  periodButtonTextActive: {
    color: colors.info.primary,
  },
  helperText: {
    fontSize: 12,
    color: colors.text.tertiary,
    marginTop: -theme.spacing.sm,
    marginBottom: theme.spacing.md,
  },
  submitButton: {
    marginTop: theme.spacing.lg,
  },
  insightCard: {
    marginBottom: theme.spacing.md,
  },
  insightTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
    marginBottom: theme.spacing.sm,
  },
  insightRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 6,
  },
  insightLabel: {
    fontSize: 14,
    color: colors.text.secondary,
  },
  insightValue: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text.primary,
  },
  insightText: {
    fontSize: 14,
    color: colors.text.secondary,
    lineHeight: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text.primary,
    marginTop: theme.spacing.md,
    marginBottom: theme.spacing.sm,
  },
  adjustmentCard: {
    marginBottom: theme.spacing.sm,
  },
  adjustmentHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.xs,
  },
  adjustmentCategory: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text.primary,
    letterSpacing: 0.5,
  },
  adjustmentBadge: {
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 4,
    borderRadius: theme.radius.sm,
    borderWidth: 1,
  },
  adjustmentBadgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  adjustmentAmounts: {
    marginBottom: theme.spacing.xs,
  },
  adjustmentText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text.primary,
  },
  adjustmentReason: {
    fontSize: 13,
    color: colors.text.secondary,
    lineHeight: 18,
  },
  applyButton: {
    marginTop: theme.spacing.lg,
  },
});
