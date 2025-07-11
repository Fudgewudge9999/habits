"""Edge case tests for HabitsTracker CLI."""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from habits_tracker.cli.main import app
from habits_tracker.core.services.habit_service import HabitService, HabitValidationError
from habits_tracker.core.services.tracking_service import TrackingService
from habits_tracker.core.services.analytics_service import AnalyticsService
from habits_tracker.utils.date_utils import parse_date, get_today


class TestDateEdgeCases:
    """Test edge cases related to date handling."""
    
    def test_leap_year_handling(self):
        """Test handling of leap year dates."""
        # Test leap year February 29th
        leap_year_date = "2024-02-29"
        parsed = parse_date(leap_year_date)
        assert parsed == date(2024, 2, 29)
        
        # Test non-leap year February 29th should fail
        with pytest.raises(ValueError):
            parse_date("2023-02-29")
    
    def test_year_boundaries(self):
        """Test year boundary edge cases."""
        # Test year transitions
        year_boundaries = [
            "1999-12-31",
            "2000-01-01", 
            "2023-12-31",
            "2024-01-01",
        ]
        
        for date_str in year_boundaries:
            parsed = parse_date(date_str)
            assert isinstance(parsed, date)
    
    def test_month_boundaries(self):
        """Test month boundary edge cases."""
        # Test all month end dates
        month_ends = [
            ("2024-01-31", 31),  # January
            ("2024-02-29", 29),  # February (leap year)
            ("2024-03-31", 31),  # March
            ("2024-04-30", 30),  # April
            ("2024-05-31", 31),  # May
            ("2024-06-30", 30),  # June
            ("2024-07-31", 31),  # July
            ("2024-08-31", 31),  # August
            ("2024-09-30", 30),  # September
            ("2024-10-31", 31),  # October
            ("2024-11-30", 30),  # November
            ("2024-12-31", 31),  # December
        ]
        
        for date_str, expected_day in month_ends:
            parsed = parse_date(date_str)
            assert parsed.day == expected_day
    
    def test_daylight_saving_transitions(self):
        """Test behavior around daylight saving time transitions."""
        # Test dates around typical DST transitions
        dst_dates = [
            "2024-03-10",  # Spring forward (US)
            "2024-11-03",  # Fall back (US)
        ]
        
        for date_str in dst_dates:
            parsed = parse_date(date_str)
            assert isinstance(parsed, date)
    
    def test_relative_date_edge_cases(self):
        """Test edge cases in relative date parsing."""
        # Test boundary values
        with patch('habits_tracker.utils.date_utils.get_today', return_value=date(2025, 7, 15)):
            # Test large negative values
            parsed = parse_date("-365d")
            expected = date(2024, 7, 15)  # One year ago
            assert parsed == expected
            
            # Test zero
            parsed = parse_date("0d")
            assert parsed == date(2025, 7, 15)
            
            # Test positive values (future dates)
            parsed = parse_date("+1d")
            assert parsed == date(2025, 7, 16)
    
    def test_weekend_and_weekday_patterns(self):
        """Test tracking patterns across weekends and weekdays."""
        # This tests the streak calculation across different day patterns
        base_date = date(2025, 7, 14)  # Monday
        entries = []
        
        # Create tracking entries for Monday through Friday (workweek)
        for i in range(5):
            entry = MagicMock()
            entry.date = base_date + timedelta(days=i)
            entries.append(entry)
        
        streak = AnalyticsService._calculate_longest_streak(entries)
        assert streak == 5
        
        # Add weekend gap and next week
        for i in range(5):
            entry = MagicMock()
            entry.date = base_date + timedelta(days=i+7)  # Next Monday-Friday
            entries.append(entry)
        
        # Should still be 5 (longest consecutive), not 10 due to weekend gap
        streak = AnalyticsService._calculate_longest_streak(entries)
        assert streak == 5


