"""CLI commands for habit management (add, list, remove, delete)."""

import typer
from typing import Optional
from rich.console import Console

from habits_tracker.core.services.habit_service import (
    HabitService, 
    HabitValidationError, 
    HabitNotFoundError
)
from habits_tracker.utils.display import (
    print_success, 
    print_error, 
    print_warning, 
    create_habits_table,
    show_table,
    console
)

def add_habit(
    name: str = typer.Argument(..., help="Name of the habit to add"),
    frequency: str = typer.Option(
        "daily", 
        "--frequency", 
        "-f", 
        help="Habit frequency (daily, weekly, custom)",
        show_default=True
    ),
    description: Optional[str] = typer.Option(
        None, 
        "--description", 
        "-d", 
        help="Optional habit description (max 500 characters)"
    ),
):
    """Add a new habit to track.
    
    Creates a new habit with the specified frequency. If a habit with the same
    name was previously archived, it will be restored instead of creating a duplicate.
    
    Examples:
        habits add "Exercise"
        habits add "Read" --frequency daily --description "Read for 30 minutes"
        habits add "Gym" -f weekly -d "Go to the gym"
    """
    try:
        habit = HabitService.create_habit(
            name=name,
            frequency=frequency,
            description=description
        )
        
        # Success message
        message = f"Added habit '[bold]{habit.name}[/bold]' with {habit.frequency} frequency"
        if habit.description:
            message += f"\n💭 {habit.description}"
        
        print_success(message)
        
        # Show helpful next steps
        console.print(f"\n💡 [dim]Next steps:[/dim]")
        console.print(f"   • Track it: [cyan]habits track \"{habit.name}\"[/cyan]")
        console.print(f"   • View all: [cyan]habits list[/cyan]")
        
    except HabitValidationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def list_habits(
    filter_type: str = typer.Option(
        "active", 
        "--filter", 
        "-f", 
        help="Filter habits (active, archived, all)",
        show_default=True
    ),
    no_stats: bool = typer.Option(
        False,
        "--no-stats",
        help="Skip calculating statistics for faster display"
    )
):
    """List your habits with their current status and statistics.
    
    Shows a formatted table with habit information including streaks, completion
    rates, and last tracked dates. Use filters to show different habit states.
    
    Examples:
        habits list                    # Show active habits
        habits list --filter all       # Show all habits
        habits list -f archived        # Show archived habits only
        habits list --no-stats         # Fast display without statistics
    """
    try:
        # Validate filter type
        valid_filters = ["active", "archived", "all"]
        if filter_type not in valid_filters:
            print_error(f"Invalid filter '{filter_type}'. Valid options: {', '.join(valid_filters)}")
            raise typer.Exit(1)
        
        # Get habits
        habits = HabitService.list_habits(
            filter_type=filter_type,
            include_stats=not no_stats
        )
        
        if not habits:
            if filter_type == "active":
                print_warning("No active habits found.")
                console.print("\n💡 [dim]Get started:[/dim]")
                console.print("   • Add a habit: [cyan]habits add \"Exercise\"[/cyan]")
            elif filter_type == "archived":
                print_warning("No archived habits found.")
            else:
                print_warning("No habits found.")
                console.print("\n💡 [dim]Get started:[/dim]")
                console.print("   • Add a habit: [cyan]habits add \"Exercise\"[/cyan]")
            return
        
        # Create and display table
        table = create_habits_table(habits)
        show_table(table)
        
        # Show summary
        total = len(habits)
        if filter_type == "active":
            console.print(f"📊 [dim]Showing {total} active habit{'s' if total != 1 else ''}[/dim]")
        elif filter_type == "archived":
            console.print(f"📦 [dim]Showing {total} archived habit{'s' if total != 1 else ''}[/dim]")
        else:
            active_count = sum(1 for h in habits if h["active"])
            archived_count = total - active_count
            console.print(f"📊 [dim]Showing {total} total habits ({active_count} active, {archived_count} archived)[/dim]")
        
    except Exception as e:
        print_error(f"Failed to list habits: {str(e)}")
        raise typer.Exit(1)


