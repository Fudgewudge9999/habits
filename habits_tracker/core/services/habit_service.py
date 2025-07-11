"""Service layer for habit management operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..models import Habit, TrackingEntry
from ..database import get_session


class HabitValidationError(Exception):
    """Raised when habit validation fails."""
    pass


class HabitNotFoundError(Exception):
    """Raised when a habit is not found."""
    pass


class HabitService:
    """Service for managing habits with business logic and validation."""
    
    VALID_FREQUENCIES = ["daily", "weekly", "custom"]
    MAX_NAME_LENGTH = 255
    MAX_DESCRIPTION_LENGTH = 500
    
    @classmethod
    def validate_habit_name(cls, name: str) -> str:
        """Validate and normalize habit name.
        
        Args:
            name: Raw habit name
            
        Returns:
            Normalized habit name
            
        Raises:
            HabitValidationError: If name is invalid
        """
        if not name or not name.strip():
            raise HabitValidationError("Habit name cannot be empty")
        
        name = name.strip()
        
        if len(name) > cls.MAX_NAME_LENGTH:
            raise HabitValidationError(f"Habit name too long (max {cls.MAX_NAME_LENGTH} characters)")
        
        # Check for invalid characters that might cause issues
        invalid_chars = ['\n', '\r', '\t']
        if any(char in name for char in invalid_chars):
            raise HabitValidationError("Habit name cannot contain newlines or tabs")
        
        return name
    
    @classmethod
    def validate_frequency(cls, frequency: str) -> str:
        """Validate habit frequency.
        
        Args:
            frequency: Frequency string
            
        Returns:
            Normalized frequency
            
        Raises:
            HabitValidationError: If frequency is invalid
        """
        if not frequency:
            frequency = "daily"
        
        frequency = frequency.lower().strip()
        
        if frequency not in cls.VALID_FREQUENCIES:
            valid_options = ", ".join(cls.VALID_FREQUENCIES)
            raise HabitValidationError(f"Invalid frequency '{frequency}'. Valid options: {valid_options}")
        
        return frequency
    
    @classmethod
    def validate_description(cls, description: Optional[str]) -> Optional[str]:
        """Validate habit description.
        
        Args:
            description: Optional description
            
        Returns:
            Normalized description or None
            
        Raises:
            HabitValidationError: If description is invalid
        """
        if not description:
            return None
        
        description = description.strip()
        
        if len(description) > cls.MAX_DESCRIPTION_LENGTH:
            raise HabitValidationError(f"Description too long (max {cls.MAX_DESCRIPTION_LENGTH} characters)")
        
        return description if description else None
    
    @classmethod
    def create_habit(
        cls, 
        name: str, 
        frequency: str = "daily", 
        description: Optional[str] = None
    ) -> Habit:
        """Create a new habit with validation.
        
        Args:
            name: Habit name
            frequency: Habit frequency (daily, weekly, custom)
            description: Optional description
            
        Returns:
            Created Habit object
            
        Raises:
            HabitValidationError: If validation fails
            HabitNotFoundError: If habit already exists
        """
        # Validate inputs
        name = cls.validate_habit_name(name)
        frequency = cls.validate_frequency(frequency)
        description = cls.validate_description(description)
        
        try:
            with get_session() as session:
                # Check if habit already exists
                existing = session.query(Habit).filter(Habit.name == name).first()
                if existing:
                    if existing.active:
                        raise HabitValidationError(f"Habit '{name}' already exists")
                    else:
                        # Reactivate archived habit
                        existing.restore()
                        existing.frequency = frequency
                        existing.description = description
                        session.commit()
                        session.refresh(existing)
                        return existing
                
                # Create new habit
                habit = Habit(
                    name=name,
                    frequency=frequency,
                    description=description,
                    active=True
                )
                
                session.add(habit)
                session.commit()
                session.refresh(habit)
                
                return habit
                
        except IntegrityError as e:
            raise HabitValidationError(f"Database constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            raise HabitValidationError(f"Database error: {str(e)}")
    
    @classmethod
    def get_habit_by_name(cls, name: str, include_archived: bool = False) -> Optional[Habit]:
        """Get a habit by name.
        
        Args:
            name: Habit name
            include_archived: Whether to include archived habits
            
        Returns:
            Habit object or None if not found
        """
        try:
            with get_session() as session:
                query = session.query(Habit).filter(Habit.name == name)
                
                if not include_archived:
                    query = query.filter(Habit.active == True)
                
                return query.first()
                
        except SQLAlchemyError:
            return None
    
    @classmethod
    def list_habits(
        cls, 
        filter_type: str = "active",
        include_stats: bool = True
    ) -> List[Dict[str, Any]]:
        """List habits with optional statistics.
        
        Args:
            filter_type: Filter type ("active", "archived", "all")
            include_stats: Whether to include streak and tracking statistics
            
        Returns:
            List of habit dictionaries with statistics
        """
        try:
            with get_session() as session:
                query = session.query(Habit)
                
                if filter_type == "active":
                    query = query.filter(Habit.active == True)
                elif filter_type == "archived":
                    query = query.filter(Habit.active == False)
                # "all" includes both active and archived
                
                habits = query.order_by(Habit.created_at.desc()).all()
                
                result = []
                for habit in habits:
                    habit_dict = {
                        "id": habit.id,
                        "name": habit.name,
                        "description": habit.description,
                        "frequency": habit.frequency,
                        "created_at": habit.created_at,
                        "active": habit.active,
                        "archived_at": habit.archived_at,
                    }
                    
                    if include_stats:
                        # Add statistics
                        stats = cls._calculate_habit_stats(session, habit)
                        habit_dict.update(stats)
                    
                    result.append(habit_dict)
                
                return result
                
        except SQLAlchemyError:
            return []
    
    @classmethod
    def remove_habit(cls, name: str, permanent: bool = False) -> bool:
        """Remove (archive) or permanently delete a habit.
        
        Args:
            name: Habit name
            permanent: Whether to permanently delete (vs archive)
            
        Returns:
            True if successful, False if habit not found
            
        Raises:
            HabitValidationError: If operation fails
        """
        try:
            with get_session() as session:
                habit = session.query(Habit).filter(Habit.name == name).first()
                
                if not habit:
                    return False
                
                if permanent:
                    # Permanently delete habit and all tracking data
                    session.delete(habit)
                else:
                    # Archive habit (soft delete)
                    habit.archive()
                
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            raise HabitValidationError(f"Failed to remove habit: {str(e)}")
    
    @classmethod
    def restore_habit(cls, name: str) -> bool:
        """Restore an archived habit.
        
        Args:
            name: Habit name
            
        Returns:
            True if successful, False if habit not found
        """
        try:
            with get_session() as session:
                habit = session.query(Habit).filter(
                    Habit.name == name,
                    Habit.active == False
                ).first()
                
                if not habit:
                    return False
                
                habit.restore()
                session.commit()
                return True
                
        except SQLAlchemyError:
            return False
    
    @classmethod
    def _calculate_habit_stats(cls, session: Session, habit: Habit) -> Dict[str, Any]:
        """Calculate statistics for a habit.
        
        Args:
            session: Database session
            habit: Habit object
            
        Returns:
            Dictionary with statistics
        """
        from ..services.analytics_service import AnalyticsService
        
        # Get basic tracking stats
        entries = session.query(TrackingEntry).filter(
            TrackingEntry.habit_id == habit.id,
            TrackingEntry.completed == True
        ).order_by(TrackingEntry.date).all()
        
        if not entries:
            return {
                "streak": 0,
                "longest_streak": 0,
                "total_completions": 0,
                "last_tracked": None
            }
        
        # Calculate current and longest streak
        current_streak = AnalyticsService._calculate_current_streak(entries)
        longest_streak = AnalyticsService._calculate_longest_streak(entries)
        
        return {
            "streak": current_streak,
            "longest_streak": longest_streak,
            "total_completions": len(entries),
            "last_tracked": entries[-1].date if entries else None
        }