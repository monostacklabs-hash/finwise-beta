/**
 * User Preferences Context
 * Manages user currency, timezone, and country preferences globally
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { financialService } from '../services/financial';
import type { UserPreferences } from '../types';

interface UserPreferencesContextType {
  preferences: UserPreferences;
  loading: boolean;
  updatePreferences: (prefs: Partial<UserPreferences>) => Promise<void>;
  refreshPreferences: () => Promise<void>;
}

const defaultPreferences: UserPreferences = {
  currency: 'USD',
  timezone: 'UTC',
  country: undefined,
};

const UserPreferencesContext = createContext<UserPreferencesContextType>({
  preferences: defaultPreferences,
  loading: true,
  updatePreferences: async () => {},
  refreshPreferences: async () => {},
});

export const useUserPreferences = () => {
  const context = useContext(UserPreferencesContext);
  if (!context) {
    throw new Error('useUserPreferences must be used within UserPreferencesProvider');
  }
  return context;
};

interface UserPreferencesProviderProps {
  children: ReactNode;
}

export const UserPreferencesProvider: React.FC<UserPreferencesProviderProps> = ({ children }) => {
  const [preferences, setPreferences] = useState<UserPreferences>(defaultPreferences);
  const [loading, setLoading] = useState(true);

  const loadPreferences = async () => {
    try {
      const prefs = await financialService.getUserPreferences();
      setPreferences({
        currency: prefs.currency || 'USD',
        timezone: prefs.timezone || 'UTC',
        country: prefs.country,
      });
    } catch (error) {
      console.error('Failed to load user preferences:', error);
      // Use defaults on error
      setPreferences(defaultPreferences);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPreferences();
  }, []);

  const updatePreferences = async (prefs: Partial<UserPreferences>) => {
    try {
      const updated = await financialService.updateUserPreferences(prefs);
      setPreferences({
        currency: updated.currency || 'USD',
        timezone: updated.timezone || 'UTC',
        country: updated.country,
      });
    } catch (error) {
      console.error('Failed to update user preferences:', error);
      throw error;
    }
  };

  const refreshPreferences = async () => {
    await loadPreferences();
  };

  return (
    <UserPreferencesContext.Provider
      value={{
        preferences,
        loading,
        updatePreferences,
        refreshPreferences,
      }}
    >
      {children}
    </UserPreferencesContext.Provider>
  );
};
