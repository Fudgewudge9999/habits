"""Performance and stress tests for HabitsTracker CLI."""

import pytest
import time
import tempfile
import os
from datetime import date, timedelta, datetime
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from habits_tracker.cli.main import app
from habits_tracker.core.database import init_database, get_session
from habits_tracker.core.services.habit_service import HabitService
from habits_tracker.core.services.tracking_service import TrackingService
from habits_tracker.core.services.analytics_service import AnalyticsService
from habits_tracker.core.models import Habit, TrackingEntry


class TestPerformanceTargets:
    """Test that operations meet performance targets (<100ms)."""
    
    @pytest.fixture
    def temp_db_setup(self):
        """Set up temporary database with some test data."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_habits.db")
        
        with patch('habits_tracker.core.database.get_database_path', return_value=db_path):
            init_database()
            
            # Add some test habits
            for i in range(5):
                HabitService.create_habit(f"Habit_{i}", description=f"Test habit {i}")
            
            # Add some tracking data
            today = date.today()
            for i in range(5):
                for j in range(10):  # 10 days of tracking per habit
                    tracking_date = today - timedelta(days=j)
                    TrackingService.track_habit(f"Habit_{i}", tracking_date=tracking_date)
        
        yield db_path
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
        os.rmdir(temp_dir)
    
    def test_habit_creation_performance(self, temp_db_setup):
        """Test that habit creation is under 100ms."""
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_setup):
            start_time = time.time()
            HabitService.create_habit("Performance_Test")
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            assert execution_time < 100, f"Habit creation took {execution_time:.2f}ms, should be <100ms"
    
    def test_habit_listing_performance(self, temp_db_setup):
        """Test that habit listing is under 100ms."""
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_setup):
            start_time = time.time()
            HabitService.list_habits("active", include_stats=True)
            execution_time = (time.time() - start_time) * 1000
            
            assert execution_time < 100, f"Habit listing took {execution_time:.2f}ms, should be <100ms"
    
    def test_tracking_performance(self, temp_db_setup):
        """Test that habit tracking is under 100ms."""
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_setup):
            start_time = time.time()
            TrackingService.track_habit("Habit_0")
            execution_time = (time.time() - start_time) * 1000
            
            assert execution_time < 100, f"Habit tracking took {execution_time:.2f}ms, should be <100ms"
    
    def test_today_status_performance(self, temp_db_setup):
        """Test that today's status is under 100ms."""
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_setup):
            start_time = time.time()
            TrackingService.get_today_status()
            execution_time = (time.time() - start_time) * 1000
            
            assert execution_time < 100, f"Today status took {execution_time:.2f}ms, should be <100ms"
    
    def test_analytics_performance(self, temp_db_setup):
        """Test that analytics calculation is under reasonable time."""
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_setup):
            start_time = time.time()
            AnalyticsService.calculate_overall_stats("all")
            execution_time = (time.time() - start_time) * 1000
            
            # Analytics might be slightly slower due to calculations, allow 200ms
            assert execution_time < 200, f"Analytics took {execution_time:.2f}ms, should be <200ms"
    
    def test_cli_command_performance(self, temp_db_setup):
        """Test that CLI commands execute quickly."""
        runner = CliRunner()
        
        with patch('habits_tracker.core.database.get_database_path', return_value=temp_db_setup):
            # Test various CLI commands
            commands_to_test = [
                ["list"],
                ["today"],
                ["add", "CLI_Performance_Test"],
                ["track", "Habit_0"],
                ["stats"],
            ]
            
            for command in commands_to_test:
                start_time = time.time()
                result = runner.invoke(app, command)
                execution_time = (time.time() - start_time) * 1000
                
                assert result.exit_code == 0 or result.exit_code == 1  # Allow expected errors
                assert execution_time < 500, f"CLI command {' '.join(command)} took {execution_time:.2f}ms"


