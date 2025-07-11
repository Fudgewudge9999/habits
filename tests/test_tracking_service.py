"""Unit tests for TrackingService."""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock

from habits_tracker.core.services.tracking_service import TrackingService
from habits_tracker.core.models import Habit, TrackingEntry


class TestTrackHabit:
    """Test habit tracking functionality."""
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    @patch('habits_tracker.core.services.tracking_service.get_today')
    def test_track_habit_success(self, mock_get_today, mock_get_session):
        """Test successful habit tracking."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock habit exists and is active
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_habit.name = "Exercise"
        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_habit, None]
        
        result = TrackingService.track_habit("Exercise")
        
        assert result["success"] is True
        assert result["habit_name"] == "Exercise"
        assert result["date"] == today
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    @patch('habits_tracker.core.services.tracking_service.get_today')
    def test_track_habit_with_custom_date(self, mock_get_today, mock_get_session):
        """Test habit tracking with custom date."""
        custom_date = date(2025, 7, 10)
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_habit, None]
        
        result = TrackingService.track_habit("Exercise", tracking_date=custom_date)
        
        assert result["success"] is True
        assert result["date"] == custom_date
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    def test_track_habit_with_notes(self, mock_get_session):
        """Test habit tracking with notes."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_habit, None]
        
        notes = "Great workout today!"
        result = TrackingService.track_habit("Exercise", notes=notes)
        
        assert result["success"] is True
        assert result["notes"] == notes
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    def test_track_habit_notes_too_long(self, mock_get_session):
        """Test habit tracking with notes that are too long."""
        long_notes = "x" * 501  # Over 500 character limit
        
        result = TrackingService.track_habit("Exercise", notes=long_notes)
        
        assert result["success"] is False
        assert "cannot exceed 500 characters" in result["error"]
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    def test_track_habit_not_found(self, mock_get_session):
        """Test tracking habit that doesn't exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = TrackingService.track_habit("NonExistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
        assert "habits list" in result["suggestion"]
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    def test_track_habit_already_tracked(self, mock_get_session):
        """Test tracking habit that's already tracked for the date."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_existing_entry = MagicMock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_habit, mock_existing_entry]
        
        result = TrackingService.track_habit("Exercise")
        
        assert result["success"] is False
        assert "already tracked" in result["error"]
        assert "habits untrack" in result["suggestion"]


