/**
 * Metric Card Component - 2025
 * Modern card for displaying financial metrics
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Card } from './Card';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';

interface MetricCardProps {
  label: string;
  value: string;
  icon: keyof typeof Ionicons.glyphMap;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  variant?: 'default' | 'income' | 'expense' | 'info';
  onPress?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon,
  trend,
  trendValue,
  variant = 'default',
  onPress,
}) => {
  const trendIcons = {
    up: 'trending-up' as const,
    down: 'trending-down' as const,
    neutral: 'remove' as const,
  };

  const trendColors = {
    up: colors.income.primary,
    down: colors.expense.primary,
    neutral: colors.gray[500],
  };

  const getGradientColors = () => {
    switch (variant) {
      case 'income':
        return colors.gradients.success;
      case 'expense':
        return colors.gradients.sunset;
      case 'info':
        return colors.gradients.primary;
      default:
        return colors.gradients.primary;
    }
  };

  const getIconColor = () => {
    switch (variant) {
      case 'income':
        return colors.income.primary;
      case 'expense':
        return colors.expense.primary;
      case 'info':
        return colors.info.primary;
      default:
        return colors.primary[500];
    }
  };

  const iconColor = getIconColor();

  return (
    <Card
      variant="elevated"
      style={styles.card}
      onPress={onPress}
      pressable={!!onPress}
    >
      <View style={styles.iconContainer}>
        <LinearGradient
          colors={getGradientColors()}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.iconGradient}
        >
          <Ionicons name={icon} size={24} color={colors.white} />
        </LinearGradient>
      </View>
      
      <Text style={styles.label}>{label}</Text>
      <Text style={styles.value} numberOfLines={1}>
        {value}
      </Text>
      
      {trend && trendValue && (
        <View style={styles.trendContainer}>
          <Ionicons name={trendIcons[trend]} size={14} color={trendColors[trend]} />
          <Text style={[styles.trendText, { color: trendColors[trend] }]}>
            {trendValue}
          </Text>
        </View>
      )}
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minHeight: 130,
  },
  iconContainer: {
    marginBottom: theme.spacing.md,
  },
  iconGradient: {
    width: 48,
    height: 48,
    borderRadius: theme.radius.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  label: {
    ...theme.typography.caption,
    color: colors.text.secondary,
    marginBottom: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  value: {
    ...theme.typography.h3,
    color: colors.text.primary,
    fontWeight: '700',
    marginBottom: 4,
  },
  trendContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
    gap: 4,
  },
  trendText: {
    ...theme.typography.caption,
    fontWeight: '600',
  },
});
