"""Database connection and migration utilities."""

import os
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .models import Base, db_config


class DatabaseManager:
    """Manages database operations, migrations, and backups."""
    
    def __init__(self, database_path: Optional[str] = None):
        """Initialize database manager.
        
        Args:
            database_path: Optional custom database path
        """
        if database_path:
            # Update global config with custom path
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            db_config.database_url = f"sqlite:///{database_path}"
            db_config.engine = create_engine(db_config.database_url)
            db_config.SessionLocal = sessionmaker(bind=db_config.engine)
    
    def get_database_path(self) -> str:
        """Get the current database file path."""
        if "sqlite" in db_config.database_url:
            return db_config.database_url.replace("sqlite:///", "")
        raise ValueError("Only SQLite databases are supported")
    
    def ensure_database_directory(self) -> None:
        """Ensure the database directory exists with proper permissions."""
        db_path = Path(self.get_database_path())
        db_dir = db_path.parent
        
        # Create directory if it doesn't exist
        db_dir.mkdir(parents=True, exist_ok=True)
        
        # Set macOS-appropriate permissions (user only)
        try:
            os.chmod(db_dir, 0o700)  # rwx------
        except OSError:
            # Continue if we can't set permissions
            pass
    
    def database_exists(self) -> bool:
        """Check if the database file exists."""
        try:
            db_path = Path(self.get_database_path())
            return db_path.exists() and db_path.is_file()
        except (ValueError, OSError):
            return False
    
    def create_backup(self, backup_suffix: Optional[str] = None) -> Optional[str]:
        """Create a backup of the database file.
        
        Args:
            backup_suffix: Optional suffix for backup filename
            
        Returns:
            Path to backup file or None if backup failed
        """
        if not self.database_exists():
            return None
            
        try:
            db_path = Path(self.get_database_path())
            
            if backup_suffix:
                backup_name = f"{db_path.stem}_{backup_suffix}{db_path.suffix}"
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"
            
            backup_path = db_path.parent / backup_name
            shutil.copy2(db_path, backup_path)
            
            # Set backup file permissions
            os.chmod(backup_path, 0o600)  # rw-------
            
            return str(backup_path)
            
        except (OSError, shutil.Error) as e:
            print(f"Warning: Failed to create database backup: {e}")
            return None
    
    def initialize_database(self, create_backup: bool = True) -> bool:
        """Initialize the database with tables and initial data.
        
        Args:
            create_backup: Whether to create backup before initialization
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.ensure_database_directory()
            
            # Create backup if database exists
            if create_backup and self.database_exists():
                backup_path = self.create_backup("pre_init")
                if backup_path:
                    print(f"Database backup created: {backup_path}")
            
            # Create all tables
            db_config.create_tables()
            
            # Set database file permissions (SQLite only)
            if self.database_exists():
                db_path = Path(self.get_database_path())
                os.chmod(db_path, 0o600)  # rw-------
            
            return True
            
        except SQLAlchemyError as e:
            print(f"Database initialization failed: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during database initialization: {e}")
            return False
    
    def verify_database_integrity(self) -> bool:
        """Verify database integrity and connectivity.
        
        Returns:
            True if database is accessible and intact
        """
        try:
            session = db_config.SessionLocal()
            try:
                # Check if required tables exist
                from sqlalchemy import inspect, text
                inspector = inspect(session.bind)
                tables = inspector.get_table_names()
                
                # Check for required core tables
                required_tables = ['habits', 'tracking_entries', 'config']
                if not all(table in tables for table in required_tables):
                    return False
                
                # Check if Phase 2A migration is needed
                phase_2a_tables = ['categories', 'habit_categories', 'habit_history']
                missing_2a_tables = [table for table in phase_2a_tables if table not in tables]
                
                if missing_2a_tables:
                    # Run Phase 2A migration
                    if not self.migrate_to_phase_2a():
                        return False
                
                # Check if Phase 2C migration is needed
                phase_2c_tables = ['templates']
                missing_2c_tables = [table for table in phase_2c_tables if table not in tables]
                
                if missing_2c_tables:
                    # Run Phase 2C migration
                    if not self.migrate_to_phase_2c():
                        return False
                
                # Try a simple query on the habits table
                session.execute(text("SELECT COUNT(*) FROM habits")).fetchone()
                return True
            finally:
                session.close()
                
        except SQLAlchemyError:
            return False
    
    def migrate_to_phase_2a(self) -> bool:
        """Migrate database to Phase 2A schema (add new tables).
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            print("Running Phase 2A migration (adding new tables)...")
            
            # Create backup before migration
            backup_path = self.create_backup("pre_phase_2a_migration")
            if backup_path:
                print(f"Backup created: {backup_path}")
            
            # Import new models to ensure they're registered
            from .models import Category, HabitHistory, habit_categories
            
            # Create only the new tables
            session = db_config.SessionLocal()
            try:
                # Create new tables
                Category.__table__.create(db_config.engine, checkfirst=True)
                HabitHistory.__table__.create(db_config.engine, checkfirst=True)
                habit_categories.create(db_config.engine, checkfirst=True)
                
                print("Phase 2A migration completed successfully")
                return True
                
            except SQLAlchemyError as e:
                print(f"Phase 2A migration failed: {e}")
                return False
            finally:
                session.close()
                
        except Exception as e:
            print(f"Unexpected error during Phase 2A migration: {e}")
            return False
    
    def migrate_to_phase_2c(self) -> bool:
        """Migrate database to Phase 2C schema (add templates table).
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            print("Running Phase 2C migration (adding templates table)...")
            
            # Create backup before migration
            backup_path = self.create_backup("pre_phase_2c_migration")
            if backup_path:
                print(f"Backup created: {backup_path}")
            
            # Import new models to ensure they're registered
            from .models import Template
            
            # Create only the new tables
            session = db_config.SessionLocal()
            try:
                # Create templates table
                Template.__table__.create(db_config.engine, checkfirst=True)
                
                print("Phase 2C migration completed successfully")
                return True
                
            except SQLAlchemyError as e:
                print(f"Phase 2C migration failed: {e}")
                return False
            finally:
                session.close()
                
        except Exception as e:
            print(f"Unexpected error during Phase 2C migration: {e}")
            return False
    
    def check_migration_status(self) -> dict:
        """Check which migrations have been applied.
        
        Returns:
            Dictionary with migration status
        """
        status = {
            "core_tables": False,
            "phase_2a_tables": False,
            "phase_2c_tables": False,
            "missing_tables": []
        }
        
        try:
            session = db_config.SessionLocal()
            try:
                from sqlalchemy import inspect
                inspector = inspect(session.bind)
                tables = inspector.get_table_names()
                
                # Check core tables
                core_tables = ['habits', 'tracking_entries', 'config']
                status["core_tables"] = all(table in tables for table in core_tables)
                
                # Check Phase 2A tables
                phase_2a_tables = ['categories', 'habit_categories', 'habit_history']
                status["phase_2a_tables"] = all(table in tables for table in phase_2a_tables)
                
                # Check Phase 2C tables
                phase_2c_tables = ['templates']
                status["phase_2c_tables"] = all(table in tables for table in phase_2c_tables)
                
                # List missing tables
                all_expected_tables = core_tables + phase_2a_tables + phase_2c_tables
                status["missing_tables"] = [table for table in all_expected_tables if table not in tables]
                
            finally:
                session.close()
                
        except SQLAlchemyError:
            status["error"] = "Database connectivity issues"
            
        return status
    
    def get_database_stats(self) -> dict:
        """Get basic database statistics.
        
        Returns:
            Dictionary with database statistics
        """
        stats = {
            "database_exists": self.database_exists(),
            "database_path": self.get_database_path(),
            "total_habits": 0,
            "active_habits": 0,
            "total_entries": 0,
        }
        
        if not stats["database_exists"]:
            return stats
            
        try:
            with get_session() as session:
                from .models import Habit, TrackingEntry
                
                stats["total_habits"] = session.query(Habit).count()
                stats["active_habits"] = session.query(Habit).filter(Habit.active == True).count()
                stats["total_entries"] = session.query(TrackingEntry).count()
                
                # Add Phase 2A statistics if tables exist
                migration_status = self.check_migration_status()
                if migration_status["phase_2a_tables"]:
                    from .models import Category, HabitHistory
                    stats["total_categories"] = session.query(Category).count()
                    stats["total_history_entries"] = session.query(HabitHistory).count()
                
                # Add Phase 2C statistics if tables exist
                if migration_status["phase_2c_tables"]:
                    from .models import Template
                    stats["total_templates"] = session.query(Template).count()
                    stats["predefined_templates"] = session.query(Template).filter(Template.is_predefined == True).count()
                
        except SQLAlchemyError:
            # Database exists but might be corrupted
            stats["error"] = "Database connectivity issues"
            
        return stats


# Global database manager instance
db_manager = DatabaseManager()


@contextmanager
def get_session():
    """Get a database session (context manager friendly).
    
    Usage:
        with get_session() as session:
            # Use session here
            pass
    """
    session = db_config.SessionLocal()
    try:
        yield session
    finally:
        session.close()


def ensure_database() -> bool:
    """Ensure database is initialized and ready.
    
    Returns:
        True if database is ready, False otherwise
    """
    if not db_manager.database_exists():
        print("Initializing database...")
        return db_manager.initialize_database(create_backup=False)
    
    if not db_manager.verify_database_integrity():
        print("Database tables missing or corrupted. Reinitializing...")
        return db_manager.initialize_database(create_backup=True)
    
    return True