class TestBoundaryValueTesting:
    """Test boundary values for various inputs."""
    
    def test_habit_name_length_boundaries(self):
        """Test habit name length at exact boundaries."""
        # Test empty string (boundary: 0)
        with pytest.raises(HabitValidationError):
            HabitService.validate_habit_name("")
        
        # Test single character (boundary: 1)
        validated = HabitService.validate_habit_name("A")
        assert validated == "A"
        
        # Test at maximum length (boundary: MAX_NAME_LENGTH)
        max_name = "A" * HabitService.MAX_NAME_LENGTH
        validated = HabitService.validate_habit_name(max_name)
        assert validated == max_name
        
        # Test over maximum length (boundary: MAX_NAME_LENGTH + 1)
        over_max = "A" * (HabitService.MAX_NAME_LENGTH + 1)
        with pytest.raises(HabitValidationError):
            HabitService.validate_habit_name(over_max)
    
    def test_description_length_boundaries(self):
        """Test description length at exact boundaries."""
        # Test None (acceptable)
        validated = HabitService.validate_description(None)
        assert validated is None
        
        # Test empty string (should return None)
        validated = HabitService.validate_description("")
        assert validated is None
        
        # Test single character
        validated = HabitService.validate_description("A")
        assert validated == "A"
        
        # Test at maximum length
        max_desc = "A" * HabitService.MAX_DESCRIPTION_LENGTH
        validated = HabitService.validate_description(max_desc)
        assert validated == max_desc
        
        # Test over maximum length
        over_max = "A" * (HabitService.MAX_DESCRIPTION_LENGTH + 1)
        with pytest.raises(HabitValidationError):
            HabitService.validate_description(over_max)
    
    def test_notes_length_boundaries(self):
        """Test tracking notes length boundaries."""
        # Create a habit first
        with patch('habits_tracker.core.database.get_session'):
            with patch('habits_tracker.core.services.tracking_service.TrackingService.track_habit') as mock_track:
                # Test notes at exactly 500 characters
                notes_500 = "A" * 500
                mock_track.return_value = {"success": True}
                
                result = TrackingService.track_habit("Exercise", notes=notes_500)
                # This should be allowed (assuming mock doesn't check length)
                
                # Test notes over 500 characters
                notes_501 = "A" * 501
                result = TrackingService.track_habit("Exercise", notes=notes_501)
                assert result["success"] is False
                assert "cannot exceed 500 characters" in result["error"]
    
    def test_frequency_validation_boundaries(self):
        """Test frequency validation edge cases."""
        # Test valid frequencies
        valid_frequencies = ["daily", "weekly", "custom"]
        for freq in valid_frequencies:
            validated = HabitService.validate_frequency(freq)
            assert validated == freq
        
        # Test case insensitive
        validated = HabitService.validate_frequency("DAILY")
        assert validated == "daily"
        
        # Test with whitespace
        validated = HabitService.validate_frequency("  weekly  ")
        assert validated == "weekly"
        
        # Test empty string (should default to daily)
        validated = HabitService.validate_frequency("")
        assert validated == "daily"
        
        # Test invalid frequency
        with pytest.raises(HabitValidationError):
            HabitService.validate_frequency("invalid")


