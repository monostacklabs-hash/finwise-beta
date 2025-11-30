/**
 * App Configuration - 2025
 */

import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Get the appropriate localhost URL based on platform
const getDevApiUrl = () => {
  // iOS Simulator can use localhost
  if (Platform.OS === 'ios') {
    return 'http://localhost:8000/api/v1';
  }
  // Android Emulator needs special IP
  if (Platform.OS === 'android') {
    return 'http://10.0.2.2:8000/api/v1';
  }
  // Fallback
  return 'http://localhost:8000/api/v1';
};

// API Configuration
export const API_CONFIG = {
  // Read from environment variable or use default
  BASE_URL: Constants.expoConfig?.extra?.apiBaseUrl || 
    (__DEV__
      ? getDevApiUrl()
      : 'https://your-production-api.com/api/v1'),

  TIMEOUT: 30000, // 30 seconds
};

// Storage Keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: '@fin_planner_token',
  USER_DATA: '@fin_planner_user',
};

// App Info
export const APP_INFO = {
  NAME: 'Financial Planner',
  VERSION: '1.0.0',
};
