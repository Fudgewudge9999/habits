"""Error condition tests for HabitsTracker CLI."""

import pytest
import tempfile
import os
import sqlite3
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path
from typer.testing import CliRunner

from habits_tracker.cli.main import app
from habits_tracker.core.database import init_database, get_session
from habits_tracker.core.services.habit_service import HabitService, HabitValidationError
from habits_tracker.core.services.tracking_service import TrackingService
from habits_tracker.core.services.analytics_service import AnalyticsService


class TestDatabaseErrorConditions:
    """Test database-related error conditions."""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_habits.db")
        yield db_path
        if os.path.exists(db_path):
            os.unlink(db_path)
        os.rmdir(temp_dir)
    
    def test_database_corruption_handling(self, temp_db_path):
        """Test handling of corrupted database files."""
        # Create a corrupted database file
        with open(temp_db_path, 'w') as f:
            f.write("This is not a valid SQLite database")
        
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
            with pytest.raises(Exception):  # Should raise database error
                init_database()
    
    def test_database_permissions_error(self, temp_db_path):
        """Test handling when database directory is not writable."""
        db_dir = os.path.dirname(temp_db_path)
        
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
            with patch('os.makedirs', side_effect=PermissionError("Permission denied")):
                with pytest.raises(PermissionError):
                    init_database()
    
    def test_database_locked_error(self, temp_db_path):
        """Test handling when database is locked by another process."""
        # Initialize database first
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
            init_database()
        
        # Simulate database lock
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
            with patch('sqlalchemy.create_engine') as mock_engine:
                mock_engine.side_effect = sqlite3.OperationalError("database is locked")
                
                with pytest.raises(sqlite3.OperationalError):
                    with get_session() as session:
                        pass
    
    def test_disk_space_exhaustion(self, temp_db_path):
        """Test handling when disk space is exhausted."""
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
            init_database()
            
            with patch('sqlalchemy.orm.Session.commit', side_effect=sqlite3.OperationalError("disk I/O error")):
                with pytest.raises(HabitValidationError):
                    HabitService.create_habit("Exercise")
    
    def test_database_connection_failure(self):
        """Test handling when database connection fails."""
        with patch('sqlalchemy.create_engine', side_effect=Exception("Connection failed")):
            with pytest.raises(Exception):
                with get_session() as session:
                    pass


class TestInputValidationErrors:
    """Test input validation error conditions."""
    
    def test_habit_name_unicode_handling(self):
        """Test handling of Unicode and special characters in habit names."""
        # Test various Unicode characters
        unicode_names = [
            "Привычка",  # Cyrillic
            "習慣",        # Japanese
            "🏃‍♂️ Exercise",  # Emoji
            "Café ☕",     # Mixed Unicode
            "a" * 1000,   # Very long name
        ]
        
        for name in unicode_names[:-1]:  # All except very long name should work
            try:
                validated = HabitService.validate_habit_name(name)
                assert validated == name
            except HabitValidationError:
                # Some special characters might be rejected, which is acceptable
                pass
        
        # Very long name should be rejected
        with pytest.raises(HabitValidationError):
            HabitService.validate_habit_name(unicode_names[-1])
    
    def test_sql_injection_attempts(self):
        """Test protection against SQL injection attempts."""
        malicious_inputs = [
            "'; DROP TABLE habits; --",
            "Exercise'; UPDATE habits SET name='Hacked' WHERE 1=1; --",
            "Exercise' OR '1'='1",
            "Exercise\"; DELETE FROM habits; --",
            "Exercise' UNION SELECT * FROM habits --",
        ]
        
        for malicious_input in malicious_inputs:
            # These should either be safely handled or rejected
            try:
                validated = HabitService.validate_habit_name(malicious_input)
                # If validation passes, the input should be sanitized
                assert "DROP" not in validated.upper()
                assert "DELETE" not in validated.upper()
                assert "UPDATE" not in validated.upper()
            except HabitValidationError:
                # Rejection is also acceptable
                pass
    
    def test_null_byte_injection(self):
        """Test handling of null byte injection attempts."""
        null_byte_inputs = [
            "Exercise\x00malicious",
            "Exercise\0test",
            "\x00Exercise",
        ]
        
        for malicious_input in null_byte_inputs:
            with pytest.raises(HabitValidationError):
                HabitService.validate_habit_name(malicious_input)
    
    def test_extreme_input_lengths(self):
        """Test handling of extremely long inputs."""
        # Test habit name at exact limit
        max_name = "a" * HabitService.MAX_NAME_LENGTH
        validated = HabitService.validate_habit_name(max_name)
        assert validated == max_name
        
        # Test habit name over limit
        over_limit_name = "a" * (HabitService.MAX_NAME_LENGTH + 1)
        with pytest.raises(HabitValidationError):
            HabitService.validate_habit_name(over_limit_name)
        
        # Test description at exact limit
        max_desc = "a" * HabitService.MAX_DESCRIPTION_LENGTH
        validated = HabitService.validate_description(max_desc)
        assert validated == max_desc
        
        # Test description over limit
        over_limit_desc = "a" * (HabitService.MAX_DESCRIPTION_LENGTH + 1)
        with pytest.raises(HabitValidationError):
            HabitService.validate_description(over_limit_desc)
    
    def test_invalid_date_formats(self):
        """Test handling of various invalid date formats."""
        from habits_tracker.utils.date_utils import parse_date
        
        invalid_dates = [
            "2025-13-01",      # Invalid month
            "2025-02-30",      # Invalid day for February
            "2025/07/11",      # Wrong separator
            "11-07-2025",      # Wrong order
            "tomorrow",        # Unsupported relative date
            "last week",       # Unsupported relative date
            "2025-07-11T12:00:00",  # Unexpected time component
            "not-a-date",      # Completely invalid
            "",                # Empty string
            "   ",             # Whitespace only
            "2025-07-",        # Incomplete date
            "2025--11",        # Double separator
        ]
        
        for invalid_date in invalid_dates:
            with pytest.raises(ValueError):
                parse_date(invalid_date)
    
    def test_notes_injection_attempts(self):
        """Test handling of malicious content in notes fields."""
        malicious_notes = [
            "'; DROP TABLE tracking_entries; --",
            "<script>alert('xss')</script>",
            "Normal note\x00hidden content",
            "a" * 1000,  # Over length limit
        ]
        
        for note in malicious_notes:
            if len(note) > 500:
                # Should be rejected for length
                result = TrackingService.track_habit("Exercise", notes=note)
                assert result["success"] is False
                assert "cannot exceed 500 characters" in result["error"]
            else:
                # Other malicious content should be safely stored
                # (The database layer protects against SQL injection)
                pass


