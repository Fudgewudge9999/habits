"""Tracking service for habit tracking operations."""

from datetime import date, datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..database import get_session
from ..models import Habit, TrackingEntry
from ...utils.date_utils import parse_date, get_today
from ...utils.performance import performance_target, profile_query
from ...utils.cache import cached, query_cache, cache_key_for_today_status, invalidate_tracking_caches


class TrackingService:
    """Service for managing habit tracking entries."""
    
    @classmethod
    @performance_target(50)  # 50ms target for tracking
    @profile_query("habit_tracking")
    def track_habit(
        cls, 
        habit_name: str, 
        tracking_date: Optional[date] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Track a habit for a specific date.
        
        Args:
            habit_name: Name of the habit to track
            tracking_date: Date to track (defaults to today)
            notes: Optional notes for the tracking entry
            
        Returns:
            Dictionary with success status and entry details
        """
        if tracking_date is None:
            tracking_date = get_today()
        
        # Validate notes length
        if notes and len(notes) > 500:
            return {
                "success": False,
                "error": "Notes cannot exceed 500 characters",
                "details": f"Current length: {len(notes)}"
            }
        
        with get_session() as session:
            # Find the habit
            habit = session.query(Habit).filter(
                Habit.name == habit_name,
                Habit.active == True
            ).first()
            
            if not habit:
                return {
                    "success": False,
                    "error": f"Active habit '{habit_name}' not found",
                    "suggestion": "Use 'habits list' to see available habits"
                }
            
            # Check if already tracked for this date
            existing_entry = session.query(TrackingEntry).filter(
                TrackingEntry.habit_id == habit.id,
                TrackingEntry.date == tracking_date
            ).first()
            
            if existing_entry:
                return {
                    "success": False,
                    "error": f"Habit '{habit_name}' already tracked for {tracking_date}",
                    "suggestion": f"Use 'habits untrack \"{habit_name}\" --date {tracking_date}' to remove first"
                }
            
            # Create new tracking entry
            try:
                entry = TrackingEntry(
                    habit_id=habit.id,
                    date=tracking_date,
                    completed=True,
                    notes=notes,
                    tracked_at=datetime.utcnow()
                )
                
                session.add(entry)
                session.commit()
                
                # Invalidate caches after tracking
                invalidate_tracking_caches()
                
                return {
                    "success": True,
                    "habit_name": habit_name,
                    "date": tracking_date,
                    "notes": notes,
                    "message": f"Successfully tracked '{habit_name}' for {tracking_date}"
                }
                
            except IntegrityError:
                session.rollback()
                return {
                    "success": False,
                    "error": "Database integrity error occurred",
                    "suggestion": "Please try again"
                }
    
    @classmethod
    def untrack_habit(
        cls,
        habit_name: str,
        tracking_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Remove tracking for a habit on a specific date.
        
        Args:
            habit_name: Name of the habit to untrack
            tracking_date: Date to untrack (defaults to today)
            
        Returns:
            Dictionary with success status and details
        """
        if tracking_date is None:
            tracking_date = get_today()
        
        with get_session() as session:
            # Find the habit
            habit = session.query(Habit).filter(
                Habit.name == habit_name
            ).first()
            
            if not habit:
                return {
                    "success": False,
                    "error": f"Habit '{habit_name}' not found",
                    "suggestion": "Use 'habits list --filter all' to see all habits"
                }
            
            # Find the tracking entry
            entry = session.query(TrackingEntry).filter(
                TrackingEntry.habit_id == habit.id,
                TrackingEntry.date == tracking_date
            ).first()
            
            if not entry:
                return {
                    "success": False,
                    "error": f"No tracking found for '{habit_name}' on {tracking_date}",
                    "suggestion": f"Use 'habits track \"{habit_name}\"' to track it first"
                }
            
            try:
                session.delete(entry)
                session.commit()
                
                # Invalidate caches after untracking
                invalidate_tracking_caches()
                
                return {
                    "success": True,
                    "habit_name": habit_name,
                    "date": tracking_date,
                    "message": f"Successfully untracked '{habit_name}' for {tracking_date}"
                }
                
            except Exception as e:
                session.rollback()
                return {
                    "success": False,
                    "error": "Failed to remove tracking entry",
                    "details": str(e)
                }
    
    @classmethod
    @cached(query_cache, ttl=30, key_func=lambda *args, **kwargs: cache_key_for_today_status())
    @performance_target(100)  # 100ms target for today status
    @profile_query("today_status")
    def get_today_status(cls) -> Dict[str, Any]:
        """Get today's tracking status for all active habits.
        
        Returns:
            Dictionary with today's habit status and statistics
        """
        today = get_today()
        
        with get_session() as session:
            # Get all active habits
            active_habits = session.query(Habit).filter(
                Habit.active == True
            ).order_by(Habit.name).all()
            
            if not active_habits:
                return {
                    "success": True,
                    "date": today,
                    "habits": [],
                    "message": "No active habits found",
                    "suggestion": "Use 'habits add' to create your first habit"
                }
            
            habits_status = []
            tracked_count = 0
            
            for habit in active_habits:
                # Check if tracked today
                entry = session.query(TrackingEntry).filter(
                    TrackingEntry.habit_id == habit.id,
                    TrackingEntry.date == today
                ).first()
                
                is_tracked = entry is not None
                if is_tracked:
                    tracked_count += 1
                
                # Calculate current streak
                streak = cls._calculate_current_streak_for_habit(session, habit.id)
                
                habits_status.append({
                    "name": habit.name,
                    "description": habit.description,
                    "frequency": habit.frequency,
                    "tracked_today": is_tracked,
                    "notes": entry.notes if entry else None,
                    "current_streak": streak
                })
            
            completion_rate = (tracked_count / len(active_habits) * 100) if active_habits else 0
            
            return {
                "success": True,
                "date": today,
                "habits": habits_status,
                "summary": {
                    "total_habits": len(active_habits),
                    "tracked_today": tracked_count,
                    "completion_rate": round(completion_rate, 1)
                }
            }
    
    @classmethod
    def _calculate_current_streak_for_habit(cls, session: Session, habit_id: int) -> int:
        """Calculate current streak for a specific habit.
        
        Args:
            session: Database session
            habit_id: ID of the habit
            
        Returns:
            Current streak count
        """
        # Get only recent entries for streak calculation (performance optimization)
        entries = session.query(TrackingEntry).filter(
            TrackingEntry.habit_id == habit_id,
            TrackingEntry.completed == True
        ).order_by(TrackingEntry.date.desc()).limit(30).all()  # Limit to last 30 days for performance
        
        if not entries:
            return 0
        
        from datetime import timedelta
        
        today = get_today()
        latest_entry = entries[0]
        
        # Check if streak is current (today or yesterday)
        days_since_latest = (today - latest_entry.date).days
        if days_since_latest > 1:
            return 0
        
        # Count consecutive days
        streak = 0
        expected_date = latest_entry.date
        
        for entry in entries:
            if entry.date == expected_date:
                streak += 1
                expected_date = expected_date - timedelta(days=1)
            else:
                break
        
        return streak
    
    @classmethod
    def get_habit_entries(
        cls,
        habit_name: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get tracking entries for a habit within a date range.
        
        Args:
            habit_name: Name of the habit
            start_date: Start date (optional)
            end_date: End date (optional)
            
        Returns:
            Dictionary with entries and metadata
        """
        with get_session() as session:
            # Find the habit
            habit = session.query(Habit).filter(
                Habit.name == habit_name
            ).first()
            
            if not habit:
                return {
                    "success": False,
                    "error": f"Habit '{habit_name}' not found"
                }
            
            # Build query
            query = session.query(TrackingEntry).filter(
                TrackingEntry.habit_id == habit.id
            )
            
            if start_date:
                query = query.filter(TrackingEntry.date >= start_date)
            if end_date:
                query = query.filter(TrackingEntry.date <= end_date)
            
            entries = query.order_by(TrackingEntry.date.desc()).all()
            
            return {
                "success": True,
                "habit_name": habit_name,
                "entries": [
                    {
                        "date": entry.date,
                        "completed": entry.completed,
                        "notes": entry.notes,
                        "tracked_at": entry.tracked_at
                    }
                    for entry in entries
                ],
                "total_entries": len(entries)
            }