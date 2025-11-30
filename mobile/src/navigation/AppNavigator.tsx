/**
 * App Navigation - 2025
 * Native headers with consistent styling
 */

import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Ionicons } from '@expo/vector-icons';
import { TouchableOpacity } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { DashboardScreen } from '../screens/DashboardScreen';
import { ChatScreen } from '../screens/ChatScreen';
import { TransactionsScreen } from '../screens/TransactionsScreen';
import { GoalsScreen } from '../screens/GoalsScreen';
import { ProfileScreen } from '../screens/ProfileScreen';
import { BudgetsScreen } from '../screens/BudgetsScreen';
import { RecurringTransactionsScreen } from '../screens/RecurringTransactionsScreen';
import { CashFlowScreen } from '../screens/CashFlowScreen';
import { NotificationsScreen } from '../screens/NotificationsScreen';
import { ExportScreen } from '../screens/ExportScreen';
import { SettingsScreen } from '../screens/SettingsScreen';
import { AccountsScreen } from '../screens/AccountsScreen';
import { AccountDetailsScreen } from '../screens/AccountDetailsScreen';
import { CreditCardDetailsScreen } from '../screens/CreditCardDetailsScreen';
import { AddAccountScreen } from '../screens/AddAccountScreen';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

interface AppNavigatorProps {
  onLogout: () => void;
}

// Common header style
const headerStyle = {
  backgroundColor: colors.background.primary,
  elevation: 0,
  shadowOpacity: 0,
  borderBottomWidth: 1,
  borderBottomColor: colors.border.light,
};

const headerTitleStyle = {
  fontSize: 20,
  fontWeight: '600' as const,
  color: colors.text.primary,
};

// Dashboard Stack
const DashboardStack = createNativeStackNavigator();
const DashboardStackNavigator: React.FC = () => {
  return (
    <DashboardStack.Navigator
      screenOptions={{
        headerStyle,
        headerTitleStyle,
        headerShadowVisible: false,
      }}
    >
      <DashboardStack.Screen
        name="DashboardMain"
        component={DashboardScreen}
        options={{
          headerShown: false,
        }}
      />
    </DashboardStack.Navigator>
  );
};

// Accounts Stack
const AccountsStack = createNativeStackNavigator();
const AccountsStackNavigator: React.FC = () => {
  return (
    <AccountsStack.Navigator
      screenOptions={{
        headerStyle,
        headerTitleStyle,
        headerShadowVisible: false,
      }}
    >
      <AccountsStack.Screen
        name="AccountsList"
        component={AccountsScreen}
        options={({ navigation }) => ({
          title: 'Accounts',
          headerRight: () => (
            <TouchableOpacity
              onPress={() => navigation.navigate('AddAccount' as never)}
              style={{ marginRight: 8 }}
            >
              <Ionicons name="add" size={28} color={colors.primary[500]} />
            </TouchableOpacity>
          ),
        })}
      />
      <AccountsStack.Screen
        name="AccountDetails"
        component={AccountDetailsScreen}
        options={{ title: 'Account Details' }}
      />
      <AccountsStack.Screen
        name="CreditCardDetails"
        component={CreditCardDetailsScreen}
        options={{ title: 'Credit Card' }}
      />
      <AccountsStack.Screen
        name="AddAccount"
        component={AddAccountScreen}
        options={{ title: 'Add Account', presentation: 'modal' }}
      />
    </AccountsStack.Navigator>
  );
};

// Chat Stack
const ChatStack = createNativeStackNavigator();
const ChatStackNavigator: React.FC = () => {
  return (
    <ChatStack.Navigator
      screenOptions={{
        headerStyle,
        headerTitleStyle,
        headerShadowVisible: false,
      }}
    >
      <ChatStack.Screen
        name="ChatMain"
        component={ChatScreen}
        options={{
          title: 'AI Assistant',
          headerLargeTitle: false,
        }}
      />
    </ChatStack.Navigator>
  );
};

// Transactions Stack
const TransactionsStack = createNativeStackNavigator();
const TransactionsStackNavigator: React.FC = () => {
  return (
    <TransactionsStack.Navigator
      screenOptions={{
        headerStyle,
        headerTitleStyle,
        headerShadowVisible: false,
      }}
    >
      <TransactionsStack.Screen
        name="TransactionsMain"
        component={TransactionsScreen}
        options={{
          title: 'Transactions',
        }}
      />
    </TransactionsStack.Navigator>
  );
};

