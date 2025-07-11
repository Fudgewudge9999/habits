"""Rich-based display utilities for beautiful terminal output."""

from datetime import date, datetime
from typing import List, Dict, Any, Optional, Union
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.text import Text
from rich.align import Align
from rich import box
from rich.style import Style

# Create a global console instance
console = Console()


class Colors:
    """Color constants for consistent theming."""
    PRIMARY = "blue"
    SUCCESS = "green" 
    WARNING = "yellow"
    ERROR = "red"
    MUTED = "dim white"
    ACCENT = "cyan"
    STREAK = "magenta"


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"✅ {message}", style=Colors.SUCCESS)


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"❌ {message}", style=Colors.ERROR)


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"⚠️  {message}", style=Colors.WARNING)


def print_info(message: str) -> None:
    """Print an informational message."""
    console.print(f"ℹ️  {message}", style=Colors.PRIMARY)


def create_habits_table(habits: List[Dict[str, Any]]) -> Table:
    """Create a formatted table for displaying habits.
    
    Args:
        habits: List of habit dictionaries with keys:
                name, description, frequency, streak, last_tracked, active
    
    Returns:
        Rich Table object
    """
    table = Table(
        title="📋 Your Habits",
        box=box.ROUNDED,
        header_style="bold blue",
        show_lines=True
    )
    
    table.add_column("Habit", style="bold", no_wrap=True, min_width=20)
    table.add_column("Frequency", justify="center", style=Colors.ACCENT, min_width=10)
    table.add_column("Streak", justify="center", style=Colors.STREAK, min_width=8)
    table.add_column("Last Tracked", justify="center", style=Colors.MUTED, min_width=12)
    table.add_column("Status", justify="center", min_width=8)
    
    for habit in habits:
        # Format habit name with description
        habit_display = Text(habit["name"], style="bold")
        if habit.get("description"):
            habit_display.append(f"\n{habit['description']}", style="dim")
        
        # Format frequency
        frequency = habit.get("frequency", "daily").title()
        
        # Format streak with emoji
        streak = habit.get("streak", 0)
        if streak > 0:
            streak_display = f"🔥 {streak}"
            if streak >= 30:
                streak_display = f"🏆 {streak}"
            elif streak >= 7:
                streak_display = f"⭐ {streak}"
        else:
            streak_display = "0"
        
        # Format last tracked date
        last_tracked = habit.get("last_tracked")
        if last_tracked:
            if isinstance(last_tracked, (date, datetime)):
                from .date_utils import format_relative_date
                last_display = format_relative_date(last_tracked)
            else:
                last_display = str(last_tracked)
        else:
            last_display = "Never"
        
        # Format status
        if habit.get("active", True):
            status = Text("✅ Active", style=Colors.SUCCESS)
        else:
            status = Text("📦 Archived", style=Colors.MUTED)
        
        table.add_row(
            habit_display,
            frequency,
            streak_display,
            last_display,
            status
        )
    
    if not habits:
        table.add_row(
            Text("No habits found", style="dim italic"),
            "", "", "", ""
        )
    
    return table


def create_stats_panel(stats: Dict[str, Any]) -> Panel:
    """Create a formatted panel for displaying habit statistics.
    
    Args:
        stats: Dictionary with statistics data
    
    Returns:
        Rich Panel object
    """
    content = []
    
    # Current streak
    streak = stats.get("current_streak", 0)
    if streak > 0:
        streak_emoji = "🔥" if streak < 7 else "⭐" if streak < 30 else "🏆"
        content.append(f"{streak_emoji} Current Streak: [bold]{streak}[/bold] days")
    else:
        content.append("🔥 Current Streak: [dim]0 days[/dim]")
    
    # Longest streak
    longest = stats.get("longest_streak", 0)
    if longest > 0:
        content.append(f"🏅 Longest Streak: [bold]{longest}[/bold] days")
    
    # Completion rate
    rate = stats.get("completion_rate", 0)
    rate_color = Colors.SUCCESS if rate >= 80 else Colors.WARNING if rate >= 60 else Colors.ERROR
    content.append(f"📊 Completion Rate: [{rate_color}]{rate:.1f}%[/{rate_color}]")
    
    # Total completions
    total = stats.get("total_completions", 0)
    content.append(f"✅ Total Completions: [bold]{total}[/bold]")
    
    # Period info
    period = stats.get("period", "all time")
    content.append(f"📅 Period: [dim]{period}[/dim]")
    
    panel_content = "\n".join(content)
    
    habit_name = stats.get("habit_name", "All Habits")
    title = f"📈 Statistics - {habit_name}"
    
    return Panel(
        panel_content,
        title=title,
        border_style=Colors.PRIMARY,
        padding=(1, 2)
    )