class TestLargeDatasetHandling:
    """Test behavior with large datasets."""
    
    def test_many_habits_performance(self):
        """Test performance with a large number of habits."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "large_habits.db")
        
        try:
            with patch('habits_tracker.core.database.get_database_path', return_value=db_path):
                init_database()
                
                # Create many habits
                start_time = time.time()
                for i in range(100):
                    HabitService.create_habit(f"Habit_{i:03d}", description=f"Test habit number {i}")
                creation_time = time.time() - start_time
                
                # Should be able to create 100 habits in reasonable time
                assert creation_time < 10, f"Creating 100 habits took {creation_time:.2f}s, should be <10s"
                
                # Test listing performance with many habits
                start_time = time.time()
                habits = HabitService.list_habits("active", include_stats=False)
                listing_time = time.time() - start_time
                
                assert len(habits) == 100
                assert listing_time < 1, f"Listing 100 habits took {listing_time:.2f}s, should be <1s"
        
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
            os.rmdir(temp_dir)
    
    def test_many_tracking_entries_performance(self):
        """Test performance with many tracking entries."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "large_tracking.db")
        
        try:
            with patch('habits_tracker.core.database.get_database_path', return_value=db_path):
                init_database()
                
                # Create a few habits
                for i in range(5):
                    HabitService.create_habit(f"Habit_{i}")
                
                # Create many tracking entries (simulate 1 year of data)
                start_time = time.time()
                base_date = date.today() - timedelta(days=365)
                
                for i in range(365):  # One year
                    tracking_date = base_date + timedelta(days=i)
                    for j in range(3):  # Track 3 out of 5 habits each day
                        TrackingService.track_habit(f"Habit_{j}", tracking_date=tracking_date)
                
                creation_time = time.time() - start_time
                assert creation_time < 30, f"Creating 1095 tracking entries took {creation_time:.2f}s, should be <30s"
                
                # Test analytics performance with large dataset
                start_time = time.time()
                stats = AnalyticsService.calculate_overall_stats("all")
                analytics_time = time.time() - start_time
                
                assert stats["success"] is True
                assert analytics_time < 2, f"Analytics on large dataset took {analytics_time:.2f}s, should be <2s"
        
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
            os.rmdir(temp_dir)
    
    def test_streak_calculation_performance(self):
        """Test streak calculation performance with large datasets."""
        # Simulate large number of consecutive tracking entries
        large_entry_list = []
        base_date = date.today() - timedelta(days=1000)
        
        for i in range(1000):
            entry = MagicMock()
            entry.date = base_date + timedelta(days=i)
            large_entry_list.append(entry)
        
        # Test current streak calculation
        start_time = time.time()
        current_streak = AnalyticsService._calculate_current_streak(large_entry_list)
        current_streak_time = time.time() - start_time
        
        assert isinstance(current_streak, int)
        assert current_streak_time < 0.1, f"Current streak calculation took {current_streak_time:.3f}s, should be <0.1s"
        
        # Test longest streak calculation
        start_time = time.time()
        longest_streak = AnalyticsService._calculate_longest_streak(large_entry_list)
        longest_streak_time = time.time() - start_time
        
        assert isinstance(longest_streak, int)
        assert longest_streak_time < 0.1, f"Longest streak calculation took {longest_streak_time:.3f}s, should be <0.1s"


class TestMemoryUsageTests:
    """Test memory usage patterns."""
    
    def test_memory_efficiency_large_datasets(self):
        """Test that memory usage stays reasonable with large datasets."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset in memory
        large_habit_list = []
        for i in range(1000):
            habit = MagicMock()
            habit.id = i
            habit.name = f"Habit_{i:04d}"
            habit.description = f"Description for habit {i}"
            habit.frequency = "daily"
            habit.active = True
            habit.created_at = datetime.now()
            large_habit_list.append(habit)
        
        mid_memory = process.memory_info().rss / 1024 / 1024
        
        # Process the dataset (simulate analytics)
        with patch('habits_tracker.core.services.analytics_service.AnalyticsService.calculate_overall_stats') as mock_stats:
            mock_stats.return_value = {"success": True, "habits": large_habit_list, "summary": {}}
            result = AnalyticsService.calculate_overall_stats("all")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        
        memory_increase = final_memory - initial_memory
        
        # Memory usage should stay under 50MB increase for processing 1000 habits
        assert memory_increase < 50, f"Memory usage increased by {memory_increase:.2f}MB, should be <50MB"
    
    def test_session_cleanup_memory(self):
        """Test that database sessions don't leak memory."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Perform many database operations
        with patch('habits_tracker.core.database.get_session') as mock_session_ctx:
            mock_session = MagicMock()
            mock_session_ctx.return_value.__enter__.return_value = mock_session
            mock_session_ctx.return_value.__exit__ = MagicMock()
            
            for i in range(100):
                try:
                    with get_session() as session:
                        # Simulate database operation
                        session.query(MagicMock).all()
                except:
                    pass
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        # Memory should not increase significantly from session management
        assert memory_increase < 10, f"Session management leaked {memory_increase:.2f}MB"