class TestUntrackHabit:
    """Test habit untracking functionality."""
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    @patch('habits_tracker.core.services.tracking_service.get_today')
    def test_untrack_habit_success(self, mock_get_today, mock_get_session):
        """Test successful habit untracking."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_entry = MagicMock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_habit, mock_entry]
        
        result = TrackingService.untrack_habit("Exercise")
        
        assert result["success"] is True
        assert result["habit_name"] == "Exercise"
        assert result["date"] == today
        mock_session.delete.assert_called_once_with(mock_entry)
        mock_session.commit.assert_called_once()
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    def test_untrack_habit_not_found(self, mock_get_session):
        """Test untracking habit that doesn't exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = TrackingService.untrack_habit("NonExistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    def test_untrack_habit_no_tracking_entry(self, mock_get_session):
        """Test untracking habit with no tracking entry for the date."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_habit, None]
        
        result = TrackingService.untrack_habit("Exercise")
        
        assert result["success"] is False
        assert "No tracking found" in result["error"]


class TestTodayStatus:
    """Test today's status functionality."""
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    @patch('habits_tracker.core.services.tracking_service.get_today')
    def test_get_today_status_no_habits(self, mock_get_today, mock_get_session):
        """Test today's status with no active habits."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        result = TrackingService.get_today_status()
        
        assert result["success"] is True
        assert result["habits"] == []
        assert "No active habits found" in result["message"]
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    @patch('habits_tracker.core.services.tracking_service.get_today')
    @patch.object(TrackingService, '_calculate_current_streak_for_habit')
    def test_get_today_status_with_habits(self, mock_streak, mock_get_today, mock_get_session):
        """Test today's status with active habits."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock habit
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_habit.name = "Exercise"
        mock_habit.description = "Daily workout"
        mock_habit.frequency = "daily"
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_habit]
        
        # Mock tracking entry (habit is tracked today)
        mock_entry = MagicMock()
        mock_entry.notes = "Great workout!"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_entry
        
        mock_streak.return_value = 5
        
        result = TrackingService.get_today_status()
        
        assert result["success"] is True
        assert len(result["habits"]) == 1
        
        habit_status = result["habits"][0]
        assert habit_status["name"] == "Exercise"
        assert habit_status["tracked_today"] is True
        assert habit_status["notes"] == "Great workout!"
        assert habit_status["current_streak"] == 5
        
        assert result["summary"]["total_habits"] == 1
        assert result["summary"]["tracked_today"] == 1
        assert result["summary"]["completion_rate"] == 100.0
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    @patch('habits_tracker.core.services.tracking_service.get_today')
    @patch.object(TrackingService, '_calculate_current_streak_for_habit')
    def test_get_today_status_mixed_tracking(self, mock_streak, mock_get_today, mock_get_session):
        """Test today's status with some habits tracked and some not."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Mock two habits
        mock_habit1 = MagicMock()
        mock_habit1.id = 1
        mock_habit1.name = "Exercise"
        mock_habit1.description = "Daily workout"
        mock_habit1.frequency = "daily"
        
        mock_habit2 = MagicMock()
        mock_habit2.id = 2
        mock_habit2.name = "Reading"
        mock_habit2.description = "Read 30 minutes"
        mock_habit2.frequency = "daily"
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_habit1, mock_habit2]
        
        # Mock tracking entries - only first habit tracked
        mock_entry = MagicMock()
        mock_entry.notes = "Great workout!"
        mock_session.query.return_value.filter.return_value.first.side_effect = [mock_entry, None]
        
        mock_streak.return_value = 3
        
        result = TrackingService.get_today_status()
        
        assert result["success"] is True
        assert len(result["habits"]) == 2
        
        # First habit should be tracked
        assert result["habits"][0]["tracked_today"] is True
        assert result["habits"][0]["notes"] == "Great workout!"
        
        # Second habit should not be tracked
        assert result["habits"][1]["tracked_today"] is False
        assert result["habits"][1]["notes"] is None
        
        assert result["summary"]["total_habits"] == 2
        assert result["summary"]["tracked_today"] == 1
        assert result["summary"]["completion_rate"] == 50.0


class TestStreakCalculation:
    """Test streak calculation functionality."""
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    @patch('habits_tracker.core.services.tracking_service.get_today')
    def test_calculate_current_streak_for_habit_no_entries(self, mock_get_today, mock_get_session):
        """Test streak calculation with no entries."""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        result = TrackingService._calculate_current_streak_for_habit(mock_session, 1)
        
        assert result == 0
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    @patch('habits_tracker.core.services.tracking_service.get_today')
    def test_calculate_current_streak_for_habit_current_streak(self, mock_get_today, mock_get_session):
        """Test streak calculation with current streak."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        
        # Mock entries for the last 3 days
        mock_entries = []
        for i in range(3):
            entry = MagicMock()
            entry.date = today - timedelta(days=i)
            mock_entries.append(entry)
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_entries
        
        result = TrackingService._calculate_current_streak_for_habit(mock_session, 1)
        
        assert result == 3
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    @patch('habits_tracker.core.services.tracking_service.get_today')
    def test_calculate_current_streak_for_habit_broken_streak(self, mock_get_today, mock_get_session):
        """Test streak calculation with broken streak."""
        today = date(2025, 7, 11)
        mock_get_today.return_value = today
        
        mock_session = MagicMock()
        
        # Mock entries with a gap (no entry yesterday)
        mock_entry = MagicMock()
        mock_entry.date = today - timedelta(days=2)  # 2 days ago
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_entry]
        
        result = TrackingService._calculate_current_streak_for_habit(mock_session, 1)
        
        assert result == 0


class TestGetHabitEntries:
    """Test getting habit entries functionality."""
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    def test_get_habit_entries_success(self, mock_get_session):
        """Test getting habit entries successfully."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        
        mock_entry = MagicMock()
        mock_entry.date = date(2025, 7, 11)
        mock_entry.completed = True
        mock_entry.notes = "Great workout!"
        mock_entry.tracked_at = datetime.now()
        
        mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_entry]
        
        result = TrackingService.get_habit_entries("Exercise")
        
        assert result["success"] is True
        assert result["habit_name"] == "Exercise"
        assert len(result["entries"]) == 1
        assert result["entries"][0]["date"] == date(2025, 7, 11)
        assert result["entries"][0]["completed"] is True
        assert result["entries"][0]["notes"] == "Great workout!"
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    def test_get_habit_entries_habit_not_found(self, mock_get_session):
        """Test getting entries for habit that doesn't exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = TrackingService.get_habit_entries("NonExistent")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    @patch('habits_tracker.core.services.tracking_service.get_session')
    def test_get_habit_entries_with_date_range(self, mock_get_session):
        """Test getting habit entries with date range filters."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        start_date = date(2025, 7, 1)
        end_date = date(2025, 7, 11)
        
        result = TrackingService.get_habit_entries("Exercise", start_date=start_date, end_date=end_date)
        
        assert result["success"] is True
        assert result["total_entries"] == 0