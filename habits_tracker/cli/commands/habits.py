"""CLI commands for habit management (add, list, remove, delete)."""

import typer
from typing import Optional, List
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.panel import Panel

from habits_tracker.core.services.habit_service import (
    HabitService, 
    HabitValidationError, 
    HabitNotFoundError
)
from habits_tracker.core.services.editing_service import (
    EditingService,
    EditValidationError,
    EditConflictError
)
from habits_tracker.core.services.category_service import (
    CategoryService,
    CategoryValidationError,
    CategoryNotFoundError
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
    categories: Optional[List[str]] = typer.Option(
        None,
        "--category",
        "-c",
        help="Categories to assign (can be used multiple times)"
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
        
        # Assign categories if specified
        category_results = []
        if categories:
            for category_name in categories:
                try:
                    success = CategoryService.assign_category_to_habit(habit.name, category_name)
                    if success:
                        category_results.append(f"✅ {category_name}")
                    else:
                        category_results.append(f"❌ {category_name} (failed)")
                except CategoryNotFoundError:
                    category_results.append(f"❌ {category_name} (not found)")
                except Exception:
                    category_results.append(f"❌ {category_name} (error)")
        
        # Success message
        message = f"Added habit '[bold]{habit.name}[/bold]' with {habit.frequency} frequency"
        if habit.description:
            message += f"\n💭 {habit.description}"
        
        if category_results:
            message += f"\n🏷️ Categories: {', '.join(category_results)}"
        
        print_success(message)
        
        # Show helpful next steps
        console.print(f"\n💡 [dim]Next steps:[/dim]")
        console.print(f"   • Track it: [cyan]habits track \"{habit.name}\"[/cyan]")
        console.print(f"   • View all: [cyan]habits list[/cyan]")
        if categories and any("not found" in result for result in category_results):
            console.print(f"   • Create missing categories: [cyan]habits categories add \"Category Name\"[/cyan]")
        
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
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by category name"
    ),
    search: Optional[str] = typer.Option(
        None,
        "--search",
        "-s",
        help="Search habits by name or description"
    ),
    no_stats: bool = typer.Option(
        False,
        "--no-stats",
        help="Skip calculating statistics for faster display"
    )
):
    """List your habits with their current status and statistics.
    
    Shows a formatted table with habit information including streaks, completion
    rates, categories, and last tracked dates. Use filters to show different habit states.
    
    Examples:
        habits list                         # Show active habits
        habits list --filter all            # Show all habits
        habits list -f archived             # Show archived habits only
        habits list --category "Health"     # Show habits in Health category
        habits list --search "exercise"     # Search for habits containing "exercise"
        habits list -c "Work" -s "daily"    # Combine category and search filters
        habits list --no-stats              # Fast display without statistics
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
        
        # Apply category filtering if specified
        if category:
            try:
                category_habits = CategoryService.get_habits_by_category(
                    category, 
                    active_only=(filter_type == "active")
                )
                category_habit_ids = {h["id"] for h in category_habits}
                habits = [h for h in habits if h["id"] in category_habit_ids]
            except CategoryNotFoundError:
                print_error(f"Category '{category}' not found.")
                console.print("\n💡 [dim]View available categories:[/dim] [cyan]habits categories list[/cyan]")
                return
        
        # Apply search filtering if specified
        if search:
            search_lower = search.lower()
            habits = [
                h for h in habits 
                if search_lower in h["name"].lower() or 
                   (h.get("description") and search_lower in h["description"].lower())
            ]
        
        if not habits:
            message = "No habits found"
            if category:
                message += f" in category '{category}'"
            if search:
                message += f" matching '{search}'"
            if filter_type != "all":
                message += f" ({filter_type})"
            
            print_warning(f"{message}.")
            
            if not category and not search:
                console.print("\n💡 [dim]Get started:[/dim]")
                console.print("   • Add a habit: [cyan]habits add \"Exercise\"[/cyan]")
            else:
                console.print("\n💡 [dim]Try different filters:[/dim]")
                console.print("   • View all habits: [cyan]habits list --filter all[/cyan]")
                if category:
                    console.print("   • View all categories: [cyan]habits categories list[/cyan]")
            return
        
        # Create and display table with category information
        table = create_habits_table(habits, show_categories=True)
        show_table(table)
        
        # Show summary with filters
        total = len(habits)
        summary_parts = []
        
        if filter_type == "active":
            summary_parts.append(f"{total} active habit{'s' if total != 1 else ''}")
        elif filter_type == "archived":
            summary_parts.append(f"{total} archived habit{'s' if total != 1 else ''}")
        else:
            active_count = sum(1 for h in habits if h["active"])
            archived_count = total - active_count
            summary_parts.append(f"{total} total habits ({active_count} active, {archived_count} archived)")
        
        if category:
            summary_parts.append(f"in category '{category}'")
        if search:
            summary_parts.append(f"matching '{search}'")
        
        summary = " ".join(summary_parts)
        icon = "📊" if filter_type != "archived" else "📦"
        console.print(f"{icon} [dim]Showing {summary}[/dim]")
        
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
            console.print(f"Archive habit '[bold]{name}[/bold]'? (tracking data will be preserved)")
            confirm = Confirm.ask("Continue?", default=False)
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


def edit_habit(
    name: str = typer.Argument(..., help="Name of the habit to edit"),
    new_name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help="New name for the habit"
    ),
    frequency: Optional[str] = typer.Option(
        None,
        "--frequency",
        "-f",
        help="New frequency for the habit (daily, weekly, custom)"
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="New description for the habit"
    ),
    categories: Optional[List[str]] = typer.Option(
        None,
        "--category",
        "-c",
        help="Categories to assign (can be used multiple times)"
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Launch interactive editing session"
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        "-p",
        help="Preview changes without applying them"
    )
):
    """Edit an existing habit with guided prompts or direct parameters.
    
    Use without parameters for interactive mode, or specify parameters for direct editing.
    Preview mode shows what changes would be made without applying them.
    
    Examples:
        habits edit "Exercise"                    # Interactive mode
        habits edit "Exercise" --name "Workout"   # Direct name change
        habits edit "Exercise" -f weekly -d "New description"
        habits edit "Exercise" --preview          # Preview changes
    """
    try:
        # If no parameters specified or interactive flag is set, use interactive mode
        if interactive or (new_name is None and frequency is None and description is None and not categories):
            _edit_habit_interactive(name)
        else:
            # Direct editing mode
            _edit_habit_direct(name, new_name, frequency, description, categories, preview)
            
    except (HabitNotFoundError, EditValidationError, EditConflictError) as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


def _edit_habit_interactive(habit_name: str) -> None:
    """Interactive habit editing session.
    
    Args:
        habit_name: Name of the habit to edit
    """
    try:
        # Get current habit details
        habit = HabitService.get_habit_by_name(habit_name)
        if not habit:
            print_error(f"Habit '{habit_name}' not found.")
            return
        
        if not habit.active:
            print_error(f"Cannot edit archived habit '{habit_name}'. Restore it first.")
            console.print(f"💡 [dim]Restore it:[/dim] [cyan]habits restore \"{habit_name}\"[/cyan]")
            return
        
        # Display current habit information
        console.print(f"\n[bold]Editing habit: {habit.name}[/bold]")
        
        current_table = Table(title="Current Values", show_header=True, header_style="bold cyan")
        current_table.add_column("Field", style="cyan")
        current_table.add_column("Value", style="white")
        
        current_table.add_row("Name", habit.name)
        current_table.add_row("Frequency", habit.frequency)
        current_table.add_row("Description", habit.description or "[dim](none)[/dim]")
        
        # Get current categories
        try:
            current_categories = CategoryService.get_habit_categories(habit_name)
            category_names = [cat["name"] for cat in current_categories] if current_categories else []
            current_table.add_row("Categories", ", ".join(category_names) or "[dim](none)[/dim]")
        except Exception:
            current_table.add_row("Categories", "[dim](error retrieving)[/dim]")
        
        console.print(current_table)
        console.print()
        
        # Interactive prompts for each field
        changes = {}
        
        # Name change
        console.print("[bold cyan]Name[/bold cyan]")
        new_name = Prompt.ask(
            f"New name (current: {habit.name})",
            default="",
            show_default=False
        )
        if new_name and new_name != habit.name:
            changes["name"] = new_name
        
        # Frequency change
        console.print("\n[bold cyan]Frequency[/bold cyan]")
        console.print("Valid options: daily, weekly, custom")
        new_frequency = Prompt.ask(
            f"New frequency (current: {habit.frequency})",
            default="",
            show_default=False
        )
        if new_frequency and new_frequency != habit.frequency:
            changes["frequency"] = new_frequency
        
        # Description change
        console.print("\n[bold cyan]Description[/bold cyan]")
        current_desc = habit.description or ""
        new_description = Prompt.ask(
            f"New description (current: {current_desc or '(none)'})",
            default="",
            show_default=False
        )
        if new_description != current_desc:
            changes["description"] = new_description if new_description else None
        
        # Categories (simplified for now - full category editing will come with category commands)
        console.print("\n[bold cyan]Categories[/bold cyan]")
        console.print("[dim]Note: Full category management will be available with 'habits categories' commands[/dim]")
        
        # Check if any changes were made
        if not changes:
            console.print("\n[yellow]No changes specified.[/yellow]")
            return
        
        # Preview changes
        console.print("\n[bold]Preview of Changes:[/bold]")
        preview_table = Table(show_header=True, header_style="bold cyan")
        preview_table.add_column("Field", style="cyan")
        preview_table.add_column("From", style="red")
        preview_table.add_column("To", style="green")
        
        for field, new_value in changes.items():
            if field == "name":
                preview_table.add_row("Name", habit.name, new_value)
            elif field == "frequency":
                preview_table.add_row("Frequency", habit.frequency, new_value)
            elif field == "description":
                old_desc = habit.description or "(none)"
                new_desc = new_value or "(none)"
                preview_table.add_row("Description", old_desc, new_desc)
        
        console.print(preview_table)
        
        # Confirmation
        console.print()
        confirm = Confirm.ask("Apply these changes?", default=True)
        
        if not confirm:
            console.print("Edit cancelled.")
            return
        
        # Apply changes
        result = EditingService.edit_habit(
            habit_name=habit_name,
            name=changes.get("name"),
            frequency=changes.get("frequency"),
            description=changes.get("description")
        )
        
        if result["success"]:
            print_success(f"Successfully updated habit '{result['habit']['name']}'")
            
            # Show what changed
            for field, change in result["changes"].items():
                if isinstance(change, dict) and "old" in change and "new" in change:
                    console.print(f"  • {field.capitalize()}: {change['old']} → {change['new']}")
            
            console.print(f"\n💡 [dim]View updated habit:[/dim] [cyan]habits list[/cyan]")
        else:
            print_error("Failed to update habit")
            
    except Exception as e:
        print_error(f"Interactive editing failed: {str(e)}")


def _edit_habit_direct(
    habit_name: str,
    new_name: Optional[str],
    frequency: Optional[str],
    description: Optional[str],
    categories: Optional[List[str]],
    preview_only: bool
) -> None:
    """Direct habit editing with command line parameters.
    
    Args:
        habit_name: Name of the habit to edit
        new_name: New name for the habit
        frequency: New frequency
        description: New description
        categories: New categories list
        preview_only: If True, only show preview without applying
    """
    try:
        if preview_only:
            # Get preview of changes
            preview = EditingService.get_edit_preview(
                habit_name=habit_name,
                name=new_name,
                frequency=frequency,
                description=description,
                categories=categories
            )
            
            if not preview["valid"]:
                console.print("[red bold]Preview failed - validation errors:[/red bold]")
                for error in preview["errors"]:
                    print_error(f"  • {error}")
                return
            
            # Show preview
            console.print("[bold cyan]Preview of Changes:[/bold cyan]")
            
            if preview["warnings"]:
                console.print("\n[yellow bold]Warnings:[/yellow bold]")
                for warning in preview["warnings"]:
                    console.print(f"  ⚠️  {warning}")
            
            if preview["changes"]:
                preview_table = Table(show_header=True, header_style="bold cyan")
                preview_table.add_column("Field", style="cyan")
                preview_table.add_column("From", style="red")
                preview_table.add_column("To", style="green")
                
                for field, change in preview["changes"].items():
                    preview_table.add_row(field.capitalize(), change["from"], change["to"])
                
                console.print(preview_table)
                console.print("\n[dim]To apply these changes, run the same command without --preview[/dim]")
            else:
                console.print("[yellow]No changes would be made.[/yellow]")
            
            return
        
        # Apply changes directly
        result = EditingService.edit_habit(
            habit_name=habit_name,
            name=new_name,
            frequency=frequency,
            description=description,
            categories=categories
        )
        
        if result["success"]:
            print_success(result["message"])
            
            # Show summary of changes
            if result["changes"]:
                console.print("\n[bold]Changes applied:[/bold]")
                for field, change in result["changes"].items():
                    if isinstance(change, dict) and "old" in change and "new" in change:
                        console.print(f"  • {field.capitalize()}: [red]{change['old']}[/red] → [green]{change['new']}[/green]")
                    else:
                        console.print(f"  • {field.capitalize()}: {change}")
            
            console.print(f"\n💡 [dim]Next steps:[/dim]")
            console.print(f"   • View updated habit: [cyan]habits list[/cyan]")
            console.print(f"   • Track it: [cyan]habits track \"{result['habit']['name']}\"[/cyan]")
        else:
            print_error("Failed to update habit")
            
    except Exception as e:
        print_error(f"Direct editing failed: {str(e)}")


def show_habit_history(
    name: str = typer.Argument(..., help="Name of the habit to show history for"),
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum number of history entries to show"
    )
):
    """Show edit history for a habit.
    
    Displays a chronological list of all modifications made to a habit,
    including what was changed, when, and the old/new values.
    
    Examples:
        habits history "Exercise"          # Show last 20 changes
        habits history "Exercise" -l 50    # Show last 50 changes
    """
    try:
        history = EditingService.get_habit_history(name, limit=limit)
        
        if not history:
            console.print(f"No edit history found for habit '{name}'.")
            console.print("[dim]Note: History tracking was added in Phase 2A - only changes after upgrade are tracked.[/dim]")
            return
        
        console.print(f"\n[bold]Edit History for '{name}'[/bold]")
        
        history_table = Table(show_header=True, header_style="bold cyan")
        history_table.add_column("Date/Time", style="cyan")
        history_table.add_column("Field", style="yellow")
        history_table.add_column("Change", style="white")
        history_table.add_column("Type", style="blue")
        
        for entry in history:
            # Format the change description
            if entry["old_value"] and entry["new_value"]:
                change_desc = f"[red]{entry['old_value']}[/red] → [green]{entry['new_value']}[/green]"
            elif entry["new_value"]:
                change_desc = f"Set to [green]{entry['new_value']}[/green]"
            elif entry["old_value"]:
                change_desc = f"Removed [red]{entry['old_value']}[/red]"
            else:
                change_desc = "[dim]No details[/dim]"
            
            # Format timestamp
            timestamp = entry["changed_at"].strftime("%Y-%m-%d %H:%M")
            
            history_table.add_row(
                timestamp,
                entry["field_name"],
                change_desc,
                entry["change_type"]
            )
        
        console.print(history_table)
        console.print(f"\n[dim]Showing {len(history)} of last {limit} changes[/dim]")
        
    except HabitNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Failed to retrieve history: {str(e)}")
        raise typer.Exit(1)


# Export the functions for integration with main CLI
__all__ = ["add_habit", "list_habits", "remove_habit", "delete_habit", "restore_habit", "edit_habit", "show_habit_history"]