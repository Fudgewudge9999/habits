"""Analytics commands for habit statistics and insights."""

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

from ...core.services.analytics_service import AnalyticsService
from ...utils.display import create_success_panel, create_error_panel, create_info_panel
from ...utils.date_utils import format_date

console = Console()


def show_stats(
    habit_name: Optional[str] = typer.Option(
        None, 
        "--habit", 
        "-h", 
        help="Show stats for specific habit"
    ),
    period: str = typer.Option(
        "all", 
        "--period", 
        "-p", 
        help="Time period: week, month, year, all"
    )
) -> None:
    """Show habit statistics and analytics."""
    
    # Validate period
    valid_periods = ["week", "month", "year", "all"]
    if period not in valid_periods:
        console.print(create_error_panel(
            "Invalid Period",
            f"Period '{period}' is not valid",
            f"Valid periods: {', '.join(valid_periods)}"
        ))
        raise typer.Exit(1)
    
    if habit_name:
        # Show stats for specific habit
        _show_habit_stats(habit_name, period)
    else:
        # Show overall stats for all habits
        _show_overall_stats(period)


def _show_habit_stats(habit_name: str, period: str) -> None:
    """Show statistics for a specific habit."""
    
    result = AnalyticsService.calculate_habit_stats(habit_name, period)
    
    if not result["success"]:
        console.print(create_error_panel(
            "Habit Not Found",
            result["error"],
            "Use 'habits list --filter all' to see all available habits"
        ))
        raise typer.Exit(1)
    
    stats = result["statistics"]
    
    # Header with habit name and period
    period_display = period.title() if period != "all" else "All Time"
    console.print(f"\n[bold blue]📊 Statistics for '{habit_name}' - {period_display}[/bold blue]\n")
    
    # Main statistics panel
    main_stats_content = _format_main_stats(stats)
    console.print(Panel(
        main_stats_content,
        title="📈 Key Metrics",
        border_style="blue"
    ))
    
    # Recent activity if we have entries
    if result["recent_entries"]:
        console.print("\n[bold]📅 Recent Activity (Last 10 entries)[/bold]\n")
        
        activity_table = Table(show_header=True, header_style="bold magenta")
        activity_table.add_column("Date", style="cyan", min_width=12)
        activity_table.add_column("Notes", style="dim italic", overflow="fold")
        
        for entry in reversed(result["recent_entries"]):  # Show most recent first
            date_str = format_date(entry["date"])
            notes = entry["notes"] or "—"
            activity_table.add_row(date_str, notes)
        
        console.print(activity_table)
    
    # Motivational message based on performance
    completion_rate = stats["completion_rate"]
    current_streak = stats["current_streak"]
    
    if completion_rate >= 90:
        motivation = "🏆 Outstanding consistency! You're a habit champion!"
    elif completion_rate >= 75:
        motivation = "⭐ Great job! You're building strong habits."
    elif completion_rate >= 50:
        motivation = "👍 Good progress! Keep building momentum."
    elif completion_rate >= 25:
        motivation = "💪 You're getting started! Focus on consistency."
    else:
        motivation = "🌱 Every journey begins with a single step. You've got this!"
    
    if current_streak > 0:
        motivation += f" Current streak: {current_streak} day{'s' if current_streak != 1 else ''}! 🔥"
    
    console.print(f"\n[dim]{motivation}[/dim]")


def _show_overall_stats(period: str) -> None:
    """Show overall statistics across all habits."""
    
    result = AnalyticsService.calculate_overall_stats(period)
    
    if not result["success"]:
        console.print(create_error_panel(
            "Error Loading Statistics",
            "Failed to retrieve habit statistics",
            "Please check your database connection"
        ))
        raise typer.Exit(1)
    
    if not result["habits"]:
        console.print(create_info_panel(
            "No Habits Found",
            "No habits available for statistics",
            "Use 'habits add' to create your first habit"
        ))
        return
    
    summary = result["summary"]
    period_display = period.title() if period != "all" else "All Time"
    
    # Header
    console.print(f"\n[bold blue]📊 Overall Statistics - {period_display}[/bold blue]\n")
    
    # Summary panel
    summary_content = _format_overall_summary(summary)
    console.print(Panel(
        summary_content,
        title="📈 Summary",
        border_style="blue"
    ))
    
    # Habits breakdown table
    console.print("\n[bold]📋 Habit Breakdown[/bold]\n")
    
    habits_table = Table(show_header=True, header_style="bold magenta")
    habits_table.add_column("Habit", style="cyan", no_wrap=True, min_width=20)
    habits_table.add_column("Status", justify="center", min_width=8)
    habits_table.add_column("Completions", justify="center", min_width=12)
    habits_table.add_column("Rate", justify="center", min_width=8)
    habits_table.add_column("Streak", justify="center", min_width=8)
    
    # Sort habits by completion rate (descending)
    sorted_habits = sorted(result["habits"], key=lambda x: x["completion_rate"], reverse=True)
    
    for habit in sorted_habits:
        # Status indicator
        status = "✅" if habit["active"] else "📦"
        
        # Completion rate with color coding
        rate = habit["completion_rate"]
        if rate >= 75:
            rate_display = f"[green]{rate}%[/green]"
        elif rate >= 50:
            rate_display = f"[yellow]{rate}%[/yellow]"
        else:
            rate_display = f"[red]{rate}%[/red]"
        
        # Streak with emoji
        streak = habit["current_streak"]
        if streak == 0:
            streak_display = "0"
        elif streak < 7:
            streak_display = f"🔥 {streak}"
        elif streak < 30:
            streak_display = f"⭐ {streak}"
        else:
            streak_display = f"🏆 {streak}"
        
        habits_table.add_row(
            habit["name"],
            status,
            str(habit["completions"]),
            rate_display,
            streak_display
        )
    
    console.print(habits_table)
    
    # Performance insights
    _show_performance_insights(summary, sorted_habits)