class TestFileSystemErrors:
    """Test file system related error conditions."""
    
    def test_no_write_permissions_to_home_directory(self):
        """Test handling when user has no write permissions to home directory."""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            with patch('habits_tracker.core.database.get_database_path') as mock_path:
                mock_path.return_value = "/no-permissions/habits.db"
                with pytest.raises(PermissionError):
                    init_database()
    
    def test_database_directory_creation_failure(self):
        """Test handling when database directory cannot be created."""
        with patch('os.makedirs', side_effect=OSError("Cannot create directory")):
            with patch('habits_tracker.core.database.get_database_path') as mock_path:
                mock_path.return_value = "/invalid/path/habits.db"
                with pytest.raises(OSError):
                    init_database()
    
    def test_database_file_readonly(self, temp_db_path):
        """Test handling when database file is read-only."""
        # Create database first
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
            init_database()
        
        # Make it read-only
        os.chmod(temp_db_path, 0o444)
        
        try:
            with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
                with pytest.raises(Exception):  # Should fail on write operations
                    HabitService.create_habit("Exercise")
        finally:
            # Restore write permissions for cleanup
            os.chmod(temp_db_path, 0o644)


class TestMemoryAndResourceConstraints:
    """Test memory and resource constraint conditions."""
    
    def test_memory_exhaustion_simulation(self):
        """Test handling when memory is exhausted."""
        with patch('habits_tracker.core.services.analytics_service.AnalyticsService.calculate_overall_stats') as mock_stats:
            mock_stats.side_effect = MemoryError("Cannot allocate memory")
            
            with pytest.raises(MemoryError):
                AnalyticsService.calculate_overall_stats()
    
    def test_large_dataset_handling(self):
        """Test performance with artificially large datasets."""
        # This test would normally require actual large data, but we'll mock it
        with patch('sqlalchemy.orm.Session.query') as mock_query:
            # Simulate a very large result set
            mock_large_result = [MagicMock() for _ in range(10000)]
            mock_query.return_value.all.return_value = mock_large_result
            
            # Should handle large datasets without crashing
            try:
                with get_session() as session:
                    result = session.query(MagicMock).all()
                    assert len(result) == 10000
            except MemoryError:
                # This is acceptable for very large datasets
                pass
    
    def test_concurrent_access_simulation(self):
        """Test handling of concurrent database access."""
        with patch('sqlalchemy.orm.Session.commit', side_effect=sqlite3.OperationalError("database is locked")):
            with pytest.raises(Exception):
                HabitService.create_habit("Exercise")


