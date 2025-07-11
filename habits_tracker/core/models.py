"""SQLAlchemy data models for HabitsTracker."""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, 
    ForeignKey, UniqueConstraint, Index, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


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


# Database configuration and session factory
class DatabaseConfig:
    """Database configuration and session management."""
    
    def __init__(self, database_url: str = "sqlite:///~/.habits/habits.db"):
        """Initialize database configuration.
        
        Args:
            database_url: SQLAlchemy database URL
        """
        # Expand user path for macOS
        if database_url.startswith("sqlite:///~/"):
            import os
            database_url = database_url.replace("~/", f"{os.path.expanduser('~')}/")
            
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            # SQLite specific optimizations
            pool_pre_ping=True,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
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