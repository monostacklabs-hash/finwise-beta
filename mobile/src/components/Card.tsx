/**
 * Modern Card Component - 2025
 * Clean, elevated cards with subtle shadows
 */

import React from 'react';
import { View, StyleSheet, ViewStyle, TouchableOpacity, StyleProp } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';

interface CardProps {
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
  padding?: number;
  variant?: 'flat' | 'elevated' | 'outlined';
  onPress?: () => void;
  pressable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  style,
  padding = theme.spacing.lg,
  variant = 'elevated',
  onPress,
  pressable = false,
}) => {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = () => {
    if (pressable || onPress) {
      scale.value = withSpring(0.98);
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  };

  const handlePressOut = () => {
    if (pressable || onPress) {
      scale.value = withSpring(1);
    }
  };

  const handlePress = () => {
    if (onPress) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      onPress();
    }
  };

  const getVariantStyle = () => {
    switch (variant) {
      case 'flat':
        return [styles.card, styles.flat];
      case 'outlined':
        return [styles.card, styles.outlined];
      case 'elevated':
      default:
        return [styles.card, styles.elevated, theme.shadows.md];
    }
  };

  const cardStyles = [
    ...getVariantStyle(),
    { padding },
    style,
  ];

  if (pressable || onPress) {
    return (
      <Animated.View style={animatedStyle}>
        <TouchableOpacity
          style={cardStyles}
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          onPress={handlePress}
          activeOpacity={0.95}
        >
          {children}
        </TouchableOpacity>
      </Animated.View>
    );
  }

  return <View style={cardStyles}>{children}</View>;
};

const styles = StyleSheet.create({
  card: {
    borderRadius: theme.radius.lg,
  },
  flat: {
    backgroundColor: colors.surface.primary,
    borderWidth: 1,
    borderColor: colors.border.light,
  },
  elevated: {
    backgroundColor: colors.surface.elevated,
  },
  outlined: {
    backgroundColor: colors.surface.primary,
    borderWidth: 1,
    borderColor: colors.border.medium,
  },
});
