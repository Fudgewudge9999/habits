"""Integration tests for CLI commands."""

import pytest
import tempfile
import os
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from habits_tracker.cli.main import app
from habits_tracker.core.database import init_database, get_session
from habits_tracker.core.models import Habit, TrackingEntry


class TestCLIIntegration:
    """Integration tests for CLI commands using real database."""
    
    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Set up a temporary database for each test."""
        # Create temporary directory for test database
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_habits.db")
        
        # Patch the database path to use our test database
        with patch('habits_tracker.core.database.get_database_path', return_value=self.test_db_path):
            # Initialize the test database
            init_database()
            yield
        
        # Cleanup
        if os.path.exists(self.test_db_path):
            os.unlink(self.test_db_path)
        os.rmdir(self.temp_dir)
    
    def run_command(self, command: str):
        """Helper to run CLI commands with test database."""
        runner = CliRunner()
        with patch('habits_tracker.core.database.get_database_path', return_value=self.test_db_path):
            return runner.invoke(app, command.split())


class TestHabitCommands(TestCLIIntegration):
    """Test habit management CLI commands."""
    
    def test_add_habit_success(self):
        """Test adding a habit successfully."""
        result = self.run_command("add Exercise")
        
        assert result.exit_code == 0
        assert "Successfully added habit 'Exercise'" in result.stdout
        assert "Next steps:" in result.stdout
    
    def test_add_habit_with_options(self):
        """Test adding a habit with frequency and description."""
        result = self.run_command("add 'Read Books' --frequency weekly --description 'Read for 30 minutes'")
        
        assert result.exit_code == 0
        assert "Successfully added habit 'Read Books'" in result.stdout
    
    def test_add_habit_duplicate(self):
        """Test adding a duplicate habit."""
        # Add first habit
        self.run_command("add Exercise")
        
        # Try to add duplicate
        result = self.run_command("add Exercise")
        
        assert result.exit_code == 1
        assert "already exists" in result.stdout
    
    def test_add_habit_invalid_frequency(self):
        """Test adding a habit with invalid frequency."""
        result = self.run_command("add Exercise --frequency invalid")
        
        assert result.exit_code == 1
        assert "Invalid frequency" in result.stdout
    
    def test_list_habits_empty(self):
        """Test listing habits when none exist."""
        result = self.run_command("list")
        
        assert result.exit_code == 0
        assert "No habits found" in result.stdout
        assert "Use 'habits add'" in result.stdout
    
    def test_list_habits_with_data(self):
        """Test listing habits with existing data."""
        # Add some habits
        self.run_command("add Exercise --description 'Daily workout'")
        self.run_command("add Reading --frequency weekly")
        
        result = self.run_command("list")
        
        assert result.exit_code == 0
        assert "Exercise" in result.stdout
        assert "Reading" in result.stdout
        assert "Daily workout" in result.stdout
    
    def test_list_habits_with_filter(self):
        """Test listing habits with filter."""
        # Add and then archive a habit
        self.run_command("add Exercise")
        self.run_command("remove Exercise")
        
        # List active habits (should be empty)
        result = self.run_command("list --filter active")
        assert result.exit_code == 0
        assert "No habits found" in result.stdout
        
        # List archived habits
        result = self.run_command("list --filter archived")
        assert result.exit_code == 0
        assert "Exercise" in result.stdout
    
    def test_remove_habit_success(self):
        """Test removing a habit successfully."""
        # Add habit first
        self.run_command("add Exercise")
        
        # Remove it (use echo to simulate 'y' confirmation)
        with patch('typer.confirm', return_value=True):
            result = self.run_command("remove Exercise")
        
        assert result.exit_code == 0
        assert "Successfully archived habit 'Exercise'" in result.stdout
    
    def test_remove_habit_not_found(self):
        """Test removing a habit that doesn't exist."""
        with patch('typer.confirm', return_value=True):
            result = self.run_command("remove NonExistent")
        
        assert result.exit_code == 1
        assert "not found" in result.stdout
    
    def test_delete_habit_success(self):
        """Test permanently deleting a habit."""
        # Add habit first
        self.run_command("add Exercise")
        
        # Delete it permanently
        result = self.run_command("delete Exercise --confirm")
        
        assert result.exit_code == 0
        assert "Permanently deleted habit 'Exercise'" in result.stdout
    
    def test_delete_habit_without_confirm(self):
        """Test deleting a habit without confirmation flag."""
        self.run_command("add Exercise")
        
        result = self.run_command("delete Exercise")
        
        assert result.exit_code == 1
        assert "Use --confirm flag" in result.stdout
    
    def test_restore_habit_success(self):
        """Test restoring an archived habit."""
        # Add and archive habit
        self.run_command("add Exercise")
        with patch('typer.confirm', return_value=True):
            self.run_command("remove Exercise")
        
        # Restore it
        result = self.run_command("restore Exercise")
        
        assert result.exit_code == 0
        assert "Successfully restored habit 'Exercise'" in result.stdout
    
    def test_restore_habit_not_found(self):
        """Test restoring a habit that doesn't exist or isn't archived."""
        result = self.run_command("restore NonExistent")
        
        assert result.exit_code == 1
        assert "No archived habit found" in result.stdout


