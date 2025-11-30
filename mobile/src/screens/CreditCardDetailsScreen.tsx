/**
 * Credit Card Details Screen - View Credit Card Info with Utilization Chart
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  ActivityIndicator,
  Alert,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRoute, useNavigation } from '@react-navigation/native';
import { GlassCard } from '../components/GlassCard';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { IconButton } from '../components/IconButton';
import { BottomSheet } from '../components/BottomSheet';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import { formatCurrency } from '../utils/currency';
import type { Account } from '../types';
import * as Haptics from 'expo-haptics';
import { format } from 'date-fns';

export const CreditCardDetailsScreen: React.FC = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { preferences } = useUserPreferences();
  const { accountId } = route.params as { accountId: string };
  
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    credit_limit: '',
    available_credit: '',
    statement_balance: '',
    minimum_payment: '',
  });

  useEffect(() => {
    loadAccount();
  }, [accountId]);

  const loadAccount = async () => {
    try {
      const data = await financialService.getAccount(accountId);
      setAccount(data.account);
      if (data.account.credit_card) {
        setFormData({
          credit_limit: data.account.credit_card.credit_limit.toString(),
          available_credit: data.account.credit_card.available_credit.toString(),
          statement_balance: data.account.credit_card.statement_balance.toString(),
          minimum_payment: data.account.credit_card.minimum_payment.toString(),
        });
      }
    } catch (error) {
      console.error('Failed to load account:', error);
      Alert.alert('Error', 'Failed to load credit card details');
      navigation.goBack();
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!formData.credit_limit || !formData.available_credit) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    try {
      await financialService.updateCreditCard(accountId, {
        credit_limit: parseFloat(formData.credit_limit),
        available_credit: parseFloat(formData.available_credit),
        statement_balance: parseFloat(formData.statement_balance),
        minimum_payment: parseFloat(formData.minimum_payment),
      });
      
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setEditModalVisible(false);
      loadAccount();
    } catch (error) {
      Alert.alert('Error', 'Failed to update credit card');
    } finally {
      setSubmitting(false);
    }
  };

  const getUtilizationColor = (utilization: number) => {
    if (utilization >= 80) return colors.expense.primary;
    if (utilization >= 50) return '#f59e0b';
    return colors.income.primary;
  };

  if (loading || !account || !account.credit_card) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.white} />
      </View>
    );
  }

  const cc = account.credit_card;
  const utilizationColor = getUtilizationColor(cc.credit_utilization);

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text.primary} />
        </TouchableOpacity>
        <IconButton
          icon="create-outline"
          onPress={() => setEditModalVisible(true)}
          variant="glass"
          size="sm"
        />
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Card Header */}
        <GlassCard variant="strong" style={styles.cardHeader}>
          <View style={styles.cardIcon}>
            <Ionicons name="card" size={32} color={colors.expense.primary} />
          </View>
          <Text style={styles.cardName}>{account.account_name}</Text>
          {account.institution_name && (
            <Text style={styles.institutionName}>{account.institution_name}</Text>
          )}
          {cc.card_last4 && (
            <Text style={styles.cardNumber}>•••• {cc.card_last4}</Text>
          )}
        </GlassCard>

        {/* Utilization Chart */}
        <GlassCard variant="medium">
          <Text style={styles.sectionTitle}>Credit Utilization</Text>
          <View style={styles.utilizationChart}>
            <View style={styles.chartCircle}>
              <Text style={[styles.utilizationPercent, { color: utilizationColor }]}>
                {cc.credit_utilization.toFixed(0)}%
              </Text>
              <Text style={styles.utilizationLabel}>Used</Text>
            </View>
          </View>
          
          <View style={styles.utilizationBar}>
            <View
              style={[
                styles.utilizationFill,
                {
                  width: `${Math.min(cc.credit_utilization, 100)}%`,
                  backgroundColor: utilizationColor,
                }
              ]}
            />
          </View>

          <View style={styles.creditRow}>
            <View style={styles.creditItem}>
              <Text style={styles.creditLabel}>Available</Text>
              <Text style={[styles.creditValue, { color: colors.income.primary }]}>
                {formatCurrency(cc.available_credit, preferences.currency)}
              </Text>
            </View>
            <View style={styles.creditDivider} />
            <View style={styles.creditItem}>
              <Text style={styles.creditLabel}>Limit</Text>
              <Text style={styles.creditValue}>
                {formatCurrency(cc.credit_limit, preferences.currency)}
              </Text>
            </View>
          </View>
        </GlassCard>

        {/* Balance Info */}
        <GlassCard variant="medium">
          <Text style={styles.sectionTitle}>Balance Information</Text>
          
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Current Balance</Text>
            <Text style={[styles.infoValue, { color: colors.expense.primary }]}>
              {formatCurrency(account.current_balance, preferences.currency)}
            </Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Statement Balance</Text>
            <Text style={styles.infoValue}>
              {formatCurrency(cc.statement_balance, preferences.currency)}
            </Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Minimum Payment</Text>
            <Text style={styles.infoValue}>
              {formatCurrency(cc.minimum_payment, preferences.currency)}
            </Text>
          </View>

          {cc.last_payment_amount > 0 && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Last Payment</Text>
              <Text style={styles.infoValue}>
                {formatCurrency(cc.last_payment_amount, preferences.currency)}
              </Text>
            </View>
          )}
        </GlassCard>

        {/* Card Details */}
        <GlassCard variant="medium">
          <Text style={styles.sectionTitle}>Card Details</Text>
          
          {cc.apr && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>APR</Text>
              <Text style={styles.infoValue}>{cc.apr}%</Text>
            </View>
          )}

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Annual Fee</Text>
            <Text style={styles.infoValue}>
              {formatCurrency(cc.annual_fee, preferences.currency)}
            </Text>
          </View>

          {cc.card_network && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Network</Text>
              <Text style={styles.infoValue}>
                {cc.card_network.replace('_', ' ').toUpperCase()}
              </Text>
            </View>
          )}

          {cc.payment_due_date && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Payment Due</Text>
              <Text style={styles.infoValue}>
                {format(new Date(cc.payment_due_date), 'MMM dd, yyyy')}
              </Text>
            </View>
          )}

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Autopay</Text>
            <View style={[
              styles.statusBadge,
              { backgroundColor: cc.autopay_enabled ? colors.income.glass : colors.glass.light }
            ]}>
              <Text style={[
                styles.statusText,
                { color: cc.autopay_enabled ? colors.income.primary : colors.text.secondary }
              ]}>
                {cc.autopay_enabled ? 'ENABLED' : 'DISABLED'}
              </Text>
            </View>
          </View>

          {cc.autopay_enabled && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Autopay Amount</Text>
              <Text style={styles.infoValue}>{cc.autopay_amount.toUpperCase()}</Text>
            </View>
          )}
        </GlassCard>

        {/* Rewards */}
        {(cc.rewards_program || cc.rewards_balance > 0) && (
          <GlassCard variant="medium">
            <Text style={styles.sectionTitle}>Rewards</Text>
            
            {cc.rewards_program && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Program</Text>
                <Text style={styles.infoValue}>{cc.rewards_program}</Text>
              </View>
            )}

            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Balance</Text>
              <Text style={[styles.infoValue, { color: colors.income.primary }]}>
                {cc.rewards_balance.toLocaleString()} pts
              </Text>
            </View>

            {cc.cashback_rate && (
              <View style={styles.infoRow}>
                <Text style={styles.infoLabel}>Cashback Rate</Text>
                <Text style={styles.infoValue}>{cc.cashback_rate}%</Text>
              </View>
            )}
          </GlassCard>
        )}
      </ScrollView>

      {/* Edit Modal */}
      <BottomSheet
        visible={editModalVisible}
        onClose={() => setEditModalVisible(false)}
        title="Edit Credit Card"
        subtitle="Update card details"
      >
        <Input
              label="Credit Limit"
              value={formData.credit_limit}
              onChangeText={(text) => setFormData({ ...formData, credit_limit: text })}
              keyboardType="decimal-pad"
              placeholder="0.00"
            />

            <Input
              label="Available Credit"
              value={formData.available_credit}
              onChangeText={(text) => setFormData({ ...formData, available_credit: text })}
              keyboardType="decimal-pad"
              placeholder="0.00"
            />

            <Input
              label="Statement Balance"
              value={formData.statement_balance}
              onChangeText={(text) => setFormData({ ...formData, statement_balance: text })}
              keyboardType="decimal-pad"
              placeholder="0.00"
            />

            <Input
              label="Minimum Payment"
              value={formData.minimum_payment}
              onChangeText={(text) => setFormData({ ...formData, minimum_payment: text })}
              keyboardType="decimal-pad"
              placeholder="0.00"
            />

            <Button
              title="Update Card"
              onPress={handleUpdate}
              loading={submitting}
              variant="primary"
              style={styles.submitButton}
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
    backgroundColor: colors.background.primary,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.xxl,
    paddingBottom: theme.spacing.md,
  },
  backButton: {
    padding: theme.spacing.sm,
  },
  content: {
    padding: theme.spacing.lg,
    gap: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
  cardHeader: {
    alignItems: 'center',
    padding: theme.spacing.xl,
  },
  cardIcon: {
    width: 64,
    height: 64,
    borderRadius: theme.radius.lg,
    backgroundColor: `${colors.expense.primary}20`,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  cardName: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.text.primary,
    marginBottom: theme.spacing.xs,
  },
  institutionName: {
    fontSize: 14,
    color: colors.text.secondary,
    marginBottom: theme.spacing.xs,
  },
  cardNumber: {
    fontSize: 16,
    fontFamily: 'monospace',
    color: colors.text.tertiary,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text.primary,
    marginBottom: theme.spacing.md,
  },
  utilizationChart: {
    alignItems: 'center',
    marginVertical: theme.spacing.lg,
  },
  chartCircle: {
    width: 140,
    height: 140,
    borderRadius: 70,
    borderWidth: 12,
    borderColor: colors.border.light,
    justifyContent: 'center',
    alignItems: 'center',
  },
  utilizationPercent: {
    fontSize: 36,
    fontWeight: '700',
  },
  utilizationLabel: {
    fontSize: 12,
    color: colors.text.secondary,
    marginTop: 4,
  },
  utilizationBar: {
    height: 8,
    backgroundColor: colors.gray[800],
    borderRadius: theme.radius.full,
    overflow: 'hidden',
    marginBottom: theme.spacing.lg,
  },
  utilizationFill: {
    height: '100%',
    borderRadius: theme.radius.full,
  },
  creditRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  creditItem: {
    flex: 1,
    alignItems: 'center',
  },
  creditDivider: {
    width: 1,
    height: 40,
    backgroundColor: colors.border.light,
  },
  creditLabel: {
    fontSize: 12,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  creditValue: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text.primary,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border.light,
  },
  infoLabel: {
    fontSize: 14,
    color: colors.text.secondary,
  },
  infoValue: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.text.primary,
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
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
  submitButton: {
    marginTop: theme.spacing.lg,
  },
});
