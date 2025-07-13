"""Tests for visualization service functionality."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch

from habits_tracker.core.services.visualization_service import VisualizationService, ChartData
from habits_tracker.core.models import Habit, TrackingEntry


class TestVisualizationService:
    """Test cases for the VisualizationService."""

    def test_get_chart_data_valid_habit(self):
        """Test getting chart data for a valid habit."""
        
        # Mock the session and habit
        mock_session = Mock()
        mock_habit = Mock()
        mock_habit.id = 1
        mock_habit.name = "Exercise"
        
        # Mock tracking entries
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        mock_entries = [
            Mock(date=today, completed=True),
            Mock(date=yesterday, completed=True)
        ]
        
        # Setup query mocks
        mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
        mock_session.query.return_value.filter.return_value.all.return_value = mock_entries
        
        with patch('habits_tracker.core.services.visualization_service.get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            # Test the method
            chart_data = VisualizationService.get_chart_data("Exercise", "week")
            
            assert chart_data is not None
            assert chart_data.habit_name == "Exercise"
            assert chart_data.period == "week"
            assert chart_data.total_days == 7  # Week period
            assert chart_data.completed_days == 2
            assert chart_data.completion_rate > 0

    def test_get_chart_data_nonexistent_habit(self):
        """Test getting chart data for a non-existent habit."""
        
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch('habits_tracker.core.services.visualization_service.get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            chart_data = VisualizationService.get_chart_data("NonExistent", "month")
            
            assert chart_data is None

    def test_generate_calendar_chart(self):
        """Test calendar chart generation."""
        
        today = date.today()
        data_points = [
            (today - timedelta(days=2), True),
            (today - timedelta(days=1), False),
            (today, True)
        ]
        
        chart_data = ChartData(
            habit_name="Test Habit",
            period="week",
            data_points=data_points,
            completion_rate=66.7,
            total_days=3,
            completed_days=2,
            streaks=[1, 1],
            longest_streak=1,
            current_streak=1
        )
        
        chart_output = VisualizationService.generate_calendar_chart(chart_data, "calendar")
        
        assert "Test Habit" in chart_output
        assert "Week View" in chart_output
        assert "Legend:" in chart_output
        assert "Statistics:" in chart_output
        assert "66.7%" in chart_output

    def test_generate_heatmap_chart(self):
        """Test heatmap chart generation."""
        
        today = date.today()
        data_points = [
            (today - timedelta(days=6), True),
            (today - timedelta(days=5), False),
            (today - timedelta(days=4), True),
            (today - timedelta(days=3), False),
            (today - timedelta(days=2), True),
            (today - timedelta(days=1), False),
            (today, True)
        ]
        
        chart_data = ChartData(
            habit_name="Test Habit",
            period="week",
            data_points=data_points,
            completion_rate=57.1,
            total_days=7,
            completed_days=4,
            streaks=[1, 1, 1, 1],
            longest_streak=1,
            current_streak=1
        )
        
        chart_output = VisualizationService.generate_heatmap_chart(chart_data)
        
        assert "Test Habit" in chart_output
        assert "Heatmap" in chart_output
        assert "Mon Tue Wed Thu Fri Sat Sun" in chart_output
        assert "Legend:" in chart_output
        assert "Statistics:" in chart_output
        assert "57.1%" in chart_output

    def test_generate_progress_bars(self):
        """Test progress bars generation."""
        
        habits_data = [
            {
                "name": "Exercise",
                "completion_rate": 85.0,
                "completed_days": 17,
                "total_days": 20,
                "current_streak": 5
            },
            {
                "name": "Reading",
                "completion_rate": 60.0,
                "completed_days": 12,
                "total_days": 20,
                "current_streak": 2
            },
            {
                "name": "Meditation",
                "completion_rate": 30.0,
                "completed_days": 6,
                "total_days": 20,
                "current_streak": 0
            }
        ]
        
        progress_output = VisualizationService.generate_progress_bars(habits_data, "month")
        
        assert "Habits Progress - Month" in progress_output
        assert "Exercise" in progress_output
        assert "Reading" in progress_output
        assert "Meditation" in progress_output
        assert "85.0%" in progress_output
        assert "60.0%" in progress_output
        assert "30.0%" in progress_output
        assert "Summary:" in progress_output
        assert "Average Completion:" in progress_output

    def test_generate_trend_analysis(self):
        """Test trend analysis generation."""
        
        # Create data points showing improvement over time
        today = date.today()
        data_points = []
        
        # First half: low completion (2 out of 10)
        for i in range(10, 0, -1):
            completed = i <= 2  # Only complete first 2 days
            data_points.append((today - timedelta(days=i), completed))
        
        # Second half: high completion (8 out of 10)
        for i in range(10, 0, -1):
            completed = i <= 8  # Complete 8 out of 10 days
            data_points.append((today - timedelta(days=i) + timedelta(days=10), completed))
        
        chart_data = ChartData(
            habit_name="Improving Habit",
            period="month",
            data_points=data_points,
            completion_rate=50.0,
            total_days=20,
            completed_days=10,
            streaks=[2, 8],
            longest_streak=8,
            current_streak=8
        )
        
        trend_output = VisualizationService.generate_trend_analysis(chart_data)
        
        assert "Trend Analysis for Improving Habit" in trend_output
        assert "upward trend" in trend_output.lower()
        assert "Recommendations:" in trend_output
        assert "Early Period:" in trend_output
        assert "Recent Period:" in trend_output

    def test_calculate_streaks(self):
        """Test streak calculation from data points."""
        
        data_points = [
            (date(2025, 7, 1), True),   # Day 1: completed
            (date(2025, 7, 2), True),   # Day 2: completed
            (date(2025, 7, 3), False),  # Day 3: missed
            (date(2025, 7, 4), True),   # Day 4: completed
            (date(2025, 7, 5), True),   # Day 5: completed
            (date(2025, 7, 6), True),   # Day 6: completed
            (date(2025, 7, 7), False),  # Day 7: missed
        ]
        
        streaks = VisualizationService._calculate_streaks(data_points)
        
        assert streaks == [2, 3]  # Two streaks: 2 days, then 3 days

    def test_calculate_current_streak_from_data(self):
        """Test current streak calculation from data points."""
        
        # Test case 1: Current streak at end
        data_points_current = [
            (date(2025, 7, 1), False),
            (date(2025, 7, 2), True),
            (date(2025, 7, 3), True),
            (date(2025, 7, 4), True),
        ]
        
        current_streak = VisualizationService._calculate_current_streak_from_data(data_points_current)
        assert current_streak == 3
        
        # Test case 2: No current streak (ends with miss)
        data_points_no_current = [
            (date(2025, 7, 1), True),
            (date(2025, 7, 2), True),
            (date(2025, 7, 3), False),
        ]
        
        current_streak = VisualizationService._calculate_current_streak_from_data(data_points_no_current)
        assert current_streak == 0

    def test_get_multiple_habits_progress_data(self):
        """Test getting progress data for multiple habits."""
        
        # Mock session and habits
        mock_session = Mock()
        
        # Mock habits
        habit1 = Mock(id=1, name="Exercise", active=True)
        habit2 = Mock(id=2, name="Reading", active=True)
        mock_habits = [habit1, habit2]
        
        # Mock tracking entries (simplified) - need to handle multiple query chains
        mock_session.query.return_value.filter.return_value.all.return_value = mock_habits
        mock_session.query.return_value.filter.return_value.scalar.return_value = 5  # Completion count
        
        # Create proper mock chain for the streak calculation query
        mock_query_chain = Mock()
        mock_query_chain.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_session.query.side_effect = [
            Mock(filter=Mock(return_value=Mock(all=Mock(return_value=mock_habits)))),  # habits query
            Mock(filter=Mock(return_value=Mock(scalar=Mock(return_value=5)))),  # completion count for habit1
            mock_query_chain,  # streak entries for habit1
            Mock(filter=Mock(return_value=Mock(scalar=Mock(return_value=3)))),  # completion count for habit2
            mock_query_chain,  # streak entries for habit2
        ]
        
        with patch('habits_tracker.core.services.visualization_service.get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            
            progress_data = VisualizationService.get_multiple_habits_progress_data("month")
            
            assert len(progress_data) == 2
            assert all("name" in habit for habit in progress_data)
            assert all("completion_rate" in habit for habit in progress_data)
            assert all("current_streak" in habit for habit in progress_data)

    def test_empty_data_handling(self):
        """Test handling of empty data sets."""
        
        # Test empty progress bars
        empty_output = VisualizationService.generate_progress_bars([], "month")
        assert "No habits data available" in empty_output
        
        # Test empty chart data
        empty_chart_data = ChartData(
            habit_name="Empty Habit",
            period="month",
            data_points=[],
            completion_rate=0,
            total_days=0,
            completed_days=0,
            streaks=[],
            longest_streak=0,
            current_streak=0
        )
        
        calendar_output = VisualizationService.generate_calendar_chart(empty_chart_data)
        assert "No data available" in calendar_output
        
        heatmap_output = VisualizationService.generate_heatmap_chart(empty_chart_data)
        assert "No data available" in heatmap_output

    def test_period_validation(self):
        """Test that different periods produce appropriate date ranges."""
        
        with patch('habits_tracker.core.services.visualization_service.get_today') as mock_today:
            mock_today.return_value = date(2025, 7, 15)
            
            mock_session = Mock()
            mock_habit = Mock(id=1, name="Test")
            mock_session.query.return_value.filter.return_value.first.return_value = mock_habit
            mock_session.query.return_value.filter.return_value.all.return_value = []
            
            with patch('habits_tracker.core.services.visualization_service.get_session') as mock_get_session:
                mock_get_session.return_value.__enter__.return_value = mock_session
                
                # Test week period (7 days)
                chart_data_week = VisualizationService.get_chart_data("Test", "week")
                assert chart_data_week.total_days == 7
                
                # Test month period (30 days)
                chart_data_month = VisualizationService.get_chart_data("Test", "month")
                assert chart_data_month.total_days == 30
                
                # Test year period (365 days)
                chart_data_year = VisualizationService.get_chart_data("Test", "year")
                assert chart_data_year.total_days == 365


class TestVisualizationEdgeCases:
    """Test edge cases and error conditions for visualization service."""

    def test_very_long_habit_names(self):
        """Test handling of very long habit names."""
        
        long_name = "A" * 100  # Very long habit name
        data_points = [(date.today(), True)]
        
        chart_data = ChartData(
            habit_name=long_name,
            period="week",
            data_points=data_points,
            completion_rate=100.0,
            total_days=1,
            completed_days=1,
            streaks=[1],
            longest_streak=1,
            current_streak=1
        )
        
        # Should not crash with long names
        calendar_output = VisualizationService.generate_calendar_chart(chart_data)
        assert long_name in calendar_output
        
        heatmap_output = VisualizationService.generate_heatmap_chart(chart_data)
        assert long_name in heatmap_output

    def test_high_completion_rates(self):
        """Test visualization with 100% completion rates."""
        
        habits_data = [
            {
                "name": "Perfect Habit",
                "completion_rate": 100.0,
                "completed_days": 30,
                "total_days": 30,
                "current_streak": 30
            }
        ]
        
        progress_output = VisualizationService.generate_progress_bars(habits_data, "month")
        
        assert "100.0%" in progress_output
        assert "🏆30" in progress_output  # Should show trophy for long streak

    def test_zero_completion_rates(self):
        """Test visualization with 0% completion rates."""
        
        habits_data = [
            {
                "name": "Struggling Habit",
                "completion_rate": 0.0,
                "completed_days": 0,
                "total_days": 30,
                "current_streak": 0
            }
        ]
        
        progress_output = VisualizationService.generate_progress_bars(habits_data, "month")
        
        assert "0.0%" in progress_output
        assert "Struggling Habit" in progress_output

    def test_single_day_data(self):
        """Test visualization with only one day of data."""
        
        today = date.today()
        data_points = [(today, True)]
        
        chart_data = ChartData(
            habit_name="New Habit",
            period="week",
            data_points=data_points,
            completion_rate=14.3,  # 1/7 days
            total_days=7,
            completed_days=1,
            streaks=[1],
            longest_streak=1,
            current_streak=1
        )
        
        # Should handle single day gracefully
        calendar_output = VisualizationService.generate_calendar_chart(chart_data)
        assert "New Habit" in calendar_output
        
        # Trend analysis should indicate insufficient data
        trend_output = VisualizationService.generate_trend_analysis(chart_data)
        assert "Insufficient data" in trend_output