class TestTrackingCommands(TestCLIIntegration):
    """Test tracking CLI commands."""
    
    def test_track_habit_success(self):
        """Test tracking a habit successfully."""
        # Add habit first
        self.run_command("add Exercise")
        
        # Track it
        result = self.run_command("track Exercise")
        
        assert result.exit_code == 0
        assert "Successfully tracked 'Exercise'" in result.stdout
    
    def test_track_habit_with_date(self):
        """Test tracking a habit with specific date."""
        self.run_command("add Exercise")
        
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        result = self.run_command(f"track Exercise --date {yesterday}")
        
        assert result.exit_code == 0
        assert f"Successfully tracked 'Exercise' for {yesterday}" in result.stdout
    
    def test_track_habit_with_notes(self):
        """Test tracking a habit with notes."""
        self.run_command("add Exercise")
        
        result = self.run_command("track Exercise --note 'Great workout today!'")
        
        assert result.exit_code == 0
        assert "Successfully tracked 'Exercise'" in result.stdout
    
    def test_track_habit_not_found(self):
        """Test tracking a habit that doesn't exist."""
        result = self.run_command("track NonExistent")
        
        assert result.exit_code == 1
        assert "not found" in result.stdout
    
    def test_track_habit_already_tracked(self):
        """Test tracking a habit that's already tracked."""
        self.run_command("add Exercise")
        self.run_command("track Exercise")
        
        # Try to track again
        result = self.run_command("track Exercise")
        
        assert result.exit_code == 1
        assert "already tracked" in result.stdout
    
    def test_track_habit_invalid_date(self):
        """Test tracking with invalid date format."""
        self.run_command("add Exercise")
        
        result = self.run_command("track Exercise --date invalid-date")
        
        assert result.exit_code == 1
        assert "Invalid Date Format" in result.stdout
    
    def test_untrack_habit_success(self):
        """Test untracking a habit successfully."""
        self.run_command("add Exercise")
        self.run_command("track Exercise")
        
        result = self.run_command("untrack Exercise")
        
        assert result.exit_code == 0
        assert "Successfully untracked 'Exercise'" in result.stdout
    
    def test_untrack_habit_not_tracked(self):
        """Test untracking a habit that wasn't tracked."""
        self.run_command("add Exercise")
        
        result = self.run_command("untrack Exercise")
        
        assert result.exit_code == 1
        assert "No tracking found" in result.stdout
    
    def test_show_today_no_habits(self):
        """Test showing today's status with no habits."""
        result = self.run_command("today")
        
        assert result.exit_code == 0
        assert "No active habits found" in result.stdout
        assert "Use 'habits add'" in result.stdout
    
    def test_show_today_with_habits(self):
        """Test showing today's status with habits."""
        self.run_command("add Exercise")
        self.run_command("add Reading")
        self.run_command("track Exercise")
        
        result = self.run_command("today")
        
        assert result.exit_code == 0
        assert "Exercise" in result.stdout
        assert "Reading" in result.stdout
        assert "✅" in result.stdout  # Tracked habit indicator
        assert "❌" in result.stdout  # Untracked habit indicator
        assert "Completion Rate:" in result.stdout


class TestAnalyticsCommands(TestCLIIntegration):
    """Test analytics CLI commands."""
    
    def test_show_stats_no_habits(self):
        """Test showing stats with no habits."""
        result = self.run_command("stats")
        
        assert result.exit_code == 0
        assert "No habits found" in result.stdout
    
    def test_show_stats_overall(self):
        """Test showing overall statistics."""
        # Add habits and some tracking data
        self.run_command("add Exercise")
        self.run_command("add Reading")
        self.run_command("track Exercise")
        
        result = self.run_command("stats")
        
        assert result.exit_code == 0
        assert "Overall Habit Statistics" in result.stdout
        assert "Exercise" in result.stdout
        assert "Reading" in result.stdout
    
    def test_show_stats_specific_habit(self):
        """Test showing stats for a specific habit."""
        self.run_command("add Exercise")
        self.run_command("track Exercise")
        
        result = self.run_command("stats --habit Exercise")
        
        assert result.exit_code == 0
        assert "Statistics for 'Exercise'" in result.stdout
        assert "Total Completions:" in result.stdout
        assert "Current Streak:" in result.stdout
    
    def test_show_stats_habit_not_found(self):
        """Test showing stats for non-existent habit."""
        result = self.run_command("stats --habit NonExistent")
        
        assert result.exit_code == 1
        assert "not found" in result.stdout
    
    def test_show_stats_with_period(self):
        """Test showing stats with different periods."""
        self.run_command("add Exercise")
        self.run_command("track Exercise")
        
        result = self.run_command("stats --period week")
        
        assert result.exit_code == 0
        assert "Period: week" in result.stdout or "Last 7 days" in result.stdout
    
    def test_show_stats_invalid_period(self):
        """Test showing stats with invalid period."""
        result = self.run_command("stats --period invalid")
        
        assert result.exit_code == 1
        assert "Invalid Period" in result.stdout