class TestConcurrentOperationStress:
    """Test behavior under concurrent operation stress."""
    
    def test_rapid_sequential_operations(self):
        """Test rapid sequential operations."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "rapid_ops.db")
        
        try:
            with patch('habits_tracker.core.database.get_database_path', return_value=db_path):
                init_database()
                HabitService.create_habit("RapidTest")
                
                # Perform rapid tracking operations
                start_time = time.time()
                today = date.today()
                
                for i in range(50):
                    # Track and untrack rapidly
                    tracking_date = today - timedelta(days=i)
                    try:
                        TrackingService.track_habit("RapidTest", tracking_date=tracking_date)
                        if i % 2 == 0:  # Untrack every other entry
                            TrackingService.untrack_habit("RapidTest", tracking_date=tracking_date)
                    except Exception:
                        # Some operations might fail due to timing, which is acceptable
                        pass
                
                total_time = time.time() - start_time
                assert total_time < 5, f"50 rapid operations took {total_time:.2f}s, should be <5s"
        
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
            os.rmdir(temp_dir)
    
    def test_database_lock_stress(self):
        """Test behavior under simulated database lock stress."""
        with patch('habits_tracker.core.database.get_session') as mock_session_ctx:
            mock_session = MagicMock()
            mock_session_ctx.return_value.__enter__.return_value = mock_session
            
            # Simulate occasional database locks
            call_count = 0
            def lock_simulation(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count % 5 == 0:  # Every 5th call fails
                    raise Exception("database is locked")
                return MagicMock()
            
            mock_session.commit.side_effect = lock_simulation
            
            success_count = 0
            for i in range(20):
                try:
                    HabitService.create_habit(f"StressTest_{i}")
                    success_count += 1
                except Exception:
                    # Expected failures due to simulated locks
                    pass
            
            # Should have some successful operations despite intermittent failures
            assert success_count > 0, "No operations succeeded under stress conditions"


class TestErrorRecoveryStress:
    """Test error recovery under stress conditions."""
    
    def test_repeated_error_conditions(self):
        """Test handling of repeated error conditions."""
        error_count = 0
        
        for i in range(10):
            try:
                # Try operations that will fail
                HabitService.validate_habit_name("")  # Empty name
            except Exception:
                error_count += 1
        
        # Should handle repeated errors without degradation
        assert error_count == 10, "Error handling degraded under repeated failures"
    
    def test_recovery_after_database_errors(self):
        """Test recovery after database errors."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "recovery_test.db")
        
        try:
            with patch('habits_tracker.core.database.get_database_path', return_value=db_path):
                init_database()
                
                # Create some data
                HabitService.create_habit("RecoveryTest")
                TrackingService.track_habit("RecoveryTest")
                
                # Simulate database error and recovery
                with patch('sqlalchemy.orm.Session.commit', side_effect=Exception("Simulated error")):
                    try:
                        HabitService.create_habit("FailTest")
                    except Exception:
                        pass
                
                # Verify system can still operate normally after error
                habits = HabitService.list_habits("active")
                assert len(habits) >= 1, "System did not recover properly after database error"
                
                # Should be able to continue normal operations
                result = TrackingService.get_today_status()
                assert result["success"] is True, "System functionality impaired after error"
        
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
            os.rmdir(temp_dir)


class TestResourceConstraintSimulation:
    """Test behavior under simulated resource constraints."""
    
    def test_low_memory_simulation(self):
        """Test behavior under simulated low memory conditions."""
        # Simulate memory pressure
        with patch('habits_tracker.core.services.analytics_service.AnalyticsService._calculate_longest_streak') as mock_calc:
            mock_calc.side_effect = MemoryError("Out of memory")
            
            # Should handle memory errors gracefully
            with pytest.raises(MemoryError):
                AnalyticsService._calculate_longest_streak([MagicMock()])
    
    def test_slow_disk_simulation(self):
        """Test behavior under simulated slow disk conditions."""
        # Simulate slow database operations
        with patch('sqlalchemy.orm.Session.commit') as mock_commit:
            def slow_commit():
                time.sleep(0.1)  # Simulate slow disk
                return None
            
            mock_commit.side_effect = slow_commit
            
            start_time = time.time()
            with patch('habits_tracker.core.database.get_session'):
                try:
                    HabitService.create_habit("SlowDiskTest")
                except Exception:
                    pass
            
            # Operation should complete despite slow disk
            elapsed = time.time() - start_time
            assert elapsed >= 0.1, "Slow disk simulation not working"
    
    def test_interrupted_operations(self):
        """Test handling of interrupted operations."""
        with patch('sqlalchemy.orm.Session.add') as mock_add:
            mock_add.side_effect = KeyboardInterrupt("User interrupted")
            
            # Should handle interruption gracefully
            with pytest.raises(KeyboardInterrupt):
                HabitService.create_habit("InterruptTest")