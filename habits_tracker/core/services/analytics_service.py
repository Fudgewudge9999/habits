"""Analytics service for calculating habit statistics and streaks."""

from datetime import date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from ..models import TrackingEntry
from ...utils.date_utils import get_today


class AnalyticsService:
    """Service for calculating habit analytics and statistics."""
    
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