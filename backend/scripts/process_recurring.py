#!/usr/bin/env python3
"""
Manual script to process recurring transactions and reminders
Use this for testing or manual triggering
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.connection import SessionLocal
from app.services.recurring_scheduler import RecurringScheduler
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Process recurring transactions and reminders"""
    db = SessionLocal()
    
    try:
        logger.info("=" * 60)
        logger.info("Starting recurring transaction processing")
        logger.info("=" * 60)
        
        # Process due transactions
        logger.info("\n1. Processing due transactions...")
        transaction_stats = RecurringScheduler.process_due_transactions(db)
        logger.info(f"   ✓ Processed: {transaction_stats['processed']}")
        logger.info(f"   ✓ Created transactions: {transaction_stats['created_transactions']}")
        logger.info(f"   ✗ Errors: {transaction_stats['errors']}")
        
        # Process bill reminders
        logger.info("\n2. Processing bill reminders...")
        reminder_stats = RecurringScheduler.process_bill_reminders(db)
        logger.info(f"   ✓ Processed: {reminder_stats['processed']}")
        logger.info(f"   ✓ Reminders created: {reminder_stats['reminders_created']}")
        logger.info(f"   ✗ Errors: {reminder_stats['errors']}")
        
        logger.info("\n" + "=" * 60)
        logger.info("Processing complete!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"Fatal error during processing: {e}", exc_info=True)
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
