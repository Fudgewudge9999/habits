"""CLI commands for category management."""

import typer
from typing import Optional
from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from habits_tracker.core.services.category_service import (
    CategoryService,
    CategoryValidationError,
    CategoryNotFoundError
)
from habits_tracker.utils.display import (
    print_success,
    print_error,
    print_warning,
    show_table,
    console
)

# Create a Typer app for category commands
app = typer.Typer(
    name="categories",
    help="Manage habit categories for organization and filtering",
    no_args_is_help=True
)


@app.command("list")
def list_categories(
    no_stats: bool = typer.Option(
        False,
        "--no-stats",
        help="Skip calculating habit count statistics for faster display"
    )
):
    """List all habit categories with statistics.
    
    Shows a formatted table with category information including the number
    of habits assigned to each category.
    
    Examples:
        habits categories list              # Show all categories with stats
        habits categories list --no-stats  # Fast display without statistics
    """
    try:
        categories = CategoryService.list_categories(include_stats=not no_stats)
        
        if not categories:
            print_warning("No categories found.")
            console.print("\n💡 [dim]Get started:[/dim]")
            console.print("   • Add a category: [cyan]habits categories add \"Health\"[/cyan]")
            return
        
        # Create and display table
        table = Table(title="Habit Categories", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("Color", style="white")
        table.add_column("Description", style="white")
        
        if not no_stats:
            table.add_column("Habits", style="yellow", justify="right")
            table.add_column("Active", style="green", justify="right")
        
        table.add_column("Created", style="dim", justify="right")
        
        for category in categories:
            color_display = ""
            if category["color"]:
                # Show color code with colored square
                color_display = f"[{category['color']}]■[/{category['color']}] {category['color']}"
            else:
                color_display = "[dim](none)[/dim]"
            
            description = category["description"] or "[dim](none)[/dim]"
            created = category["created_at"].strftime("%Y-%m-%d")
            
            row = [
                category["name"],
                color_display,
                description,
            ]
            
            if not no_stats:
                row.extend([
                    str(category.get("total_habits", 0)),
                    str(category.get("active_habits", 0))
                ])
            
            row.append(created)
            table.add_row(*row)
        
        show_table(table)
        
        # Show summary
        total = len(categories)
        console.print(f"📊 [dim]Showing {total} categor{'ies' if total != 1 else 'y'}[/dim]")
        
    except Exception as e:
        print_error(f"Failed to list categories: {str(e)}")
        raise typer.Exit(1)


@app.command("add")
def add_category(
    name: str = typer.Argument(..., help="Name of the category to add"),
    color: Optional[str] = typer.Option(
        None,
        "--color",
        "-c",
        help="Color for the category (hex code like #FF0000)"
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Optional category description"
    ),
):
    """Add a new habit category.
    
    Creates a new category that can be assigned to habits for organization
    and filtering. Colors are displayed in the terminal for visual distinction.
    
    Examples:
        habits categories add "Health"
        habits categories add "Fitness" --color "#00FF00" --description "Physical activities"
        habits categories add "Work" -c "#0066CC" -d "Professional habits"
    """
    try:
        category = CategoryService.create_category(
            name=name,
            color=color,
            description=description
        )
        
        # Success message
        message = f"Added category '[bold]{category.name}[/bold]'"
        if category.color:
            message += f" with color [{category.color}]■[/{category.color}] {category.color}"
        if category.description:
            message += f"\n💭 {category.description}"
        
        print_success(message)
        
        # Show helpful next steps
        console.print(f"\n💡 [dim]Next steps:[/dim]")
        console.print(f"   • Assign to habit: [cyan]habits edit \"Exercise\" --category \"{category.name}\"[/cyan]")
        console.print(f"   • View all categories: [cyan]habits categories list[/cyan]")
        
    except CategoryValidationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@app.command("remove")
def remove_category(
    name: str = typer.Argument(..., help="Name of the category to remove"),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Remove category even if assigned to habits"
    )
):
    """Remove a habit category.
    
    Removes a category from the system. If the category is assigned to habits,
    you must use --force to remove it from all habits first.
    
    Examples:
        habits categories remove "Old Category"    # Will fail if in use
        habits categories remove "Old Category" -f # Remove from habits too
    """
    try:
        # Check if category exists
        category = CategoryService.get_category_by_name(name)
        if not category:
            print_error(f"Category '{name}' not found.")
            console.print("\n💡 [dim]View available categories:[/dim] [cyan]habits categories list[/cyan]")
            return
        
        # Try to delete the category
        success = CategoryService.delete_category(name, force=force)
        
        if success:
            if force:
                print_warning(f"Removed category '[bold]{name}[/bold]' and unassigned it from all habits")
            else:
                print_success(f"Removed category '[bold]{name}[/bold]'")
            
            console.print(f"\n💡 [dim]View remaining categories:[/dim] [cyan]habits categories list[/cyan]")
        else:
            print_error(f"Failed to remove category '{name}'")
            
    except CategoryValidationError as e:
        if "assigned to" in str(e):
            print_error(str(e))
            console.print(f"\n💡 [dim]To force removal:[/dim] [cyan]habits categories remove \"{name}\" --force[/cyan]")
        else:
            print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@app.command("rename")
