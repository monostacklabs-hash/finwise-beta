/**
 * Goals Screen - Financial Goals Management
 * Glassmorphic Finance Theme
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Alert,
  TouchableOpacity,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { ScreenContainer } from '../components/ScreenContainer';
import { GlassCard } from '../components/GlassCard';
import { BottomSheet } from '../components/BottomSheet';
import * as Haptics from 'expo-haptics';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import { useUserPreferences } from '../contexts/UserPreferencesContext';
import { formatCurrency } from '../utils/currency';

interface Goal {
  id: string;
  name: string;
  target_amount: number;
  current_amount: number;
  target_date: string;
  status: string;
  progress_percentage: number;
}

export const GoalsScreen: React.FC = () => {
  const { preferences } = useUserPreferences();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showMilestones, setShowMilestones] = useState(false);
  const [milestones, setMilestones] = useState<any>(null);
  const [loadingMilestones, setLoadingMilestones] = useState(false);

  useEffect(() => {
    loadGoals();
  }, []);

  const loadGoals = async () => {
    try {
      const response = await financialService.getGoals();
      setGoals(response.goals || []);
    } catch (error) {
      console.error('Failed to load goals:', error);
      Alert.alert('Error', 'Failed to load goals. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadGoals();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return colors.income.primary;
      case 'active':
        return colors.info.primary;
      case 'abandoned':
        return colors.gray[400];
      default:
        return colors.gray[400];
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return 'checkmark-circle';
      case 'active':
        return 'time';
      case 'abandoned':
        return 'close-circle';
      default:
        return 'help-circle';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric' 
    });
  };

  const loadAIMilestones = async () => {
    if (goals.length === 0) {
      Alert.alert('No Goals', 'Create some goals first to see AI milestones.');
      return;
    }

    setLoadingMilestones(true);
    try {
      const data = await financialService.getGoalMilestones();
      setMilestones(data);
      setShowMilestones(true);
    } catch (error) {
      Alert.alert('Error', 'Failed to load AI milestones. Please try again.');
    } finally {
      setLoadingMilestones(false);
    }
  };

  const renderGoalCard = (goal: Goal) => (
    <Card key={goal.id} elevation="lg" style={styles.goalCard}>
      <View style={styles.goalHeader}>
        <View style={styles.goalTitleRow}>
          <Ionicons name="flag" size={24} color={colors.info.primary} />
          <Text style={styles.goalName}>{goal.name}</Text>
        </View>
        <View style={[styles.statusBadge, {
          backgroundColor: goal.status === 'completed' ? colors.income.glass :
                          goal.status === 'active' ? colors.info.glass :
                          colors.glass.light
        }]}>
          <Ionicons name={getStatusIcon(goal.status)} size={16} color={getStatusColor(goal.status)} />
          <Text style={[styles.statusText, { color: getStatusColor(goal.status) }]}>
            {goal.status}
          </Text>
        </View>
      </View>

      <View style={styles.amountRow}>
        <View style={styles.amountItem}>
          <Text style={styles.amountLabel}>Current</Text>
          <Text style={styles.amountValue}>{formatCurrency(goal.current_amount, preferences.currency)}</Text>
        </View>
        <View style={styles.amountDivider} />
        <View style={styles.amountItem}>
          <Text style={styles.amountLabel}>Target</Text>
          <Text style={styles.amountValue}>{formatCurrency(goal.target_amount, preferences.currency)}</Text>
        </View>
      </View>

      <View style={styles.progressContainer}>
        <View style={styles.progressBar}>
          <View
            style={[
              styles.progressFill,
              {
                width: `${Math.min(goal.progress_percentage, 100)}%`,
                backgroundColor: goal.progress_percentage >= 100
                  ? colors.income.primary
                  : colors.info.primary
              }
            ]}
          />
        </View>
        <Text style={styles.progressText}>
          {goal.progress_percentage.toFixed(1)}%
        </Text>
      </View>

      <View style={styles.goalFooter}>
        <View style={styles.dateRow}>
          <Ionicons name="calendar-outline" size={16} color={colors.text.secondary} />
          <Text style={styles.dateText}>Target: {formatDate(goal.target_date)}</Text>
        </View>
      </View>
    </Card>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.info.primary} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScreenContainer
        refreshing={refreshing}
        onRefresh={onRefresh}
      >
        {goals.length === 0 ? (
          <Card elevation="lg">
            <View style={styles.emptyState}>
              <Ionicons name="flag-outline" size={64} color={colors.info.primary} />
              <Text style={styles.emptyTitle}>No Goals Yet</Text>
              <Text style={styles.emptyText}>
                Start setting financial goals to track your progress
              </Text>
              <Button
                title="Ask AI to Set Goals"
                onPress={() => Alert.alert('Tip', 'Go to AI Chat and ask: "Help me set a savings goal"')}
                variant="primary"
                icon="sparkles"
                style={styles.emptyButton}
              />
            </View>
          </Card>
        ) : (
          <>
            <View style={styles.statsRow}>
              <Card elevation="md" style={styles.statCard}>
                <Text style={[styles.statValue, { color: colors.info.primary }]}>
                  {goals.filter(g => g.status === 'active').length}
                </Text>
                <Text style={styles.statLabel}>Active</Text>
              </Card>
              <Card elevation="md" style={styles.statCard}>
                <Text style={[styles.statValue, { color: colors.income.primary }]}>
                  {goals.filter(g => g.status === 'completed').length}
                </Text>
                <Text style={styles.statLabel}>Completed</Text>
              </Card>
              <Card elevation="md" style={styles.statCard}>
                <Text style={[styles.statValue, { color: colors.info.primary }]}>
                  ${goals.reduce((sum, g) => sum + g.current_amount, 0).toLocaleString()}
                </Text>
                <Text style={styles.statLabel}>Total Saved</Text>
              </Card>
            </View>

            {goals.map(renderGoalCard)}
          </>
        )}
      </ScreenContainer>

      {/* AI Milestones Modal */}
      <BottomSheet
        visible={showMilestones}
        onClose={() => setShowMilestones(false)}
        title="AI Goal Milestones"
        subtitle="Track your progress"
      >
        <ScrollView showsVerticalScrollIndicator={false}>
              {milestones && Array.isArray(milestones) && milestones.map((goalData: any, index: number) => (
                <GlassCard key={index} variant="medium" style={styles.milestoneCard}>
                  <View style={styles.milestoneHeader}>
                    <Text style={styles.milestoneName}>{goalData.goal_name}</Text>
                    <View style={[styles.milestoneStatusBadge, {
                      backgroundColor: goalData.on_track ? colors.income.glass : colors.warning.glass,
                      borderColor: goalData.on_track ? colors.income.primary : colors.warning.primary,
                    }]}>
                      <Ionicons 
                        name={goalData.on_track ? 'checkmark-circle' : 'alert-circle'} 
                        size={14} 
                        color={goalData.on_track ? colors.income.primary : colors.warning.primary} 
                      />
                      <Text style={[styles.milestoneStatusText, {
                        color: goalData.on_track ? colors.income.primary : colors.warning.primary,
                      }]}>
                        {goalData.on_track ? 'On Track' : 'Behind'}
                      </Text>
                    </View>
                  </View>

                  <View style={styles.milestoneStats}>
                    <View style={styles.milestoneStatItem}>
                      <Text style={styles.milestoneStatLabel}>Progress</Text>
                      <Text style={styles.milestoneStatValue}>
                        {formatCurrency(goalData.current_amount, preferences.currency)} / {formatCurrency(goalData.target_amount, preferences.currency)}
                      </Text>
                      <Text style={styles.statPercentage}>{goalData.progress_percentage.toFixed(1)}%</Text>
                    </View>
                  </View>

                  <View style={styles.savingsRow}>
                    <View style={styles.savingsItem}>
                      <Text style={styles.savingsLabel}>Required/month</Text>
                      <Text style={styles.savingsValue}>
                        {formatCurrency(goalData.required_monthly_contribution, preferences.currency)}
                      </Text>
                    </View>
                    <View style={styles.savingsItem}>
                      <Text style={styles.savingsLabel}>Current savings</Text>
                      <Text style={[styles.savingsValue, {
                        color: goalData.current_monthly_savings >= goalData.required_monthly_contribution
                          ? colors.income.primary
                          : colors.warning.primary
                      }]}>
                        {formatCurrency(goalData.current_monthly_savings, preferences.currency)}
                      </Text>
                    </View>
                  </View>

                  {goalData.recommendations && goalData.recommendations.length > 0 && (
                    <View style={styles.recommendationBox}>
                      <Ionicons name="bulb-outline" size={20} color={colors.warning.primary} style={styles.recommendationIcon} />
                      <Text style={styles.recommendationText}>
                        {goalData.recommendations[0]}
                      </Text>
                    </View>
                  )}

                  {goalData.milestones && goalData.milestones.length > 0 && (
                    <View style={styles.milestonesTimeline}>
                      <Text style={styles.timelineTitle}>Milestones</Text>
                      {goalData.milestones.slice(0, 4).map((milestone: any, idx: number) => (
                        <View key={idx} style={styles.timelineItem}>
                          <View style={[styles.timelineDot, {
                            backgroundColor: milestone.is_achieved 
                              ? colors.income.primary 
                              : milestone.status === 'on_track'
                              ? colors.info.primary
                              : colors.gray[600]
                          }]} />
                          <View style={styles.timelineContent}>
                            <Text style={styles.timelinePercentage}>{milestone.percentage}%</Text>
                            <Text style={styles.timelineAmount}>
                              {formatCurrency(milestone.amount, preferences.currency)}
                            </Text>
                            <Text style={styles.timelineDate}>
                              {milestone.is_achieved ? '✓ Achieved' : formatDate(milestone.estimated_date)}
                            </Text>
                          </View>
                        </View>
                      ))}
                    </View>
                  )}
                </GlassCard>
              ))}
        </ScrollView>
      </BottomSheet>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.secondary,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background.secondary,
  },
  statsRow: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.lg,
  },
  statCard: {
    flex: 1,
    alignItems: 'center',
    padding: theme.spacing.lg,
  },
  statValue: {
    ...theme.typography.h3,
    color: colors.text.primary,
  },
  statLabel: {
    ...theme.typography.caption,
    color: colors.text.secondary,
    marginTop: 4,
  },
  goalCard: {
    marginBottom: theme.spacing.lg,
    padding: theme.spacing.lg,
  },
  goalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: theme.spacing.md,
  },
  goalTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    flex: 1,
  },
  goalName: {
    ...theme.typography.h4,
    color: colors.text.primary,
    flex: 1,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  statusText: {
    ...theme.typography.caption,
    fontWeight: '600',
    textTransform: 'capitalize',
  },
  amountRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  amountItem: {
    flex: 1,
    alignItems: 'center',
  },
  amountDivider: {
    width: 1,
    height: 40,
    backgroundColor: colors.border.light,
  },
  amountLabel: {
    ...theme.typography.caption,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  amountValue: {
    ...theme.typography.h3,
    color: colors.text.primary,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.md,
  },
  progressBar: {
    flex: 1,
    height: 8,
    backgroundColor: colors.gray[800],
    borderRadius: theme.radius.full,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: theme.radius.full,
  },
  progressText: {
    ...theme.typography.caption,
    fontWeight: '600',
    color: colors.text.primary,
    minWidth: 45,
    textAlign: 'right',
  },
  goalFooter: {
    borderTopWidth: 1,
    borderTopColor: colors.border.light,
    paddingTop: theme.spacing.sm,
  },
  dateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.xs,
  },
  dateText: {
    ...theme.typography.caption,
    color: colors.text.secondary,
  },
  emptyState: {
    alignItems: 'center',
    padding: theme.spacing.xl,
  },
  emptyTitle: {
    ...theme.typography.h3,
    color: colors.text.primary,
    marginTop: theme.spacing.md,
  },
  emptyText: {
    ...theme.typography.body,
    color: colors.text.secondary,
    textAlign: 'center',
    marginTop: theme.spacing.sm,
  },
  emptyButton: {
    marginTop: theme.spacing.lg,
  },
  milestoneCard: {
    marginBottom: theme.spacing.lg,
  },
  milestoneHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing.md,
  },
  milestoneName: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text.primary,
    flex: 1,
  },
  milestoneStatusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: theme.radius.md,
    borderWidth: 1,
  },
  milestoneStatusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  milestoneStats: {
    marginBottom: theme.spacing.md,
  },
  milestoneStatItem: {
    alignItems: 'center',
  },
  milestoneStatLabel: {
    fontSize: 12,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  milestoneStatValue: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text.primary,
    marginBottom: 2,
  },
  statPercentage: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.info.primary,
  },
  savingsRow: {
    flexDirection: 'row',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.md,
  },
  savingsItem: {
    flex: 1,
    alignItems: 'center',
    padding: theme.spacing.sm,
    backgroundColor: colors.background.secondary,
    borderRadius: theme.radius.md,
  },
  savingsLabel: {
    fontSize: 11,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  savingsValue: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text.primary,
  },
  recommendationBox: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    padding: theme.spacing.md,
    backgroundColor: colors.info.glass,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: colors.info.primary,
    marginBottom: theme.spacing.md,
  },
  recommendationIcon: {
    marginRight: theme.spacing.sm,
  },
  recommendationText: {
    flex: 1,
    fontSize: 13,
    color: colors.text.primary,
    lineHeight: 18,
  },
  milestonesTimeline: {
    marginTop: theme.spacing.sm,
  },
  timelineTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.text.secondary,
    marginBottom: theme.spacing.sm,
  },
  timelineItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.sm,
  },
  timelineDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  timelineContent: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timelinePercentage: {
    fontSize: 13,
    fontWeight: '700',
    color: colors.text.primary,
    width: 40,
  },
  timelineAmount: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.text.primary,
    flex: 1,
  },
  timelineDate: {
    fontSize: 12,
    color: colors.text.secondary,
  },
});
