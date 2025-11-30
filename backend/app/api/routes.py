# Add to the existing imports
from ..utils.validators import FinancialValidator, FinancialValidationError

class UpdateGoalProgressRequest(BaseModel):
    """Pydantic model for goal progress update"""
    amount: float = Field(
        ...,
        description="Amount to add to goal progress",
        gt=0,  # Must be positive
        le=1_000_000  # Maximum amount
    )
    date: Optional[str] = Field(
        default=None,
        description="Date of progress update (optional, ISO format)"
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional description for the progress update",
        max_length=500
    )

    @validator('amount')
    def validate_amount(cls, v):
        """Validate progress amount"""
        try:
            # Use financial validator to ensure amount is valid
            validated_amount = FinancialValidator.validate_amount(
                v,
                transaction_type='income',
                max_amount=1_000_000,
                precision=2
            )
            return validated_amount
        except FinancialValidationError as e:
            raise ValueError(str(e))

    @validator('date')
    def validate_date(cls, v):
        """Validate date format if provided"""
        if v is None:
            return v

        try:
            # Convert to datetime to validate format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError("Invalid date format. Use ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)")

    @validator('description')
    def validate_description(cls, v):
        """Sanitize description if provided"""
        if v is None:
            return v

        try:
            return FinancialValidator.sanitize_description(
                v,
                max_length=500,
                allow_html=False
            )
        except FinancialValidationError as e:
            raise ValueError(str(e))

@router.put("/goals/{goal_id}/progress")
def update_goal_progress(
    goal_id: str,
    request: UpdateGoalProgressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update goal progress with comprehensive validation"""
    from ..database.models import GoalStatus, GoalProgressEntry
    from ..database.exceptions import handle_sqlalchemy_error
    from sqlalchemy.exc import SQLAlchemyError

    try:
        # Find the goal and verify ownership
        goal = db.query(Goal).filter(
            Goal.id == goal_id,
            Goal.user_id == current_user.id
        ).first()

        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )

        # Validate progress won't exceed target
        proposed_total = goal.current_amount + request.amount
        if proposed_total > goal.target_amount:
            # Option 1: Truncate to target amount
            actual_amount = goal.target_amount - goal.current_amount
            logger.warning(f"Progress amount exceeds goal. Truncating to {actual_amount}")
        else:
            actual_amount = request.amount

        # Update goal amount
        goal.current_amount += actual_amount

        # Determine goal status
        progress_percentage = (goal.current_amount / goal.target_amount) * 100
        if progress_percentage >= 100:
            goal.status = GoalStatus.completed
            goal.completed_at = datetime.utcnow()

        # Create progress entry for audit trail
        progress_entry = GoalProgressEntry(
            id=str(uuid.uuid4()),
            goal_id=goal.id,
            user_id=current_user.id,
            amount=actual_amount,
            date=datetime.fromisoformat(request.date.replace('Z', '+00:00')) if request.date else datetime.utcnow(),
            description=request.description
        )
        db.add(progress_entry)

        # Commit changes
        db.commit()
        db.refresh(goal)
        db.refresh(progress_entry)

        # Prepare response
        return {
            "id": goal.id,
            "name": goal.name,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount,
            "progress_percentage": round(progress_percentage, 2),
            "target_date": goal.target_date.isoformat(),
            "status": goal.status.value,
            "progress_entry_id": progress_entry.id,
            "message": "Goal progress updated successfully" +
                      (" (goal completed!)" if goal.status == GoalStatus.completed else "")
        }

    except SQLAlchemyError as db_error:
        # Use custom error handler for SQLAlchemy errors
        handle_sqlalchemy_error(db_error, "update_goal_progress")

    except ValueError as validation_error:
        # Handle validation errors from Pydantic
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(validation_error)
        )

    except Exception as unexpected_error:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in goal progress update: {unexpected_error}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating goal progress."
        )