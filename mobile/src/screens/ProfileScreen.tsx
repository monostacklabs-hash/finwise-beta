/**
 * Profile Screen - Settings & Info
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { ScreenContainer } from '../components/ScreenContainer';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { APP_INFO } from '../constants/config';
import { authService } from '../services/auth';
import { apiClient } from '../services/api';

interface ProfileScreenProps {
  onLogout: () => void;
}

interface UserProfile {
  id: string;
  email: string;
  name: string;
  created_at: string;
}

export const ProfileScreen: React.FC<ProfileScreenProps> = ({ onLogout }) => {
  const navigation = useNavigation();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const data = await apiClient.get<UserProfile>('/auth/profile');
      setProfile(data);
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await authService.logout();
            onLogout();
          },
        },
      ]
    );
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary[600]} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScreenContainer scrollable>
        {/* User Info */}
        <Card variant="elevated">
          <View style={styles.cardHeader}>
            <Ionicons name="person-circle" size={24} color={colors.primary[500]} />
            <Text style={styles.cardTitle}>Account Details</Text>
          </View>
          <View style={styles.infoRow}>
            <View style={styles.infoLeft}>
              <Ionicons name="mail" size={20} color={colors.text.secondary} />
              <Text style={styles.infoLabel}>Email</Text>
            </View>
            <Text style={styles.infoValue}>{profile?.email || 'N/A'}</Text>
          </View>
          <View style={styles.infoRow}>
            <View style={styles.infoLeft}>
              <Ionicons name="calendar" size={20} color={colors.text.secondary} />
              <Text style={styles.infoLabel}>Member Since</Text>
            </View>
            <Text style={styles.infoValue}>
              {profile?.created_at ? formatDate(profile.created_at) : 'N/A'}
            </Text>
          </View>
        </Card>

        {/* Financial Tools */}
        <Card variant="elevated">
          <View style={styles.cardHeader}>
            <Ionicons name="apps" size={24} color={colors.primary[500]} />
            <Text style={styles.cardTitle}>Financial Tools</Text>
          </View>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => navigation.navigate('Settings' as never)}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="settings" size={22} color={colors.primary[500]} />
              <Text style={styles.menuLabel}>Settings</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.text.secondary} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => navigation.navigate('RecurringTransactions' as never)}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="repeat" size={22} color={colors.primary[500]} />
              <Text style={styles.menuLabel}>Recurring Transactions</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.text.secondary} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => navigation.navigate('CashFlow' as never)}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="trending-up" size={22} color={colors.primary[500]} />
              <Text style={styles.menuLabel}>Cash Flow Forecast</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.text.secondary} />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.menuItem}
            onPress={() => navigation.navigate('Notifications' as never)}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="notifications" size={22} color={colors.primary[500]} />
              <Text style={styles.menuLabel}>Notifications</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.text.secondary} />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.menuItem, styles.menuItemLast]}
            onPress={() => navigation.navigate('Export' as never)}
          >
            <View style={styles.menuLeft}>
              <Ionicons name="download" size={22} color={colors.primary[500]} />
              <Text style={styles.menuLabel}>Export & Reports</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color={colors.text.secondary} />
          </TouchableOpacity>
        </Card>

        {/* App Info */}
        <Card variant="elevated">
          <View style={styles.cardHeader}>
            <Ionicons name="information-circle" size={24} color={colors.primary[500]} />
            <Text style={styles.cardTitle}>App Information</Text>
          </View>
          <View style={styles.infoRow}>
            <View style={styles.infoLeft}>
              <Ionicons name="code-slash" size={20} color={colors.text.secondary} />
              <Text style={styles.infoLabel}>Version</Text>
            </View>
            <Text style={styles.infoValue}>{APP_INFO.VERSION}</Text>
          </View>
          <View style={styles.infoRow}>
            <View style={styles.infoLeft}>
              <Ionicons name="construct" size={20} color={colors.text.secondary} />
              <Text style={styles.infoLabel}>Build</Text>
            </View>
            <Text style={styles.infoValue}>2025 Standards</Text>
          </View>
        </Card>

        {/* Logout */}
        <Button
          title="Logout"
          onPress={handleLogout}
          variant="danger"
          icon="log-out"
        />
      </ScreenContainer>
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
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.md,
  },
  cardTitle: {
    ...theme.typography.h4,
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
  infoLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  infoLabel: {
    ...theme.typography.body,
    color: colors.text.primary,
  },
  infoValue: {
    ...theme.typography.body,
    fontWeight: '600',
    color: colors.text.primary,
  },
  menuItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: theme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.border.light,
  },
  menuItemLast: {
    borderBottomWidth: 0,
  },
  menuLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.md,
  },
  menuLabel: {
    ...theme.typography.body,
    fontWeight: '500',
    color: colors.text.primary,
  },
});