def remove_habit(
    name: str = typer.Argument(..., help="Name of the habit to remove (archive)"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Skip confirmation prompt"
    )
):
    """Remove (archive) a habit without deleting its tracking data.
    
    This performs a "soft delete" - the habit is archived but all tracking data
    is preserved. Archived habits can be restored later if needed.
    
    Examples:
        habits remove "Old Habit"      # Will prompt for confirmation
        habits remove "Old Habit" -f   # Skip confirmation
    """
    try:
        # Check if habit exists
        habit = HabitService.get_habit_by_name(name)
        if not habit:
            print_error(f"Habit '{name}' not found.")
            return
        
        if not habit.active:
            print_warning(f"Habit '{name}' is already archived.")
            return
        
        # Confirmation prompt
        if not force:
            confirm = typer.confirm(
                f"Archive habit '[bold]{name}[/bold]'? (tracking data will be preserved)"
            )
            if not confirm:
                console.print("Operation cancelled.")
                return
        
        # Remove habit
        success = HabitService.remove_habit(name, permanent=False)
        
        if success:
            print_warning(f"Archived habit '[bold]{name}[/bold]'")
            console.print("\n💡 [dim]Note:[/dim] Archived habits can be restored or permanently deleted later")
            console.print(f"   • Restore: [cyan]habits restore \"{name}\"[/cyan]")
            console.print(f"   • Delete permanently: [cyan]habits delete \"{name}\"[/cyan]")
        else:
            print_error(f"Failed to archive habit '{name}'")
            
    except HabitValidationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def delete_habit(
    name: str = typer.Argument(..., help="Name of the habit to permanently delete"),
    confirm: bool = typer.Option(
        False, 
        "--confirm", 
        help="Skip confirmation prompt (dangerous!)"
    )
):
    """Permanently delete a habit and ALL its tracking data.
    
    ⚠️  WARNING: This action cannot be undone! All tracking data for this habit
    will be permanently deleted. Consider using 'habits remove' instead to archive.
    
    Examples:
        habits delete "Unwanted Habit"     # Will show warning and prompt
        habits delete "Unwanted Habit" --confirm  # Skip prompts (dangerous!)
    """
    try:
        # Check if habit exists
        habit = HabitService.get_habit_by_name(name, include_archived=True)
        if not habit:
            print_error(f"Habit '{name}' not found.")
            return
        
        # Double confirmation for permanent deletion
        if not confirm:
            console.print(f"[red bold]⚠️  WARNING: PERMANENT DELETION[/red bold]")
            console.print(f"This will permanently delete habit '[bold]{name}[/bold]' and ALL its tracking data.")
            console.print(f"This action [red]CANNOT BE UNDONE[/red].")
            console.print()
            
            # First confirmation
            confirm1 = typer.confirm("Do you really want to permanently delete this habit?")
            if not confirm1:
                console.print("Operation cancelled.")
                return
            
            # Second confirmation with exact name
            console.print(f"\nTo confirm, please type the habit name exactly: [bold]{name}[/bold]")
            typed_name = typer.prompt("Habit name")
            
            if typed_name != name:
                print_error("Habit name does not match. Operation cancelled.")
                return
        
        # Delete habit
        success = HabitService.remove_habit(name, permanent=True)
        
        if success:
            print_warning(f"Permanently deleted habit '[bold]{name}[/bold]' and all its data")
        else:
            print_error(f"Failed to delete habit '{name}'")
            
    except HabitValidationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def restore_habit(
    name: str = typer.Argument(..., help="Name of the archived habit to restore")
):
    """Restore an archived habit back to active status.
    
    Reactivates a previously archived habit, making it available for tracking again.
    All historical tracking data is preserved.
    
    Examples:
        habits restore "Exercise"      # Restore archived habit
    """
    try:
        # Check if habit exists and is archived
        habit = HabitService.get_habit_by_name(name, include_archived=True)
        if not habit:
            print_error(f"Habit '{name}' not found.")
            console.print("\n💡 [dim]View archived habits:[/dim] [cyan]habits list --filter archived[/cyan]")
            return
        
        if habit.active:
            print_warning(f"Habit '{name}' is already active.")
            return
        
        # Restore habit
        success = HabitService.restore_habit(name)
        
        if success:
            print_success(f"Restored habit '[bold]{name}[/bold]'")
            console.print(f"\n💡 [dim]Start tracking again:[/dim] [cyan]habits track \"{name}\"[/cyan]")
        else:
            print_error(f"Failed to restore habit '{name}'")
            
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


# Export the functions for integration with main CLI
__all__ = ["add_habit", "list_habits", "remove_habit", "delete_habit", "restore_habit"]