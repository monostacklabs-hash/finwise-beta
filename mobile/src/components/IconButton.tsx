/**
 * Icon Button Component - Black & White Theme - 2025
 * Modern circular icon button with haptics
 */

import React from 'react';
import { TouchableOpacity, StyleSheet, ViewStyle } from 'react-native';
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { Ionicons } from '@expo/vector-icons';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';

interface IconButtonProps {
  icon: keyof typeof Ionicons.glyphMap;
  onPress: () => void;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'secondary' | 'ghost' | 'glass';
  disabled?: boolean;
  style?: ViewStyle;
}

const AnimatedTouchable = Animated.createAnimatedComponent(TouchableOpacity);

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  onPress,
  size = 'md',
  variant = 'ghost',
  disabled = false,
  style,
}) => {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  const handlePressIn = () => {
    scale.value = withSpring(0.9);
    if (!disabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    }
  };

  const handlePressOut = () => {
    scale.value = withSpring(1);
  };

  const handlePress = () => {
    if (!disabled) {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      onPress();
    }
  };

  const iconSizes = { sm: 18, md: 24, lg: 32 };
  const iconSize = iconSizes[size];

  const iconColors = {
    primary: colors.black,         // Black icon on white
    secondary: colors.white,       // White icon on dark
    ghost: colors.white,           // White icon on transparent
    glass: colors.white,           // White icon on glass
  };

  const buttonStyles = [
    styles.button,
    styles[variant],
    styles[`size_${size}`],
    disabled && styles.disabled,
    style,
  ];

  return (
    <AnimatedTouchable
      style={[buttonStyles, animatedStyle]}
      onPressIn={handlePressIn}
      onPressOut={handlePressOut}
      onPress={handlePress}
      disabled={disabled}
      activeOpacity={0.9}
    >
      <Ionicons name={icon} size={iconSize} color={iconColors[variant]} />
    </AnimatedTouchable>
  );
};

const styles = StyleSheet.create({
  button: {
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.full,
  },

  // Variants
  primary: {
    backgroundColor: colors.white,  // White button
  },
  secondary: {
    backgroundColor: colors.gray[800],  // Dark gray button
    borderWidth: 1,
    borderColor: colors.border.light,
  },
  ghost: {
    backgroundColor: 'transparent',
  },
  glass: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },

  // Sizes
  size_sm: {
    width: 36,
    height: 36,
  },
  size_md: {
    width: 48,
    height: 48,
  },
  size_lg: {
    width: 64,
    height: 64,
  },

  disabled: {
    opacity: 0.5,
  },
});
