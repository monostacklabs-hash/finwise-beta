/**
 * Export Screen - Export Financial Data
 * Glassmorphic Finance Theme - TIER 1 Feature
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  TouchableOpacity,
  Pressable,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from '../components/GlassCard';
import { Button } from '../components/Button';
import { Input } from '../components/Input';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import * as Haptics from 'expo-haptics';
import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system';

export const ExportScreen: React.FC = () => {
  const [exportType, setExportType] = useState<'transactions' | 'report' | 'tax'>('transactions');
  const [loading, setLoading] = useState(false);

  // Transactions CSV
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  // PDF Report
  const [reportYear, setReportYear] = useState(new Date().getFullYear().toString());
  const [reportMonth, setReportMonth] = useState((new Date().getMonth() + 1).toString());

  // Tax Document
  const [taxYear, setTaxYear] = useState((new Date().getFullYear() - 1).toString());

  const handleExportTransactions = async () => {
    if (!startDate || !endDate) {
      Alert.alert('Error', 'Please enter both start and end dates');
      return;
    }

    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const csvData = await financialService.exportTransactionsCSV(startDate, endDate);

      // Save to file
      const filename = `transactions_${startDate}_to_${endDate}.csv`;
      const fileUri = FileSystem.documentDirectory + filename;
      await FileSystem.writeAsStringAsync(fileUri, csvData);

      // Share the file
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(fileUri, {
          mimeType: 'text/csv',
          dialogTitle: 'Export Transactions',
        });
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        Alert.alert('Success', 'Transactions exported successfully!');
      } else {
        Alert.alert('Success', `Saved to ${fileUri}`);
      }
    } catch (error: any) {
      console.error('Export transactions error:', error);
      Alert.alert('Error', error.message || 'Failed to export transactions');
    } finally {
      setLoading(false);
    }
  };

  const handleExportReport = async () => {
    const year = parseInt(reportYear);
    const month = parseInt(reportMonth);

    if (isNaN(year) || isNaN(month) || month < 1 || month > 12) {
      Alert.alert('Error', 'Please enter valid year and month (1-12)');
      return;
    }

    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const htmlData = await financialService.exportFinancialReport(year, month);

      // Save to file
      const filename = `financial_report_${year}_${month.toString().padStart(2, '0')}.html`;
      const fileUri = FileSystem.documentDirectory + filename;
      await FileSystem.writeAsStringAsync(fileUri, htmlData);

      // Share the file
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(fileUri, {
          mimeType: 'text/html',
          dialogTitle: 'Financial Report',
        });
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        Alert.alert('Success', 'Financial report generated successfully!');
      } else {
        Alert.alert('Success', `Saved to ${fileUri}`);
      }
    } catch (error: any) {
      console.error('Export report error:', error);
      Alert.alert('Error', error.message || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const handleExportTaxDocument = async () => {
    const year = parseInt(taxYear);

    if (isNaN(year) || year < 2000 || year > new Date().getFullYear()) {
      Alert.alert('Error', 'Please enter a valid tax year');
      return;
    }

    setLoading(true);
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    try {
      const csvData = await financialService.exportTaxDocument(year);

      // Save to file
      const filename = `tax_document_${year}.csv`;
      const fileUri = FileSystem.documentDirectory + filename;
      await FileSystem.writeAsStringAsync(fileUri, csvData);

      // Share the file
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(fileUri, {
          mimeType: 'text/csv',
          dialogTitle: `Tax Document ${year}`,
        });
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        Alert.alert('Success', 'Tax document exported successfully!');
      } else {
        Alert.alert('Success', `Saved to ${fileUri}`);
      }
    } catch (error: any) {
      console.error('Export tax document error:', error);
      Alert.alert('Error', error.message || 'Failed to export tax document');
    } finally {
      setLoading(false);
    }
  };

  const renderTransactionsExport = () => (
    <GlassCard variant="medium" style={styles.exportCard}>
      <View style={styles.cardHeader}>
        <Ionicons name="document-text" size={32} color={colors.info.primary} />
        <View style={styles.cardHeaderText}>
          <Text style={styles.cardTitle}>Transactions CSV</Text>
          <Text style={styles.cardDescription}>
            Export all transactions within a date range
          </Text>
        </View>
      </View>

      <View style={styles.inputsContainer}>
        <Input
          label="Start Date (YYYY-MM-DD)"
          value={startDate}
          onChangeText={setStartDate}
          placeholder="2025-01-01"
        />
        <Input
          label="End Date (YYYY-MM-DD)"
          value={endDate}
          onChangeText={setEndDate}
          placeholder="2025-12-31"
        />
      </View>

      <Button
        title="Export Transactions"
        onPress={handleExportTransactions}
        loading={loading}
        variant="primary"
        icon="download"
      />
    </GlassCard>
  );

  const renderReportExport = () => (
    <GlassCard variant="medium" style={styles.exportCard}>
      <View style={styles.cardHeader}>
        <Ionicons name="bar-chart" size={32} color={colors.income.primary} />
        <View style={styles.cardHeaderText}>
          <Text style={styles.cardTitle}>Financial Report</Text>
          <Text style={styles.cardDescription}>
            Generate comprehensive monthly report (HTML)
          </Text>
        </View>
      </View>

      <View style={styles.inputsContainer}>
        <View style={styles.twoColumnInputs}>
          <View style={styles.halfWidth}>
            <Input
              label="Year"
              value={reportYear}
              onChangeText={setReportYear}
              keyboardType="number-pad"
              placeholder="2025"
            />
          </View>
          <View style={styles.halfWidth}>
            <Input
              label="Month (1-12)"
              value={reportMonth}
              onChangeText={setReportMonth}
              keyboardType="number-pad"
              placeholder="1"
            />
          </View>
        </View>
      </View>

      <Button
        title="Generate Report"
        onPress={handleExportReport}
        loading={loading}
        variant="primary"
        icon="document"
      />
    </GlassCard>
  );

  const renderTaxExport = () => (
    <GlassCard variant="medium" style={styles.exportCard}>
      <View style={styles.cardHeader}>
        <Ionicons name="calculator" size={32} color={colors.warning.primary} />
        <View style={styles.cardHeaderText}>
          <Text style={styles.cardTitle}>Tax Document</Text>
          <Text style={styles.cardDescription}>
            Export income & deductible expenses for tax filing
          </Text>
        </View>
      </View>

      <View style={styles.inputsContainer}>
        <Input
          label="Tax Year"
          value={taxYear}
          onChangeText={setTaxYear}
          keyboardType="number-pad"
          placeholder="2024"
        />
        <Text style={styles.helperText}>
          Includes all income and categorized deductible expenses
        </Text>
      </View>

      <Button
        title="Export Tax Document"
        onPress={handleExportTaxDocument}
        loading={loading}
        variant="primary"
        icon="download"
      />
    </GlassCard>
  );

  return (
    <View style={styles.container}>
      {/* Export Type Selector */}
      <View style={styles.typeSelector}>
        <Pressable
          style={[
            styles.typeButton,
            exportType === 'transactions' && styles.typeButtonActive,
          ]}
          onPress={() => {
            setExportType('transactions');
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          <Ionicons
            name="document-text"
            size={20}
            color={exportType === 'transactions' ? colors.info.primary : colors.gray[600]}
          />
          <Text style={[
            styles.typeButtonText,
            exportType === 'transactions' && styles.typeButtonTextActive,
          ]}>
            Transactions
          </Text>
        </Pressable>

        <Pressable
          style={[
            styles.typeButton,
            exportType === 'report' && styles.typeButtonActive,
          ]}
          onPress={() => {
            setExportType('report');
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          <Ionicons
            name="bar-chart"
            size={20}
            color={exportType === 'report' ? colors.income.primary : colors.gray[600]}
          />
          <Text style={[
            styles.typeButtonText,
            exportType === 'report' && styles.typeButtonTextActive,
          ]}>
            Report
          </Text>
        </Pressable>

        <Pressable
          style={[
            styles.typeButton,
            exportType === 'tax' && styles.typeButtonActive,
          ]}
          onPress={() => {
            setExportType('tax');
            Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          }}
        >
          <Ionicons
            name="calculator"
            size={20}
            color={exportType === 'tax' ? colors.warning.primary : colors.gray[600]}
          />
          <Text style={[
            styles.typeButtonText,
            exportType === 'tax' && styles.typeButtonTextActive,
          ]}>
            Tax
          </Text>
        </Pressable>
      </View>

      {/* Export Content */}
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {exportType === 'transactions' && renderTransactionsExport()}
        {exportType === 'report' && renderReportExport()}
        {exportType === 'tax' && renderTaxExport()}

        {/* Info Card */}
        <GlassCard variant="light" style={styles.infoCard}>
          <View style={styles.infoHeader}>
            <Ionicons name="information-circle" size={24} color={colors.info.primary} />
            <Text style={styles.infoTitle}>Export Information</Text>
          </View>
          <View style={styles.infoItems}>
            <View style={styles.infoItem}>
              <Ionicons name="checkmark-circle" size={16} color={colors.income.primary} />
              <Text style={styles.infoText}>
                All exports are generated in real-time from your data
              </Text>
            </View>
            <View style={styles.infoItem}>
              <Ionicons name="checkmark-circle" size={16} color={colors.income.primary} />
              <Text style={styles.infoText}>
                Files can be shared or saved to your device
              </Text>
            </View>
            <View style={styles.infoItem}>
              <Ionicons name="checkmark-circle" size={16} color={colors.income.primary} />
              <Text style={styles.infoText}>
                Tax documents are formatted for easy filing
              </Text>
            </View>
          </View>
        </GlassCard>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.secondary,
  },
  typeSelector: {
    flexDirection: 'row',
    gap: theme.spacing.sm,
    paddingHorizontal: theme.spacing.lg,
    paddingBottom: theme.spacing.lg,
  },
  typeButton: {
    flex: 1,
    flexDirection: 'column',
    alignItems: 'center',
    gap: theme.spacing.xs,
    padding: theme.spacing.md,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    borderColor: colors.border.light,
    backgroundColor: colors.background.secondary,
  },
  typeButtonActive: {
    backgroundColor: colors.glass.ultraLight,
    borderColor: colors.white,
  },
  typeButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.gray[600],
  },
  typeButtonTextActive: {
    color: colors.text.primary,
  },
  scrollContent: {
    padding: theme.spacing.lg,
    paddingTop: 0,
    gap: theme.spacing.lg,
    paddingBottom: theme.spacing.xxl,
  },
  exportCard: {
    padding: theme.spacing.lg,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.md,
    marginBottom: theme.spacing.lg,
  },
  cardHeaderText: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.text.primary,
    marginBottom: 4,
  },
  cardDescription: {
    fontSize: 14,
    color: colors.text.secondary,
    lineHeight: 20,
  },
  inputsContainer: {
    marginBottom: theme.spacing.lg,
  },
  twoColumnInputs: {
    flexDirection: 'row',
    gap: theme.spacing.md,
  },
  halfWidth: {
    flex: 1,
  },
  helperText: {
    fontSize: 12,
    color: colors.text.tertiary,
    marginTop: theme.spacing.xs,
  },
  infoCard: {
    padding: theme.spacing.lg,
  },
  infoHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: theme.spacing.sm,
    marginBottom: theme.spacing.md,
  },
  infoTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.text.primary,
  },
  infoItems: {
    gap: theme.spacing.sm,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: theme.spacing.xs,
  },
  infoText: {
    fontSize: 14,
    color: colors.text.secondary,
    flex: 1,
    lineHeight: 20,
  },
});