def rename_category(
    old_name: str = typer.Argument(..., help="Current name of the category"),
    new_name: str = typer.Argument(..., help="New name for the category")
):
    """Rename an existing category.
    
    Changes the name of a category. All habit assignments are preserved.
    
    Examples:
        habits categories rename "Old Name" "New Name"
        habits categories rename "Fitness" "Health & Fitness"
    """
    try:
        # Check if category exists
        category = CategoryService.get_category_by_name(old_name)
        if not category:
            print_error(f"Category '{old_name}' not found.")
            console.print("\n💡 [dim]View available categories:[/dim] [cyan]habits categories list[/cyan]")
            return
        
        # Update the category
        success = CategoryService.update_category(old_name, new_name=new_name)
        
        if success:
            print_success(f"Renamed category '[bold]{old_name}[/bold]' to '[bold]{new_name}[/bold]'")
            console.print(f"\n💡 [dim]View updated category:[/dim] [cyan]habits categories list[/cyan]")
        else:
            print_error(f"Failed to rename category '{old_name}'")
            
    except CategoryValidationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@app.command("update")
def update_category(
    name: str = typer.Argument(..., help="Name of the category to update"),
    color: Optional[str] = typer.Option(
        None,
        "--color",
        "-c",
        help="New color for the category (hex code like #FF0000)"
    ),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="New description for the category"
    ),
):
    """Update category properties (color, description).
    
    Modify the color or description of an existing category without changing
    its name or habit assignments.
    
    Examples:
        habits categories update "Health" --color "#00FF00"
        habits categories update "Work" --description "Professional development"
        habits categories update "Fitness" -c "#FF6600" -d "Physical activities"
    """
    try:
        # Check if category exists
        category = CategoryService.get_category_by_name(name)
        if not category:
            print_error(f"Category '{name}' not found.")
            console.print("\n💡 [dim]View available categories:[/dim] [cyan]habits categories list[/cyan]")
            return
        
        # Check if any changes were specified
        if color is None and description is None:
            print_error("No changes specified. Provide --color or --description.")
            return
        
        # Update the category
        success = CategoryService.update_category(
            name,
            color=color,
            description=description
        )
        
        if success:
            changes = []
            if color is not None:
                changes.append(f"color to [{color}]■[/{color}] {color}")
            if description is not None:
                changes.append(f"description to \"{description}\"")
            
            change_text = " and ".join(changes)
            print_success(f"Updated category '[bold]{name}[/bold]' {change_text}")
            console.print(f"\n💡 [dim]View updated category:[/dim] [cyan]habits categories list[/cyan]")
        else:
            print_error(f"Failed to update category '{name}'")
            
    except CategoryValidationError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@app.command("assign")
