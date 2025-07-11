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


# Add command groups (will be implemented in separate files)
@app.command()
def add(
    name: str = typer.Argument(..., help="Name of the habit to add"),
    frequency: str = typer.Option("daily", "--frequency", "-f", help="Habit frequency (daily, weekly, custom)"),
    description: str = typer.Option("", "--description", "-d", help="Optional habit description"),
):
    """Add a new habit to track."""
    console.print(f"[green]Adding habit: {name}[/green] (frequency: {frequency})")
    if description:
        console.print(f"Description: {description}")
    # Implementation will be moved to commands/habits.py


@app.command()
def list(
    filter_type: str = typer.Option("active", "--filter", "-f", help="Filter habits (active, archived, all)"),
):
    """List all habits."""
    console.print(f"[blue]Listing {filter_type} habits:[/blue]")
    # Implementation will be moved to commands/habits.py


@app.command()
def track(
    habit_name: str = typer.Argument(..., help="Name of the habit to track"),
    date: str = typer.Option("", "--date", "-d", help="Date to track (YYYY-MM-DD, defaults to today)"),
    note: str = typer.Option("", "--note", "-n", help="Optional note about the tracking"),
):
    """Track completion of a habit."""
    console.print(f"[green]Tracking habit: {habit_name}[/green]")
    if date:
        console.print(f"Date: {date}")
    if note:
        console.print(f"Note: {note}")
    # Implementation will be moved to commands/tracking.py


@app.command()
def today():
    """Show today's habits and their completion status."""
    console.print("[blue]Today's Habits:[/blue]")
    # Implementation will be moved to commands/tracking.py


@app.command()
def stats(
    habit_name: str = typer.Option("", "--habit", "-h", help="Show stats for specific habit"),
    period: str = typer.Option("all", "--period", "-p", help="Time period (week, month, year, all)"),
):
    """Show habit statistics and analytics."""
    console.print(f"[blue]Statistics[/blue]")
    if habit_name:
        console.print(f"Habit: {habit_name}")
    console.print(f"Period: {period}")
    # Implementation will be moved to commands/analytics.py


@app.command()
def remove(
    habit_name: str = typer.Argument(..., help="Name of the habit to remove"),
):
    """Remove (archive) a habit."""
    confirm = typer.confirm(f"Are you sure you want to remove habit '{habit_name}'?")
    if confirm:
        console.print(f"[yellow]Removing habit: {habit_name}[/yellow]")
        # Implementation will be moved to commands/habits.py
    else:
        console.print("Operation cancelled.")


@app.command()
def delete(
    habit_name: str = typer.Argument(..., help="Name of the habit to permanently delete"),
    confirm: bool = typer.Option(False, "--confirm", help="Skip confirmation prompt"),
):
    """Permanently delete a habit and all its data."""
    if not confirm:
        confirm = typer.confirm(
            f"[red]WARNING:[/red] This will permanently delete habit '{habit_name}' "
            f"and ALL its tracking data. This cannot be undone. Continue?"
        )
    
    if confirm:
        console.print(f"[red]Permanently deleting habit: {habit_name}[/red]")
        # Implementation will be moved to commands/habits.py
    else:
        console.print("Operation cancelled.")


if __name__ == "__main__":
    app()