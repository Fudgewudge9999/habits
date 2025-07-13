"""CLI commands for template management (list, create, apply, delete)."""

import typer
from typing import Optional, List
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.panel import Panel

from habits_tracker.core.services.template_service import (
    TemplateService, 
    TemplateError, 
    TemplateNotFoundError, 
    TemplateValidationError
)
from habits_tracker.utils.display import (
    print_success, 
    print_error, 
    print_warning, 
    print_info,
    console
)

# Create template app
app = typer.Typer(
    name="template",
    help="Template management commands",
    no_args_is_help=True,
    rich_markup_mode="rich"
)


@app.command("list")
def list_templates(
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Filter by template category"
    ),
    predefined: bool = typer.Option(
        True,
        "--predefined/--no-predefined",
        help="Include predefined templates"
    ),
    user: bool = typer.Option(
        True,
        "--user/--no-user",
        help="Include user-created templates"
    )
) -> None:
    """List available habit templates.
    
    Shows all available templates with their categories and descriptions.
    Can filter by category and template type.
    
    Examples:
        habits template list
        habits template list --category health
        habits template list --no-predefined
    """
    try:
        templates = TemplateService.list_templates(
            category=category,
            include_predefined=predefined,
            include_user=user
        )
        
        if not templates:
            if category:
                print_info(f"No templates found in category '{category}'")
            else:
                print_info("No templates found")
            return
        
        # Create templates table
        table = Table(title="Available Templates", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Type", style="blue")
        table.add_column("Description", style="green")
        
        for template in templates:
            template_type = "Predefined" if template.is_predefined else "User"
            description = template.description or ""
            # Truncate long descriptions
            if len(description) > 50:
                description = description[:47] + "..."
            
            table.add_row(
                template.name,
                template.category or "",
                template_type,
                description
            )
        
        console.print("\n")
        console.print(table)
        console.print(f"\n[bold]Total templates:[/bold] {len(templates)}")
        
        if not predefined or not user:
            filter_info = []
            if not predefined:
                filter_info.append("predefined templates excluded")
            if not user:
                filter_info.append("user templates excluded")
            console.print(f"[dim]({', '.join(filter_info)})[/dim]")
        
    except TemplateError as e:
        print_error(f"Failed to list templates: {str(e)}")
        raise typer.Exit(1)


@app.command("show")
def show_template(
    name: str = typer.Argument(..., help="Template name to show")
) -> None:
    """Show detailed template information.
    
    Displays template details including all habits it would create.
    
    Examples:
        habits template show "Daily Exercise"
        habits template show "Deep Work"
    """
    try:
        preview = TemplateService.get_template_preview(name)
        
        # Show template header
        console.print(f"\n[bold cyan]Template: {preview['name']}[/bold cyan]")
        
        if preview['description']:
            console.print(f"[green]{preview['description']}[/green]")
        
        # Template info
        info_table = Table(show_header=False, box=None, padding=(0, 1))
        info_table.add_column("Property", style="bold")
        info_table.add_column("Value")
        
        info_table.add_row("Category:", preview['category'] or "None")
        info_table.add_row("Type:", "Predefined" if preview['is_predefined'] else "User")
        info_table.add_row("Habits:", str(preview['habit_count']))
        info_table.add_row("Created:", preview['created_at'][:19].replace("T", " "))
        
        console.print(info_table)
        
        # Show habits
        if preview['habits']:
            console.print(f"\n[bold]Habits in this template:[/bold]")
            
            habits_table = Table(show_header=True, header_style="bold")
            habits_table.add_column("Name", style="cyan")
            habits_table.add_column("Frequency", style="yellow")
            habits_table.add_column("Description", style="green")
            
            for habit in preview['habits']:
                description = habit.get('description', '') or ''
                if len(description) > 60:
                    description = description[:57] + "..."
                
                habits_table.add_row(
                    habit['name'],
                    habit.get('frequency', 'daily'),
                    description
                )
            
            console.print(habits_table)
        
    except TemplateNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except TemplateError as e:
        print_error(f"Failed to show template: {str(e)}")
        raise typer.Exit(1)


@app.command("create")
def create_template(
    name: str = typer.Argument(..., help="Template name"),
    description: Optional[str] = typer.Option(
        None,
        "--description",
        "-d",
        help="Template description"
    ),
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Template category"
    ),
    from_habits: Optional[List[str]] = typer.Option(
        None,
        "--from-habits",
        "-h",
        help="Create template from existing habits (space-separated)"
    )
) -> None:
    """Create a new habit template.
    
    Can create an empty template or from existing habits.
    
    Examples:
        habits template create "My Routine" --description "Personal routine"
        habits template create "Workout Set" --from-habits "Exercise" "Stretch"
        habits template create "Health Pack" --category health --from-habits "Water" "Vitamins"
    """
    try:
        if from_habits:
            # Create template from existing habits
            template = TemplateService.create_template_from_habits(
                template_name=name,
                habit_names=from_habits,
                description=description,
                category=category
            )
            
            print_success(f"Template '{name}' created from {len(from_habits)} habits")
            print_info(f"Template ID: {template.id}")
            
        else:
            # Create empty template (user would need to add habits manually)
            template = TemplateService.create_template(
                name=name,
                description=description,
                category=category,
                habits=[]
            )
            
            print_success(f"Empty template '{name}' created")
            print_info(f"Template ID: {template.id}")
            print_info("Use 'habits template edit' to add habits to this template")
        
    except TemplateValidationError as e:
        print_error(f"Template validation failed: {str(e)}")
        raise typer.Exit(1)
    except TemplateError as e:
        print_error(f"Failed to create template: {str(e)}")
        raise typer.Exit(1)