// Profile/More Stack
const ProfileStack = createNativeStackNavigator();
const ProfileStackNavigator: React.FC<{ onLogout: () => void }> = ({ onLogout }) => {
  return (
    <ProfileStack.Navigator
      screenOptions={{
        headerStyle,
        headerTitleStyle,
        headerShadowVisible: false,
      }}
    >
      <ProfileStack.Screen
        name="ProfileMain"
        options={{ title: 'More' }}
      >
        {() => <ProfileScreen onLogout={onLogout} />}
      </ProfileStack.Screen>
      <ProfileStack.Screen
        name="Settings"
        component={SettingsScreen}
        options={{ title: 'Settings' }}
      />
      <ProfileStack.Screen
        name="Budgets"
        component={BudgetsScreen}
        options={({ navigation }) => ({
          title: 'Budgets',
          headerRight: () => (
            <TouchableOpacity
              onPress={() => {
                // Will be handled by screen
              }}
              style={{ marginRight: 8 }}
            >
              <Ionicons name="add" size={28} color={colors.primary[500]} />
            </TouchableOpacity>
          ),
        })}
      />
      <ProfileStack.Screen
        name="RecurringTransactions"
        component={RecurringTransactionsScreen}
        options={({ navigation }) => ({
          title: 'Recurring',
          headerRight: () => (
            <TouchableOpacity
              onPress={() => {
                // Will be handled by screen
              }}
              style={{ marginRight: 8 }}
            >
              <Ionicons name="add" size={28} color={colors.primary[500]} />
            </TouchableOpacity>
          ),
        })}
      />
      <ProfileStack.Screen
        name="CashFlow"
        component={CashFlowScreen}
        options={{ title: 'Cash Flow Forecast' }}
      />
      <ProfileStack.Screen
        name="Notifications"
        component={NotificationsScreen}
        options={{ title: 'Notifications' }}
      />
      <ProfileStack.Screen
        name="Export"
        component={ExportScreen}
        options={{ title: 'Export Data' }}
      />
      <ProfileStack.Screen
        name="Goals"
        component={GoalsScreen}
        options={({ navigation }) => ({
          title: 'Goals',
          headerRight: () => (
            <TouchableOpacity
              onPress={() => {
                // Will be handled by screen
              }}
              style={{ marginRight: 8 }}
            >
              <Ionicons name="add" size={28} color={colors.primary[500]} />
            </TouchableOpacity>
          ),
        })}
      />
    </ProfileStack.Navigator>
  );
};

export const AppNavigator: React.FC<AppNavigatorProps> = ({ onLogout }) => {
  const insets = useSafeAreaInsets();

  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.primary[500],
        tabBarInactiveTintColor: colors.gray[400],
        tabBarStyle: {
          borderTopColor: colors.border.light,
          backgroundColor: colors.background.primary,
          height: 60 + insets.bottom,
          paddingBottom: insets.bottom > 0 ? insets.bottom : 8,
          paddingTop: 8,
          paddingHorizontal: 8,
          ...theme.shadows.sm,
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 4,
          marginBottom: 4,
        },
      }}
    >
      <Tab.Screen
        name="Dashboard"
        component={DashboardStackNavigator}
        options={{
          tabBarLabel: 'Home',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons
              name={focused ? 'home' : 'home-outline'}
              size={24}
              color={color}
            />
          ),
        }}
      />
      <Tab.Screen
        name="Accounts"
        component={AccountsStackNavigator}
        options={{
          tabBarLabel: 'Accounts',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons
              name={focused ? 'wallet' : 'wallet-outline'}
              size={24}
              color={color}
            />
          ),
        }}
      />
      <Tab.Screen
        name="Chat"
        component={ChatStackNavigator}
        options={{
          tabBarLabel: 'AI Chat',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons
              name={focused ? 'sparkles' : 'sparkles-outline'}
              size={24}
              color={color}
            />
          ),
        }}
      />
      <Tab.Screen
        name="Transactions"
        component={TransactionsStackNavigator}
        options={{
          tabBarLabel: 'Transactions',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons
              name={focused ? 'receipt' : 'receipt-outline'}
              size={24}
              color={color}
            />
          ),
        }}
      />
      <Tab.Screen
        name="More"
        options={{
          tabBarLabel: 'More',
          tabBarIcon: ({ color, focused }) => (
            <Ionicons
              name={focused ? 'menu' : 'menu-outline'}
              size={24}
              color={color}
            />
          ),
        }}
      >
        {() => <ProfileStackNavigator onLogout={onLogout} />}
      </Tab.Screen>
    </Tab.Navigator>
  );
};
