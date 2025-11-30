import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
  Pressable,
  TextInput,
} from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import Animated, {
  FadeIn,
  FadeInDown,
  SlideInDown,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { Input } from '../components/Input';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { authService } from '../services/auth';

interface RegisterScreenProps {
  navigation: any;
  onRegisterSuccess: () => void;
}

type PasswordStrength = 'weak' | 'fair' | 'good' | 'strong';

export const RegisterScreen: React.FC<RegisterScreenProps> = ({
  navigation,
  onRegisterSuccess,
}) => {
  const insets = useSafeAreaInsets();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>('weak');
  const passwordInputRef = useRef<TextInput>(null);

  // Calculate password strength
  const calculatePasswordStrength = (pwd: string): PasswordStrength => {
    if (pwd.length === 0) return 'weak';
    if (pwd.length < 6) return 'weak';

    let strength = 0;

    // Length
    if (pwd.length >= 8) strength++;
    if (pwd.length >= 12) strength++;

    // Contains lowercase
    if (/[a-z]/.test(pwd)) strength++;

    // Contains uppercase
    if (/[A-Z]/.test(pwd)) strength++;

    // Contains number
    if (/[0-9]/.test(pwd)) strength++;

    // Contains special char
    if (/[^a-zA-Z0-9]/.test(pwd)) strength++;

    if (strength <= 2) return 'weak';
    if (strength <= 3) return 'fair';
    if (strength <= 4) return 'good';
    return 'strong';
  };

  const handlePasswordChange = (text: string) => {
    setPassword(text);
    setPasswordStrength(calculatePasswordStrength(text));
    setError(''); // Clear error on input
  };

  const getStrengthColor = (): string => {
    switch (passwordStrength) {
      case 'weak': return colors.error.primary;
      case 'fair': return colors.warning.primary;
      case 'good': return '#10b981';
      case 'strong': return colors.income.primary;
    }
  };

  const getStrengthWidth = (): string => {
    switch (passwordStrength) {
      case 'weak': return '25%';
      case 'fair': return '50%';
      case 'good': return '75%';
      case 'strong': return '100%';
    }
  };

  const handleRegister = async () => {
    // Clear previous error
    setError('');

    // Validation
    if (!email) {
      setError('Please enter your email');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      return;
    }

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      return;
    }

    if (!password) {
      setError('Please create a password');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      return;
    }

    if (passwordStrength === 'weak') {
      setError('Please choose a stronger password');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      return;
    }

    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      // Register with just email and password
      // Name will be collected in onboarding
      await authService.register({
        email,
        password,
        name: 'User', // Placeholder - will update in onboarding
      });

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      onRegisterSuccess();
    } catch (error: any) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      const errorMessage = error.response?.data?.detail || 'Unable to create account';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignUp = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    // TODO: Implement Google Sign Up
    Alert.alert('Coming Soon', 'Google Sign Up will be available soon!');
  };

  const handleAppleSignUp = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    // TODO: Implement Apple Sign Up
    Alert.alert('Coming Soon', 'Apple Sign Up will be available soon!');
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      {/* Gradient Header */}
      <LinearGradient
        colors={colors.gradients.primary}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.headerGradient}
      >
        <SafeAreaView edges={['top']} style={styles.headerSafeArea}>
          {/* Back Button */}
          <Animated.View entering={FadeIn.duration(300)} style={styles.backButton}>
            <Pressable
              style={{ width: '100%', height: '100%', alignItems: 'center', justifyContent: 'center' }}
              onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                navigation.goBack();
              }}
            >
              <Ionicons name="arrow-back" size={24} color={colors.white} />
            </Pressable>
          </Animated.View>

          <View style={styles.headerContent}>
            <Animated.View entering={FadeInDown.delay(100).duration(500)}>
              <Text style={styles.title}>Create Account</Text>
              <Text style={styles.subtitle}>Start your journey to financial freedom</Text>
            </Animated.View>
          </View>
        </SafeAreaView>
      </LinearGradient>

      {/* Main Content Sheet */}
      <View style={styles.sheetContainer}>
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.keyboardView}
        >
          <ScrollView
            contentContainerStyle={[
              styles.scrollContent,
              { paddingBottom: theme.spacing.xl + insets.bottom }
            ]}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >


            {/* Error Message */}
            {error ? (
              <Animated.View
                entering={SlideInDown.duration(300)}
                style={styles.errorContainer}
              >
                <Ionicons name="alert-circle" size={20} color={colors.error.primary} />
                <Text style={styles.errorText}>{error}</Text>
              </Animated.View>
            ) : null}

            {/* Registration Form */}
            <Animated.View entering={FadeInDown.delay(300).duration(500)}>
              <View style={styles.form}>
                <Input
                  label="Email"
                  value={email}
                  onChangeText={(text) => {
                    setEmail(text);
                    setError('');
                  }}
                  placeholder="you@example.com"
                  keyboardType="email-address"
                  autoCapitalize="none"
                  autoComplete="email"
                  autoCorrect={false}
                  leftIcon="mail-outline"
                  returnKeyType="next"
                  onSubmitEditing={() => passwordInputRef.current?.focus()}
                />

                <View>
                  <Input
                    ref={passwordInputRef}
                    label="Password"
                    value={password}
                    onChangeText={handlePasswordChange}
                    placeholder="At least 8 characters"
                    secureTextEntry
                    autoCapitalize="none"
                    leftIcon="lock-closed-outline"
                    returnKeyType="go"
                    onSubmitEditing={handleRegister}
                  />

                  {/* Password Strength Indicator */}
                  {password.length > 0 && (
                    <Animated.View
                      entering={FadeIn.duration(300)}
                      style={styles.strengthContainer}
                    >
                      <View style={styles.strengthBar}>
                        <View
                          style={[
                            styles.strengthFill,
                            {
                              width: getStrengthWidth() as any,
                              backgroundColor: getStrengthColor(),
                            },
                          ]}
                        />
                      </View>
                      <Text
                        style={[
                          styles.strengthText,
                          { color: getStrengthColor() },
                        ]}
                      >
                        {passwordStrength.charAt(0).toUpperCase() + passwordStrength.slice(1)}
                      </Text>
                    </Animated.View>
                  )}

                  {/* Password Requirements */}
                  <View style={styles.requirements}>
                    <Text style={styles.requirementsTitle}>Password must contain:</Text>
                    <View style={styles.requirement}>
                      <Ionicons
                        name={password.length >= 8 ? 'checkmark-circle' : 'ellipse-outline'}
                        size={14}
                        color={password.length >= 8 ? colors.income.primary : colors.text.tertiary}
                      />
                      <Text style={[
                        styles.requirementText,
                        password.length >= 8 && styles.requirementMet,
                      ]}>
                        At least 8 characters
                      </Text>
                    </View>
                    <View style={styles.requirement}>
                      <Ionicons
                        name={/[A-Z]/.test(password) && /[a-z]/.test(password) ? 'checkmark-circle' : 'ellipse-outline'}
                        size={14}
                        color={/[A-Z]/.test(password) && /[a-z]/.test(password) ? colors.income.primary : colors.text.tertiary}
                      />
                      <Text style={[
                        styles.requirementText,
                        /[A-Z]/.test(password) && /[a-z]/.test(password) && styles.requirementMet,
                      ]}>
                        Upper & lowercase letters
                      </Text>
                    </View>
                    <View style={styles.requirement}>
                      <Ionicons
                        name={/[0-9]/.test(password) ? 'checkmark-circle' : 'ellipse-outline'}
                        size={14}
                        color={/[0-9]/.test(password) ? colors.income.primary : colors.text.tertiary}
                      />
                      <Text style={[
                        styles.requirementText,
                        /[0-9]/.test(password) && styles.requirementMet,
                      ]}>
                        At least one number
                      </Text>
                    </View>
                  </View>
                </View>

                {/* Create Account Button */}
                <Pressable
                  style={[styles.createButton, loading && styles.createButtonDisabled]}
                  onPress={handleRegister}
                  disabled={loading}
                >
                  <Text style={styles.createButtonText}>
                    {loading ? 'Creating account...' : 'Create Account'}
                  </Text>
                  {!loading && (
                    <Ionicons name="arrow-forward" size={24} color={colors.white} />
                  )}
                </Pressable>
              </View>
            </Animated.View>

            {/* Social Sign Up */}
            <Animated.View entering={FadeInDown.delay(400).duration(500)}>
              <View style={styles.divider}>
                <View style={styles.dividerLine} />
                <Text style={styles.dividerText}>or sign up with</Text>
                <View style={styles.dividerLine} />
              </View>

              <View style={styles.socialButtons}>
                <Pressable style={styles.socialButton} onPress={handleGoogleSignUp}>
                  <Ionicons name="logo-google" size={24} color="#4285F4" />
                </Pressable>

                <Pressable style={styles.socialButton} onPress={handleAppleSignUp}>
                  <Ionicons name="logo-apple" size={24} color={colors.text.primary} />
                </Pressable>
              </View>
            </Animated.View>

            {/* Sign In Link */}
            <Animated.View entering={FadeInDown.delay(500).duration(500)}>
              <Pressable
                style={styles.signInLink}
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  navigation.navigate('Login');
                }}
              >
                <Text style={styles.signInLinkText}>
                  Already have an account? <Text style={styles.signInLinkBold}>Sign In</Text>
                </Text>
              </Pressable>
            </Animated.View>

            {/* Terms */}
            <Animated.View entering={FadeInDown.delay(600).duration(500)}>
              <Text style={styles.terms}>
                By creating an account, you agree to our{' '}
                <Text style={styles.termsLink}>Terms of Service</Text> and{' '}
                <Text style={styles.termsLink}>Privacy Policy</Text>
              </Text>
            </Animated.View>
          </ScrollView>
        </KeyboardAvoidingView>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.primary[600],
  },
  headerGradient: {
    height: '30%',
  },
  headerSafeArea: {
    flex: 1,
    justifyContent: 'flex-end',
  },
  headerContent: {
    paddingHorizontal: theme.spacing.xl,
    paddingBottom: theme.spacing.xxxxl,
  },
  backButton: {
    position: 'absolute',
    top: theme.spacing.md,
    left: theme.spacing.xl,
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: theme.radius.full,
    backgroundColor: 'rgba(255,255,255,0.2)',
    zIndex: 10,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.white,
    marginBottom: theme.spacing.xs,
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.8)',
    fontWeight: '500',
  },
  sheetContainer: {
    flex: 1,
    backgroundColor: colors.background.primary,
    borderTopLeftRadius: 32,
    borderTopRightRadius: 32,
    marginTop: -24,
    overflow: 'hidden',
  },
  keyboardView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    padding: theme.spacing.xl,
    paddingTop: theme.spacing.xl,
  },



  // Error
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    backgroundColor: colors.error.light,
    padding: theme.spacing.md,
    borderRadius: theme.radius.lg,
    marginBottom: theme.spacing.lg,
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.2)',
  },
  errorText: {
    flex: 1,
    fontSize: 14,
    color: colors.error.primary,
    fontWeight: '600',
  },

  // Form
  form: {
    gap: theme.spacing.lg,
  },

  // Password Strength
  strengthContainer: {
    marginTop: theme.spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  strengthBar: {
    flex: 1,
    height: 4,
    backgroundColor: colors.gray[200],
    borderRadius: 2,
    overflow: 'hidden',
    marginRight: theme.spacing.md,
  },
  strengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  strengthText: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'capitalize',
  },

  // Requirements
  requirements: {
    marginTop: theme.spacing.md,
    gap: theme.spacing.xs,
    backgroundColor: colors.background.secondary,
    padding: theme.spacing.md,
    borderRadius: theme.radius.md,
  },
  requirementsTitle: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.text.secondary,
    marginBottom: theme.spacing.xs,
  },
  requirement: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
  },
  requirementText: {
    fontSize: 12,
    color: colors.text.tertiary,
  },
  requirementMet: {
    color: colors.text.secondary,
    fontWeight: '500',
  },

  // Create Button
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    height: 56,
    backgroundColor: colors.primary[500],
    borderRadius: theme.radius.xl,
    marginTop: theme.spacing.sm,
    ...theme.shadows.md,
  },
  createButtonDisabled: {
    opacity: 0.7,
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.white,
    letterSpacing: 0.5,
  },

  // Divider
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: theme.spacing.xl,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.border.light,
  },
  dividerText: {
    fontSize: 13,
    color: colors.text.tertiary,
    marginHorizontal: theme.spacing.md,
    fontWeight: '500',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },

  // Social Buttons
  socialButtons: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  socialButton: {
    flex: 1,
    height: 56,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.white,
    borderRadius: theme.radius.xl,
    borderWidth: 1,
    borderColor: colors.border.medium,
    ...theme.shadows.sm,
  },

  // Sign In Link
  signInLink: {
    alignItems: 'center',
    paddingVertical: theme.spacing.lg,
    marginTop: theme.spacing.sm,
  },
  signInLinkText: {
    fontSize: 15,
    color: colors.text.secondary,
  },
  signInLinkBold: {
    fontWeight: '700',
    color: colors.primary[600],
  },

  // Terms
  terms: {
    fontSize: 12,
    color: colors.text.tertiary,
    textAlign: 'center',
    lineHeight: 18,
    marginBottom: theme.spacing.xl,
  },
  termsLink: {
    color: colors.primary[600],
    fontWeight: '600',
  },
});
