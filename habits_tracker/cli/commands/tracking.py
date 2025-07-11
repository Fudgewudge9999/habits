"""Tracking commands for habit tracking operations."""

from datetime import date
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn

from ...core.services.tracking_service import TrackingService
from ...utils.date_utils import parse_date, format_date
from ...utils.display import create_success_panel, create_error_panel, create_info_panel

console = Console()


def track_habit(
    habit_name: str = typer.Argument(..., help="Name of the habit to track"),
    date_str: Optional[str] = typer.Option(
        None, 
        "--date", 
        "-d", 
        help="Date to track (YYYY-MM-DD, 'today', 'yesterday', or relative like '-1d')"
    ),
    notes: Optional[str] = typer.Option(
        None, 
        "--note", 
        "-n", 
        help="Optional notes for this tracking entry"
    )
) -> None:
    """Track a habit for a specific date (defaults to today)."""
    
    # Parse the date
    tracking_date = None
    if date_str:
        try:
            tracking_date = parse_date(date_str)
        except ValueError as e:
            console.print(create_error_panel(
                "Invalid Date Format",
                str(e),
                "Use formats like: '2025-07-11', 'today', 'yesterday', or '-1d'"
            ))
            raise typer.Exit(1)
    
    # Track the habit
    result = TrackingService.track_habit(
        habit_name=habit_name,
        tracking_date=tracking_date,
        notes=notes
    )
    
    if result["success"]:
        date_display = format_date(result["date"])
        message = f"✅ Tracked '{result['habit_name']}' for {date_display}"
        
        if result.get("notes"):
            message += f"\n📝 Note: {result['notes']}"
        
        console.print(create_success_panel(
            "Habit Tracked Successfully",
            message,
            "Use 'habits today' to see your progress or 'habits stats' for analytics"
        ))
    else:
        console.print(create_error_panel(
            "Tracking Failed",
            result["error"],
            result.get("suggestion", "Please check the habit name and try again")
        ))
        raise typer.Exit(1)


def untrack_habit(
    habit_name: str = typer.Argument(..., help="Name of the habit to untrack"),
    date_str: Optional[str] = typer.Option(
        None,
        "--date",
        "-d",
        help="Date to untrack (YYYY-MM-DD, 'today', 'yesterday', or relative like '-1d')"
    )
) -> None:
    """Remove tracking for a habit on a specific date (defaults to today)."""
    
    # Parse the date
    tracking_date = None
    if date_str:
        try:
            tracking_date = parse_date(date_str)
        except ValueError as e:
            console.print(create_error_panel(
                "Invalid Date Format",
                str(e),
                "Use formats like: '2025-07-11', 'today', 'yesterday', or '-1d'"
            ))
            raise typer.Exit(1)
    
    # Untrack the habit
    result = TrackingService.untrack_habit(
        habit_name=habit_name,
        tracking_date=tracking_date
    )
    
    if result["success"]:
        date_display = format_date(result["date"])
        message = f"❌ Untracked '{result['habit_name']}' for {date_display}"
        
        console.print(create_success_panel(
            "Habit Untracked Successfully",
            message,
            "Use 'habits today' to see your updated progress"
        ))
    else:
        console.print(create_error_panel(
            "Untracking Failed",
            result["error"],
            result.get("suggestion", "Please check the habit name and date")
        ))
        raise typer.Exit(1)


def show_today() -> None:
    """Show today's habit tracking status and progress."""
    
    result = TrackingService.get_today_status()
    
    if not result["success"]:
        console.print(create_error_panel(
            "Error Loading Today's Status",
            "Failed to retrieve today's habit status",
            "Please check your database connection"
        ))
        raise typer.Exit(1)
    
    if not result["habits"]:
        console.print(create_info_panel(
            "No Active Habits",
            result["message"],
            result.get("suggestion", "Use 'habits add' to create your first habit")
        ))
        return
    
    # Display today's date
    date_display = format_date(result["date"])
    console.print(f"\n[bold blue]📅 Today's Progress - {date_display}[/bold blue]\n")
    
    # Create habits table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Habit", style="cyan", no_wrap=True, min_width=20)
    table.add_column("Status", justify="center", min_width=8)
    table.add_column("Streak", justify="center", min_width=8)
    table.add_column("Description", style="dim", overflow="fold")
    table.add_column("Notes", style="dim italic", overflow="fold")
    
    for habit in result["habits"]:
        # Status indicator
        status = "✅" if habit["tracked_today"] else "⭕"
        
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
        
        # Handle empty values
        description = habit.get("description") or ""
        notes = habit.get("notes") or ""
        
        table.add_row(
            habit["name"],
            status,
            streak_display,
            description,
            notes
        )
    
    console.print(table)
    
    # Summary panel
    summary = result["summary"]
    completion_rate = summary["completion_rate"]
    
    # Choose color based on completion rate
    if completion_rate == 100:
        rate_color = "green"
        rate_emoji = "🎉"
    elif completion_rate >= 75:
        rate_color = "yellow"
        rate_emoji = "👍"
    elif completion_rate >= 50:
        rate_color = "orange"
        rate_emoji = "⚡"
    else:
        rate_color = "red"
        rate_emoji = "💪"
    
    summary_text = (
        f"{rate_emoji} Completion Rate: [{rate_color}]{completion_rate}%[/{rate_color}]\n"
        f"📊 Progress: {summary['tracked_today']}/{summary['total_habits']} habits tracked"
    )
    
    if completion_rate == 100:
        suggestion = "Amazing! You've completed all your habits today! 🎉"
    elif summary["tracked_today"] == 0:
        suggestion = "Ready to start your day? Track your first habit!"
    else:
        remaining = summary["total_habits"] - summary["tracked_today"]
        suggestion = f"Keep going! {remaining} more habit{'s' if remaining != 1 else ''} to complete."
    
    console.print(Panel(
        f"{summary_text}\n\n[dim]{suggestion}[/dim]",
        title="📈 Daily Summary",
        border_style="blue"
    ))


def show_progress_bar(tracked: int, total: int) -> None:
    """Show a progress bar for habit completion."""
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
        transient=True
    ) as progress:
        task = progress.add_task("Daily Progress", total=total)
        progress.update(task, advance=tracked)