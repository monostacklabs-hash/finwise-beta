/**
 * Settings Screen - User Preferences
 * Currency, Timezone, Country configuration
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  TouchableOpacity,
  Pressable,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { GlassCard } from '../components/GlassCard';
import { Button } from '../components/Button';
import { BottomSheet } from '../components/BottomSheet';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import { POPULAR_CURRENCIES } from '../utils/currency';
import { apiClient } from '../services/api';
import { authService } from '../services/auth';
import * as Haptics from 'expo-haptics';
import { ScreenContainer } from '../components/ScreenContainer';

const TIMEZONES = [
  { value: 'UTC', label: 'UTC (Coordinated Universal Time)' },
  { value: 'America/New_York', label: 'Eastern Time (US & Canada)' },
  { value: 'America/Chicago', label: 'Central Time (US & Canada)' },
  { value: 'America/Denver', label: 'Mountain Time (US & Canada)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (US & Canada)' },
  { value: 'Europe/London', label: 'London' },
  { value: 'Europe/Paris', label: 'Paris, Berlin, Rome' },
  { value: 'Asia/Tokyo', label: 'Tokyo, Seoul' },
  { value: 'Asia/Shanghai', label: 'Beijing, Hong Kong, Singapore' },
  { value: 'Asia/Kolkata', label: 'Mumbai, Kolkata, New Delhi' },
  { value: 'Australia/Sydney', label: 'Sydney, Melbourne' },
];

export const SettingsScreen: React.FC = () => {
  const navigation = useNavigation();
  const { preferences, updatePreferences } = useUserPreferences();
  const [currencyModalVisible, setCurrencyModalVisible] = useState(false);
  const [timezoneModalVisible, setTimezoneModalVisible] = useState(false);
  const [saving, setSaving] = useState(false);
  const [processing, setProcessing] = useState(false);

  const handleCurrencySelect = async (currencyCode: string) => {
    setSaving(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await updatePreferences({ currency: currencyCode });
      setCurrencyModalVisible(false);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Success', `Currency changed to ${currencyCode}`);
    } catch (error) {
      Alert.alert('Error', 'Failed to update currency');
    } finally {
      setSaving(false);
    }
  };

  const handleTimezoneSelect = async (timezone: string) => {
    setSaving(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await updatePreferences({ timezone });
      setTimezoneModalVisible(false);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      Alert.alert('Success', 'Timezone updated');
    } catch (error) {
      Alert.alert('Error', 'Failed to update timezone');
    } finally {
      setSaving(false);
    }
  };

  const handleFlushData = () => {
    Alert.alert(
      '⚠️ Clear All Data',
      'This will permanently delete all your transactions, accounts, goals, budgets, and other financial data. Your account will remain active but all data will be lost.\n\nThis action cannot be undone!',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All Data',
          style: 'destructive',
          onPress: async () => {
            // Second confirmation
            Alert.alert(
              'Final Confirmation',
              'Are you absolutely sure? This will delete everything!',
              [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Yes, Delete Everything',
                  style: 'destructive',
                  onPress: performFlushData,
                },
              ]
            );
          },
        },
      ]
    );
  };

  const performFlushData = async () => {
    setProcessing(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);

    try {
      const response = await apiClient.post<{
        success: boolean;
        message: string;
        deleted_counts: Record<string, number>;
        total_items_deleted: number;
      }>('/user/flush', {});

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

      Alert.alert(
        '✅ Data Cleared',
        `Successfully deleted ${response.total_items_deleted} items. You can start fresh now!`,
        [
          {
            text: 'OK',
            onPress: () => {
              // Navigate back to home
              navigation.navigate('Dashboard' as never);
            },
          },
        ]
      );
    } catch (error: any) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert(
        'Error',
        error.message || 'Failed to clear data. Please try again.'
      );
    } finally {
      setProcessing(false);
    }
  };

  const handleDeleteAccount = () => {
    Alert.alert(
      '🚨 Delete Account',
      'This will PERMANENTLY delete your account and ALL associated data. You will be logged out and will need to create a new account to use the app again.\n\nThis action CANNOT be undone!',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete My Account',
          style: 'destructive',
          onPress: async () => {
            // Second confirmation with text input would be ideal, but using double alert
            Alert.alert(
              'FINAL WARNING',
              'This is your last chance. Your account and all data will be permanently deleted. Are you absolutely certain?',
              [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Yes, Delete Forever',
                  style: 'destructive',
                  onPress: performDeleteAccount,
                },
              ]
            );
          },
        },
      ]
    );
  };

  const performDeleteAccount = async () => {
    setProcessing(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);

    try {
      await apiClient.delete('/user/account');

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

      // Logout and clear local data
      await authService.logout();

      Alert.alert(
        'Account Deleted',
        'Your account has been permanently deleted. Thank you for using our app.',
        [
          {
            text: 'OK',
            onPress: () => {
              // The app will automatically redirect to login screen
              // since the auth token is cleared
            },
          },
        ]
      );
    } catch (error: any) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      Alert.alert(
        'Error',
        error.message || 'Failed to delete account. Please try again.'
      );
      setProcessing(false);
    }
  };

  const selectedCurrency = POPULAR_CURRENCIES.find(c => c.code === preferences.currency);
  const selectedTimezone = TIMEZONES.find(tz => tz.value === preferences.timezone);

  if (processing) {
    return (
      <ScreenContainer>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary[600]} />
          <Text style={styles.loadingText}>Processing...</Text>
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer>
      {/* Currency Setting */}
      <GlassCard variant="medium" style={styles.settingCard}>
        <TouchableOpacity
          onPress={() => {
            setCurrencyModalVisible(true);
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
          style={styles.settingRow}
        >
          <View style={styles.settingLeft}>
            <View style={[styles.iconContainer, { backgroundColor: colors.income.glass }]}>
              <Ionicons name="cash" size={24} color={colors.income.primary} />
            </View>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Currency</Text>
              <Text style={styles.settingValue}>
                {selectedCurrency?.symbol} {selectedCurrency?.name || preferences.currency}
              </Text>
            </View>
          </View>
          <Ionicons name="chevron-forward" size={24} color={colors.text.secondary} />
        </TouchableOpacity>
      </GlassCard>

      {/* Timezone Setting */}
      <GlassCard variant="medium" style={styles.settingCard}>
        <TouchableOpacity
          onPress={() => {
            setTimezoneModalVisible(true);
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
          style={styles.settingRow}
        >
          <View style={styles.settingLeft}>
            <View style={[styles.iconContainer, { backgroundColor: colors.info.glass }]}>
              <Ionicons name="time" size={24} color={colors.info.primary} />
            </View>
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>Timezone</Text>
              <Text style={styles.settingValue} numberOfLines={1}>
                {selectedTimezone?.label || preferences.timezone}
              </Text>
            </View>
          </View>
          <Ionicons name="chevron-forward" size={24} color={colors.text.secondary} />
        </TouchableOpacity>
      </GlassCard>

      {/* Info Card */}
      <GlassCard variant="light" style={styles.infoCard}>
        <View style={styles.infoHeader}>
          <Ionicons name="information-circle" size={24} color={colors.info.primary} />
          <Text style={styles.infoTitle}>About Preferences</Text>
        </View>
        <View style={styles.infoItems}>
          <View style={styles.infoItem}>
            <Ionicons name="checkmark-circle" size={16} color={colors.income.primary} />
            <Text style={styles.infoText}>
              All amounts will be displayed in your selected currency
            </Text>
          </View>
          <View style={styles.infoItem}>
            <Ionicons name="checkmark-circle" size={16} color={colors.income.primary} />
            <Text style={styles.infoText}>
              Dates and times will use your timezone
            </Text>
          </View>
          <View style={styles.infoItem}>
            <Ionicons name="checkmark-circle" size={16} color={colors.income.primary} />
            <Text style={styles.infoText}>
              AI assistant will be aware of your location and currency
            </Text>
          </View>
        </View>
      </GlassCard>

      {/* Danger Zone */}
      <View style={styles.dangerZone}>
        <Text style={styles.dangerZoneTitle}>⚠️ Danger Zone</Text>

        {/* Flush Data */}
        <GlassCard variant="medium" style={styles.dangerCard}>
          <TouchableOpacity
            onPress={handleFlushData}
            style={styles.dangerRow}
          >
            <View style={styles.dangerLeft}>
              <View style={[styles.iconContainer, { backgroundColor: 'rgba(255, 152, 0, 0.15)' }]}>
                <Ionicons name="trash-bin" size={24} color="#FF9800" />
              </View>
              <View style={styles.dangerInfo}>
                <Text style={styles.dangerLabel}>Clear All Data</Text>
                <Text style={styles.dangerDescription}>
                  Delete all transactions, accounts, and goals. Account stays active.
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={24} color={colors.text.secondary} />
          </TouchableOpacity>
        </GlassCard>

        {/* Delete Account */}
        <GlassCard variant="medium" style={styles.dangerCard}>
          <TouchableOpacity
            onPress={handleDeleteAccount}
            style={styles.dangerRow}
          >
            <View style={styles.dangerLeft}>
              <View style={[styles.iconContainer, { backgroundColor: 'rgba(244, 67, 54, 0.15)' }]}>
                <Ionicons name="warning" size={24} color="#F44336" />
              </View>
              <View style={styles.dangerInfo}>
                <Text style={[styles.dangerLabel, { color: '#F44336' }]}>Delete Account</Text>
                <Text style={styles.dangerDescription}>
                  Permanently delete your account and all data. Cannot be undone.
                </Text>
              </View>
            </View>
            <Ionicons name="chevron-forward" size={24} color={colors.text.secondary} />
          </TouchableOpacity>
        </GlassCard>
      </View>

      {/* Currency Selection Modal */}
      <BottomSheet
        visible={currencyModalVisible}
        onClose={() => setCurrencyModalVisible(false)}
        title="Select Currency"
        subtitle="Choose your preferred currency"
      >
        <ScrollView showsVerticalScrollIndicator={false}>
          {POPULAR_CURRENCIES.map((currency) => (
            <Pressable
              key={currency.code}
              style={[
                styles.optionItem,
                preferences.currency === currency.code && styles.optionItemSelected,
              ]}
              onPress={() => handleCurrencySelect(currency.code)}
              disabled={saving}
            >
              <View style={styles.optionLeft}>
                <Text style={styles.optionSymbol}>{currency.symbol}</Text>
                <View>
                  <Text style={styles.optionCode}>{currency.code}</Text>
                  <Text style={styles.optionName}>{currency.name}</Text>
                </View>
              </View>
              {preferences.currency === currency.code && (
                <Ionicons name="checkmark-circle" size={24} color={colors.income.primary} />
              )}
            </Pressable>
          ))}
        </ScrollView>
      </BottomSheet>

      {/* Timezone Selection Modal */}
      <BottomSheet
        visible={timezoneModalVisible}
        onClose={() => setTimezoneModalVisible(false)}
        title="Select Timezone"
        subtitle="Choose your timezone"
      >
        <ScrollView showsVerticalScrollIndicator={false}>
          {TIMEZONES.map((tz) => (
            <Pressable
              key={tz.value}
              style={[
                styles.optionItem,
                preferences.timezone === tz.value && styles.optionItemSelected,
              ]}
              onPress={() => handleTimezoneSelect(tz.value)}
              disabled={saving}
            >
              <Text style={styles.timezoneLabel}>{tz.label}</Text>
              {preferences.timezone === tz.value && (
                <Ionicons name="checkmark-circle" size={24} color={colors.income.primary} />
              )}
            </Pressable>
          ))}
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
  scrollContent: {
    padding: theme.spacing.lg,
    paddingTop: 0,
    gap: theme.spacing.md,
    paddingBottom: theme.spacing.xxl,
  },
  settingCard: {
    overflow: 'visible',
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  settingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    flex: 1,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  settingInfo: {
    flex: 1,
  },
  settingLabel: {
    fontSize: 14,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  settingValue: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text.primary,
  },
  infoCard: {
    padding: theme.spacing.lg,
    marginTop: theme.spacing.lg,
  },
  infoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.md,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
  },
  infoItems: {
    gap: theme.spacing.sm,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.xs,
  },
  infoText: {
    fontSize: 14,
    color: colors.text.secondary,
    flex: 1,
    lineHeight: 20,
  },
  optionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: theme.spacing.md,
    borderRadius: theme.radius.md,
    marginBottom: theme.spacing.sm,
    backgroundColor: colors.background.secondary,
    borderWidth: 1,
    borderColor: colors.border.light,
  },
  optionItemSelected: {
    backgroundColor: colors.income.glass,
    borderColor: colors.income.primary,
  },
  optionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    flex: 1,
  },
  optionSymbol: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.text.primary,
    width: 40,
    textAlign: 'center',
  },
  optionCode: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
  },
  optionName: {
    fontSize: 13,
    color: colors.text.secondary,
  },
  timezoneLabel: {
    fontSize: 15,
    color: colors.text.primary,
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background.primary,
  },
  loadingText: {
    marginTop: theme.spacing.md,
    fontSize: 16,
    color: colors.text.secondary,
  },
  dangerZone: {
    marginTop: theme.spacing.xl,
    paddingTop: theme.spacing.xl,
    borderTopWidth: 1,
    borderTopColor: colors.border.light,
  },
  dangerZoneTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text.primary,
    marginBottom: theme.spacing.md,
    paddingHorizontal: theme.spacing.xs,
  },
  dangerCard: {
    marginBottom: theme.spacing.md,
    overflow: 'visible',
  },
  dangerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  dangerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
    flex: 1,
  },
  dangerInfo: {
    flex: 1,
  },
  dangerLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FF9800',
    marginBottom: 4,
  },
  dangerDescription: {
    fontSize: 13,
    color: colors.text.secondary,
    lineHeight: 18,
  },
});