@app.command("apply")
def apply_template(
    name: str = typer.Argument(..., help="Template name to apply"),
    category: Optional[str] = typer.Option(
        None,
        "--category",
        "-c",
        help="Category to assign to created habits"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Create habits even if they already exist (will rename duplicates)"
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        "-p",
        help="Show what would be created without creating"
    )
) -> None:
    """Apply template to create habits.
    
    Creates all habits defined in the template. By default skips existing habits.
    
    Examples:
        habits template apply "Daily Exercise"
        habits template apply "Deep Work" --category productivity
        habits template apply "Health Pack" --preview
    """
    try:
        if preview:
            # Show preview
            template_preview = TemplateService.get_template_preview(name)
            
            console.print(f"\n[bold cyan]Preview: Applying template '{name}'[/bold cyan]")
            if template_preview['description']:
                console.print(f"[green]{template_preview['description']}[/green]")
            
            console.print(f"\n[bold]Would create {template_preview['habit_count']} habits:[/bold]")
            
            for i, habit in enumerate(template_preview['habits'], 1):
                console.print(f"  {i}. [cyan]{habit['name']}[/cyan]")
                if habit.get('description'):
                    console.print(f"     {habit['description']}")
                if habit.get('frequency', 'daily') != 'daily':
                    console.print(f"     Frequency: {habit['frequency']}")
            
            if category:
                console.print(f"\n[yellow]All habits would be assigned to category: {category}[/yellow]")
            
            return
        
        # Apply template
        console.print(f"[bold blue]Applying template: {name}[/bold blue]")
        
        result = TemplateService.apply_template(
            template_name=name,
            category_name=category,
            skip_existing=not force
        )
        
        _show_template_application_results(result)
        
    except TemplateNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except TemplateError as e:
        print_error(f"Failed to apply template: {str(e)}")
        raise typer.Exit(1)