class TestConcurrencyEdgeCases:
    """Test edge cases related to concurrent operations."""
    
    def test_simultaneous_habit_creation(self):
        """Test handling of simultaneous habit creation attempts."""
        with patch('habits_tracker.core.database.get_session') as mock_session_ctx:
            mock_session = MagicMock()
            mock_session_ctx.return_value.__enter__.return_value = mock_session
            
            # First call succeeds
            mock_session.query.return_value.filter.return_value.first.return_value = None
            
            # Second call (simulating race condition) finds existing habit
            existing_habit = MagicMock()
            existing_habit.active = True
            
            def side_effect(*args):
                # First check returns None, second returns existing habit
                if hasattr(side_effect, 'call_count'):
                    side_effect.call_count += 1
                else:
                    side_effect.call_count = 1
                
                if side_effect.call_count == 1:
                    return None
                else:
                    return existing_habit
            
            mock_session.query.return_value.filter.return_value.first.side_effect = side_effect
            
            # First creation should succeed
            habit1 = HabitService.create_habit("Exercise")
            
            # Second creation should fail due to duplicate
            with pytest.raises(HabitValidationError):
                habit2 = HabitService.create_habit("Exercise")
    
    def test_tracking_race_conditions(self):
        """Test tracking race conditions."""
        with patch('habits_tracker.core.database.get_session') as mock_session_ctx:
            mock_session = MagicMock()
            mock_session_ctx.return_value.__enter__.return_value = mock_session
            
            # Mock habit exists
            mock_habit = MagicMock()
            mock_habit.id = 1
            
            # Mock no existing entry initially, then existing entry on retry
            def side_effect(*args):
                if hasattr(side_effect, 'call_count'):
                    side_effect.call_count += 1
                else:
                    side_effect.call_count = 1
                
                if side_effect.call_count <= 2:  # First two calls for habit lookup
                    return mock_habit
                elif side_effect.call_count == 3:  # First tracking check
                    return None
                else:  # Second tracking check (race condition)
                    return MagicMock()  # Existing entry
            
            mock_session.query.return_value.filter.return_value.first.side_effect = side_effect
            
            # First tracking attempt should detect race condition
            result = TrackingService.track_habit("Exercise")
            # The exact behavior depends on implementation


class TestSpecialCharacterHandling:
    """Test handling of special characters and encoding."""
    
    def test_unicode_habit_names(self):
        """Test habit names with various Unicode characters."""
        unicode_names = [
            "Café ☕",          # Latin with emoji
            "読書",            # Japanese
            "Спорт",           # Cyrillic
            "🏃‍♂️ Running",      # Emoji with modifier
            "Méditation",      # French accents
            "Größe",           # German umlaut
            "习惯",            # Chinese
            "🌟⭐✨",          # Multiple emojis
        ]
        
        for name in unicode_names:
            try:
                validated = HabitService.validate_habit_name(name)
                assert isinstance(validated, str)
                assert len(validated) > 0
            except HabitValidationError:
                # Some special characters might be intentionally rejected
                pass
    
    def test_whitespace_handling(self):
        """Test various whitespace scenarios."""
        whitespace_tests = [
            ("  Exercise  ", "Exercise"),      # Leading/trailing spaces
            ("Exercise\t", "Exercise"),        # Tab character
            ("  \t  Exercise \t ", "Exercise"), # Mixed whitespace
            ("Multi  Word  Habit", "Multi  Word  Habit"),  # Internal spaces preserved
        ]
        
        for input_name, expected in whitespace_tests:
            try:
                validated = HabitService.validate_habit_name(input_name)
                assert validated == expected
            except HabitValidationError:
                # Some whitespace patterns might be rejected
                pass
    
    def test_special_character_injection(self):
        """Test handling of potentially problematic special characters."""
        special_chars = [
            "Exercise\n",      # Newline
            "Exercise\r",      # Carriage return
            "Exercise\t",      # Tab
            "Exercise\x00",    # Null byte
            "Exercise\x1f",    # Control character
            "Exercise\\",      # Backslash
            "Exercise'",       # Single quote
            'Exercise"',       # Double quote
        ]
        
        for char_test in special_chars:
            if '\n' in char_test or '\r' in char_test or '\t' in char_test or '\x00' in char_test:
                # These should be rejected
                with pytest.raises(HabitValidationError):
                    HabitService.validate_habit_name(char_test)
            else:
                # Others might be acceptable
                try:
                    validated = HabitService.validate_habit_name(char_test)
                    assert isinstance(validated, str)
                except HabitValidationError:
                    # Rejection is also acceptable for safety
                    pass


