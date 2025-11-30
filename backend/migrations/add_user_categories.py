"""
Migration: Add user-specific categories table and seed existing users
Run this script to add the categories table and populate it for existing users
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.session import get_db, engine
from app.database.models import Base, User, Category
from app.services.category_manager import CategoryManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration():
    """Run the migration"""
    logger.info("Starting migration: Add user categories")
    
    # Create categories table
    logger.info("Creating categories table...")
    Base.metadata.create_all(bind=engine, tables=[Category.__table__])
    logger.info("✅ Categories table created")
    
    # Get all existing users
    db = next(get_db())
    try:
        users = db.query(User).all()
        logger.info(f"Found {len(users)} existing users")
        
        # Seed categories for each user
        for user in users:
            logger.info(f"Seeding categories for user {user.email}...")
            try:
                count = CategoryManager.seed_default_categories(user.id, db)
                logger.info(f"  ✅ Seeded {count} categories for {user.email}")
            except Exception as e:
                logger.error(f"  ❌ Failed to seed categories for {user.email}: {e}")
        
        logger.info("✅ Migration completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_migration()