@app.command("delete")
def delete_template(
    name: str = typer.Argument(..., help="Template name to delete"),
    force: bool = typer.Option(
        False,
        "--force",
        help="Delete without confirmation"
    )
) -> None:
    """Delete a user-created template.
    
    Cannot delete predefined templates. Requires confirmation unless --force is used.
    
    Examples:
        habits template delete "My Template"
        habits template delete "Old Routine" --force
    """
    try:
        # Get template info first
        template = TemplateService.get_template(name)
        
        if template.is_predefined:
            print_error("Cannot delete predefined templates")
            raise typer.Exit(1)
        
        # Confirm deletion
        if not force:
            console.print(f"[bold yellow]⚠️  This will permanently delete template '{name}'[/bold yellow]")
            if not Confirm.ask("Are you sure?"):
                print_info("Deletion cancelled")
                return
        
        # Delete template
        TemplateService.delete_template(name)
        print_success(f"Template '{name}' deleted successfully")
        
    except TemplateNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except TemplateError as e:
        print_error(f"Failed to delete template: {str(e)}")
        raise typer.Exit(1)


@app.command("init")
def initialize_templates() -> None:
    """Initialize predefined template collections.
    
    Creates all predefined templates in the database. Safe to run multiple times.
    
    Examples:
        habits template init
    """
    try:
        console.print("[bold blue]Initializing predefined templates...[/bold blue]")
        
        result = TemplateService.initialize_predefined_templates()
        
        # Show results
        if result["created"]:
            print_success(f"Created {len(result['created'])} predefined templates:")
            for template_name in result["created"]:
                console.print(f"  • [green]{template_name}[/green]")
        
        if result["skipped"]:
            print_info(f"Skipped {len(result['skipped'])} existing templates:")
            for template_name in result["skipped"][:5]:  # Show first 5
                console.print(f"  • [yellow]{template_name}[/yellow]")
            if len(result["skipped"]) > 5:
                console.print(f"  • [yellow]... and {len(result['skipped']) - 5} more[/yellow]")
        
        if result["errors"]:
            print_warning(f"{len(result['errors'])} errors occurred:")
            for error in result["errors"][:3]:  # Show first 3 errors
                console.print(f"  • [red]{error}[/red]")
            if len(result["errors"]) > 3:
                console.print(f"  • [red]... and {len(result['errors']) - 3} more errors[/red]")
        
        # Summary
        total_processed = len(result["created"]) + len(result["skipped"])
        console.print(f"\n[bold]Summary:[/bold] {total_processed} templates processed")
        
        if result["created"] and not result["errors"]:
            print_success("Predefined templates initialized successfully!")
        
    except TemplateError as e:
        print_error(f"Failed to initialize templates: {str(e)}")
        raise typer.Exit(1)


def _show_template_application_results(result: dict) -> None:
    """Show template application results."""
    # Show created habits
    if result["created"]:
        print_success(f"Created {len(result['created'])} habits:")
        for habit_name in result["created"]:
            console.print(f"  • [green]{habit_name}[/green]")
    
    # Show skipped habits
    if result["skipped"]:
        print_info(f"Skipped {len(result['skipped'])} existing habits:")
        for habit_name in result["skipped"][:5]:  # Show first 5
            console.print(f"  • [yellow]{habit_name}[/yellow]")
        if len(result["skipped"]) > 5:
            console.print(f"  • [yellow]... and {len(result['skipped']) - 5} more[/yellow]")
    
    # Show errors
    if result["errors"]:
        print_warning(f"{len(result['errors'])} errors occurred:")
        for error in result["errors"][:3]:  # Show first 3 errors
            console.print(f"  • [red]{error}[/red]")
        if len(result["errors"]) > 3:
            console.print(f"  • [red]... and {len(result['errors']) - 3} more errors[/red]")
    
    # Summary
    total_habits = len(result["created"]) + len(result["skipped"])
    console.print(f"\n[bold]Summary:[/bold] {total_habits} habits processed from template '{result['template_name']}'")
    
    if result["created"] and not result["errors"]:
        print_success("Template applied successfully!")
        print_info("Use 'habits list' to see your new habits")
    elif not result["created"] and not result["errors"]:
        print_info("All habits from template already exist")
    elif result["errors"]:
        print_warning("Template application completed with some errors")