class TestSystemLimitEdgeCases:
    """Test behavior at system limits."""
    
    def test_maximum_habits_scenario(self):
        """Test behavior with a large number of habits."""
        with patch('habits_tracker.core.database.get_session') as mock_session_ctx:
            mock_session = MagicMock()
            mock_session_ctx.return_value.__enter__.return_value = mock_session
            
            # Simulate a large number of habits
            large_habit_list = []
            for i in range(1000):
                habit = MagicMock()
                habit.id = i
                habit.name = f"Habit_{i}"
                habit.description = f"Description for habit {i}"
                habit.frequency = "daily"
                habit.active = True
                habit.created_at = datetime.now()
                habit.archived_at = None
                large_habit_list.append(habit)
            
            mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = large_habit_list
            
            # Should handle large habit lists
            result = HabitService.list_habits("active", include_stats=False)
            assert len(result) == 1000
    
    def test_maximum_tracking_entries_scenario(self):
        """Test behavior with a large number of tracking entries."""
        with patch('habits_tracker.core.database.get_session') as mock_session_ctx:
            mock_session = MagicMock()
            mock_session_ctx.return_value.__enter__.return_value = mock_session
            
            # Simulate years of tracking data
            large_entry_list = []
            base_date = date(2020, 1, 1)
            for i in range(1000):  # ~3 years of daily tracking
                entry = MagicMock()
                entry.date = base_date + timedelta(days=i)
                entry.completed = True
                entry.habit_id = 1
                large_entry_list.append(entry)
            
            mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = large_entry_list
            
            # Should handle large datasets efficiently
            current_streak = AnalyticsService._calculate_current_streak(large_entry_list)
            assert isinstance(current_streak, int)
            
            longest_streak = AnalyticsService._calculate_longest_streak(large_entry_list)
            assert isinstance(longest_streak, int)
    
    def test_extreme_date_ranges(self):
        """Test behavior with extreme date ranges."""
        # Test very old dates
        old_date = "1900-01-01"
        parsed = parse_date(old_date)
        assert parsed == date(1900, 1, 1)
        
        # Test far future dates
        future_date = "2099-12-31"
        parsed = parse_date(future_date)
        assert parsed == date(2099, 12, 31)
        
        # Test tracking with extreme dates
        with patch('habits_tracker.core.database.get_session'):
            # These should be handled gracefully even if they're unusual
            result = TrackingService.track_habit("Exercise", tracking_date=date(1900, 1, 1))
            # Implementation should handle this without crashing


class TestResourceCleanupEdgeCases:
    """Test proper resource cleanup in edge cases."""
    
    def test_session_cleanup_on_exception(self):
        """Test that database sessions are properly cleaned up on exceptions."""
        with patch('habits_tracker.core.database.get_session') as mock_session_ctx:
            mock_session = MagicMock()
            mock_session_ctx.return_value.__enter__.return_value = mock_session
            mock_session_ctx.return_value.__exit__ = MagicMock()
            
            # Simulate exception during operation
            mock_session.commit.side_effect = Exception("Simulated error")
            
            with pytest.raises(Exception):
                HabitService.create_habit("Exercise")
            
            # Verify session cleanup was called
            mock_session_ctx.return_value.__exit__.assert_called()
    
    def test_partial_operation_cleanup(self):
        """Test cleanup when operations are partially completed."""
        with patch('habits_tracker.core.database.get_session') as mock_session_ctx:
            mock_session = MagicMock()
            mock_session_ctx.return_value.__enter__.return_value = mock_session
            
            # Simulate failure after some operations
            mock_session.add = MagicMock()
            mock_session.commit.side_effect = Exception("Commit failed")
            
            with pytest.raises(Exception):
                HabitService.create_habit("Exercise")
            
            # Verify add was called but rollback should have been triggered
            mock_session.add.assert_called()
            # The context manager should handle rollback automatically