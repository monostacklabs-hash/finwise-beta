/**
 * Add Account Screen - Form to Add New Accounts
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { useForm, Controller } from 'react-hook-form';
import { GlassCard } from '../components/GlassCard';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import type { AccountType } from '../types';
import * as Haptics from 'expo-haptics';

interface AccountFormData {
  account_name: string;
  current_balance: string;
  credit_limit: string;
}

const ACCOUNT_TYPES: { type: AccountType; label: string; description: string; icon: keyof typeof Ionicons.glyphMap }[] = [
  { type: 'checking', label: 'Checking', description: 'Everyday spending', icon: 'card-outline' },
  { type: 'savings', label: 'Savings', description: 'Money you\'re saving', icon: 'wallet-outline' },
  { type: 'credit_card', label: 'Credit Card', description: 'Money you owe', icon: 'card' },
  { type: 'cash', label: 'Cash', description: 'Physical cash', icon: 'cash-outline' },
  { type: 'investment', label: 'Investment', description: 'Stocks, crypto, etc', icon: 'trending-up' },
  { type: 'other', label: 'Other', description: 'Anything else', icon: 'ellipse-outline' },
];

export const AddAccountScreen: React.FC = () => {
  const navigation = useNavigation();
  const { preferences } = useUserPreferences();
  const [submitting, setSubmitting] = useState(false);
  const [step, setStep] = useState<'type' | 'details'>('type');
  const [accountType, setAccountType] = useState<AccountType>('' as AccountType);

  const { control, handleSubmit, formState: { errors }, watch } = useForm<AccountFormData>({
    defaultValues: {
      account_name: '',
      current_balance: '',
      credit_limit: '',
    },
  });

  const handleTypeSelect = (type: AccountType) => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    setAccountType(type);
    setStep('details');
  };

  const onSubmit = async (data: AccountFormData) => {
    setSubmitting(true);
    try {
      let balance = data.current_balance ? parseFloat(data.current_balance) : 0;
      
      // For credit cards, store balance as negative (debt)
      if (accountType === 'credit_card' && balance > 0) {
        balance = -balance;
      }

      const accountData = {
        account_type: accountType,
        account_name: data.account_name.trim(),
        current_balance: balance,
        currency: preferences.currency,
      };

      const newAccount = await financialService.addAccount(accountData);

      // If credit card, add credit limit
      if (accountType === 'credit_card' && data.credit_limit) {
        const creditLimit = parseFloat(data.credit_limit);
        await financialService.addCreditCard({
          account_id: newAccount.id,
          credit_limit: creditLimit,
          available_credit: creditLimit,
          annual_fee: 0,
          statement_balance: 0,
          minimum_payment: 0,
        });
      }

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      navigation.goBack();
    } catch (error) {
      console.error('Failed to add account:', error);
      Alert.alert('Error', 'Failed to add account. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const renderTypeSelection = () => (
    <View style={styles.typeList}>
      {ACCOUNT_TYPES.map((item) => (
        <Pressable
          key={item.type}
          onPress={() => handleTypeSelect(item.type)}
        >
          <GlassCard variant="medium" style={styles.typeCard}>
            <View style={[styles.typeIcon, { backgroundColor: `${colors.primary[500]}20` }]}>
              <Ionicons name={item.icon} size={24} color={colors.primary[500]} />
            </View>
            <View style={styles.typeInfo}>
              <Text style={styles.typeLabel}>{item.label}</Text>
              <Text style={styles.typeDescription}>{item.description}</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.text.tertiary} />
          </GlassCard>
        </Pressable>
      ))}
    </View>
  );

  const renderDetailsForm = () => (
    <View style={styles.form}>
      <Controller
        control={control}
        name="account_name"
        rules={{
          required: 'Account name is required',
          validate: (value) => value.trim().length > 0 || 'Account name cannot be empty',
        }}
        render={({ field: { onChange, value } }) => (
          <>
            <Input
              label="Name this account"
              value={value}
              onChangeText={onChange}
              placeholder={
                accountType === 'checking' ? 'Main Checking' :
                accountType === 'savings' ? 'Emergency Fund' :
                accountType === 'credit_card' ? 'Visa Card' :
                accountType === 'investment' ? 'Robinhood' :
                accountType === 'cash' ? 'Cash Wallet' :
                'My Account'
              }
              autoFocus
            />
            {errors.account_name && (
              <Text style={styles.errorText}>{errors.account_name.message}</Text>
            )}
          </>
        )}
      />

      <Controller
        control={control}
        name="current_balance"
        rules={{
          validate: (value) => {
            if (!value) return true;
            const num = parseFloat(value);
            if (isNaN(num)) return 'Please enter a valid number';
            
            if (accountType === 'credit_card' && watch('credit_limit')) {
              const limit = parseFloat(watch('credit_limit'));
              if (num > limit) return `Balance cannot exceed credit limit ($${limit})`;
            }
            return true;
          },
        }}
        render={({ field: { onChange, value } }) => (
          <>
            <Input
              label={accountType === 'credit_card' ? 'How much do you owe?' : 'Current balance'}
              value={value}
              onChangeText={onChange}
              placeholder="0"
              keyboardType="numeric"
            />
            {accountType === 'credit_card' && (
              <Text style={styles.helperText}>Enter as positive number (e.g., 1200 means you owe $1,200)</Text>
            )}
            {errors.current_balance && (
              <Text style={styles.errorText}>{errors.current_balance.message}</Text>
            )}
          </>
        )}
      />

      {accountType === 'credit_card' && (
        <Controller
          control={control}
          name="credit_limit"
          rules={{
            required: 'Credit limit is required',
            validate: (value) => {
              const num = parseFloat(value);
              if (isNaN(num)) return 'Please enter a valid number';
              if (num <= 0) return 'Credit limit must be greater than 0';
              return true;
            },
          }}
          render={({ field: { onChange, value } }) => (
            <>
              <Input
                label="Credit limit"
                value={value}
                onChangeText={onChange}
                placeholder="5000"
                keyboardType="numeric"
              />
              {errors.credit_limit && (
                <Text style={styles.errorText}>{errors.credit_limit.message}</Text>
              )}
            </>
          )}
        />
      )}

      <View style={styles.buttonRow}>
        <Button
          title="Back"
          onPress={() => setStep('type')}
          variant="secondary"
          style={styles.halfButton}
        />
        <Button
          title="Add Account"
          onPress={handleSubmit(onSubmit)}
          loading={submitting}
          variant="primary"
          style={styles.halfButton}
        />
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="close" size={28} color={colors.text.primary} />
        </TouchableOpacity>
        <View style={styles.headerContent}>
          <Text style={styles.headerTitle}>
            {step === 'type' ? 'What type of account?' : 'Just the basics'}
          </Text>
        </View>
        <View style={styles.headerSpacer} />
      </View>

      <ScrollView
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {step === 'type' && renderTypeSelection()}
        {step === 'details' && renderDetailsForm()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.primary,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.lg,
    paddingTop: theme.spacing.xxl,
    paddingBottom: theme.spacing.xl,
  },
  backButton: {
    padding: theme.spacing.sm,
  },
  headerContent: {
    flex: 1,
    alignItems: 'center',
  },
  headerSpacer: {
    width: 40,
  },
  headerTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.text.primary,
  },
  content: {
    padding: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
  typeList: {
    gap: theme.spacing.md,
  },
  typeCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: theme.spacing.lg,
    gap: theme.spacing.md,
  },
  typeIcon: {
    width: 48,
    height: 48,
    borderRadius: theme.radius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  typeInfo: {
    flex: 1,
  },
  typeLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text.primary,
    marginBottom: 2,
  },
  typeDescription: {
    fontSize: 13,
    color: colors.text.secondary,
  },
  form: {
    gap: theme.spacing.md,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginTop: theme.spacing.lg,
  },
  halfButton: {
    flex: 1,
  },
  helperText: {
    fontSize: 13,
    color: colors.text.secondary,
    marginTop: -8,
    marginBottom: 8,
  },
  errorText: {
    fontSize: 13,
    color: colors.expense.primary,
    marginTop: -8,
    marginBottom: 8,
  },
});
