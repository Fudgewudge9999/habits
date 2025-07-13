"""SQLAlchemy data models for HabitsTracker."""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, 
    ForeignKey, UniqueConstraint, Index, Table, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


# Association table for many-to-many relationship between habits and categories
habit_categories = Table(
    'habit_categories',
    Base.metadata,
    Column('habit_id', Integer, ForeignKey('habits.id'), primary_key=True),
    Column('category_id', Integer, ForeignKey('categories.id'), primary_key=True),
    Column('assigned_at', DateTime, default=func.now(), nullable=False),
    Index('idx_habit_categories_habit', 'habit_id'),
    Index('idx_habit_categories_category', 'category_id')
)


class Habit(Base):
    """Habit model representing a trackable habit."""
    
    __tablename__ = "habits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text)
    frequency = Column(String(50), nullable=False, default="daily")
    frequency_details = Column(Text)  # JSON for custom frequencies
    created_at = Column(DateTime, default=func.now(), nullable=False)
    archived_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Relationships
    tracking_entries = relationship(
        "TrackingEntry", 
        back_populates="habit", 
        cascade="all, delete-orphan"
    )
    categories = relationship(
        "Category",
        secondary=habit_categories,
        back_populates="habits"
    )
    history_entries = relationship(
        "HabitHistory",
        back_populates="habit",
        cascade="all, delete-orphan",
        order_by="HabitHistory.changed_at.desc()"
    )
    
    def __repr__(self) -> str:
        return f"<Habit(id={self.id}, name='{self.name}', frequency='{self.frequency}')>"
    
    def archive(self) -> None:
        """Archive this habit (soft delete)."""
        self.active = False
        self.archived_at = datetime.utcnow()
    
    def restore(self) -> None:
        """Restore an archived habit."""
        self.active = True
        self.archived_at = None


class TrackingEntry(Base):
    """Tracking entry representing a habit completion on a specific date."""
    
    __tablename__ = "tracking_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    completed = Column(Boolean, default=True, nullable=False)
    notes = Column(Text)
    tracked_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    habit = relationship("Habit", back_populates="tracking_entries")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('habit_id', 'date', name='uq_habit_date'),
        Index('idx_habit_date', 'habit_id', 'date'),
        Index('idx_completed_date', 'completed', 'date'),  # For analytics queries
        Index('idx_habit_completed', 'habit_id', 'completed'),  # For streak calculations
        Index('idx_habit_date_completed', 'habit_id', 'date', 'completed'),  # Composite for performance
        Index('idx_date_desc', 'date', postgresql_ops={'date': 'DESC'}),  # For recent queries
    )
    
    def __repr__(self) -> str:
        return f"<TrackingEntry(habit_id={self.habit_id}, date={self.date}, completed={self.completed})>"


class Config(Base):
    """Application configuration storage."""
    
    __tablename__ = "config"
    
    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        return f"<Config(key='{self.key}', value='{self.value}')>"


class Category(Base):
    """Category model for organizing habits."""
    
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    color = Column(String(20))  # Hex color code for display
    description = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    habits = relationship(
        "Habit",
        secondary=habit_categories,
        back_populates="categories"
    )
    
    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class HabitHistory(Base):
    """Habit modification history for audit trail."""
    
    __tablename__ = "habit_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False, index=True)
    field_name = Column(String(50), nullable=False)
    old_value = Column(Text)
    new_value = Column(Text)
    change_type = Column(String(20), nullable=False)  # create, update, delete, archive, restore
    changed_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    habit = relationship("Habit", back_populates="history_entries")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_habit_history_habit_id', 'habit_id'),
        Index('idx_habit_history_changed_at', 'changed_at'),
        Index('idx_habit_history_change_type', 'change_type'),
        Index('idx_habit_history_field', 'field_name'),
    )
    
    def __repr__(self) -> str:
        return f"<HabitHistory(habit_id={self.habit_id}, field='{self.field_name}', type='{self.change_type}')>"


# Database configuration and session factory
class DatabaseConfig:
    """Database configuration and session management."""
    
    def __init__(self, database_url: str = None):
        """Initialize database configuration.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        # Set default database path if not provided
        if database_url is None:
            import os
            db_dir = os.path.expanduser("~/.habits")
            database_url = f"sqlite:///{db_dir}/habits.db"
        
        # Expand user path for macOS
        if database_url.startswith("sqlite:///~/"):
            import os
            database_url = database_url.replace("~/", f"{os.path.expanduser('~')}/")
            
        self.database_url = database_url
        # SQLite specific optimizations
        sqlite_connect_args = {
            "check_same_thread": False,
            # SQLite performance optimizations
            "timeout": 20,
            "isolation_level": None,  # Autocommit mode for better performance
        }
        
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            # SQLite specific optimizations
            pool_pre_ping=True,
            pool_recycle=3600,  # Recycle connections every hour
            connect_args=sqlite_connect_args if "sqlite" in database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self) -> None:
        """Create all database tables."""
        # Ensure directory exists for SQLite
        if "sqlite" in self.database_url:
            import os
            db_path = self.database_url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Get a database session."""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()


# Global database instance
db_config = DatabaseConfig()