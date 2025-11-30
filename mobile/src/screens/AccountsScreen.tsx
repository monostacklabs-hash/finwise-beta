/**
 * Accounts Screen - Multi-Account Management
 * Lists all accounts with balances and quick actions
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { GlassCard } from '../components/GlassCard';
import { Card } from '../components/Card';
import { IconButton } from '../components/IconButton';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import { formatCurrency } from '../utils/currency';
import type { Account, AccountType } from '../types';
import * as Haptics from 'expo-haptics';

import { ScreenContainer } from '../components/ScreenContainer';

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
  netWorthCard: {
    marginHorizontal: theme.spacing.lg,
    marginTop: theme.spacing.lg,
    marginBottom: theme.spacing.lg,
    alignItems: 'center',
    paddingVertical: theme.spacing.xxl,
  },
  netWorthLabel: {
    ...theme.typography.bodySmall,
    color: colors.text.secondary,
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  netWorthValue: {
    ...theme.typography.h1,
    color: colors.text.primary,
    fontWeight: '700',
  },
  listContent: {
    padding: theme.spacing.lg,
    paddingTop: 0,
    gap: theme.spacing.lg,
    paddingBottom: theme.spacing.xxxl,
  },
  accountCard: {
    marginBottom: 0,
  },
  accountRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: theme.radius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  accountInfo: {
    flex: 1,
  },
  accountName: {
    ...theme.typography.h5,
    color: colors.text.primary,
    marginBottom: theme.spacing.xs,
  },
  institutionName: {
    fontSize: 13,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  accountMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  accountType: {
    fontSize: 11,
    fontWeight: '600',
    color: colors.text.tertiary,
    letterSpacing: 0.5,
  },
  metaDivider: {
    fontSize: 11,
    color: colors.text.tertiary,
  },
  accountNumber: {
    fontSize: 11,
    color: colors.text.tertiary,
    fontFamily: 'monospace',
  },
  balanceContainer: {
    alignItems: 'flex-end',
  },
  balance: {
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 2,
  },
  utilization: {
    fontSize: 11,
    color: colors.text.tertiary,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.xl,
  },
  emptyContent: {
    alignItems: 'center',
    maxWidth: 320,
  },
  emptyIconContainer: {
    width: 80,
    height: 80,
    borderRadius: theme.radius.xl,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: theme.spacing.lg,
  },
  emptyTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.text.primary,
    marginTop: theme.spacing.lg,
    marginBottom: theme.spacing.sm,
  },
  emptyText: {
    fontSize: 15,
    color: colors.text.secondary,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: theme.spacing.xl,
  },
  emptyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.primary[500],
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: theme.radius.full,
  },
  emptyButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.white,
  },
});

export const AccountsScreen: React.FC = () => {
  const navigation = useNavigation();
  const { preferences } = useUserPreferences();
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadAccounts();
  }, []);

  const loadAccounts = async () => {
    try {
      const response = await financialService.getAccounts();
      setAccounts(response.accounts || []);
    } catch (error) {
      console.error('Failed to load accounts:', error);
      Alert.alert('Error', 'Failed to load accounts');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadAccounts();
  };

  const getAccountIcon = (type: AccountType): keyof typeof Ionicons.glyphMap => {
    switch (type) {
      case 'checking': return 'card-outline';
      case 'savings': return 'wallet-outline';
      case 'credit_card': return 'card';
      case 'investment': return 'trending-up';
      case 'cash': return 'cash-outline';
      default: return 'ellipse-outline';
    }
  };

  const getAccountColor = (type: AccountType) => {
    switch (type) {
      case 'checking': return colors.info.primary;
      case 'savings': return colors.income.primary;
      case 'credit_card': return colors.expense.primary;
      case 'investment': return '#9333ea';
      case 'cash': return '#10b981';
      default: return colors.text.secondary;
    }
  };

  const getTotalBalance = () => {
    return accounts.reduce((sum, acc) => {
      if (acc.account_type === 'credit_card') {
        return sum - acc.current_balance;
      }
      return sum + acc.current_balance;
    }, 0);
  };

  const handleAccountPress = (account: Account) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    if (account.account_type === 'credit_card') {
      (navigation as any).navigate('CreditCardDetails', { accountId: account.id });
    } else {
      (navigation as any).navigate('AccountDetails', { accountId: account.id });
    }
  };

  const handleAddAccount = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    (navigation as any).navigate('AddAccount');
  };

  const renderAccount = ({ item }: { item: Account }) => {
    const accountColor = getAccountColor(item.account_type);
    const isCreditCard = item.account_type === 'credit_card';

    return (
      <TouchableOpacity onPress={() => handleAccountPress(item)}>
        <GlassCard variant="medium" style={styles.accountCard}>
          <View style={styles.accountRow}>
            <View style={[styles.iconContainer, { backgroundColor: `${accountColor}20` }]}>
              <Ionicons name={getAccountIcon(item.account_type)} size={24} color={accountColor} />
            </View>

            <View style={styles.accountInfo}>
              <Text style={styles.accountName}>{item.account_name}</Text>
              {item.institution_name && (
                <Text style={styles.institutionName}>{item.institution_name}</Text>
              )}
              <View style={styles.accountMeta}>
                <Text style={styles.accountType}>
                  {item.account_type.replace('_', ' ').toUpperCase()}
                </Text>
                {item.account_number_last4 && (
                  <>
                    <Text style={styles.metaDivider}>•</Text>
                    <Text style={styles.accountNumber}>••{item.account_number_last4}</Text>
                  </>
                )}
              </View>
            </View>

            <View style={styles.balanceContainer}>
              <Text style={[
                styles.balance,
                { color: isCreditCard ? colors.expense.primary : colors.text.primary }
              ]}>
                {formatCurrency(isCreditCard ? Math.abs(item.current_balance) : item.current_balance, preferences.currency)}
              </Text>
              {isCreditCard && item.credit_card && (
                <Text style={styles.utilization}>
                  {item.credit_card.credit_utilization.toFixed(0)}% used
                </Text>
              )}
            </View>
          </View>
        </GlassCard>
      </TouchableOpacity>
    );
  };

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
      {/* Account List */}
      {accounts.length === 0 ? (
        <View style={styles.emptyState}>
          <View style={styles.emptyContent}>
            <View style={[styles.emptyIconContainer, { backgroundColor: `${colors.primary[500]}20` }]}>
              <Ionicons name="wallet-outline" size={40} color={colors.primary[500]} />
            </View>
            <Text style={styles.emptyTitle}>Track Your Money</Text>
            <Text style={styles.emptyText}>
              Add your checking, savings, credit cards, and other accounts to get started
            </Text>
            <TouchableOpacity
              style={styles.emptyButton}
              onPress={handleAddAccount}
              activeOpacity={0.7}
            >
              <Ionicons name="add-circle" size={20} color={colors.white} />
              <Text style={styles.emptyButtonText}>Add Account</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : (
        <FlatList
          data={accounts}
          renderItem={renderAccount}
          keyExtractor={(item) => item.id}
          ListHeaderComponent={() => (
            <Card variant="elevated" style={styles.netWorthCard}>
              <Text style={styles.netWorthLabel}>Total Net Worth</Text>
              <Text style={styles.netWorthValue}>
                {formatCurrency(getTotalBalance(), preferences.currency)}
              </Text>
            </Card>
          )}
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
    </ScreenContainer>
  );
};
