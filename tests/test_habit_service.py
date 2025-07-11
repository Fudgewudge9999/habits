"""Unit tests for HabitService."""

import pytest
from datetime import datetime, date
from unittest.mock import patch, MagicMock

from habits_tracker.core.services.habit_service import (
    HabitService, 
    HabitValidationError, 
    HabitNotFoundError
)
from habits_tracker.core.models import Habit, TrackingEntry


class TestHabitValidation:
    """Test habit validation methods."""
    
    def test_validate_habit_name_valid(self):
        """Test valid habit name validation."""
        name = HabitService.validate_habit_name("Exercise")
        assert name == "Exercise"
    
    def test_validate_habit_name_strips_whitespace(self):
        """Test habit name whitespace stripping."""
        name = HabitService.validate_habit_name("  Exercise  ")
        assert name == "Exercise"
    
    def test_validate_habit_name_empty_raises_error(self):
        """Test empty habit name raises validation error."""
        with pytest.raises(HabitValidationError, match="cannot be empty"):
            HabitService.validate_habit_name("")
    
    def test_validate_habit_name_whitespace_only_raises_error(self):
        """Test whitespace-only habit name raises validation error."""
        with pytest.raises(HabitValidationError, match="cannot be empty"):
            HabitService.validate_habit_name("   ")
    
    def test_validate_habit_name_too_long_raises_error(self):
        """Test overly long habit name raises validation error."""
        long_name = "x" * (HabitService.MAX_NAME_LENGTH + 1)
        with pytest.raises(HabitValidationError, match="too long"):
            HabitService.validate_habit_name(long_name)
    
    def test_validate_habit_name_invalid_chars_raises_error(self):
        """Test habit name with invalid characters raises validation error."""
        with pytest.raises(HabitValidationError, match="cannot contain newlines"):
            HabitService.validate_habit_name("Exercise\nDaily")
    
    def test_validate_frequency_valid(self):
        """Test valid frequency validation."""
        freq = HabitService.validate_frequency("daily")
        assert freq == "daily"
    
    def test_validate_frequency_normalizes_case(self):
        """Test frequency case normalization."""
        freq = HabitService.validate_frequency("DAILY")
        assert freq == "daily"
    
    def test_validate_frequency_strips_whitespace(self):
        """Test frequency whitespace stripping."""
        freq = HabitService.validate_frequency("  weekly  ")
        assert freq == "weekly"
    
    def test_validate_frequency_defaults_to_daily(self):
        """Test empty frequency defaults to daily."""
        freq = HabitService.validate_frequency("")
        assert freq == "daily"
    
    def test_validate_frequency_invalid_raises_error(self):
        """Test invalid frequency raises validation error."""
        with pytest.raises(HabitValidationError, match="Invalid frequency"):
            HabitService.validate_frequency("invalid")
    
    def test_validate_description_valid(self):
        """Test valid description validation."""
        desc = HabitService.validate_description("Daily exercise routine")
        assert desc == "Daily exercise routine"
    
    def test_validate_description_none(self):
        """Test None description validation."""
        desc = HabitService.validate_description(None)
        assert desc is None
    
    def test_validate_description_empty_string_returns_none(self):
        """Test empty string description returns None."""
        desc = HabitService.validate_description("")
        assert desc is None
    
    def test_validate_description_whitespace_only_returns_none(self):
        """Test whitespace-only description returns None."""
        desc = HabitService.validate_description("   ")
        assert desc is None
    
    def test_validate_description_too_long_raises_error(self):
        """Test overly long description raises validation error."""
        long_desc = "x" * (HabitService.MAX_DESCRIPTION_LENGTH + 1)
        with pytest.raises(HabitValidationError, match="too long"):
            HabitService.validate_description(long_desc)