def _format_main_stats(stats: dict) -> str:
    """Format main statistics for a habit."""
    
    # Format dates
    created_date = format_date(stats["created_at"])
    
    # Status emoji
    status_emoji = "✅" if stats["is_active"] else "📦"
    
    content = f"""[bold]Status:[/bold] {status_emoji} {'Active' if stats['is_active'] else 'Archived'}
[bold]Created:[/bold] {created_date}

[bold]📊 Performance Metrics[/bold]
━━━━━━━━━━━━━━━━━━━━━━
[bold]Total Completions:[/bold] {stats['total_completions']}
[bold]Completion Rate:[/bold] {stats['completion_rate']}%
[bold]Current Streak:[/bold] {stats['current_streak']} day{'s' if stats['current_streak'] != 1 else ''}
[bold]Longest Streak:[/bold] {stats['longest_streak']} day{'s' if stats['longest_streak'] != 1 else ''}"""
    
    return content


def _format_overall_summary(summary: dict) -> str:
    """Format overall summary statistics."""
    
    content = f"""[bold]📋 Habit Overview[/bold]
━━━━━━━━━━━━━━━━━━━━━━
[bold]Total Habits:[/bold] {summary['total_habits']}
[bold]Active Habits:[/bold] {summary['active_habits']}
[bold]Archived Habits:[/bold] {summary['total_habits'] - summary['active_habits']}

[bold]📈 Performance Overview[/bold]
━━━━━━━━━━━━━━━━━━━━━━
[bold]Total Completions:[/bold] {summary['total_completions']}
[bold]Average Completion Rate:[/bold] {summary['average_completion_rate']}%"""
    
    return content


def _show_performance_insights(summary: dict, habits: list) -> None:
    """Show performance insights and recommendations."""
    
    console.print("\n[bold]🔍 Performance Insights[/bold]\n")
    
    insights = []
    
    # Best performing habit
    if habits:
        best_habit = habits[0]  # Already sorted by completion rate
        if best_habit["completion_rate"] > 0:
            insights.append(f"🏆 Your best habit is '{best_habit['name']}' with {best_habit['completion_rate']}% completion rate")
    
    # Habits needing attention
    struggling_habits = [h for h in habits if h["active"] and h["completion_rate"] < 50]
    if struggling_habits:
        habit_names = [f"'{h['name']}'" for h in struggling_habits[:3]]  # Show up to 3
        if len(struggling_habits) == 1:
            insights.append(f"💪 {habit_names[0]} could use more attention (below 50% completion)")
        else:
            names_str = ", ".join(habit_names)
            insights.append(f"💪 These habits could use more attention: {names_str}")
    
    # Overall performance assessment
    avg_rate = summary["average_completion_rate"]
    if avg_rate >= 80:
        insights.append("🎉 Excellent overall performance! You're crushing your goals!")
    elif avg_rate >= 60:
        insights.append("👍 Solid performance across your habits. Keep up the momentum!")
    elif avg_rate >= 40:
        insights.append("📈 Room for improvement. Focus on consistency with your most important habits.")
    else:
        insights.append("🌱 Building habits takes time. Start with just one habit and be consistent.")
    
    # Active vs total habits
    if summary["active_habits"] < summary["total_habits"]:
        archived_count = summary["total_habits"] - summary["active_habits"]
        insights.append(f"📦 You have {archived_count} archived habit{'s' if archived_count != 1 else ''}. Consider using 'habits restore' if you want to restart any.")
    
    # Display insights
    for insight in insights:
        console.print(f"• {insight}")
    
    # Suggestions
    if summary["active_habits"] > 0:
        console.print(f"\n[dim]💡 Use 'habits today' to see today's progress or 'habits stats --habit \"[habit_name]\"' for detailed habit analysis.[/dim]")