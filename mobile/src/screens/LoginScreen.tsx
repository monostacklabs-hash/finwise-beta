import React, { useState, useEffect, useRef } from 'react';
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
import * as LocalAuthentication from 'expo-local-authentication';
import * as Haptics from 'expo-haptics';
import Animated, {
  FadeInDown,
  SlideInDown,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import { Input } from '../components/Input';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { authService } from '../services/auth';

interface LoginScreenProps {
  navigation: any;
  onLoginSuccess: () => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({
  navigation,
  onLoginSuccess,
}) => {
  const insets = useSafeAreaInsets();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [biometricAvailable, setBiometricAvailable] = useState(false);
  const [biometricType, setBiometricType] = useState<string>('');
  const passwordInputRef = useRef<TextInput>(null);

  useEffect(() => {
    checkBiometricAvailability();
  }, []);

  const checkBiometricAvailability = async () => {
    try {
      const compatible = await LocalAuthentication.hasHardwareAsync();
      const enrolled = await LocalAuthentication.isEnrolledAsync();

      if (compatible && enrolled) {
        const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
        setBiometricAvailable(true);

        if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
          setBiometricType('Face ID');
        } else if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
          setBiometricType('Touch ID');
        } else {
          setBiometricType('Biometric');
        }
      }
    } catch (error) {
      console.log('Biometric check failed:', error);
    }
  };

  const handleBiometricLogin = async () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: `Sign in to FinWise`,
        fallbackLabel: 'Use password',
        cancelLabel: 'Cancel',
      });

      if (result.success) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        Alert.alert('Success', 'Biometric authentication successful!');
        onLoginSuccess();
      }
    } catch (error) {
      console.error('Biometric auth error:', error);
    }
  };

  const handleLogin = async () => {
    setError('');

    if (!email) {
      setError('Please enter your email');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      return;
    }

    if (!password) {
      setError('Please enter your password');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError('Please enter a valid email address');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      return;
    }

    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      await authService.login({ username: email, password });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      onLoginSuccess();
    } catch (error: any) {
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      const errorMessage = error.response?.data?.detail || 'Invalid email or password';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    Alert.alert('Coming Soon', 'Google Sign In will be available soon!');
  };

  const handleAppleSignIn = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    Alert.alert('Coming Soon', 'Apple Sign In will be available soon!');
  };

  const handleForgotPassword = () => {
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    Alert.alert(
      'Reset Password',
      'Enter your email address and we\'ll send you a reset link.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Send Link', onPress: () => {
            Alert.alert('Success', 'Password reset link sent to your email!');
          }
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <StatusBar style="light" />

      {/* Gradient Header Background */}
      <LinearGradient
        colors={colors.gradients.primary}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={styles.headerGradient}
      >
        <SafeAreaView edges={['top']} style={styles.headerSafeArea}>
          <Animated.View entering={FadeInDown.delay(100).duration(500)} style={styles.headerContent}>
            <View style={styles.logoContainer}>
              <Ionicons name="wallet" size={40} color={colors.white} />
            </View>
            <Text style={styles.title}>Welcome Back</Text>
            <Text style={styles.subtitle}>Sign in to continue your financial journey</Text>
          </Animated.View>
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
            {/* Biometric Login */}
            {biometricAvailable && (
              <Animated.View entering={FadeInDown.delay(200).duration(500)}>
                <Pressable
                  style={styles.biometricButton}
                  onPress={handleBiometricLogin}
                >
                  <View style={styles.biometricIcon}>
                    <Ionicons
                      name={biometricType === 'Face ID' ? 'scan' : 'finger-print'}
                      size={28}
                      color={colors.primary[500]}
                    />
                  </View>
                  <Text style={styles.biometricText}>Sign in with {biometricType}</Text>
                </Pressable>
              </Animated.View>
            )}

            {/* Divider */}
            {biometricAvailable && (
              <Animated.View
                entering={FadeInDown.delay(300).duration(500)}
                style={styles.divider}
              >
                <View style={styles.dividerLine} />
                <Text style={styles.dividerText}>or use email</Text>
                <View style={styles.dividerLine} />
              </Animated.View>
            )}

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

            {/* Login Form */}
            <Animated.View entering={FadeInDown.delay(400).duration(500)}>
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

                <Input
                  ref={passwordInputRef}
                  label="Password"
                  value={password}
                  onChangeText={(text) => {
                    setPassword(text);
                    setError('');
                  }}
                  placeholder="Enter your password"
                  secureTextEntry
                  autoCapitalize="none"
                  autoComplete="password"
                  leftIcon="lock-closed-outline"
                  returnKeyType="go"
                  onSubmitEditing={handleLogin}
                />

                {/* Remember Me & Forgot Password */}
                <View style={styles.formFooter}>
                  <Pressable
                    style={styles.rememberMe}
                    onPress={() => {
                      setRememberMe(!rememberMe);
                      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                    }}
                  >
                    <View style={[styles.checkbox, rememberMe && styles.checkboxChecked]}>
                      {rememberMe && (
                        <Ionicons name="checkmark" size={14} color={colors.white} />
                      )}
                    </View>
                    <Text style={styles.rememberMeText}>Remember me</Text>
                  </Pressable>

                  <Pressable onPress={handleForgotPassword}>
                    <Text style={styles.forgotPassword}>Forgot password?</Text>
                  </Pressable>
                </View>

                {/* Sign In Button */}
                <Pressable
                  style={[styles.signInButton, loading && styles.signInButtonDisabled]}
                  onPress={handleLogin}
                  disabled={loading}
                >
                  <Text style={styles.signInButtonText}>
                    {loading ? 'Signing in...' : 'Sign In'}
                  </Text>
                  {!loading && (
                    <Ionicons name="arrow-forward" size={24} color={colors.white} />
                  )}
                </Pressable>
              </View>
            </Animated.View>

            {/* Social Login */}
            <Animated.View entering={FadeInDown.delay(500).duration(500)}>
              <View style={styles.divider}>
                <View style={styles.dividerLine} />
                <Text style={styles.dividerText}>or continue with</Text>
                <View style={styles.dividerLine} />
              </View>

              <View style={styles.socialButtons}>
                <Pressable style={styles.socialButton} onPress={handleGoogleSignIn}>
                  <Ionicons name="logo-google" size={24} color="#4285F4" />
                </Pressable>

                <Pressable style={styles.socialButton} onPress={handleAppleSignIn}>
                  <Ionicons name="logo-apple" size={24} color={colors.text.primary} />
                </Pressable>
              </View>
            </Animated.View>

            {/* Sign Up Link */}
            <Animated.View entering={FadeInDown.delay(600).duration(500)}>
              <Pressable
                style={styles.signUpLink}
                onPress={() => {
                  Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  navigation.navigate('Register');
                }}
              >
                <Text style={styles.signUpLinkText}>
                  Don't have an account? <Text style={styles.signUpLinkBold}>Sign Up</Text>
                </Text>
              </Pressable>
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
    backgroundColor: colors.primary[600], // Fallback color matches gradient start
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
  logoContainer: {
    width: 64,
    height: 64,
    backgroundColor: 'rgba(255,255,255,0.2)',
    borderRadius: theme.radius.xl,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: theme.spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.3)',
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

  // Biometric
  biometricButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: theme.spacing.md,
    backgroundColor: colors.primary[50],
    borderRadius: theme.radius.xl,
    borderWidth: 1,
    borderColor: colors.primary[100],
    marginBottom: theme.spacing.lg,
    gap: theme.spacing.md,
  },
  biometricIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.white,
    alignItems: 'center',
    justifyContent: 'center',
    ...theme.shadows.sm,
  },
  biometricText: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.primary[700],
  },

  // Divider
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: theme.spacing.lg,
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
  formFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: -theme.spacing.xs,
  },
  rememberMe: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: colors.border.medium,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxChecked: {
    backgroundColor: colors.primary[500],
    borderColor: colors.primary[500],
  },
  rememberMeText: {
    fontSize: 14,
    color: colors.text.secondary,
    fontWeight: '500',
  },
  forgotPassword: {
    fontSize: 14,
    color: colors.primary[600],
    fontWeight: '600',
  },

  // Sign In Button
  signInButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: theme.spacing.sm,
    height: 56,
    backgroundColor: colors.primary[500],
    borderRadius: theme.radius.xl,
    marginTop: theme.spacing.xs,
    ...theme.shadows.md,
  },
  signInButtonDisabled: {
    opacity: 0.7,
  },
  signInButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.white,
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

  // Sign Up Link
  signUpLink: {
    alignItems: 'center',
    paddingVertical: theme.spacing.lg,
    marginTop: theme.spacing.sm,
  },
  signUpLinkText: {
    fontSize: 15,
    color: colors.text.secondary,
  },
  signUpLinkBold: {
    fontWeight: '700',
    color: colors.primary[600],
  },
});
