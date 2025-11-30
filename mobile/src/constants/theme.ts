/**
 * Modern Design System - 2025
 * Industry-standard design tokens and theme configuration
 * Consistent spacing, typography, and visual hierarchy
 */

export const theme = {
  // Spacing scale (4pt grid system - more granular control)
  spacing: {
    xxs: 2,
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    xxl: 24,
    xxxl: 32,
    xxxxl: 40,
  },

  // Border radius (Modern, rounded feel)
  radius: {
    xs: 6,
    sm: 10,
    md: 14,
    lg: 20,
    xl: 26,
    xxl: 32,
    full: 9999,
  },

  // Typography (Inter/System font stack with tight tracking)
  typography: {
    h1: {
      fontSize: 34,
      fontWeight: '700' as const,
      lineHeight: 42,
      letterSpacing: -0.8,
      color: '#0F172A',
    },
    h2: {
      fontSize: 28,
      fontWeight: '700' as const,
      lineHeight: 36,
      letterSpacing: -0.6,
      color: '#0F172A',
    },
    h3: {
      fontSize: 24,
      fontWeight: '600' as const,
      lineHeight: 32,
      letterSpacing: -0.4,
      color: '#0F172A',
    },
    h4: {
      fontSize: 20,
      fontWeight: '600' as const,
      lineHeight: 28,
      letterSpacing: -0.2,
      color: '#0F172A',
    },
    h5: {
      fontSize: 18,
      fontWeight: '600' as const,
      lineHeight: 26,
      letterSpacing: -0.1,
      color: '#0F172A',
    },
    body: {
      fontSize: 16,
      fontWeight: '400' as const,
      lineHeight: 24,
      letterSpacing: 0,
      color: '#334155',
    },
    bodyLarge: {
      fontSize: 18,
      fontWeight: '400' as const,
      lineHeight: 28,
      letterSpacing: 0,
      color: '#334155',
    },
    bodySmall: {
      fontSize: 14,
      fontWeight: '400' as const,
      lineHeight: 20,
      letterSpacing: 0,
      color: '#64748B',
    },
    caption: {
      fontSize: 12,
      fontWeight: '500' as const,
      lineHeight: 16,
      letterSpacing: 0.2,
      color: '#94A3B8',
    },
    overline: {
      fontSize: 11,
      fontWeight: '700' as const,
      lineHeight: 16,
      letterSpacing: 1.2,
      textTransform: 'uppercase' as const,
      color: '#94A3B8',
    },
    button: {
      fontSize: 16,
      fontWeight: '600' as const,
      lineHeight: 24,
      letterSpacing: 0.1,
    },
  },

  // Shadows (Ultra-soft, diffuse shadows for depth)
  shadows: {
    none: {
      shadowColor: 'transparent',
      shadowOffset: { width: 0, height: 0 },
      shadowOpacity: 0,
      shadowRadius: 0,
      elevation: 0,
    },
    sm: {
      shadowColor: '#64748B',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.06,
      shadowRadius: 4,
      elevation: 2,
    },
    md: {
      shadowColor: '#64748B',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.08,
      shadowRadius: 8,
      elevation: 4,
    },
    lg: {
      shadowColor: '#64748B',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.1,
      shadowRadius: 16,
      elevation: 8,
    },
    xl: {
      shadowColor: '#64748B',
      shadowOffset: { width: 0, height: 12 },
      shadowOpacity: 0.12,
      shadowRadius: 24,
      elevation: 12,
    },
    glow: {
      shadowColor: '#6366F1',
      shadowOffset: { width: 0, height: 8 },
      shadowOpacity: 0.25,
      shadowRadius: 16,
      elevation: 10,
    },
  },

  // Card elevations
  card: {
    flat: {
      backgroundColor: '#FFFFFF',
      borderWidth: 1,
      borderColor: '#F1F5F9',
    },
    elevated: {
      backgroundColor: '#FFFFFF',
      borderWidth: 0,
    },
    outlined: {
      backgroundColor: '#FFFFFF',
      borderWidth: 1,
      borderColor: '#E2E8F0',
    },
    glass: {
      backgroundColor: 'rgba(255, 255, 255, 0.7)',
      borderWidth: 1,
      borderColor: 'rgba(255, 255, 255, 0.5)',
    },
  },

  // Animation durations
  animation: {
    fast: 200,
    normal: 300,
    slow: 500,
    spring: {
      damping: 15,
      stiffness: 100,
    },
  },

  // Icon sizes
  iconSize: {
    xs: 16,
    sm: 20,
    md: 24,
    lg: 28,
    xl: 32,
    xxl: 48,
  },

  // Container padding
  container: {
    padding: 20,
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
};

export type Theme = typeof theme;
