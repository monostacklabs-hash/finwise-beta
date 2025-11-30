/**
 * Modern Fintech Design System - 2025
 * Clean, professional color palette inspired by Stripe, Revolut, N26
 */

export const colors = {
  // Base Colors
  black: '#000000',
  white: '#FFFFFF',
  transparent: 'transparent',

  // Primary Brand - Cashew-inspired Modern Blue/Purple
  primary: {
    50: '#EEF2FF',
    100: '#E0E7FF',
    200: '#C7D2FE',
    300: '#A5B4FC',
    400: '#818CF8',
    500: '#6366F1',   // Indigo-500
    600: '#4F46E5',
    700: '#4338CA',
    800: '#3730A3',
    900: '#312E81',
    DEFAULT: '#6366F1',
  },

  // Secondary Brand - Vibrant Pink/Rose
  secondary: {
    50: '#FFF1F2',
    100: '#FFE4E6',
    200: '#FECDD3',
    300: '#FDA4AF',
    400: '#FB7185',
    500: '#F43F5E',
    600: '#E11D48',
    700: '#BE123C',
    800: '#9F1239',
    900: '#881337',
    DEFAULT: '#F43F5E',
  },

  // Grayscale - Warm & Cool Neutrals
  gray: {
    50: '#F9FAFB',
    100: '#F3F4F6',
    200: '#E5E7EB',
    300: '#D1D5DB',
    400: '#9CA3AF',
    500: '#6B7280',
    600: '#4B5563',
    700: '#374151',
    800: '#1F2937',
    900: '#111827',
    950: '#030712',
  },

  // Financial Semantic Colors - Soft & Vibrant
  income: {
    primary: '#10B981',     // Emerald 500
    light: '#ECFDF5',       // Emerald 50
    dark: '#047857',        // Emerald 700
    gradient: ['#34D399', '#10B981'] as const,
    glass: 'rgba(16, 185, 129, 0.15)',
    text: '#065F46',
  },

  expense: {
    primary: '#EF4444',     // Red 500
    light: '#FEF2F2',       // Red 50
    dark: '#B91C1C',        // Red 700
    gradient: ['#F87171', '#EF4444'] as const,
    glass: 'rgba(239, 68, 68, 0.15)',
    text: '#991B1B',
  },

  info: {
    primary: '#3B82F6',     // Blue 500
    light: '#EFF6FF',       // Blue 50
    dark: '#1D4ED8',        // Blue 700
    gradient: ['#60A5FA', '#3B82F6'] as const,
    glass: 'rgba(59, 130, 246, 0.15)',
    text: '#1E40AF',
  },

  warning: {
    primary: '#F59E0B',     // Amber 500
    light: '#FFFBEB',       // Amber 50
    dark: '#B45309',        // Amber 700
    gradient: ['#FBBF24', '#F59E0B'] as const,
    glass: 'rgba(245, 158, 11, 0.15)',
    text: '#92400E',
  },

  error: {
    primary: '#EF4444',     // Red 500
    light: '#FEF2F2',       // Red 50
    dark: '#B91C1C',        // Red 700
    gradient: ['#F87171', '#EF4444'] as const,
    glass: 'rgba(239, 68, 68, 0.15)',
    text: '#991B1B',
  },

  // Backgrounds
  background: {
    primary: '#FFFFFF',
    secondary: '#F8FAFC',    // Slate 50
    tertiary: '#F1F5F9',     // Slate 100
    elevated: '#FFFFFF',
    modal: '#FFFFFF',
    overlay: 'rgba(15, 23, 42, 0.6)', // Slate 900 with opacity
    dark: '#0F172A',         // Slate 900 for dark mode
  },

  // Borders
  border: {
    light: '#F1F5F9',
    medium: '#E2E8F0',
    dark: '#CBD5E1',
    active: '#6366F1',
  },

  // Text colors
  text: {
    primary: '#0F172A',      // Slate 900
    secondary: '#64748B',    // Slate 500
    tertiary: '#94A3B8',     // Slate 400
    inverse: '#FFFFFF',
    link: '#6366F1',
    disabled: '#CBD5E1',
  },

  // Modern Gradients
  gradients: {
    primary: ['#6366F1', '#4F46E5'] as const, // Indigo
    secondary: ['#F43F5E', '#E11D48'] as const, // Rose
    success: ['#34D399', '#10B981'] as const, // Emerald
    warning: ['#FBBF24', '#F59E0B'] as const, // Amber
    error: ['#F87171', '#EF4444'] as const, // Red
    purple: ['#A855F7', '#9333EA'] as const, // Purple
    blue: ['#3B82F6', '#2563EB'] as const, // Blue
    orange: ['#FB923C', '#EA580C'] as const, // Orange
    dark: ['#1E293B', '#0F172A'] as const, // Slate
    glass: ['rgba(255,255,255,0.8)', 'rgba(255,255,255,0.4)'] as const,
  },

  // Surface colors
  surface: {
    primary: '#FFFFFF',
    secondary: '#F8FAFC',
    elevated: '#FFFFFF',
    card: '#FFFFFF',
    glass: 'rgba(255, 255, 255, 0.7)',
  },

  // Glass effects
  glass: {
    light: 'rgba(255, 255, 255, 0.7)',
    medium: 'rgba(255, 255, 255, 0.5)',
    heavy: 'rgba(255, 255, 255, 0.3)',
    border: 'rgba(255, 255, 255, 0.2)',
  },

  // Legacy compatibility
  neutral: {
    400: '#9CA3AF',
  },
  textSecondary: '#64748B',

  // Gradient colors for login screen
  gradientStart: '#6366F1',
  gradientEnd: '#4F46E5',
};

export type ColorScheme = typeof colors;
