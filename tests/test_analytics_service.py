"""Unit tests for AnalyticsService."""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from habits_tracker.core.services.analytics_service import AnalyticsService
from habits_tracker.core.models import Habit, TrackingEntry


class TestCalculateHabitStats:
    """Test individual habit statistics calculation."""
    
    @patch('habits_tracker.core.services.analytics_service.get_session')
    @patch('habits_tracker.core.services.analytics_service.get_today')
    def test_calculate_habit_stats_success(self, mock_get_today, mock_get_session):
        """Test successful habit statistics calculation."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock habit
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_habit.name = "Exercise"
        mock_habit.created_at = datetime(2025, 7, 1)  # 11 days ago
        mock_habit.active = True
        mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
        
        # Mock tracking entries
        mock_entries = []
        for i in range(5):  # 5 completed entries
            entry = MagicMock()
            entry.date = today - timedelta(days=i)
            entry.notes = f"Day {i+1}"
            mock_entries.append(entry)
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_entries
        
        with patch.object(AnalyticsService, '_calculate_current_streak', return_value=5), \
             patch.object(AnalyticsService, '_calculate_longest_streak', return_value=7):
            
            result = AnalyticsService.calculate_habit_stats("Exercise", "all")
        
        assert result["success"] is True
        assert result["habit_name"] == "Exercise"
        assert result["period"] == "all"
        
        stats = result["statistics"]
        assert stats["total_completions"] == 5
        assert stats["current_streak"] == 5
        assert stats["longest_streak"] == 7
        assert stats["completion_rate"] == 45.5  # 5/11 * 100, rounded to 1 decimal
        assert stats["is_active"] is True
        
        # Check recent entries (last 10)
        assert len(result["recent_entries"]) == 5
        assert result["recent_entries"][0]["notes"] == "Day 1"
    
    @patch('habits_tracker.core.services.analytics_service.get_session')
    def test_calculate_habit_stats_not_found(self, mock_get_session):
        """Test statistics calculation for non-existent habit."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = AnalyticsService.calculate_habit_stats("NonExistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @patch('habits_tracker.core.services.analytics_service.get_session')
    @patch('habits_tracker.core.services.analytics_service.get_today')
    def test_calculate_habit_stats_weekly_period(self, mock_get_today, mock_get_session):
        """Test habit statistics calculation for weekly period."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_habit.created_at = datetime(2025, 7, 1)
        mock_habit.active = True
        mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
        
        # Mock 3 entries in the last week
        mock_entries = []
        for i in range(3):
            entry = MagicMock()
            entry.date = today - timedelta(days=i)
            entry.notes = f"Week day {i+1}"
            mock_entries.append(entry)
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_entries
        
        with patch.object(AnalyticsService, '_calculate_current_streak', return_value=3), \
             patch.object(AnalyticsService, '_calculate_longest_streak', return_value=5):
            
            result = AnalyticsService.calculate_habit_stats("Exercise", "week")
        
        assert result["success"] is True
        assert result["period"] == "week"
        
        stats = result["statistics"]
        assert stats["total_completions"] == 3
        assert stats["completion_rate"] == 37.5  # 3/8 * 100 (8 days in week period)
    
    @patch('habits_tracker.core.services.analytics_service.get_session')
    @patch('habits_tracker.core.services.analytics_service.get_today')
    def test_calculate_habit_stats_no_entries(self, mock_get_today, mock_get_session):
        """Test habit statistics calculation with no tracking entries."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_habit.created_at = datetime(2025, 7, 1)
        mock_habit.active = True
        mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        with patch.object(AnalyticsService, '_calculate_current_streak', return_value=0), \
             patch.object(AnalyticsService, '_calculate_longest_streak', return_value=0):
            
            result = AnalyticsService.calculate_habit_stats("Exercise")
        
        assert result["success"] is True
        stats = result["statistics"]
        assert stats["total_completions"] == 0
        assert stats["current_streak"] == 0
        assert stats["longest_streak"] == 0
        assert stats["completion_rate"] == 0.0


class TestCalculateOverallStats:
    """Test overall statistics calculation across all habits."""
    
    @patch('habits_tracker.core.services.analytics_service.get_session')
    @patch('habits_tracker.core.services.analytics_service.get_today')
    def test_calculate_overall_stats_no_habits(self, mock_get_today, mock_get_session):
        """Test overall statistics with no habits."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.all.return_value = []
        
        result = AnalyticsService.calculate_overall_stats()
        
        assert result["success"] is True
        assert result["habits"] == []
        
        summary = result["summary"]
        assert summary["total_habits"] == 0
        assert summary["active_habits"] == 0
        assert summary["total_completions"] == 0
        assert summary["average_completion_rate"] == 0
    
    @patch('habits_tracker.core.services.analytics_service.get_session')
    @patch('habits_tracker.core.services.analytics_service.get_today')
    def test_calculate_overall_stats_with_habits(self, mock_get_today, mock_get_session):
        """Test overall statistics with multiple habits."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock habits
        mock_habit1 = MagicMock()
        mock_habit1.id = 1
        mock_habit1.name = "Exercise"
        mock_habit1.created_at = datetime(2025, 7, 1)
        mock_habit1.active = True
        
        mock_habit2 = MagicMock()
        mock_habit2.id = 2
        mock_habit2.name = "Reading"
        mock_habit2.created_at = datetime(2025, 7, 1)
        mock_habit2.active = True
        
        mock_session.query.return_value.all.return_value = [mock_habit1, mock_habit2]
        
        # Mock count queries returning different completion counts
        mock_session.query.return_value.filter.return_value.scalar.side_effect = [5, 3]  # 5 and 3 completions
        
        # Mock streak entries
        mock_entries1 = [MagicMock() for _ in range(5)]
        mock_entries2 = [MagicMock() for _ in range(3)]
        
        # Configure query calls for streak calculation
        def side_effect(*args, **kwargs):
            # First call returns entries for habit 1, second for habit 2
            if hasattr(side_effect, 'call_count'):
                side_effect.call_count += 1
            else:
                side_effect.call_count = 1
            
            if side_effect.call_count == 1:
                return mock_entries1
            else:
                return mock_entries2
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.side_effect = side_effect
        
        with patch.object(AnalyticsService, '_calculate_current_streak', side_effect=[5, 3]):
            result = AnalyticsService.calculate_overall_stats("all")
        
        assert result["success"] is True
        assert len(result["habits"]) == 2
        
        # Check individual habit stats
        habit1_stats = result["habits"][0]
        assert habit1_stats["name"] == "Exercise"
        assert habit1_stats["completions"] == 5
        assert habit1_stats["current_streak"] == 5
        assert habit1_stats["active"] is True
        
        habit2_stats = result["habits"][1]
        assert habit2_stats["name"] == "Reading"
        assert habit2_stats["completions"] == 3
        assert habit2_stats["current_streak"] == 3
        
        # Check summary
        summary = result["summary"]
        assert summary["total_habits"] == 2
        assert summary["active_habits"] == 2
        assert summary["total_completions"] == 8  # 5 + 3
        # Average completion rate should be calculated from individual rates
        assert summary["average_completion_rate"] > 0