def assign_category(
    habit_name: str = typer.Argument(..., help="Name of the habit"),
    category_name: str = typer.Argument(..., help="Name of the category to assign")
):
    """Assign a category to a habit.
    
    Adds the specified category to a habit. Habits can have multiple categories.
    
    Examples:
        habits categories assign "Exercise" "Health"
        habits categories assign "Reading" "Personal Development"
    """
    try:
        success = CategoryService.assign_category_to_habit(habit_name, category_name)
        
        if success:
            print_success(f"Assigned category '[bold]{category_name}[/bold]' to habit '[bold]{habit_name}[/bold]'")
            console.print(f"\n💡 [dim]Next steps:[/dim]")
            console.print(f"   • View habit: [cyan]habits list --filter active[/cyan]")
            console.print(f"   • Filter by category: [cyan]habits list --category \"{category_name}\"[/cyan]")
        else:
            print_error("Assignment failed")
            
    except (CategoryValidationError, CategoryNotFoundError) as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@app.command("unassign")
def unassign_category(
    habit_name: str = typer.Argument(..., help="Name of the habit"),
    category_name: str = typer.Argument(..., help="Name of the category to unassign")
):
    """Remove a category from a habit.
    
    Removes the specified category assignment from a habit.
    
    Examples:
        habits categories unassign "Exercise" "Old Category"
        habits categories unassign "Reading" "Work"
    """
    try:
        success = CategoryService.remove_category_from_habit(habit_name, category_name)
        
        if success:
            print_success(f"Removed category '[bold]{category_name}[/bold]' from habit '[bold]{habit_name}[/bold]'")
            console.print(f"\n💡 [dim]View updated habit:[/dim] [cyan]habits list[/cyan]")
        else:
            print_warning(f"Category '[bold]{category_name}[/bold]' was not assigned to habit '[bold]{habit_name}[/bold]'")
            
    except (CategoryValidationError, CategoryNotFoundError) as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        raise typer.Exit(1)


@app.command("show")
def show_category(
    name: str = typer.Argument(..., help="Name of the category to show details for")
):
    """Show detailed information about a category.
    
    Displays category details and lists all habits assigned to it.
    
    Examples:
        habits categories show "Health"
        habits categories show "Work"
    """
    try:
        # Get category details
        category = CategoryService.get_category_by_name(name)
        if not category:
            print_error(f"Category '{name}' not found.")
            console.print("\n💡 [dim]View available categories:[/dim] [cyan]habits categories list[/cyan]")
            return
        
        # Display category information
        console.print(f"\n[bold cyan]Category: {category.name}[/bold cyan]")
        
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("Field", style="cyan")
        info_table.add_column("Value", style="white")
        
        # Color
        if category.color:
            color_display = f"[{category.color}]■[/{category.color}] {category.color}"
        else:
            color_display = "[dim](none)[/dim]"
        info_table.add_row("Color:", color_display)
        
        # Description
        description = category.description or "[dim](none)[/dim]"
        info_table.add_row("Description:", description)
        
        # Created date
        created = category.created_at.strftime("%Y-%m-%d %H:%M")
        info_table.add_row("Created:", created)
        
        console.print(info_table)
        
        # Get habits in this category
        habits = CategoryService.get_habits_by_category(name, active_only=False)
        
        if habits:
            console.print(f"\n[bold]Habits in this category ({len(habits)}):[/bold]")
            
            habits_table = Table(show_header=True, header_style="bold cyan")
            habits_table.add_column("Name", style="cyan")
            habits_table.add_column("Frequency", style="yellow")
            habits_table.add_column("Status", style="white")
            habits_table.add_column("Created", style="dim")
            
            for habit in habits:
                status = "✅ Active" if habit["active"] else "📦 Archived"
                created = habit["created_at"].strftime("%Y-%m-%d")
                
                habits_table.add_row(
                    habit["name"],
                    habit["frequency"],
                    status,
                    created
                )
            
            console.print(habits_table)
            
            # Show active/total summary
            active_count = sum(1 for h in habits if h["active"])
            total_count = len(habits)
            console.print(f"\n📊 [dim]{active_count} active, {total_count} total[/dim]")
        else:
            console.print(f"\n[dim]No habits assigned to this category yet.[/dim]")
            console.print(f"\n💡 [dim]Assign a habit:[/dim] [cyan]habits categories assign \"Habit Name\" \"{name}\"[/cyan]")
        
    except Exception as e:
        print_error(f"Failed to show category details: {str(e)}")
        raise typer.Exit(1)


# Export functions for integration
__all__ = ["app"]