class TestCommandChaining(TestCLIIntegration):
    """Test realistic workflows with multiple commands."""
    
    def test_complete_workflow(self):
        """Test a complete habit tracking workflow."""
        # 1. Add multiple habits
        result1 = self.run_command("add Exercise --description 'Daily workout'")
        assert result1.exit_code == 0
        
        result2 = self.run_command("add Reading --frequency daily")
        assert result2.exit_code == 0
        
        # 2. List habits to verify
        result3 = self.run_command("list")
        assert result3.exit_code == 0
        assert "Exercise" in result3.stdout
        assert "Reading" in result3.stdout
        
        # 3. Track habits
        result4 = self.run_command("track Exercise --note 'Great workout!'")
        assert result4.exit_code == 0
        
        result5 = self.run_command("track Reading")
        assert result5.exit_code == 0
        
        # 4. Check today's status
        result6 = self.run_command("today")
        assert result6.exit_code == 0
        assert "100.0%" in result6.stdout  # Both habits tracked
        
        # 5. View statistics
        result7 = self.run_command("stats")
        assert result7.exit_code == 0
        assert "Exercise" in result7.stdout
        assert "Reading" in result7.stdout
        
        # 6. Archive one habit
        with patch('typer.confirm', return_value=True):
            result8 = self.run_command("remove Reading")
        assert result8.exit_code == 0
        
        # 7. Verify active habits list
        result9 = self.run_command("list --filter active")
        assert result9.exit_code == 0
        assert "Exercise" in result9.stdout
        assert "Reading" not in result9.stdout
    
    def test_error_recovery_workflow(self):
        """Test workflow with error conditions and recovery."""
        # 1. Try to track non-existent habit
        result1 = self.run_command("track NonExistent")
        assert result1.exit_code == 1
        
        # 2. Add the habit
        result2 = self.run_command("add Exercise")
        assert result2.exit_code == 0
        
        # 3. Track it successfully
        result3 = self.run_command("track Exercise")
        assert result3.exit_code == 0
        
        # 4. Try to track again (should fail)
        result4 = self.run_command("track Exercise")
        assert result4.exit_code == 1
        
        # 5. Untrack and track again
        result5 = self.run_command("untrack Exercise")
        assert result5.exit_code == 0
        
        result6 = self.run_command("track Exercise --note 'Second attempt'")
        assert result6.exit_code == 0
    
    def test_archiving_and_restoration_workflow(self):
        """Test habit archiving and restoration workflow."""
        # 1. Add habit
        result1 = self.run_command("add Exercise")
        assert result1.exit_code == 0
        
        # 2. Track it a few times
        result2 = self.run_command("track Exercise")
        assert result2.exit_code == 0
        
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        result3 = self.run_command(f"track Exercise --date {yesterday}")
        assert result3.exit_code == 0
        
        # 3. Check stats before archiving
        result4 = self.run_command("stats --habit Exercise")
        assert result4.exit_code == 0
        assert "Total Completions: 2" in result4.stdout
        
        # 4. Archive the habit
        with patch('typer.confirm', return_value=True):
            result5 = self.run_command("remove Exercise")
        assert result5.exit_code == 0
        
        # 5. Verify it's not in active list
        result6 = self.run_command("list --filter active")
        assert result6.exit_code == 0
        assert "Exercise" not in result6.stdout
        
        # 6. Verify it's in archived list
        result7 = self.run_command("list --filter archived")
        assert result7.exit_code == 0
        assert "Exercise" in result7.stdout
        
        # 7. Restore the habit
        result8 = self.run_command("restore Exercise")
        assert result8.exit_code == 0
        
        # 8. Verify it's back in active list
        result9 = self.run_command("list --filter active")
        assert result9.exit_code == 0
        assert "Exercise" in result9.stdout
        
        # 9. Check that tracking history is preserved
        result10 = self.run_command("stats --habit Exercise")
        assert result10.exit_code == 0
        assert "Total Completions: 2" in result10.stdout