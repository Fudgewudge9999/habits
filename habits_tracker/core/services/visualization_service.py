"""Visualization service for ASCII charts, progress bars, and habit analytics visualizations."""

import calendar
from datetime import date, timedelta, datetime
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from ..models import Habit, TrackingEntry
from ..database import get_session
from ...utils.date_utils import get_today, format_date
from ...utils.cache import cached, stats_cache
from ...utils.performance import profile_query, performance_target


@dataclass
class ChartData:
    """Data structure for chart generation."""
    habit_name: str
    period: str
    data_points: List[Tuple[date, bool]]  # (date, completed)
    completion_rate: float
    total_days: int
    completed_days: int
    streaks: List[int]
    longest_streak: int
    current_streak: int


class VisualizationService:
    """Service for generating ASCII charts and progress visualizations."""
    
    # Color mapping for different completion levels
    COMPLETION_COLORS = {
        "none": "dim white",      # No data
        "low": "red",             # 0-25%
        "medium": "yellow",       # 26-75%
        "high": "green",          # 76-100%
        "complete": "bright_green" # 100%
    }
    
    # Symbols for different chart styles
    CHART_SYMBOLS = {
        "heatmap": {
            "none": "⬜",
            "low": "🟥", 
            "medium": "🟨",
            "high": "🟩",
            "complete": "🟢"
        },
        "calendar": {
            "none": "·",
            "low": "▁",
            "medium": "▃", 
            "high": "▅",
            "complete": "█"
        },
        "simple": {
            "none": "⭕",
            "completed": "✅",
            "missed": "❌"
        }
    }

    @classmethod
    @performance_target(200)
    @profile_query("chart_data")
    def get_chart_data(
        cls,
        habit_name: str,
        period: str = "month",
        style: str = "calendar"
    ) -> Optional[ChartData]:
        """Get data needed for chart generation.
        
        Args:
            habit_name: Name of the habit to chart
            period: Time period ('week', 'month', 'year')
            style: Chart style ('calendar', 'heatmap', 'simple')
            
        Returns:
            ChartData object or None if habit not found
        """
        with get_session() as session:
            # Find the habit
            habit = session.query(Habit).filter(
                Habit.name == habit_name
            ).first()
            
            if not habit:
                return None
            
            # Calculate date range
            today = get_today()
            if period == "week":
                start_date = today - timedelta(days=6)  # 7 days total including today
            elif period == "month":
                start_date = today - timedelta(days=29)  # 30 days total
            elif period == "year":
                start_date = today - timedelta(days=364)  # 365 days total
            else:
                # Default to month
                start_date = today - timedelta(days=29)
            
            # Get all tracking entries for the period
            entries = session.query(TrackingEntry).filter(
                TrackingEntry.habit_id == habit.id,
                TrackingEntry.date >= start_date,
                TrackingEntry.date <= today,
                TrackingEntry.completed == True
            ).all()
            
            # Create a set of completed dates for fast lookup
            completed_dates = {entry.date for entry in entries}
            
            # Generate data points for each day in the period
            data_points = []
            current_date = start_date
            
            while current_date <= today:
                completed = current_date in completed_dates
                data_points.append((current_date, completed))
                current_date += timedelta(days=1)
            
            # Calculate statistics
            total_days = len(data_points)
            completed_days = len(completed_dates)
            completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
            
            # Calculate streaks
            streaks = cls._calculate_streaks(data_points)
            current_streak = cls._calculate_current_streak_from_data(data_points)
            longest_streak = max(streaks) if streaks else 0
            
            return ChartData(
                habit_name=habit_name,
                period=period,
                data_points=data_points,
                completion_rate=completion_rate,
                total_days=total_days,
                completed_days=completed_days,
                streaks=streaks,
                longest_streak=longest_streak,
                current_streak=current_streak
            )

    @classmethod
    def generate_calendar_chart(
        cls,
        chart_data: ChartData,
        style: str = "calendar"
    ) -> str:
        """Generate a calendar-style ASCII chart.
        
        Args:
            chart_data: Chart data to visualize
            style: Chart style ('calendar', 'heatmap', 'simple')
            
        Returns:
            ASCII calendar chart as string
        """
        if not chart_data.data_points:
            return "No data available for chart generation."
        
        symbols = cls.CHART_SYMBOLS.get(style, cls.CHART_SYMBOLS["calendar"])
        
        # Group data by month for calendar layout
        months_data = defaultdict(list)
        for date_obj, completed in chart_data.data_points:
            month_key = (date_obj.year, date_obj.month)
            months_data[month_key].append((date_obj, completed))
        
        chart_lines = []
        chart_lines.append(f"📊 {chart_data.habit_name} - {chart_data.period.title()} View")
        chart_lines.append("=" * 50)
        
        # Generate calendar for each month
        for (year, month), month_data in sorted(months_data.items()):
            chart_lines.append(f"\n{calendar.month_name[month]} {year}")
            chart_lines.append("Mo Tu We Th Fr Sa Su")
            
            # Create calendar grid
            cal = calendar.monthcalendar(year, month)
            
            # Create data lookup for this month
            month_completed = {d.day: completed for d, completed in month_data}
            
            for week in cal:
                week_line = ""
                for day in week:
                    if day == 0:
                        week_line += "   "  # Empty day
                    else:
                        if day in month_completed:
                            symbol = symbols["complete"] if month_completed[day] else symbols["none"]
                        else:
                            symbol = symbols["none"]
                        week_line += f"{symbol:2} "
                chart_lines.append(week_line)
        
        # Add legend and statistics
        chart_lines.append(f"\nLegend:")
        chart_lines.append(f"  {symbols['complete']} Completed")
        chart_lines.append(f"  {symbols['none']} Not completed")
        
        chart_lines.append(f"\nStatistics:")
        chart_lines.append(f"  Completion Rate: {chart_data.completion_rate:.1f}%")
        chart_lines.append(f"  Completed Days: {chart_data.completed_days}/{chart_data.total_days}")
        chart_lines.append(f"  Current Streak: {chart_data.current_streak} days")
        chart_lines.append(f"  Longest Streak: {chart_data.longest_streak} days")
        
        return "\n".join(chart_lines)

    @classmethod
    def generate_heatmap_chart(
        cls,
        chart_data: ChartData
    ) -> str:
        """Generate a GitHub-style heatmap chart.
        
        Args:
            chart_data: Chart data to visualize
            
        Returns:
            ASCII heatmap chart as string
        """
        if not chart_data.data_points:
            return "No data available for heatmap generation."
        
        symbols = cls.CHART_SYMBOLS["heatmap"]
        
        chart_lines = []
        chart_lines.append(f"🔥 {chart_data.habit_name} - Heatmap ({chart_data.period.title()})")
        chart_lines.append("=" * 60)
        
        # For heatmap, organize by weeks
        weeks = []
        current_week = []
        
        # Start from Monday of the first week
        start_date = chart_data.data_points[0][0]
        days_to_monday = start_date.weekday()
        week_start = start_date - timedelta(days=days_to_monday)
        
        # Group data by weeks
        data_dict = {d: completed for d, completed in chart_data.data_points}
        
        current_date = week_start
        end_date = chart_data.data_points[-1][0]
        
        while current_date <= end_date + timedelta(days=6):
            if current_date in data_dict:
                completed = data_dict[current_date]
                symbol = symbols["complete"] if completed else symbols["none"]
            else:
                symbol = symbols["none"]
            
            current_week.append(symbol)
            
            if len(current_week) == 7:  # Week complete
                weeks.append(current_week[:])
                current_week = []
            
            current_date += timedelta(days=1)
        
        # Add remaining days if any
        if current_week:
            while len(current_week) < 7:
                current_week.append(symbols["none"])
            weeks.append(current_week)
        
        # Add day labels
        chart_lines.append("      Mon Tue Wed Thu Fri Sat Sun")
        
        # Add weeks with month labels
        for i, week in enumerate(weeks):
            if i % 4 == 0:  # Add month indicator every 4 weeks
                week_start_date = week_start + timedelta(weeks=i)
                month_label = week_start_date.strftime("%b")[:3]
            else:
                month_label = "   "
            
            week_str = " ".join(week)
            chart_lines.append(f"{month_label}   {week_str}")
        
        # Add legend and stats
        chart_lines.append(f"\nLegend:")
        chart_lines.append(f"  {symbols['complete']} Completed  {symbols['none']} Not completed")
        
        chart_lines.append(f"\nStatistics:")
        chart_lines.append(f"  Total Days: {chart_data.total_days}")
        chart_lines.append(f"  Completed: {chart_data.completed_days} ({chart_data.completion_rate:.1f}%)")
        chart_lines.append(f"  Current Streak: {chart_data.current_streak} days 🔥")
        chart_lines.append(f"  Best Streak: {chart_data.longest_streak} days 🏆")
        
        return "\n".join(chart_lines)

    @classmethod
    def generate_progress_bars(
        cls,
        habits_data: List[Dict[str, Any]],
        period: str = "month"
    ) -> str:
        """Generate ASCII progress bars for multiple habits.
        
        Args:
            habits_data: List of habit data dictionaries
            period: Time period for the progress bars
            
        Returns:
            ASCII progress bars as string
        """
        if not habits_data:
            return "No habits data available for progress visualization."
        
        chart_lines = []
        chart_lines.append(f"📈 Habits Progress - {period.title()}")
        chart_lines.append("=" * 60)
        
        # Sort habits by completion rate (descending)
        sorted_habits = sorted(habits_data, key=lambda x: x.get("completion_rate", 0), reverse=True)
        
        for habit in sorted_habits:
            name = habit["name"]
            rate = habit.get("completion_rate", 0)
            completed = habit.get("completed_days", 0)
            total = habit.get("total_days", 0)
            streak = habit.get("current_streak", 0)
            
            # Generate progress bar
            bar_length = 25
            filled_length = int(bar_length * rate / 100) if rate > 0 else 0
            empty_length = bar_length - filled_length
            
            # Color coding based on completion rate
            if rate >= 80:
                bar_color = "bright_green"
                bar_char = "█"
            elif rate >= 60:
                bar_color = "green"
                bar_char = "█"
            elif rate >= 40:
                bar_color = "yellow"
                bar_char = "█"
            else:
                bar_color = "red"
                bar_char = "█"
            
            progress_bar = bar_char * filled_length + "░" * empty_length
            
            # Format habit line
            habit_line = f"{name:<20} [{progress_bar}] {rate:5.1f}% ({completed}/{total})"
            
            # Add streak indicator
            if streak > 0:
                if streak >= 30:
                    streak_indicator = f" 🏆{streak}"
                elif streak >= 7:
                    streak_indicator = f" ⭐{streak}"
                else:
                    streak_indicator = f" 🔥{streak}"
                habit_line += streak_indicator
            
            chart_lines.append(habit_line)
        
        # Add summary statistics
        total_habits = len(habits_data)
        avg_rate = sum(h.get("completion_rate", 0) for h in habits_data) / total_habits if total_habits > 0 else 0
        top_performers = len([h for h in habits_data if h.get("completion_rate", 0) >= 80])
        
        chart_lines.append(f"\nSummary:")
        chart_lines.append(f"  Average Completion: {avg_rate:.1f}%")
        chart_lines.append(f"  High Performers (≥80%): {top_performers}/{total_habits}")
        
        # Performance insights
        if avg_rate >= 80:
            insight = "🎉 Excellent overall performance!"
        elif avg_rate >= 60:
            insight = "👍 Good progress across habits"
        elif avg_rate >= 40:
            insight = "📈 Room for improvement"
        else:
            insight = "💪 Focus on building consistency"
        
        chart_lines.append(f"  {insight}")
        
        return "\n".join(chart_lines)

    @classmethod
    def generate_trend_analysis(
        cls,
        chart_data: ChartData
    ) -> str:
        """Generate trend analysis with indicators.
        
        Args:
            chart_data: Chart data to analyze
            
        Returns:
            Trend analysis as string
        """
        if len(chart_data.data_points) < 7:
            return "Insufficient data for trend analysis (need at least 7 days)."
        
        # Split data into two halves for comparison
        mid_point = len(chart_data.data_points) // 2
        first_half = chart_data.data_points[:mid_point]
        second_half = chart_data.data_points[mid_point:]
        
        first_rate = sum(1 for _, completed in first_half if completed) / len(first_half) * 100
        second_rate = sum(1 for _, completed in second_half if completed) / len(second_half) * 100
        
        trend_diff = second_rate - first_rate
        
        # Determine trend direction
        if trend_diff > 10:
            trend_emoji = "📈"
            trend_text = "Strong upward trend"
            trend_color = "green"
        elif trend_diff > 5:
            trend_emoji = "📊"
            trend_text = "Slight upward trend"
            trend_color = "green"
        elif trend_diff > -5:
            trend_emoji = "➡️"
            trend_text = "Stable trend"
            trend_color = "yellow"
        elif trend_diff > -10:
            trend_emoji = "📉"
            trend_text = "Slight downward trend"
            trend_color = "yellow"
        else:
            trend_emoji = "⬇️"
            trend_text = "Concerning downward trend"
            trend_color = "red"
        
        analysis_lines = []
        analysis_lines.append(f"📊 Trend Analysis for {chart_data.habit_name}")
        analysis_lines.append("=" * 40)
        analysis_lines.append(f"Period: {chart_data.period.title()} ({chart_data.total_days} days)")
        analysis_lines.append(f"Overall Rate: {chart_data.completion_rate:.1f}%")
        analysis_lines.append("")
        analysis_lines.append(f"Trend: {trend_emoji} {trend_text}")
        analysis_lines.append(f"  Early Period: {first_rate:.1f}%")
        analysis_lines.append(f"  Recent Period: {second_rate:.1f}%")
        analysis_lines.append(f"  Change: {trend_diff:+.1f} percentage points")
        
        # Add recommendations based on trend
        analysis_lines.append(f"\nRecommendations:")
        if trend_diff > 5:
            analysis_lines.append("✅ Keep up the excellent momentum!")
            analysis_lines.append("💡 Consider increasing difficulty or adding related habits")
        elif trend_diff > -5:
            analysis_lines.append("👍 Maintain current consistency")
            analysis_lines.append("💡 Look for patterns in successful days")
        else:
            analysis_lines.append("⚠️  Consider reviewing your approach")
            analysis_lines.append("💡 Identify obstacles and adjust your strategy")
            analysis_lines.append("💡 Perhaps lower the barrier to entry temporarily")
        
        return "\n".join(analysis_lines)

    @classmethod
    def _calculate_streaks(cls, data_points: List[Tuple[date, bool]]) -> List[int]:
        """Calculate all streaks from data points."""
        streaks = []
        current_streak = 0
        
        for _, completed in data_points:
            if completed:
                current_streak += 1
            else:
                if current_streak > 0:
                    streaks.append(current_streak)
                    current_streak = 0
        
        # Add final streak if data ends with completion
        if current_streak > 0:
            streaks.append(current_streak)
        
        return streaks

    @classmethod
    def _calculate_current_streak_from_data(cls, data_points: List[Tuple[date, bool]]) -> int:
        """Calculate current streak from data points."""
        if not data_points:
            return 0
        
        # Work backwards from the most recent date
        current_streak = 0
        for _, completed in reversed(data_points):
            if completed:
                current_streak += 1
            else:
                break
        
        return current_streak

    @classmethod
    @performance_target(150)
    def get_multiple_habits_progress_data(
        cls,
        period: str = "month",
        habit_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get progress data for multiple habits.
        
        Args:
            period: Time period ('week', 'month', 'year')
            habit_names: Optional list of specific habit names
            
        Returns:
            List of habit progress data dictionaries
        """
        with get_session() as session:
            # Get habits query
            habits_query = session.query(Habit)
            if habit_names:
                habits_query = habits_query.filter(Habit.name.in_(habit_names))
            
            habits = habits_query.filter(Habit.active == True).all()
            
            if not habits:
                return []
            
            # Calculate date range
            today = get_today()
            if period == "week":
                start_date = today - timedelta(days=6)
            elif period == "month":
                start_date = today - timedelta(days=29)
            elif period == "year":
                start_date = today - timedelta(days=364)
            else:
                start_date = today - timedelta(days=29)
            
            total_days = (today - start_date).days + 1
            
            habits_data = []
            
            for habit in habits:
                # Get completion count for this habit
                completed_count = session.query(func.count(TrackingEntry.id)).filter(
                    TrackingEntry.habit_id == habit.id,
                    TrackingEntry.date >= start_date,
                    TrackingEntry.date <= today,
                    TrackingEntry.completed == True
                ).scalar() or 0
                
                completion_rate = (completed_count / total_days * 100) if total_days > 0 else 0
                
                # Get current streak (simplified calculation)
                recent_entries = session.query(TrackingEntry).filter(
                    TrackingEntry.habit_id == habit.id,
                    TrackingEntry.completed == True
                ).order_by(TrackingEntry.date.desc()).limit(30).all()
                
                current_streak = cls._calculate_current_streak_simple(recent_entries)
                
                habits_data.append({
                    "name": habit.name,
                    "completion_rate": round(completion_rate, 1),
                    "completed_days": completed_count,
                    "total_days": total_days,
                    "current_streak": current_streak
                })
            
            return habits_data

    @classmethod
    def _calculate_current_streak_simple(cls, entries: List[TrackingEntry]) -> int:
        """Simplified current streak calculation."""
        if not entries:
            return 0
        
        today = get_today()
        sorted_entries = sorted(entries, key=lambda x: x.date, reverse=True)
        
        # Check if streak is current (today or yesterday)
        latest_entry = sorted_entries[0]
        days_since_latest = (today - latest_entry.date).days
        
        if days_since_latest > 1:
            return 0
        
        # Count consecutive days
        streak = 0
        current_date = latest_entry.date
        
        for entry in sorted_entries:
            if entry.date == current_date:
                streak += 1
                current_date -= timedelta(days=1)
            else:
                break
        
        return streak