def create_today_panel(today_habits: List[Dict[str, Any]]) -> Panel:
    """Create a panel showing today's habits and completion status.
    
    Args:
        today_habits: List of habit dictionaries with completion status
    
    Returns:
        Rich Panel object
    """
    if not today_habits:
        content = Text("No habits for today", style="dim italic")
    else:
        content_lines = []
        completed_count = 0
        
        for habit in today_habits:
            name = habit["name"]
            completed = habit.get("completed_today", False)
            
            if completed:
                line = f"✅ {name}"
                completed_count += 1
                style = Colors.SUCCESS
            else:
                line = f"⭕ {name}"
                style = Colors.MUTED
            
            content_lines.append(Text(line, style=style))
        
        # Add summary
        total = len(today_habits)
        if completed_count == total and total > 0:
            summary = Text(f"\n🎉 All done! ({completed_count}/{total})", style=Colors.SUCCESS + " bold")
        else:
            summary = Text(f"\nProgress: {completed_count}/{total} completed", style=Colors.PRIMARY)
        
        content_lines.append(summary)
        content = Text.assemble(*[Text("\n")] + content_lines)
    
    from .date_utils import format_date, get_today
    today_str = format_date(get_today(), "long")
    
    return Panel(
        content,
        title=f"📅 Today - {today_str}",
        border_style=Colors.PRIMARY,
        padding=(1, 2)
    )


def create_progress_bar(
    current: int, 
    total: int, 
    description: str = "Progress"
) -> str:
    """Create a progress bar string.
    
    Args:
        current: Current progress value
        total: Total target value
        description: Description for the progress bar
    
    Returns:
        Formatted progress bar string
    """
    if total == 0:
        percentage = 0
    else:
        percentage = min(100, (current / total) * 100)
    
    # Create visual bar
    bar_length = 20
    filled_length = int(bar_length * percentage / 100)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)
    
    return f"{description}: [{bar}] {percentage:.1f}% ({current}/{total})"


def print_habit_added(name: str, frequency: str, description: str = "") -> None:
    """Print confirmation for habit addition."""
    message = f"Added habit '[bold]{name}[/bold]' with {frequency} frequency"
    if description:
        message += f"\nDescription: {description}"
    print_success(message)


def print_habit_tracked(name: str, date_str: str, note: str = "") -> None:
    """Print confirmation for habit tracking."""
    message = f"Tracked '[bold]{name}[/bold]' for {date_str}"
    if note:
        message += f"\nNote: {note}"
    print_success(message)


def print_habit_removed(name: str, permanent: bool = False) -> None:
    """Print confirmation for habit removal."""
    action = "Permanently deleted" if permanent else "Archived"
    print_warning(f"{action} habit '[bold]{name}[/bold]'")


def print_streak_celebration(habit_name: str, streak: int) -> None:
    """Print celebration for streak milestones."""
    if streak == 1:
        message = f"🎉 Great start! You've tracked '[bold]{habit_name}[/bold]' for 1 day!"
    elif streak == 7:
        message = f"⭐ Amazing! One week streak for '[bold]{habit_name}[/bold]'!"
    elif streak == 30:
        message = f"🏆 Incredible! One month streak for '[bold]{habit_name}[/bold]'!"
    elif streak % 30 == 0:
        months = streak // 30
        message = f"🏆 Outstanding! {months} month{'s' if months > 1 else ''} streak for '[bold]{habit_name}[/bold]'!"
    elif streak % 7 == 0:
        weeks = streak // 7
        message = f"⭐ Fantastic! {weeks} week{'s' if weeks > 1 else ''} streak for '[bold]{habit_name}[/bold]'!"
    else:
        return  # No celebration for other numbers
    
    console.print(Panel(
        Align.center(message),
        border_style=Colors.SUCCESS,
        padding=(1, 2)
    ))


def show_table(table: Table) -> None:
    """Display a table using the global console."""
    console.print()
    console.print(table)
    console.print()


def show_panel(panel: Panel) -> None:
    """Display a panel using the global console."""
    console.print()
    console.print(panel)
    console.print()