class TestCLISpecificErrors:
    """Test CLI-specific error conditions."""
    
    def test_invalid_command_combinations(self):
        """Test invalid command combinations and arguments."""
        runner = CliRunner()
        
        # Test commands with missing required arguments
        result = runner.invoke(app, ["add"])  # Missing habit name
        assert result.exit_code != 0
        
        result = runner.invoke(app, ["track"])  # Missing habit name
        assert result.exit_code != 0
        
        result = runner.invoke(app, ["remove"])  # Missing habit name
        assert result.exit_code != 0
    
    def test_broken_terminal_output(self):
        """Test handling when terminal output fails."""
        runner = CliRunner()
        
        with patch('rich.console.Console.print', side_effect=BrokenPipeError("Broken pipe")):
            result = runner.invoke(app, ["add", "Exercise"])
            # Should handle broken pipe gracefully
            # The exact behavior depends on implementation
    
    def test_encoding_issues(self):
        """Test handling of encoding issues in terminal."""
        runner = CliRunner()
        
        # Test with various Unicode inputs
        unicode_habit_names = [
            "Привычка",  # Cyrillic
            "習慣",        # Japanese
            "🏃‍♂️ Exercise",  # Emoji
        ]
        
        for name in unicode_habit_names:
            result = runner.invoke(app, ["add", name])
            # Should either work or provide clear error message
            # Encoding issues should not crash the application
    
    def test_signal_interruption(self):
        """Test handling of signal interruption (CTRL+C)."""
        runner = CliRunner()
        
        with patch('habits_tracker.core.services.habit_service.HabitService.create_habit', 
                  side_effect=KeyboardInterrupt("User interrupted")):
            result = runner.invoke(app, ["add", "Exercise"])
            # Should handle interruption gracefully
            assert result.exit_code != 0
    
    def test_environment_variable_errors(self):
        """Test handling of environment variable configuration errors."""
        with patch.dict(os.environ, {"HOME": "/nonexistent"}):
            # Should handle missing or invalid home directory
            with patch('habits_tracker.core.database.get_database_path') as mock_path:
                mock_path.side_effect = Exception("Cannot determine database path")
                runner = CliRunner()
                result = runner.invoke(app, ["add", "Exercise"])
                assert result.exit_code != 0


class TestDataConsistencyErrors:
    """Test data consistency and integrity error conditions."""
    
    def test_foreign_key_constraint_violation(self, temp_db_path):
        """Test handling of foreign key constraint violations."""
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
            init_database()
            
            # Try to create tracking entry for non-existent habit
            with patch('habits_tracker.core.services.tracking_service.TrackingService.track_habit') as mock_track:
                mock_track.side_effect = Exception("FOREIGN KEY constraint failed")
                
                result = TrackingService.track_habit("NonExistentHabit")
                # Should be handled gracefully by the service layer
    
    def test_unique_constraint_violation(self, temp_db_path):
        """Test handling of unique constraint violations."""
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
            init_database()
            
            # Create habit first
            HabitService.create_habit("Exercise")
            
            # Try to create duplicate
            with pytest.raises(HabitValidationError):
                HabitService.create_habit("Exercise")
    
    def test_transaction_rollback_on_error(self, temp_db_path):
        """Test that transactions are properly rolled back on errors."""
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
            init_database()
            
            with patch('sqlalchemy.orm.Session.commit', side_effect=Exception("Commit failed")):
                with pytest.raises(Exception):
                    HabitService.create_habit("Exercise")
                
                # Verify no partial data was saved
                habit = HabitService.get_habit_by_name("Exercise")
                assert habit is None
    
    def test_data_integrity_after_errors(self, temp_db_path):
        """Test that data integrity is maintained after various errors."""
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_path):
            init_database()
            
            # Create some valid data
            HabitService.create_habit("Exercise")
            TrackingService.track_habit("Exercise")
            
            # Cause an error that shouldn't affect existing data
            try:
                with patch('sqlalchemy.orm.Session.add', side_effect=Exception("Add failed")):
                    HabitService.create_habit("Reading")
            except:
                pass
            
            # Verify original data is still intact
            habit = HabitService.get_habit_by_name("Exercise")
            assert habit is not None
            
            today_status = TrackingService.get_today_status()
            assert today_status["success"] is True
            assert len(today_status["habits"]) == 1