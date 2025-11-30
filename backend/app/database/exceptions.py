from typing import Optional, Any
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, DataError

class FinancialAgentBaseError(Exception):
    """Base exception for all financial agent errors."""
    def __init__(self, message: str, context: Optional[dict] = None):
        super().__init__(message)
        self.context = context or {}

class DatabaseOperationError(FinancialAgentBaseError):
    """Exception raised for errors during database operations."""
    def __init__(self, message: str, operation: str, details: Optional[Any] = None):
        super().__init__(message, context={
            "operation": operation,
            "details": str(details) if details else None
        })

class ConstraintViolationError(DatabaseOperationError):
    """Exception raised when database constraints are violated."""
    def __init__(self, constraint_type: str, details: Optional[Any] = None):
        super().__init__(
            f"Database constraint '{constraint_type}' violated",
            operation="constraint_check",
            details=details
        )

class InvalidInputError(FinancialAgentBaseError):
    """Exception raised for invalid input data."""
    def __init__(self, field: str, value: Any, reason: str):
        super().__init__(
            f"Invalid input for {field}: {value}. Reason: {reason}",
            context={
                "field": field,
                "value": str(value),
                "reason": reason
            }
        )

class AuthenticationError(FinancialAgentBaseError):
    """Exception raised for authentication-related errors."""
    def __init__(self, message: str, user_id: Optional[str] = None):
        super().__init__(message, context={"user_id": user_id})

def handle_sqlalchemy_error(error: SQLAlchemyError, operation: str):
    """
    Convert SQLAlchemy errors to our custom exceptions.

    Args:
        error (SQLAlchemyError): The original SQLAlchemy error
        operation (str): The database operation being performed

    Raises:
        DatabaseOperationError or ConstraintViolationError
    """
    if isinstance(error, IntegrityError):
        raise ConstraintViolationError(
            constraint_type="database_integrity",
            details=str(error)
        ) from error

    if isinstance(error, DataError):
        raise DatabaseOperationError(
            message="Data type or value error in database operation",
            operation=operation,
            details=str(error)
        ) from error

    raise DatabaseOperationError(
        message="Unexpected database error",
        operation=operation,
        details=str(error)
    ) from error