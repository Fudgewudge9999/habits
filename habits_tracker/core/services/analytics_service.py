"""Analytics service for calculating habit statistics and streaks."""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..models import Habit, TrackingEntry
from ..database import get_session
from ...utils.date_utils import get_today


class AnalyticsService:
    """Service for calculating habit analytics and statistics."""
    
    @classmethod
    def calculate_habit_stats(
        cls,
        habit_name: str,
        period: str = "all"
    ) -> Dict[str, Any]:
        """Calculate comprehensive statistics for a habit.
        
        Args:
            habit_name: Name of the habit
            period: Time period ('week', 'month', 'year', 'all')
            
        Returns:
            Dictionary with habit statistics
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
            
            # Get date range based on period
            today = get_today()
            start_date = None
            
            if period == "week":
                start_date = today - timedelta(days=7)
            elif period == "month":
                start_date = today - timedelta(days=30)
            elif period == "year":
                start_date = today - timedelta(days=365)
            
            # Get tracking entries
            query = session.query(TrackingEntry).filter(
                TrackingEntry.habit_id == habit.id,
                TrackingEntry.completed == True
            )
            
            if start_date:
                query = query.filter(TrackingEntry.date >= start_date)
            
            entries = query.order_by(TrackingEntry.date).all()
            
            # Calculate statistics
            total_completions = len(entries)
            current_streak = cls._calculate_current_streak(entries)
            longest_streak = cls._calculate_longest_streak(entries)
            
            # Calculate completion rate for the period
            if period != "all" and start_date:
                total_days = (today - start_date).days + 1
                completion_rate = (total_completions / total_days * 100) if total_days > 0 else 0
            else:
                # For "all" period, calculate based on habit creation date
                habit_days = (today - habit.created_at.date()).days + 1
                completion_rate = (total_completions / habit_days * 100) if habit_days > 0 else 0
            
            return {
                "success": True,
                "habit_name": habit_name,
                "period": period,
                "statistics": {
                    "total_completions": total_completions,
                    "current_streak": current_streak,
                    "longest_streak": longest_streak,
                    "completion_rate": round(completion_rate, 1),
                    "created_at": habit.created_at.date(),
                    "is_active": habit.active
                },
                "recent_entries": [
                    {
                        "date": entry.date,
                        "notes": entry.notes
                    }
                    for entry in entries[-10:]  # Last 10 entries
                ]
            }
    
    @classmethod
    def calculate_overall_stats(cls, period: str = "all") -> Dict[str, Any]:
        """Calculate overall statistics across all habits.
        
        Args:
            period: Time period ('week', 'month', 'year', 'all')
            
        Returns:
            Dictionary with overall statistics
        """
        with get_session() as session:
            # Get all habits
            habits = session.query(Habit).all()
            
            if not habits:
                return {
                    "success": True,
                    "period": period,
                    "habits": [],
                    "summary": {
                        "total_habits": 0,
                        "active_habits": 0,
                        "total_completions": 0,
                        "average_completion_rate": 0
                    }
                }
            
            # Get date range
            today = get_today()
            start_date = None
            
            if period == "week":
                start_date = today - timedelta(days=7)
            elif period == "month":
                start_date = today - timedelta(days=30)
            elif period == "year":
                start_date = today - timedelta(days=365)
            
            habit_stats = []
            total_completions = 0
            completion_rates = []
            
            for habit in habits:
                # Use count query for better performance
                query = session.query(func.count(TrackingEntry.id)).filter(
                    TrackingEntry.habit_id == habit.id,
                    TrackingEntry.completed == True
                )
                
                if start_date:
                    query = query.filter(TrackingEntry.date >= start_date)
                
                completions = query.scalar() or 0
                total_completions += completions
                
                # Calculate completion rate
                if period != "all" and start_date:
                    total_days = (today - start_date).days + 1
                    rate = (completions / total_days * 100) if total_days > 0 else 0
                else:
                    habit_days = (today - habit.created_at.date()).days + 1
                    rate = (completions / habit_days * 100) if habit_days > 0 else 0
                
                completion_rates.append(rate)
                
                # Get entries for streak calculation (only when needed)
                streak_entries = session.query(TrackingEntry).filter(
                    TrackingEntry.habit_id == habit.id,
                    TrackingEntry.completed == True
                ).order_by(TrackingEntry.date.desc()).limit(100).all()  # Limit for performance
                
                current_streak = cls._calculate_current_streak(streak_entries)
                
                habit_stats.append({
                    "name": habit.name,
                    "active": habit.active,
                    "completions": completions,
                    "completion_rate": round(rate, 1),
                    "current_streak": current_streak
                })
            
            active_habits = len([h for h in habits if h.active])
            avg_completion_rate = (sum(completion_rates) / len(completion_rates)) if completion_rates else 0
            
            return {
                "success": True,
                "period": period,
                "habits": habit_stats,
                "summary": {
                    "total_habits": len(habits),
                    "active_habits": active_habits,
                    "total_completions": total_completions,
                    "average_completion_rate": round(avg_completion_rate, 1)
                }
            }
    
    @classmethod
    def _calculate_current_streak(cls, entries: List[TrackingEntry]) -> int:
        """Calculate current streak from tracking entries.
        
        Args:
            entries: List of tracking entries ordered by date
            
        Returns:
            Current streak count
        """
        if not entries:
            return 0
        
        # Get today's date
        today = get_today()
        
        # Sort entries by date descending to start from most recent
        sorted_entries = sorted(entries, key=lambda x: x.date, reverse=True)
        
        # Check if the streak is current (includes today or yesterday)
        latest_entry = sorted_entries[0]
        days_since_latest = (today - latest_entry.date).days
        
        # If more than 1 day gap, streak is broken
        if days_since_latest > 1:
            return 0
        
        # Count consecutive days backward from the latest entry
        streak = 0
        current_date = latest_entry.date
        
        for entry in sorted_entries:
            if entry.date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                # Gap found, streak ends
                break
        
        return streak
    
    @classmethod
    def _calculate_longest_streak(cls, entries: List[TrackingEntry]) -> int:
        """Calculate the longest streak from tracking entries.
        
        Args:
            entries: List of tracking entries
            
        Returns:
            Longest streak count
        """
        if not entries:
            return 0
        
        # Sort entries by date
        sorted_entries = sorted(entries, key=lambda x: x.date)
        
        longest_streak = 0
        current_streak = 0
        previous_date = None
        
        for entry in sorted_entries:
            if previous_date is None:
                # First entry
                current_streak = 1
            elif entry.date == previous_date + timedelta(days=1):
                # Consecutive day
                current_streak += 1
            else:
                # Gap found, reset current streak
                current_streak = 1
            
            # Update longest streak if current is longer
            longest_streak = max(longest_streak, current_streak)
            previous_date = entry.date
        
        return longest_streak