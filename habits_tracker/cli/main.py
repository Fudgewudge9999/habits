"""Main CLI application entry point for HabitsTracker."""

import typer
from rich.console import Console
from rich.traceback import install

from habits_tracker import __version__
from habits_tracker.core.database import ensure_database

# Install rich traceback handler for better error display
install(show_locals=True)

# Create console for rich output
console = Console()

# Create main Typer app
app = typer.Typer(
    name="habits",
    help="HabitsTracker CLI - A minimalist habit tracking tool for macOS",
    epilog="Made with ❤️ for productivity enthusiasts",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool):
    """Print version information."""
    if value:
        console.print(f"HabitsTracker CLI v{__version__}")
        console.print("A minimalist habit tracking tool for macOS")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, 
        "--version", 
        "-v",
        callback=version_callback,
        help="Show version information"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Enable debug mode"
    )
):
    """HabitsTracker CLI - Track your habits effortlessly from the terminal.
    
    A lightweight, fast, and intuitive command-line tool for building and
    maintaining positive habits. Perfect for developers and power users who
    prefer terminal interfaces.
    
    Examples:
        habits add "Exercise" --frequency daily
        habits track "Exercise"
        habits list
        habits stats
    """
    # Set debug mode globally if needed
    if debug:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    
    # Ensure database is ready before running commands
    if not ensure_database():
        console.print("[red]Error: Failed to initialize database[/red]")
        raise typer.Exit(1)


# Import habit commands and add them directly to main app
from .commands.habits import (
    add_habit,
    list_habits, 
    remove_habit,
    delete_habit,
    restore_habit,
    edit_habit,
    show_habit_history
)

# Import tracking commands
from .commands.tracking import (
    track_habit,
    untrack_habit,
    show_today
)

# Import analytics commands
from .commands.analytics import (
    show_stats,
    show_chart,
    show_progress,
    generate_report
)

# Import performance commands
from .commands.performance import (
    performance_profile,
    performance_benchmark,
    database_analyze,
    memory_usage
)

# Import category commands
from .commands.categories import app as categories_app

# Add habit management commands directly to main app
app.command("add")(add_habit)
app.command("list")(list_habits)
app.command("remove")(remove_habit)
app.command("delete")(delete_habit)
app.command("restore")(restore_habit)
app.command("edit")(edit_habit)
app.command("history")(show_habit_history)

# Add tracking commands
app.command("track")(track_habit)
app.command("untrack")(untrack_habit)
app.command("today")(show_today)

# Add analytics commands
app.command("stats")(show_stats)
app.command("chart")(show_chart)
app.command("progress")(show_progress)
app.command("report")(generate_report)

# Add performance commands
app.command("profile")(performance_profile)
app.command("benchmark")(performance_benchmark)
app.command("db-analyze")(database_analyze)
app.command("memory")(memory_usage)

# Add category management as a subcommand group
app.add_typer(categories_app, name="categories")


if __name__ == "__main__":
    app()