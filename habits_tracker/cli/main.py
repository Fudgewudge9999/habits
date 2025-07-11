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
    restore_habit
)

# Add habit management commands directly to main app
app.command("add")(add_habit)
app.command("list")(list_habits)
app.command("remove")(remove_habit)
app.command("delete")(delete_habit)
app.command("restore")(restore_habit)


# Placeholder commands for tracking and analytics (will be implemented in Phase 1B/1C)
@app.command()
def track(
    habit_name: str = typer.Argument(..., help="Name of the habit to track"),
    date: str = typer.Option("", "--date", "-d", help="Date to track (YYYY-MM-DD, defaults to today)"),
    note: str = typer.Option("", "--note", "-n", help="Optional note about the tracking"),
):
    """Track completion of a habit."""
    console.print(f"[yellow]Track command not yet implemented - coming in Phase 1B[/yellow]")
    console.print(f"Would track: {habit_name}")


@app.command()
def today():
    """Show today's habits and their completion status."""
    console.print("[yellow]Today command not yet implemented - coming in Phase 1B[/yellow]")


@app.command()
def stats(
    habit_name: str = typer.Option("", "--habit", "-h", help="Show stats for specific habit"),
    period: str = typer.Option("all", "--period", "-p", help="Time period (week, month, year, all)"),
):
    """Show habit statistics and analytics."""
    console.print("[yellow]Stats command not yet implemented - coming in Phase 1C[/yellow]")


if __name__ == "__main__":
    app()