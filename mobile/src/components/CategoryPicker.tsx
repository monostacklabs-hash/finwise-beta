/**
 * Category Picker - Hierarchical Category Selection
 * Supports parent > child > grandchild navigation
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { GlassCard } from './GlassCard';
import { colors } from '../constants/colors';
import { theme } from '../constants/theme';
import { financialService } from '../services/financial';
import type { Category } from '../types';

interface CategoryPickerProps {
  onSelect: (category: Category, fullPath: string) => void;
  selectedCategory?: string;
  showPath?: boolean;
}

export const CategoryPicker: React.FC<CategoryPickerProps> = ({
  onSelect,
  selectedCategory,
  showPath = true,
}) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [hierarchy, setHierarchy] = useState<Record<string, Category[]>>({});
  const [loading, setLoading] = useState(true);
  const [currentLevel, setCurrentLevel] = useState<Category[]>([]);
  const [breadcrumb, setBreadcrumb] = useState<Category[]>([]);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await financialService.getCategories();
      setCategories(response.categories);
      setHierarchy(response.hierarchy);
      
      // Show root categories (no parent)
      const rootCategories = response.categories.filter(c => !c.parent_category);
      setCurrentLevel(rootCategories);
    } catch (error) {
      console.error('Failed to load categories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryPress = (category: Category) => {
    const children = hierarchy[category.name] || [];
    
    if (children.length > 0) {
      // Has children, navigate deeper
      setBreadcrumb([...breadcrumb, category]);
      setCurrentLevel(children);
    } else {
      // Leaf category, select it
      const fullPath = [...breadcrumb, category].map(c => c.display_name).join(' > ');
      onSelect(category, fullPath);
    }
  };

  const handleBreadcrumbPress = (index: number) => {
    if (index === -1) {
      // Go to root
      const rootCategories = categories.filter(c => !c.parent_category);
      setCurrentLevel(rootCategories);
      setBreadcrumb([]);
    } else {
      // Go to specific level
      const newBreadcrumb = breadcrumb.slice(0, index + 1);
      const category = breadcrumb[index];
      const children = hierarchy[category.name] || [];
      setBreadcrumb(newBreadcrumb);
      setCurrentLevel(children);
    }
  };

  const getCategoryIcon = (category: Category): keyof typeof Ionicons.glyphMap => {
    // Map category icons to Ionicons
    const iconMap: Record<string, keyof typeof Ionicons.glyphMap> = {
      'shopping-cart': 'cart-outline',
      'utensils': 'restaurant-outline',
      'burger': 'fast-food-outline',
      'coffee': 'cafe-outline',
      'gas-pump': 'car-outline',
      'car': 'car-outline',
      'bus': 'bus-outline',
      'parking': 'car-outline',
      'film': 'film-outline',
      'ticket': 'ticket-outline',
      'music': 'musical-notes-outline',
      'gamepad': 'game-controller-outline',
      'tshirt': 'shirt-outline',
      'laptop': 'laptop-outline',
      'home': 'home-outline',
      'shopping-bag': 'bag-outline',
      'pills': 'medical-outline',
      'stethoscope': 'fitness-outline',
      'tooth': 'happy-outline',
      'heart': 'heart-outline',
      'bolt': 'flash-outline',
      'wifi': 'wifi-outline',
      'phone': 'call-outline',
      'dumbbell': 'barbell-outline',
      'basketball': 'basketball-outline',
      'graduation-cap': 'school-outline',
      'book': 'book-outline',
      'shield': 'shield-outline',
      'dollar-sign': 'cash-outline',
      'briefcase': 'briefcase-outline',
      'chart-line': 'trending-up-outline',
      'gift': 'gift-outline',
      'hand-holding-heart': 'heart-outline',
      'spa': 'flower-outline',
      'paw': 'paw-outline',
      'plane': 'airplane-outline',
      'repeat': 'repeat-outline',
      'question': 'help-circle-outline',
    };
    
    return iconMap[category.icon || 'question'] || 'pricetag-outline';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary[500]} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Breadcrumb Navigation */}
      {showPath && breadcrumb.length > 0 && (
        <View style={styles.breadcrumbContainer}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <TouchableOpacity
              onPress={() => handleBreadcrumbPress(-1)}
              style={styles.breadcrumbItem}
            >
              <Ionicons name="home-outline" size={16} color={colors.primary[500]} />
            </TouchableOpacity>
            {breadcrumb.map((cat, index) => (
              <View key={cat.id} style={styles.breadcrumbWrapper}>
                <Ionicons name="chevron-forward" size={16} color={colors.text.tertiary} />
                <TouchableOpacity
                  onPress={() => handleBreadcrumbPress(index)}
                  style={styles.breadcrumbItem}
                >
                  <Text style={styles.breadcrumbText}>{cat.display_name}</Text>
                </TouchableOpacity>
              </View>
            ))}
          </ScrollView>
        </View>
      )}

      {/* Category List */}
      <ScrollView style={styles.categoryList} showsVerticalScrollIndicator={false}>
        {currentLevel.map((category) => {
          const hasChildren = (hierarchy[category.name] || []).length > 0;
          const isSelected = selectedCategory === category.name;
          
          return (
            <TouchableOpacity
              key={category.id}
              onPress={() => handleCategoryPress(category)}
              activeOpacity={0.7}
            >
              <GlassCard
                variant="medium"
                style={[
                  styles.categoryCard,
                  isSelected && styles.categoryCardSelected,
                ]}
              >
                <View
                  style={[
                    styles.categoryIcon,
                    { backgroundColor: category.color ? `${category.color}20` : `${colors.primary[500]}20` },
                  ]}
                >
                  <Ionicons
                    name={getCategoryIcon(category)}
                    size={24}
                    color={category.color || colors.primary[500]}
                  />
                </View>
                
                <View style={styles.categoryInfo}>
                  <Text style={styles.categoryName}>{category.display_name}</Text>
                  {category.usage_count !== undefined && category.usage_count > 0 && (
                    <Text style={styles.categoryUsage}>Used {category.usage_count} times</Text>
                  )}
                </View>
                
                {hasChildren && (
                  <Ionicons name="chevron-forward" size={20} color={colors.text.tertiary} />
                )}
                
                {isSelected && !hasChildren && (
                  <Ionicons name="checkmark-circle" size={20} color={colors.income.primary} />
                )}
              </GlassCard>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: theme.spacing.xl,
  },
  breadcrumbContainer: {
    paddingHorizontal: theme.spacing.md,
    paddingVertical: theme.spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border.light,
  },
  breadcrumbWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  breadcrumbItem: {
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.xs,
  },
  breadcrumbText: {
    fontSize: 14,
    color: colors.primary[500],
    fontWeight: '600',
  },
  categoryList: {
    flex: 1,
    padding: theme.spacing.md,
  },
  categoryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: theme.spacing.md,
    marginBottom: theme.spacing.sm,
    gap: theme.spacing.md,
  },
  categoryCardSelected: {
    borderWidth: 2,
    borderColor: colors.income.primary,
  },
  categoryIcon: {
    width: 48,
    height: 48,
    borderRadius: theme.radius.md,
    justifyContent: 'center',
    alignItems: 'center',
  },
  categoryInfo: {
    flex: 1,
  },
  categoryName: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.text.primary,
    marginBottom: 2,
  },
  categoryUsage: {
    fontSize: 12,
    color: colors.text.secondary,
  },
});
