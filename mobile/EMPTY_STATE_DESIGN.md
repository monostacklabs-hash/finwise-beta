# Empty State Design System

Modern, clean empty state pattern for FinWise mobile app.

## Design Pattern

```tsx
<View style={styles.emptyState}>
  <View style={styles.emptyContent}>
    {/* Icon Container */}
    <View style={[styles.emptyIconContainer, { backgroundColor: `${colors.primary[500]}20` }]}>
      <Ionicons name="icon-name" size={40} color={colors.primary[500]} />
    </View>
    
    {/* Title */}
    <Text style={styles.emptyTitle}>Action-Oriented Title</Text>
    
    {/* Description */}
    <Text style={styles.emptyText}>
      Clear, concise description of what the user can do
    </Text>
    
    {/* CTA Button */}
    <TouchableOpacity 
      style={styles.emptyButton}
      onPress={handleAction}
      activeOpacity={0.7}
    >
      <Ionicons name="add-circle" size={20} color={colors.white} />
      <Text style={styles.emptyButtonText}>Action Text</Text>
    </TouchableOpacity>
  </View>
</View>
```

## Styles

```tsx
emptyState: {
  flex: 1,
  justifyContent: 'center',
  alignItems: 'center',
  padding: theme.spacing.xl,
},
emptyContent: {
  alignItems: 'center',
  maxWidth: 320,
},
emptyIconContainer: {
  width: 80,
  height: 80,
  borderRadius: theme.radius.xl,
  justifyContent: 'center',
  alignItems: 'center',
  marginBottom: theme.spacing.lg,
},
emptyTitle: {
  fontSize: 22,
  fontWeight: '700',
  color: colors.text.primary,
  marginTop: theme.spacing.lg,
  marginBottom: theme.spacing.sm,
},
emptyText: {
  fontSize: 15,
  color: colors.text.secondary,
  textAlign: 'center',
  lineHeight: 22,
  marginBottom: theme.spacing.xl,
},
emptyButton: {
  flexDirection: 'row',
  alignItems: 'center',
  gap: 8,
  backgroundColor: colors.primary[500],
  paddingHorizontal: 24,
  paddingVertical: 14,
  borderRadius: theme.radius.full,
},
emptyButtonText: {
  fontSize: 16,
  fontWeight: '600',
  color: colors.white,
},
```

## Guidelines

### Icon
- Size: 40px
- Container: 80x80px with 20% opacity background
- Use outline style icons
- Color: primary[500]

### Title
- Action-oriented (e.g., "Track Your Money", "Set Your Goals")
- Font: 22px, bold (700)
- Color: text.primary
- Keep it short (2-4 words)

### Description
- Clear explanation of what user can do
- Font: 15px, regular
- Color: text.secondary
- Line height: 22px
- Max width: 320px
- 2 lines max

### Button
- Full rounded (pill shape)
- Icon + text combination
- Icon size: 20px
- Text: 16px, semibold (600)
- Padding: 24px horizontal, 14px vertical
- Background: primary[500]
- Include haptic feedback on press

## Content Guidelines

### ❌ Avoid
- "No X Yet" (negative framing)
- "Connect" or "Link" (implies third-party integration)
- Technical jargon
- Passive voice

### ✅ Use
- Action verbs (Track, Set, Add, Create)
- User-entered data language
- Clear next steps
- Benefit-focused copy

## Examples

### Accounts
- Title: "Track Your Money"
- Description: "Add your checking, savings, credit cards, and other accounts to get started"
- Button: "Add Account"

### Goals
- Title: "Set Your Goals"
- Description: "Create savings goals and track your progress toward what matters most"
- Button: "Create Goal"

### Budgets
- Title: "Plan Your Spending"
- Description: "Set monthly budgets for different categories to stay on track"
- Button: "Create Budget"

### Transactions
- Title: "Record Your Spending"
- Description: "Add income and expenses to see where your money goes"
- Button: "Add Transaction"
