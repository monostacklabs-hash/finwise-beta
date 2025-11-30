/**
 * Account Details Screen - View/Edit Individual Account
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

export const AccountDetailsScreen: React.FC = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { preferences } = useUserPreferences();
  const { accountId } = route.params as { accountId: string };
  
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    account_name: '',
    current_balance: '',
    notes: '',
  });

  useEffect(() => {
    loadAccount();
  }, [accountId]);

  const loadAccount = async () => {
    try {
      const data = await financialService.getAccount(accountId);
      setAccount(data.account);
      setFormData({
        account_name: data.account.account_name,
        current_balance: data.account.current_balance.toString(),
        notes: data.account.notes || '',
      });
    } catch (error) {
      console.error('Failed to load account:', error);
      Alert.alert('Error', 'Failed to load account details');
      navigation.goBack();
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = () => {
    setEditModalVisible(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
  };

  const handleUpdate = async () => {
    if (!formData.account_name || !formData.current_balance) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setSubmitting(true);
    try {
      await financialService.updateAccount(accountId, {
        account_name: formData.account_name,
        current_balance: parseFloat(formData.current_balance),
        notes: formData.notes,
      });
      
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      setEditModalVisible(false);
      loadAccount();
    } catch (error) {
      Alert.alert('Error', 'Failed to update account');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Account',
      'Are you sure you want to delete this account? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await financialService.deleteAccount(accountId);
              Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
              navigation.goBack();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete account');
            }
          },
        },
      ]
    );
  };

  if (loading || !account) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.white} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.text.primary} />
        </TouchableOpacity>
        <View style={styles.headerActions}>
          <IconButton icon="create-outline" onPress={handleEdit} variant="glass" size="sm" />
          <IconButton icon="trash-outline" onPress={handleDelete} variant="glass" size="sm" />
        </View>
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* Balance Card */}
        <GlassCard variant="strong" style={styles.balanceCard}>
          <Text style={styles.balanceLabel}>Current Balance</Text>
          <Text style={styles.balanceAmount}>
            {formatCurrency(account.current_balance, preferences.currency)}
          </Text>
          <Text style={styles.accountName}>{account.account_name}</Text>
        </GlassCard>

        {/* Account Info */}
        <GlassCard variant="medium">
          <Text style={styles.sectionTitle}>Account Information</Text>
          
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Type</Text>
            <Text style={styles.infoValue}>
              {account.account_type.replace('_', ' ').toUpperCase()}
            </Text>
          </View>

          {account.institution_name && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Institution</Text>
              <Text style={styles.infoValue}>{account.institution_name}</Text>
            </View>
          )}

          {account.account_number_last4 && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Account Number</Text>
              <Text style={[styles.infoValue, { fontFamily: 'monospace' }]}>
                ••••{account.account_number_last4}
              </Text>
            </View>
          )}

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Currency</Text>
            <Text style={styles.infoValue}>{account.currency}</Text>
          </View>

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>Status</Text>
            <View style={[
              styles.statusBadge,
              { backgroundColor: account.status === 'active' ? colors.income.glass : colors.glass.light }
            ]}>
              <Text style={[
                styles.statusText,
                { color: account.status === 'active' ? colors.income.primary : colors.text.secondary }
              ]}>
                {account.status.toUpperCase()}
              </Text>
            </View>
          </View>

          {account.opening_date && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Opened</Text>
              <Text style={styles.infoValue}>
                {format(new Date(account.opening_date), 'MMM dd, yyyy')}
              </Text>
            </View>
          )}

          {account.interest_rate && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Interest Rate</Text>
              <Text style={styles.infoValue}>{account.interest_rate}%</Text>
            </View>
          )}

          {account.notes && (
            <View style={styles.notesSection}>
              <Text style={styles.infoLabel}>Notes</Text>
              <Text style={styles.notesText}>{account.notes}</Text>
            </View>
          )}
        </GlassCard>
      </ScrollView>

      {/* Edit Modal */}
      <BottomSheet
        visible={editModalVisible}
        onClose={() => setEditModalVisible(false)}
        title="Edit Account"
        subtitle="Update account details"
      >
        <Input
              label="Account Name"
              value={formData.account_name}
              onChangeText={(text) => setFormData({ ...formData, account_name: text })}
              placeholder="My Checking Account"
            />

            <Input
              label="Current Balance"
              value={formData.current_balance}
              onChangeText={(text) => setFormData({ ...formData, current_balance: text })}
              keyboardType="decimal-pad"
              placeholder="0.00"
            />

            <Input
              label="Notes (Optional)"
              value={formData.notes}
              onChangeText={(text) => setFormData({ ...formData, notes: text })}
              placeholder="Add any notes..."
              multiline
            />

            <Button
              title="Update Account"
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
  headerActions: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
  },
  content: {
    padding: theme.spacing.lg,
    gap: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
  balanceCard: {
    alignItems: 'center',
    padding: theme.spacing.xl,
  },
  balanceLabel: {
    fontSize: 14,
    color: colors.text.secondary,
    marginBottom: theme.spacing.xs,
  },
  balanceAmount: {
    fontSize: 40,
    fontWeight: '700',
    color: colors.text.primary,
    marginBottom: theme.spacing.sm,
  },
  accountName: {
    fontSize: 16,
    color: colors.text.secondary,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.text.primary,
    marginBottom: theme.spacing.md,
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
  notesSection: {
    paddingTop: theme.spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.border.light,
    marginTop: theme.spacing.sm,
  },
  notesText: {
    fontSize: 14,
    color: colors.text.primary,
    marginTop: theme.spacing.xs,
    lineHeight: 20,
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