class TestHabitCRUD:
    """Test habit CRUD operations."""
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_create_habit_success(self, mock_get_session):
        """Test successful habit creation."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_habit.name = "Exercise"
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()
        
        with patch('habits_tracker.core.services.habit_service.Habit') as mock_habit_class:
            mock_habit_class.return_value = mock_habit
            
            result = HabitService.create_habit("Exercise", "daily", "30 min workout")
            
            assert result == mock_habit
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_create_habit_already_exists_active(self, mock_get_session):
        """Test creating habit that already exists and is active."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        existing_habit = MagicMock()
        existing_habit.active = True
        mock_session.query.return_value.filter.return_value.first.return_value = existing_habit
        
        with pytest.raises(HabitValidationError, match="already exists"):
            HabitService.create_habit("Exercise")
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_create_habit_reactivates_archived(self, mock_get_session):
        """Test creating habit reactivates archived habit."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        existing_habit = MagicMock()
        existing_habit.active = False
        existing_habit.restore = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = existing_habit
        
        result = HabitService.create_habit("Exercise", "weekly", "New description")
        
        assert result == existing_habit
        existing_habit.restore.assert_called_once()
        assert existing_habit.frequency == "weekly"
        assert existing_habit.description == "New description"
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_get_habit_by_name_found(self, mock_get_session):
        """Test getting habit by name when found."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_session.query.return_value.filter.return_value.filter.return_value.first.return_value = mock_habit
        
        result = HabitService.get_habit_by_name("Exercise")
        
        assert result == mock_habit
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_get_habit_by_name_not_found(self, mock_get_session):
        """Test getting habit by name when not found."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        result = HabitService.get_habit_by_name("NonExistent")
        
        assert result is None
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_get_habit_by_name_include_archived(self, mock_get_session):
        """Test getting habit by name including archived habits."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
        
        result = HabitService.get_habit_by_name("Exercise", include_archived=True)
        
        assert result == mock_habit
        # Should not filter by active when include_archived=True
        assert mock_session.query.return_value.filter.call_count == 1
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_list_habits_active_filter(self, mock_get_session):
        """Test listing habits with active filter."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_habit.name = "Exercise"
        mock_habit.description = "Daily workout"
        mock_habit.frequency = "daily"
        mock_habit.created_at = datetime.now()
        mock_habit.active = True
        mock_habit.archived_at = None
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_habit]
        
        with patch.object(HabitService, '_calculate_habit_stats', return_value={"streak": 5}):
            result = HabitService.list_habits("active", include_stats=True)
        
        assert len(result) == 1
        assert result[0]["name"] == "Exercise"
        assert result[0]["streak"] == 5
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_list_habits_no_stats(self, mock_get_session):
        """Test listing habits without statistics."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        mock_habit.name = "Exercise"
        mock_habit.description = "Daily workout"
        mock_habit.frequency = "daily"
        mock_habit.created_at = datetime.now()
        mock_habit.active = True
        mock_habit.archived_at = None
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_habit]
        
        result = HabitService.list_habits("active", include_stats=False)
        
        assert len(result) == 1
        assert result[0]["name"] == "Exercise"
        assert "streak" not in result[0]
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_remove_habit_soft_delete(self, mock_get_session):
        """Test removing habit with soft delete."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.archive = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
        
        result = HabitService.remove_habit("Exercise", permanent=False)
        
        assert result is True
        mock_habit.archive.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_remove_habit_permanent_delete(self, mock_get_session):
        """Test removing habit with permanent delete."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
        
        result = HabitService.remove_habit("Exercise", permanent=True)
        
        assert result is True
        mock_session.delete.assert_called_once_with(mock_habit)
        mock_session.commit.assert_called_once()
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_remove_habit_not_found(self, mock_get_session):
        """Test removing habit that doesn't exist."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = HabitService.remove_habit("NonExistent")
        
        assert result is False
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_restore_habit_success(self, mock_get_session):
        """Test restoring archived habit."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        mock_habit = MagicMock()
        mock_habit.restore = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
        
        result = HabitService.restore_habit("Exercise")
        
        assert result is True
        mock_habit.restore.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_restore_habit_not_found(self, mock_get_session):
        """Test restoring habit that doesn't exist or isn't archived."""
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        result = HabitService.restore_habit("NonExistent")
        
        assert result is False


class TestHabitStats:
    """Test habit statistics calculation."""
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    @patch('habits_tracker.core.services.analytics_service.AnalyticsService._calculate_current_streak')
    @patch('habits_tracker.core.services.analytics_service.AnalyticsService._calculate_longest_streak')
    def test_calculate_habit_stats_with_entries(self, mock_longest_streak, mock_current_streak, mock_get_session):
        """Test habit stats calculation with tracking entries."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        mock_entry1 = MagicMock()
        mock_entry1.date = date.today()
        mock_entry2 = MagicMock() 
        mock_entry2.date = date.today()
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_entry1, mock_entry2]
        
        mock_current_streak.return_value = 5
        mock_longest_streak.return_value = 10
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        
        result = HabitService._calculate_habit_stats(mock_session, mock_habit)
        
        expected = {
            "streak": 5,
            "longest_streak": 10,
            "total_completions": 2,
            "last_tracked": date.today()
        }
        
        assert result == expected
    
    @patch('habits_tracker.core.services.habit_service.get_session')
    def test_calculate_habit_stats_no_entries(self, mock_get_session):
        """Test habit stats calculation with no tracking entries."""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        mock_habit = MagicMock()
        mock_habit.id = 1
        
        result = HabitService._calculate_habit_stats(mock_session, mock_habit)
        
        expected = {
            "streak": 0,
            "longest_streak": 0,
            "total_completions": 0,
            "last_tracked": None
        }
        
        assert result == expected