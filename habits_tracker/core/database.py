"""Database connection and migration utilities."""

import os
import shutil
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
            db_config.database_url = f"sqlite:///{database_path}"
            db_config.engine = db_config.create_engine(db_config.database_url)
            db_config.SessionLocal = db_config.sessionmaker(bind=db_config.engine)
    
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
            with next(db_config.get_session()) as session:
                # Try a simple query to test connectivity
                session.execute("SELECT 1").fetchone()
                return True
                
        except SQLAlchemyError:
            return False
    
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
            with next(db_config.get_session()) as session:
                from .models import Habit, TrackingEntry
                
                stats["total_habits"] = session.query(Habit).count()
                stats["active_habits"] = session.query(Habit).filter(Habit.active == True).count()
                stats["total_entries"] = session.query(TrackingEntry).count()
                
        except SQLAlchemyError:
            # Database exists but might be corrupted
            stats["error"] = "Database connectivity issues"
            
        return stats


# Global database manager instance
db_manager = DatabaseManager()


def get_session() -> Session:
    """Get a database session (context manager friendly).
    
    Usage:
        with get_session() as session:
            # Use session here
            pass
    """
    return next(db_config.get_session())


def ensure_database() -> bool:
    """Ensure database is initialized and ready.
    
    Returns:
        True if database is ready, False otherwise
    """
    if not db_manager.database_exists():
        print("Initializing database...")
        return db_manager.initialize_database(create_backup=False)
    
    if not db_manager.verify_database_integrity():
        print("Database integrity check failed. Reinitializing...")
        return db_manager.initialize_database(create_backup=True)
    
    return True