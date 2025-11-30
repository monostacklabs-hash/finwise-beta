from decimal import Decimal, InvalidOperation
from typing import Union, Literal
import re

class FinancialValidationError(ValueError):
    """Custom exception for financial validation errors"""
    pass

class FinancialValidator:
    """Comprehensive validator for financial operations"""

    @staticmethod
    def validate_amount(
        amount: Union[float, int, str],
        transaction_type: Literal['income', 'expense', 'transfer'] = None,
        allow_zero: bool = False,
        max_amount: float = 1_000_000,
        precision: int = 2
    ) -> float:
        """
        Validate financial amount with comprehensive checks

        Args:
            amount: The amount to validate
            transaction_type: Type of transaction (optional)
            allow_zero: Whether zero is allowed
            max_amount: Maximum allowed amount
            precision: Decimal precision to round to

        Raises:
            FinancialValidationError: If validation fails
        """
        # Convert to string to handle various input types
        amount_str = str(amount).strip()

        # Check if amount is a valid number
        try:
            # Use Decimal for precise decimal handling
            decimal_amount = Decimal(amount_str)
        except (InvalidOperation, TypeError):
            raise FinancialValidationError(f"Invalid amount format: {amount}")

        # Convert to float for final processing
        float_amount = float(decimal_amount.quantize(Decimal(f'0.{"0" * precision}'))

        # Zero check
        if not allow_zero and float_amount == 0:
            raise FinancialValidationError("Amount cannot be zero")

        # Negative check based on transaction type
        if transaction_type == 'income' and float_amount < 0:
            raise FinancialValidationError("Income amount cannot be negative")
        elif transaction_type == 'expense' and float_amount < 0:
            raise FinancialValidationError("Expense amount cannot be negative")

        # Maximum amount check
        if float_amount > max_amount:
            raise FinancialValidationError(f"Amount exceeds maximum allowed: ${max_amount:,.2f}")

        # Precision check
        if len(str(float_amount).split('.')[-1]) > precision:
            raise FinancialValidationError(f"Amount can only have {precision} decimal places")

        return float_amount

    @staticmethod
    def validate_percentage(
        percentage: Union[float, int, str],
        min_value: float = 0,
        max_value: float = 100
    ) -> float:
        """
        Validate percentage values

        Args:
            percentage: Percentage to validate
            min_value: Minimum allowed percentage
            max_value: Maximum allowed percentage

        Raises:
            FinancialValidationError: If validation fails
        """
        try:
            # Convert to float
            float_percentage = float(str(percentage).strip())
        except (ValueError, TypeError):
            raise FinancialValidationError(f"Invalid percentage format: {percentage}")

        # Range check
        if float_percentage < min_value or float_percentage > max_value:
            raise FinancialValidationError(
                f"Percentage must be between {min_value} and {max_value}"
            )

        return float_percentage

    @staticmethod
    def sanitize_description(
        description: str,
        max_length: int = 500,
        allow_html: bool = False
    ) -> str:
        """
        Sanitize and validate description

        Args:
            description: Text to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML tags

        Returns:
            Sanitized description

        Raises:
            FinancialValidationError: If description is invalid
        """
        # Trim whitespace
        description = description.strip()

        # Length check
        if not description:
            raise FinancialValidationError("Description cannot be empty")

        if len(description) > max_length:
            raise FinancialValidationError(
                f"Description exceeds maximum length of {max_length} characters"
            )

        # HTML tag removal if not allowed
        if not allow_html:
            description = re.sub(r'<[^>]+>', '', description)

        return description