class TestStreakCalculations:
    """Test streak calculation methods."""
    
    def test_calculate_current_streak_no_entries(self):
        """Test current streak calculation with no entries."""
        result = AnalyticsService._calculate_current_streak([])
        assert result == 0
    
    @patch('habits_tracker.core.services.analytics_service.get_today')
    def test_calculate_current_streak_current(self, mock_get_today):
        """Test current streak calculation with current streak."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        # Mock consecutive entries
        entries = []
        for i in range(3):
            entry = MagicMock()
            entry.date = today - timedelta(days=i)
            entries.append(entry)
        
        result = AnalyticsService._calculate_current_streak(entries)
        assert result == 3
    
    @patch('habits_tracker.core.services.analytics_service.get_today')
    def test_calculate_current_streak_broken(self, mock_get_today):
        """Test current streak calculation with broken streak."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        # Mock entry from 3 days ago (gap > 1 day)
        entry = MagicMock()
        entry.date = today - timedelta(days=3)
        
        result = AnalyticsService._calculate_current_streak([entry])
        assert result == 0
    
    @patch('habits_tracker.core.services.analytics_service.get_today')
    def test_calculate_current_streak_with_gap(self, mock_get_today):
        """Test current streak calculation with gap in entries."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        # Mock entries with a gap
        entries = []
        # Current streak of 2 days
        for i in range(2):
            entry = MagicMock()
            entry.date = today - timedelta(days=i)
            entries.append(entry)
        
        # Gap - no entry for day 2
        # Entry for day 4
        entry = MagicMock()
        entry.date = today - timedelta(days=4)
        entries.append(entry)
        
        result = AnalyticsService._calculate_current_streak(entries)
        assert result == 2
    
    def test_calculate_longest_streak_no_entries(self):
        """Test longest streak calculation with no entries."""
        result = AnalyticsService._calculate_longest_streak([])
        assert result == 0
    
    def test_calculate_longest_streak_single_entry(self):
        """Test longest streak calculation with single entry."""
        entry = MagicMock()
        entry.date = date(2025, 7, 11)
        
        result = AnalyticsService._calculate_longest_streak([entry])
        assert result == 1
    
    def test_calculate_longest_streak_consecutive(self):
        """Test longest streak calculation with consecutive entries."""
        base_date = date(2025, 7, 11)
        entries = []
        
        # Create 5 consecutive days
        for i in range(5):
            entry = MagicMock()
            entry.date = base_date + timedelta(days=i)
            entries.append(entry)
        
        result = AnalyticsService._calculate_longest_streak(entries)
        assert result == 5
    
    def test_calculate_longest_streak_with_gaps(self):
        """Test longest streak calculation with gaps."""
        base_date = date(2025, 7, 1)
        entries = []
        
        # First streak: 3 days (July 1-3)
        for i in range(3):
            entry = MagicMock()
            entry.date = base_date + timedelta(days=i)
            entries.append(entry)
        
        # Gap of 2 days
        
        # Second streak: 5 days (July 6-10) - this should be the longest
        for i in range(5):
            entry = MagicMock()
            entry.date = base_date + timedelta(days=5+i)
            entries.append(entry)
        
        # Gap of 1 day
        
        # Third streak: 2 days (July 12-13)
        for i in range(2):
            entry = MagicMock()
            entry.date = base_date + timedelta(days=11+i)
            entries.append(entry)
        
        result = AnalyticsService._calculate_longest_streak(entries)
        assert result == 5
    
    def test_calculate_longest_streak_multiple_equal_streaks(self):
        """Test longest streak calculation with multiple equal streaks."""
        base_date = date(2025, 7, 1)
        entries = []
        
        # First streak: 3 days
        for i in range(3):
            entry = MagicMock()
            entry.date = base_date + timedelta(days=i)
            entries.append(entry)
        
        # Gap
        
        # Second streak: 3 days (equal to first)
        for i in range(3):
            entry = MagicMock()
            entry.date = base_date + timedelta(days=5+i)
            entries.append(entry)
        
        result = AnalyticsService._calculate_longest_streak(entries)
        assert result == 3