/**
 * Dashboard Screen - 2025
 * Modern, high-impact financial overview with Cashew-inspired aesthetics
 */

import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    TouchableOpacity,
    RefreshControl,
    Dimensions,
    StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';

import { Card } from '../components/Card';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import { formatCurrency } from '../utils/currency';
import type { Account, Transaction } from '../types';

const { width } = Dimensions.get('window');

export const DashboardScreen: React.FC = () => {
    const insets = useSafeAreaInsets();
    const navigation = useNavigation();
    const { preferences } = useUserPreferences();

    const [accounts, setAccounts] = useState<Account[]>([]);
    const [recentTransactions, setRecentTransactions] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const loadData = async () => {
        try {
            const [accountsData, transactionsList] = await Promise.all([
                financialService.getAccounts(),
                financialService.getTransactions(),
            ]);

            setAccounts(accountsData.accounts || []);
            // Take first 5 transactions
            setRecentTransactions(transactionsList.slice(0, 5) || []);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const onRefresh = () => {
        setRefreshing(true);
        loadData();
    };

    const getTotalBalance = () => {
        return accounts.reduce((sum, acc) => {
            if (acc.account_type === 'credit_card') {
                return sum - acc.current_balance;
            }
            return sum + acc.current_balance;
        }, 0);
    };

    const getMonthlySpending = () => {
        // This would ideally come from an API, but for now we sum up recent expense transactions
        return recentTransactions
            .filter(t => t.amount < 0)
            .reduce((sum, t) => sum + Math.abs(t.amount), 0);
    };

    const QuickAction = ({ icon, label, onPress, color = colors.primary[500] }: any) => (
        <TouchableOpacity
            style={styles.quickAction}
            onPress={() => {
                Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                onPress();
            }}
        >
            <View style={[styles.quickActionIcon, { backgroundColor: `${color}15` }]}>
                <Ionicons name={icon} size={24} color={color} />
            </View>
            <Text style={styles.quickActionLabel}>{label}</Text>
        </TouchableOpacity>
    );

    const TransactionItem = ({ item }: { item: Transaction }) => {
        const isExpense = item.amount < 0;
        const amountColor = isExpense ? colors.text.primary : colors.income.primary;

        return (
            <TouchableOpacity
                style={styles.transactionItem}
                onPress={() => {
                    // Navigate to details if needed
                }}
            >
                <View style={[styles.categoryIcon, { backgroundColor: isExpense ? colors.gray[100] : colors.income.light }]}>
                    <Ionicons
                        name={isExpense ? 'cart-outline' : 'cash-outline'}
                        size={20}
                        color={isExpense ? colors.text.secondary : colors.income.dark}
                    />
                </View>
                <View style={styles.transactionInfo}>
                    <Text style={styles.transactionMerchant} numberOfLines={1}>{item.description || 'Unknown'}</Text>
                    <Text style={styles.transactionCategory}>{item.category || 'Uncategorized'}</Text>
                </View>
                <Text style={[styles.transactionAmount, { color: amountColor }]}>
                    {isExpense ? '' : '+'}{formatCurrency(Math.abs(item.amount), preferences.currency)}
                </Text>
            </TouchableOpacity>
        );
    };

    return (
        <View style={styles.container}>
            <StatusBar barStyle="light-content" />

            <ScrollView
                contentContainerStyle={{ paddingBottom: 100 }}
                refreshControl={
                    <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.white} />
                }
                showsVerticalScrollIndicator={false}
            >
                {/* Header Section */}
                <View style={styles.headerContainer}>
                    <LinearGradient
                        colors={colors.gradients.primary}
                        start={{ x: 0, y: 0 }}
                        end={{ x: 1, y: 1 }}
                        style={[styles.headerGradient, { paddingTop: insets.top + 20 }]}
                    >
                        <View style={styles.headerContent}>
                            <View>
                                <Text style={styles.greeting}>Total Balance</Text>
                                <Text style={styles.totalBalance}>
                                    {formatCurrency(getTotalBalance(), preferences.currency)}
                                </Text>
                            </View>
                            <TouchableOpacity style={styles.profileButton} onPress={() => navigation.navigate('More' as never)}>
                                <Ionicons name="person-circle-outline" size={32} color="rgba(255,255,255,0.9)" />
                            </TouchableOpacity>
                        </View>

                        {/* Monthly Summary Pill */}
                        <View style={styles.summaryPill}>
                            <View style={styles.summaryItem}>
                                <Ionicons name="arrow-down-circle" size={16} color={colors.income.light} />
                                <Text style={styles.summaryLabel}>Income</Text>
                                <Text style={styles.summaryValue}>$4,250</Text>
                            </View>
                            <View style={styles.summaryDivider} />
                            <View style={styles.summaryItem}>
                                <Ionicons name="arrow-up-circle" size={16} color={colors.expense.light} />
                                <Text style={styles.summaryLabel}>Spent</Text>
                                <Text style={styles.summaryValue}>${getMonthlySpending().toFixed(0)}</Text>
                            </View>
                        </View>
                    </LinearGradient>
                </View>

                {/* Main Content - Overlapping the header */}
                <View style={styles.contentContainer}>

                    {/* Quick Actions */}
                    <Text style={styles.sectionTitle}>Quick Actions</Text>
                    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.quickActionsContainer}>
                        <QuickAction
                            icon="add"
                            label="Add Txn"
                            onPress={() => (navigation as any).navigate('Transactions', { screen: 'AddTransaction' })}
                            color={colors.primary[500]}
                        />
                        <QuickAction
                            icon="scan"
                            label="Scan"
                            onPress={() => { }}
                            color={colors.secondary[500]}
                        />
                        <QuickAction
                            icon="pie-chart"
                            label="Budget"
                            onPress={() => (navigation as any).navigate('More', { screen: 'Budgets' })}
                            color={colors.warning.primary}
                        />
                        <QuickAction
                            icon="swap-horizontal"
                            label="Transfer"
                            onPress={() => { }}
                            color={colors.info.primary}
                        />
                    </ScrollView>

                    {/* Featured Cards (Budget/Goals) */}
                    <View style={styles.cardsRow}>
                        <Card style={[styles.featureCard, { marginRight: theme.spacing.md }]} variant="elevated">
                            <View style={[styles.featureIcon, { backgroundColor: colors.warning.light }]}>
                                <Ionicons name="pie-chart-outline" size={20} color={colors.warning.dark} />
                            </View>
                            <Text style={styles.featureTitle}>Monthly Budget</Text>
                            <Text style={styles.featureValue}>65% Used</Text>
                            <View style={styles.progressBarBg}>
                                <View style={[styles.progressBarFill, { width: '65%', backgroundColor: colors.warning.primary }]} />
                            </View>
                        </Card>

                        <Card style={styles.featureCard} variant="elevated">
                            <View style={[styles.featureIcon, { backgroundColor: colors.income.light }]}>
                                <Ionicons name="flag-outline" size={20} color={colors.income.dark} />
                            </View>
                            <Text style={styles.featureTitle}>Savings Goal</Text>
                            <Text style={styles.featureValue}>$2,400 / $5k</Text>
                            <View style={styles.progressBarBg}>
                                <View style={[styles.progressBarFill, { width: '48%', backgroundColor: colors.income.primary }]} />
                            </View>
                        </Card>
                    </View>

                    {/* Recent Transactions */}
                    <View style={styles.sectionHeader}>
                        <Text style={styles.sectionTitle}>Recent Transactions</Text>
                        <TouchableOpacity onPress={() => navigation.navigate('Transactions' as never)}>
                            <Text style={styles.seeAllText}>See All</Text>
                        </TouchableOpacity>
                    </View>

                    <Card variant="elevated" style={styles.transactionsCard}>
                        {recentTransactions.length > 0 ? (
                            recentTransactions.map((item, index) => (
                                <React.Fragment key={item.id}>
                                    <TransactionItem item={item} />
                                    {index < recentTransactions.length - 1 && <View style={styles.divider} />}
                                </React.Fragment>
                            ))
                        ) : (
                            <View style={styles.emptyState}>
                                <Text style={styles.emptyStateText}>No recent transactions</Text>
                            </View>
                        )}
                    </Card>

                </View>
            </ScrollView>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: colors.background.secondary,
    },
    headerContainer: {
        // No margin needed as we want the content to overlap directly
    },
    headerGradient: {
        paddingHorizontal: theme.spacing.lg,
        paddingBottom: theme.spacing.xxxl * 1.5, // Extra padding for overlap
    },
    headerContent: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: theme.spacing.xl,
    },
    greeting: {
        ...theme.typography.bodySmall,
        color: 'rgba(255,255,255,0.8)',
        marginBottom: 4,
        textTransform: 'uppercase',
        letterSpacing: 1,
        fontWeight: '600',
    },
    totalBalance: {
        fontSize: 36,
        fontWeight: '700',
        color: colors.white,
        letterSpacing: -1,
    },
    profileButton: {
        padding: 4,
    },
    summaryPill: {
        flexDirection: 'row',
        backgroundColor: 'rgba(255,255,255,0.15)',
        borderRadius: theme.radius.xl,
        padding: theme.spacing.md,
        borderWidth: 1,
        borderColor: 'rgba(255,255,255,0.2)',
    },
    summaryItem: {
        flex: 1,
        alignItems: 'center',
    },
    summaryDivider: {
        width: 1,
        backgroundColor: 'rgba(255,255,255,0.2)',
        marginHorizontal: theme.spacing.sm,
    },
    summaryLabel: {
        ...theme.typography.caption,
        color: 'rgba(255,255,255,0.8)',
        marginBottom: 2,
    },
    summaryValue: {
        ...theme.typography.body,
        color: colors.white,
        fontWeight: '600',
    },
    contentContainer: {
        marginTop: -theme.spacing.xxxl, // Overlap effect
        paddingHorizontal: theme.spacing.lg,
        backgroundColor: colors.background.secondary,
        borderTopLeftRadius: theme.radius.xxl,
        borderTopRightRadius: theme.radius.xxl,
        paddingTop: theme.spacing.xl,
    },
    sectionTitle: {
        ...theme.typography.h5,
        color: colors.text.primary,
        marginBottom: theme.spacing.md,
        marginLeft: theme.spacing.xs,
    },
    sectionHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: theme.spacing.md,
        marginTop: theme.spacing.xl,
        paddingHorizontal: theme.spacing.xs,
    },
    seeAllText: {
        ...theme.typography.bodySmall,
        color: colors.primary[500],
        fontWeight: '600',
    },
    quickActionsContainer: {
        paddingHorizontal: theme.spacing.xs,
        gap: theme.spacing.lg,
        paddingBottom: theme.spacing.lg,
    },
    quickAction: {
        alignItems: 'center',
        gap: 8,
    },
    quickActionIcon: {
        width: 56,
        height: 56,
        borderRadius: theme.radius.xl,
        justifyContent: 'center',
        alignItems: 'center',
    },
    quickActionLabel: {
        ...theme.typography.caption,
        color: colors.text.secondary,
        fontWeight: '500',
    },
    cardsRow: {
        flexDirection: 'row',
        marginTop: theme.spacing.sm,
    },
    featureCard: {
        flex: 1,
        padding: theme.spacing.lg,
    },
    featureIcon: {
        width: 36,
        height: 36,
        borderRadius: theme.radius.lg,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: theme.spacing.md,
    },
    featureTitle: {
        ...theme.typography.caption,
        color: colors.text.secondary,
        marginBottom: 4,
    },
    featureValue: {
        ...theme.typography.h5,
        color: colors.text.primary,
        marginBottom: theme.spacing.md,
    },
    progressBarBg: {
        height: 6,
        backgroundColor: colors.gray[100],
        borderRadius: theme.radius.full,
        overflow: 'hidden',
    },
    progressBarFill: {
        height: '100%',
        borderRadius: theme.radius.full,
    },
    transactionsCard: {
        padding: 0, // Remove default padding for list items
        overflow: 'hidden',
    },
    transactionItem: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: theme.spacing.lg,
    },
    categoryIcon: {
        width: 40,
        height: 40,
        borderRadius: theme.radius.full,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: theme.spacing.md,
    },
    transactionInfo: {
        flex: 1,
    },
    transactionMerchant: {
        ...theme.typography.body,
        fontWeight: '600',
        color: colors.text.primary,
        marginBottom: 2,
    },
    transactionCategory: {
        ...theme.typography.caption,
        color: colors.text.tertiary,
    },
    transactionAmount: {
        ...theme.typography.body,
        fontWeight: '600',
    },
    divider: {
        height: 1,
        backgroundColor: colors.border.light,
        marginLeft: 72, // Align with text start
    },
    emptyState: {
        padding: theme.spacing.xl,
        alignItems: 'center',
    },
    emptyStateText: {
        color: colors.text.tertiary,
    },
});
