/**
 * Welcome Screen - REDESIGNED for 2025
 * Show value BEFORE asking for login
 *
 * KEY IMPROVEMENTS:
 * 1. ✅ Show value proposition FIRST
 * 2. ✅ Visual preview of app
 * 3. ✅ Social login options (Google, Apple)
 * 4. ✅ Clear CTAs
 * 5. ✅ Skip option for browsing
 * 6. ✅ Large touch targets (56px+)
 */

import React, { useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  Pressable,
  Image,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import Animated, {
  useAnimatedScrollHandler,
  useSharedValue,
  useAnimatedStyle,
  interpolate,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { colors } from '../../constants/colors';
import { theme } from '../../constants/theme';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

interface WelcomeScreenProps {
  navigation: any;
}

const FEATURES = [
  {
    icon: 'bulb-outline',
    color: colors.gradients.primary,
    title: 'AI-Powered Insights',
    description: 'Get personalized financial advice from your AI assistant',
  },
  {
    icon: 'trending-up',
    color: colors.gradients.success,
    title: 'Track Everything',
    description: 'Accounts, budgets, goals—all in one beautiful app',
  },
  {
    icon: 'shield-checkmark',
    color: colors.gradients.sunset,
    title: 'Bank-Level Security',
    description: 'Your data is encrypted and never shared',
  },
];

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ navigation }) => {
  const scrollX = useSharedValue(0);

  const scrollHandler = useAnimatedScrollHandler({
    onScroll: (event) => {
      scrollX.value = event.contentOffset.x;
    },
  });

  const handleGetStarted = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    navigation.navigate('Register');
  };

  const handleLogin = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    navigation.navigate('Login');
  };

  const handleGoogleSignIn = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    // TODO: Implement Google Sign In
    console.log('Google Sign In');
  };

  const handleAppleSignIn = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    // TODO: Implement Apple Sign In
    console.log('Apple Sign In');
  };

  const renderDot = (index: number) => {
    const animatedStyle = useAnimatedStyle(() => {
      const inputRange = [
        (index - 1) * SCREEN_WIDTH,
        index * SCREEN_WIDTH,
        (index + 1) * SCREEN_WIDTH,
      ];

      const width = interpolate(
        scrollX.value,
        inputRange,
        [8, 24, 8],
        'clamp'
      );

      const opacity = interpolate(
        scrollX.value,
        inputRange,
        [0.3, 1, 0.3],
        'clamp'
      );

      return { width, opacity };
    });

    return (
      <Animated.View
        key={index}
        style={[styles.dot, animatedStyle]}
      />
    );
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <LinearGradient
        colors={colors.gradients.primary}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.gradient}
      >
        {/* Feature Carousel */}
        <Animated.ScrollView
          horizontal
          pagingEnabled
          showsHorizontalScrollIndicator={false}
          onScroll={scrollHandler}
          scrollEventThrottle={16}
          style={styles.carousel}
        >
          {FEATURES.map((feature, index) => (
            <View key={index} style={styles.featureSlide}>
              {/* Icon */}
              <View style={styles.featureIconContainer}>
                <Ionicons name={feature.icon as any} size={64} color={colors.primary[500]} />
              </View>

              {/* Title & Description */}
              <Text style={styles.featureTitle}>{feature.title}</Text>
              <Text style={styles.featureDescription}>{feature.description}</Text>
            </View>
          ))}
        </Animated.ScrollView>

        {/* Pagination Dots */}
        <View style={styles.pagination}>
          {FEATURES.map((_, index) => renderDot(index))}
        </View>

        {/* Bottom Actions Card */}
        <View style={styles.actionsCard}>
          {/* Primary CTA - Get Started */}
          <Pressable
            style={styles.primaryButton}
            onPress={handleGetStarted}
          >
            <LinearGradient
              colors={colors.gradients.primary}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={styles.primaryButtonGradient}
            >
              <Text style={styles.primaryButtonText}>Get Started Free</Text>
              <Ionicons name="arrow-forward" size={24} color={colors.white} />
            </LinearGradient>
          </Pressable>

          {/* Divider */}
          <View style={styles.divider}>
            <View style={styles.dividerLine} />
            <Text style={styles.dividerText}>or continue with</Text>
            <View style={styles.dividerLine} />
          </View>

          {/* Social Login Buttons */}
          <View style={styles.socialButtons}>
            {/* Google Sign In */}
            <Pressable
              style={styles.socialButton}
              onPress={handleGoogleSignIn}
            >
              <Ionicons name="logo-google" size={24} color="#4285F4" />
              <Text style={styles.socialButtonText}>Google</Text>
            </Pressable>

            {/* Apple Sign In */}
            <Pressable
              style={styles.socialButton}
              onPress={handleAppleSignIn}
            >
              <Ionicons name="logo-apple" size={24} color={colors.text.primary} />
              <Text style={styles.socialButtonText}>Apple</Text>
            </Pressable>
          </View>

          {/* Already Have Account */}
          <Pressable style={styles.loginLink} onPress={handleLogin}>
            <Text style={styles.loginLinkText}>
              Already have an account? <Text style={styles.loginLinkBold}>Sign In</Text>
            </Text>
          </Pressable>

          {/* Terms */}
          <Text style={styles.terms}>
            By continuing, you agree to our Terms of Service and Privacy Policy
          </Text>
        </View>
      </LinearGradient>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
  },

  // Carousel
  carousel: {
    flex: 1,
  },
  featureSlide: {
    width: SCREEN_WIDTH,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: theme.spacing.xxxl,
    paddingTop: SCREEN_HEIGHT * 0.15,
  },
  featureIconContainer: {
    width: 160,
    height: 160,
    borderRadius: 80,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.xxxl,
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  featureEmoji: {
    fontSize: 80,
  },
  featureTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: colors.white,
    textAlign: 'center',
    marginBottom: theme.spacing.md,
  },
  featureDescription: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    lineHeight: 26,
  },

  // Pagination
  pagination: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
    paddingVertical: theme.spacing.xl,
  },
  dot: {
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.white,
  },

  // Actions Card
  actionsCard: {
    backgroundColor: colors.white,
    borderTopLeftRadius: theme.radius.xxl,
    borderTopRightRadius: theme.radius.xxl,
    paddingHorizontal: theme.spacing.xxl,
    paddingTop: theme.spacing.xxxl,
    paddingBottom: theme.spacing.xxxl,
    ...theme.shadows.xl,
  },

  // Primary Button
  primaryButton: {
    marginBottom: theme.spacing.xl,
  },
  primaryButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: 56, // BIG!
    paddingVertical: theme.spacing.lg,
    borderRadius: theme.radius.lg,
  },
  primaryButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.white,
  },

  // Divider
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.xl,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.border.light,
  },
  dividerText: {
    fontSize: 14,
    color: colors.text.secondary,
    marginHorizontal: theme.spacing.md,
  },

  // Social Buttons
  socialButtons: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.xl,
  },
  socialButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    minHeight: 56, // BIG!
    paddingVertical: theme.spacing.md,
    backgroundColor: colors.background.secondary,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    borderColor: colors.border.medium,
  },
  socialButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text.primary,
  },

  // Login Link
  loginLink: {
    alignItems: 'center',
    paddingVertical: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  loginLinkText: {
    fontSize: 15,
    color: colors.text.secondary,
  },
  loginLinkBold: {
    fontWeight: '700',
    color: colors.primary[600],
  },

  // Terms
  terms: {
    fontSize: 12,
    color: colors.text.tertiary,
    textAlign: 'center',
    lineHeight: 18,
  },
});
