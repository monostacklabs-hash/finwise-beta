/**
 * GlassCard Component - 2025 (Legacy Compatibility)
 * Now wraps the modern Card component for backward compatibility
 */

import React from 'react';
import { ViewStyle } from 'react-native';
import { Card } from './Card';

interface GlassCardProps {
  children: React.ReactNode;
  style?: ViewStyle;
  intensity?: number;
  variant?: 'light' | 'medium' | 'strong' | 'inverted';
}

export const GlassCard: React.FC<GlassCardProps> = ({
  children,
  style,
  intensity, // Ignored for now
  variant = 'medium',
}) => {
  // Map old glass variants to new card variants
  const getCardVariant = () => {
    switch (variant) {
      case 'light':
        return 'flat';
      case 'strong':
        return 'elevated';
      case 'inverted':
        return 'outlined';
      case 'medium':
      default:
        return 'elevated';
    }
  };

  return (
    <Card variant={getCardVariant()} style={style}>
      {children}
    </Card>
  );
};
