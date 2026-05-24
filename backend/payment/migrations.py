"""
Database Migrations for Payment System
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creates all payment-related database tables.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, engine
from .models import (
    User, Subscription, Payment, Invoice, 
    UsageRecord, PaymentMethod
)

logger = logging.getLogger(__name__)


def create_payment_tables():
    """
    Create all payment-related database tables.
    
    This will create:
    - users
    - subscriptions
    - payments
    - invoices
    - usage_records
    - payment_methods
    """
    try:
        logger.info("Creating payment system database tables...")
        
        # Import all models to ensure they're registered with Base
        from .models import (
            User, Subscription, Payment, Invoice,
            UsageRecord, PaymentMethod
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Payment system tables created successfully!")
        logger.info("Tables created:")
        logger.info("  - users")
        logger.info("  - subscriptions")
        logger.info("  - payments")
        logger.info("  - invoices")
        logger.info("  - usage_records")
        logger.info("  - payment_methods")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create payment tables: {e}", exc_info=True)
        return False


def drop_payment_tables():
    """
    Drop all payment-related database tables.
    
    WARNING: This will delete all payment data!
    """
    try:
        logger.warning("⚠️  Dropping payment system database tables...")
        
        # Import all models
        from .models import (
            User, Subscription, Payment, Invoice,
            UsageRecord, PaymentMethod
        )
        
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        
        logger.info("✅ Payment system tables dropped successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to drop payment tables: {e}", exc_info=True)
        return False


def migrate_payment_system():
    """
    Run payment system migrations.
    
    This is the main migration function that should be called
    to set up the payment system database.
    """
    logger.info("="*80)
    logger.info("PAYMENT SYSTEM MIGRATION")
    logger.info("="*80)
    
    success = create_payment_tables()
    
    if success:
        logger.info("="*80)
        logger.info("✅ PAYMENT SYSTEM MIGRATION COMPLETE")
        logger.info("="*80)
    else:
        logger.error("="*80)
        logger.error("❌ PAYMENT SYSTEM MIGRATION FAILED")
        logger.error("="*80)
    
    return success


if __name__ == "__main__":
    # Run migrations when this file is executed directly
    print("Running payment system migrations...")
    success = migrate_payment_system()
    
    if success:
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        exit(1)

