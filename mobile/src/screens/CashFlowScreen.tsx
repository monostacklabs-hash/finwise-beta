/**
 * Cash Flow Forecast Screen - Balance Projections & Runway
 * Glassmorphic Finance Theme - TIER 1 Feature
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Alert,
  TouchableOpacity,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../components/GlassCard';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { BottomSheet } from '../components/BottomSheet';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import type { CashFlowForecast, SummaryPeriod, DailyBalance } from '../types';
import { format } from 'date-fns';
import * as Haptics from 'expo-haptics';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import { formatCurrency as formatCurrencyUtil } from '../utils/currency';

export const CashFlowScreen: React.FC = () => {
  const { preferences } = useUserPreferences();
  const [forecast, setForecast] = useState<CashFlowForecast | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [modalVisible, setModalVisible] = useState(true); // Show setup modal initially
  const [startingBalance, setStartingBalance] = useState('');
  const [forecastDays, setForecastDays] = useState('90');

  const loadForecast = async (balance: number, days: number) => {
    setLoading(true);
    try {
      const data = await financialService.getCashFlowForecast({
        starting_balance: balance,
        forecast_days: days,
      });
      setForecast(data);
      setModalVisible(false);
    } catch (error) {
      console.error('Failed to load cash flow forecast:', error);
      Alert.alert('Error', 'Failed to generate forecast. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleGenerate = () => {
    const balance = parseFloat(startingBalance);
    const days = parseInt(forecastDays);

    if (isNaN(balance)) {
      Alert.alert('Error', 'Please enter a valid starting balance');
      return;
    }

    if (isNaN(days) || days < 1 || days > 365) {
      Alert.alert('Error', 'Please enter forecast days between 1 and 365');
      return;
    }

    loadForecast(balance, days);
  };

  const onRefresh = () => {
    if (forecast) {
      setRefreshing(true);
      loadForecast(forecast.starting_balance, forecast.forecast_days);
    }
  };

  const formatCurrency = (amount: number) => {
    return formatCurrencyUtil(amount, preferences.currency);
  };

  const renderSummaryPeriod = (period: SummaryPeriod, index: number) => {
    const isPositive = period.net_change >= 0;

    return (
      <GlassCard key={index} variant="medium" style={styles.periodCard}>
        <View style={styles.periodHeader}>
          <Text style={styles.periodTitle}>{period.period}</Text>
          <Text style={styles.periodDate}>
            {format(new Date(period.period_start), 'MMM dd')} - {format(new Date(period.period_end), 'MMM dd')}
          </Text>
        </View>

        <View style={styles.periodGrid}>
          <View style={styles.periodItem}>
            <Text style={styles.periodLabel}>Starting</Text>
            <Text style={styles.periodValue}>{formatCurrency(period.starting_balance)}</Text>
          </View>
          <View style={styles.periodItem}>
            <Text style={styles.periodLabel}>Ending</Text>
            <Text style={[
              styles.periodValue,
              { color: period.ending_balance < 0 ? colors.expense.primary : colors.text.primary }
            ]}>
              {formatCurrency(period.ending_balance)}
            </Text>
          </View>
        </View>

        <View style={styles.periodGrid}>
          <View style={styles.periodItem}>
            <Text style={styles.periodLabel}>Income</Text>
            <Text style={[styles.periodValue, { color: colors.income.primary }]}>
              +{formatCurrency(period.total_income)}
            </Text>
          </View>
          <View style={styles.periodItem}>
            <Text style={styles.periodLabel}>Expenses</Text>
            <Text style={[styles.periodValue, { color: colors.expense.primary }]}>
              -{formatCurrency(period.total_expenses)}
            </Text>
          </View>
        </View>

        <View style={styles.periodNetChange}>
          <Text style={styles.netChangeLabel}>Net Change</Text>
          <Text style={[
            styles.netChangeValue,
            { color: isPositive ? colors.income.primary : colors.expense.primary }
          ]}>
            {isPositive ? '+' : ''}{formatCurrency(period.net_change)}
          </Text>
        </View>
      </GlassCard>
    );
  };

  const renderBalanceMiniChart = () => {
    if (!forecast || !forecast.daily_balances || forecast.daily_balances.length === 0) return null;

    const balances = forecast.daily_balances.slice(0, 30); // First 30 days
    const maxBalance = Math.max(...balances.map(d => d.balance));
    const minBalance = Math.min(...balances.map(d => d.balance));
    const range = maxBalance - minBalance || 1;

    return (
      <View style={styles.miniChart}>
        {balances.map((day, index) => {
          const heightPercent = ((day.balance - minBalance) / range) * 100;
          const isNegative = day.balance < 0;

          return (
            <View
              key={index}
              style={[
                styles.miniChartBar,
                {
                  height: `${Math.max(heightPercent, 5)}%`,
                  backgroundColor: isNegative
                    ? colors.expense.primary
                    : day.balance < forecast.starting_balance * 0.2
                    ? colors.warning.primary
                    : colors.info.primary
                }
              ]}
            />
          );
        })}
      </View>
    );
  };

  if (loading && !forecast) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.info.primary} />
        <Text style={styles.loadingText}>Generating forecast...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Content */}
      {forecast ? (
        <ScrollView
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              tintColor={colors.white}
            />
          }
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Key Metrics */}
          <View style={styles.metricsRow}>
            <GlassCard variant="medium" style={styles.metricCard}>
              <Ionicons name="wallet" size={24} color={colors.info.primary} />
              <Text style={styles.metricLabel}>Starting Balance</Text>
              <Text style={styles.metricValue}>{formatCurrency(forecast.starting_balance)}</Text>
            </GlassCard>

            <GlassCard variant="medium" style={styles.metricCard}>
              <Ionicons name="trending-down" size={24} color={
                forecast.min_balance < 0 ? colors.expense.primary : colors.warning.primary
              } />
              <Text style={styles.metricLabel}>Lowest Point</Text>
              <Text style={[
                styles.metricValue,
                { color: forecast.min_balance < 0 ? colors.expense.primary : colors.text.primary }
              ]}>
                {formatCurrency(forecast.min_balance)}
              </Text>
            </GlassCard>
          </View>

          {/* Runway */}
          {forecast.runway_days !== null ? (
            <GlassCard variant="medium" style={styles.runwayCard}>
              <View style={styles.runwayHeader}>
                <Ionicons
                  name="speedometer"
                  size={32}
                  color={forecast.runway_days < 30 ? colors.expense.primary : colors.info.primary}
                />
                <View style={styles.runwayInfo}>
                  <Text style={styles.runwayLabel}>Financial Runway</Text>
                  <Text style={[
                    styles.runwayValue,
                    { color: forecast.runway_days < 30 ? colors.expense.primary : colors.income.primary }
                  ]}>
                    {forecast.runway_days} days
                  </Text>
                </View>
              </View>
              {forecast.runway_days < 30 && (
                <View style={styles.runwayWarning}>
                  <Ionicons name="warning" size={16} color={colors.expense.primary} />
                  <Text style={styles.runwayWarningText}>
                    Balance will hit $0 on {format(new Date(forecast.min_balance_date!), 'MMM dd, yyyy')}
                  </Text>
                </View>
              )}
            </GlassCard>
          ) : (
            <GlassCard variant="medium" style={styles.runwayCard}>
              <View style={styles.runwayHeader}>
                <Ionicons name="checkmark-circle" size={32} color={colors.income.primary} />
                <View style={styles.runwayInfo}>
                  <Text style={styles.runwayLabel}>Financial Runway</Text>
                  <Text style={[styles.runwayValue, { color: colors.income.primary }]}>
                    Healthy
                  </Text>
                </View>
              </View>
              <Text style={styles.runwayText}>
                Your balance stays positive for the entire forecast period
              </Text>
            </GlassCard>
          )}

          {/* Warnings */}
          {forecast.warnings && forecast.warnings.length > 0 && (
            <GlassCard variant="medium" style={styles.warningsCard}>
              <View style={styles.warningsHeader}>
                <Ionicons name="alert-circle" size={24} color={colors.warning.primary} />
                <Text style={styles.warningsTitle}>Warnings</Text>
              </View>
              {forecast.warnings.map((warning, index) => (
                <View key={index} style={styles.warningItem}>
                  <Ionicons name="chevron-forward" size={16} color={colors.warning.primary} />
                  <Text style={styles.warningText}>{warning}</Text>
                </View>
              ))}
            </GlassCard>
          )}

          {/* Balance Visualization (Mini Chart) */}
          <GlassCard variant="medium" style={styles.chartCard}>
            <Text style={styles.chartTitle}>30-Day Balance Trend</Text>
            {renderBalanceMiniChart()}
            <View style={styles.chartLegend}>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: colors.info.primary }]} />
                <Text style={styles.legendText}>Normal</Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: colors.warning.primary }]} />
                <Text style={styles.legendText}>Low</Text>
              </View>
              <View style={styles.legendItem}>
                <View style={[styles.legendDot, { backgroundColor: colors.expense.primary }]} />
                <Text style={styles.legendText}>Negative</Text>
              </View>
            </View>
          </GlassCard>

          {/* Period Summaries */}
          {forecast.summary_periods && Array.isArray(forecast.summary_periods) && forecast.summary_periods.length > 0 && (
            <>
              <Text style={styles.sectionTitle}>Period Summaries</Text>
              {forecast.summary_periods.map(renderSummaryPeriod)}
            </>
          )}
        </ScrollView>
      ) : (
        <View style={styles.emptyState}>
          <GlassCard variant="medium">
            <View style={styles.emptyContent}>
              <Ionicons name="analytics-outline" size={64} color={colors.info.primary} />
              <Text style={styles.emptyTitle}>Generate Forecast</Text>
              <Text style={styles.emptyText}>
                Enter your starting balance to see projected cash flow
              </Text>
              <Button
                title="Setup Forecast"
                onPress={() => setModalVisible(true)}
                variant="primary"
                icon="trending-up"
                style={styles.emptyButton}
              />
            </View>
          </GlassCard>
        </View>
      )}

      {/* Setup Modal */}
      <BottomSheet
        visible={modalVisible}
        onClose={() => { if (forecast) setModalVisible(false); }}
        title="Cash Flow Forecast"
        subtitle="Customize your forecast"
      >
        <Input
              label="Starting Balance"
              value={startingBalance}
              onChangeText={setStartingBalance}
              keyboardType="decimal-pad"
              placeholder="Enter current balance"
            />

            <Text style={styles.selectorLabel}>Forecast Period</Text>
            <View style={styles.periodSelector}>
              {['30', '60', '90', '180', '365'].map((days) => (
                <Pressable
                  key={days}
                  style={[
                    styles.periodButton,
                    forecastDays === days && styles.periodButtonActive,
                  ]}
                  onPress={() => setForecastDays(days)}
                >
                  <Text style={[
                    styles.periodButtonText,
                    forecastDays === days && styles.periodButtonTextActive,
                  ]}>
                    {days} days
                  </Text>
                </Pressable>
              ))}
            </View>

            <Button
              title="Generate Forecast"
              onPress={handleGenerate}
              loading={loading}
              variant="primary"
              icon="trending-up"
              style={styles.generateButton}
            />
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
    gap: theme.spacing.md,
  },
  loadingText: {
    fontSize: 16,
    color: colors.text.secondary,
  },
  scrollContent: {
    padding: theme.spacing.lg,
    paddingTop: 0,
    gap: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
  metricsRow: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  metricCard: {
    flex: 1,
    alignItems: 'center',
    padding: theme.spacing.lg,
  },
  metricLabel: {
    fontSize: 12,
    color: colors.text.secondary,
    marginTop: theme.spacing.sm,
    textAlign: 'center',
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text.primary,
    marginTop: 4,
  },
  runwayCard: {
    padding: theme.spacing.lg,
  },
  runwayHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.sm,
  },
  runwayInfo: {
    flex: 1,
  },
  runwayLabel: {
    fontSize: 14,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  runwayValue: {
    fontSize: 28,
    fontWeight: '700',
  },
  runwayText: {
    fontSize: 14,
    color: colors.text.secondary,
    marginTop: theme.spacing.sm,
  },
  runwayWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
    backgroundColor: colors.expense.glass,
    padding: theme.spacing.sm,
    borderRadius: theme.radius.sm,
    marginTop: theme.spacing.sm,
    borderWidth: 1,
    borderColor: colors.expense.primary,
  },
  runwayWarningText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.expense.primary,
    flex: 1,
  },
  warningsCard: {
    padding: theme.spacing.lg,
  },
  warningsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.md,
  },
  warningsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text.primary,
  },
  warningItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.xs,
    marginBottom: theme.spacing.sm,
  },
  warningText: {
    fontSize: 14,
    color: colors.text.secondary,
    flex: 1,
  },
  chartCard: {
    padding: theme.spacing.lg,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
    marginBottom: theme.spacing.md,
  },
  miniChart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    height: 100,
    gap: 2,
    marginBottom: theme.spacing.md,
  },
  miniChartBar: {
    flex: 1,
    borderRadius: 2,
    minHeight: 5,
  },
  chartLegend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: theme.spacing.lg,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendText: {
    fontSize: 12,
    color: colors.text.secondary,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.text.primary,
    marginBottom: theme.spacing.sm,
  },
  periodCard: {
    padding: theme.spacing.lg,
  },
  periodHeader: {
    marginBottom: theme.spacing.md,
  },
  periodTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text.primary,
    marginBottom: 4,
  },
  periodDate: {
    fontSize: 13,
    color: colors.text.secondary,
  },
  periodGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: theme.spacing.md,
  },
  periodItem: {
    flex: 1,
    alignItems: 'center',
  },
  periodLabel: {
    fontSize: 12,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  periodValue: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
  },
  periodNetChange: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border.light,
  },
  netChangeLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text.secondary,
  },
  netChangeValue: {
    fontSize: 18,
    fontWeight: '700',
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
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.95)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: colors.gray[900],
    borderTopLeftRadius: theme.radius.xl,
    borderTopRightRadius: theme.radius.xl,
    padding: theme.spacing.xl,
    paddingBottom: theme.spacing.xxl,
    borderTopWidth: 1,
    borderColor: colors.border.light,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.xl,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.text.primary,
  },
  selectorLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text.secondary,
    marginBottom: theme.spacing.sm,
    marginTop: theme.spacing.md,
  },
  periodSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.md,
  },
  periodButton: {
    flex: 1,
    minWidth: '30%',
    paddingVertical: theme.spacing.md,
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
  },
  periodButtonTextActive: {
    color: colors.info.primary,
  },
  generateButton: {
    marginTop: theme.spacing.lg,
  },
});
