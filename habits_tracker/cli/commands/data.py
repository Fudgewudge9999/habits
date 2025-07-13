"""CLI commands for data management (export, import, backup, restore)."""

import typer
from datetime import date
from typing import Optional, List, Dict, Any
from pathlib import Path
from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.panel import Panel

from habits_tracker.core.services.export_service import ExportService, ExportError
from habits_tracker.core.services.import_service import ImportService, ImportError, ImportValidationError
from habits_tracker.core.services.backup_service import BackupService, BackupError, RestoreError
from habits_tracker.utils.display import (
    print_success, 
    print_error, 
    print_warning, 
    print_info,
    console
)
from habits_tracker.utils.date_utils import parse_date_string


def export_data(
    format_type: str = typer.Option(
        "json",
        "--format",
        "-f", 
        help="Export format (json, csv, markdown)",
        show_default=True
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (if not specified, prints to console)"
    ),
    habits: Optional[List[str]] = typer.Option(
        None,
        "--habits",
        "-h",
        help="Specific habits to export (space-separated)"
    ),
    start_date: Optional[str] = typer.Option(
        None,
        "--start-date",
        "-s",
        help="Start date for tracking data (YYYY-MM-DD, 'YYYY-MM-DD', or relative like '-30d')"
    ),
    end_date: Optional[str] = typer.Option(
        None,
        "--end-date", 
        "-e",
        help="End date for tracking data (YYYY-MM-DD, 'today', or relative like '-1d')"
    ),
    include_categories: bool = typer.Option(
        True,
        "--categories/--no-categories",
        help="Include category information in export"
    ),
    include_history: bool = typer.Option(
        False,
        "--history/--no-history", 
        help="Include modification history in export"
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        "-p",
        help="Show preview of what would be exported without exporting"
    )
) -> None:
    """Export habit data in various formats.
    
    Supports JSON, CSV, and Markdown formats with selective export capabilities.
    Can export specific habits, date ranges, and include/exclude categories and history.
    
    Examples:
        habits export --format json --output backup.json
        habits export --format csv --habits "Exercise" "Reading" --start-date "2025-01-01"
        habits export --format markdown --preview
    """
    try:
        # Validate format
        if format_type not in ExportService.SUPPORTED_FORMATS:
            print_error(f"Unsupported format: {format_type}")
            print_info(f"Supported formats: {', '.join(ExportService.SUPPORTED_FORMATS)}")
            raise typer.Exit(1)
        
        # Parse dates if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            parsed_start_date = parse_date_string(start_date)
            if parsed_start_date is None:
                print_error(f"Invalid start date format: {start_date}")
                print_info("Use formats like: 2025-01-01, today, yesterday, -7d")
                raise typer.Exit(1)
        
        if end_date:
            parsed_end_date = parse_date_string(end_date)
            if parsed_end_date is None:
                print_error(f"Invalid end date format: {end_date}")
                print_info("Use formats like: 2025-01-01, today, yesterday, -1d")
                raise typer.Exit(1)
        
        # Validate date range
        if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
            print_error("Start date cannot be after end date")
            raise typer.Exit(1)
        
        # Show preview if requested
        if preview:
            preview_data = ExportService.get_export_preview(
                habit_names=habits,
                start_date=parsed_start_date,
                end_date=parsed_end_date
            )
            
            _show_export_preview(preview_data, format_type, parsed_start_date, parsed_end_date)
            return
        
        # Perform export
        console.print(f"[bold blue]Exporting data in {format_type.upper()} format...[/bold blue]")
        
        result = ExportService.export_data(
            format_type=format_type,
            output_path=output,
            habit_names=habits,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            include_categories=include_categories,
            include_history=include_history
        )
        
        if output:
            print_success(f"Data exported successfully to: {output}")
            
            # Show file info
            file_path = Path(output)
            if file_path.exists():
                file_size = file_path.stat().st_size
                print_info(f"File size: {file_size:,} bytes")
        else:
            # Print to console
            console.print("\n[bold green]Export Result:[/bold green]")
            console.print(result)
        
    except ExportError as e:
        print_error(f"Export failed: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error during export: {str(e)}")
        raise typer.Exit(1)


def _show_export_preview(
    preview_data: dict, 
    format_type: str, 
    start_date: Optional[date], 
    end_date: Optional[date]
) -> None:
    """Show export preview information."""
    
    # Create preview table
    table = Table(title="Export Preview", show_header=True, header_style="bold magenta")
    table.add_column("Item", style="cyan")
    table.add_column("Count", justify="right", style="green")
    
    table.add_row("Format", format_type.upper())
    table.add_row("Habits", str(preview_data["habit_count"]))
    table.add_row("Tracking Entries", f"{preview_data['entry_count']:,}")
    
    if preview_data["date_range"]:
        date_range_str = f"{preview_data['date_range']['earliest']} to {preview_data['date_range']['latest']}"
        table.add_row("Data Date Range", date_range_str)
    
    if start_date or end_date:
        filter_range = f"{start_date or 'earliest'} to {end_date or 'latest'}"
        table.add_row("Filter Date Range", filter_range)
    
    console.print(table)
    
    # Show habit names if not too many
    if preview_data["habit_count"] > 0 and preview_data["habit_count"] <= 10:
        console.print(f"\n[bold cyan]Habits to export:[/bold cyan]")
        for habit_name in preview_data["habit_names"]:
            console.print(f"  • {habit_name}")
    elif preview_data["habit_count"] > 10:
        console.print(f"\n[bold cyan]Habits to export:[/bold cyan] {preview_data['habit_count']} habits (too many to list)")
    
    if preview_data["entry_count"] == 0:
        print_warning("No tracking entries found matching the specified criteria")


def import_data(
    file_path: str = typer.Argument(..., help="Path to file to import"),
    format_type: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Import format (json, csv) - auto-detected if not specified"
    ),
    mode: str = typer.Option(
        "merge",
        "--mode",
        "-m",
        help="Import mode: merge (add new), replace (overwrite), or append (add all)",
        show_default=True
    ),
    preview: bool = typer.Option(
        False,
        "--preview",
        "-p",
        help="Show preview of what would be imported without importing"
    ),
    backup: bool = typer.Option(
        True,
        "--backup/--no-backup",
        help="Create backup before importing"
    )
) -> None:
    """Import habit data from file.
    
    Supports importing from JSON and CSV files with intelligent conflict resolution.
    Always creates a backup before importing unless disabled.
    
    Import modes:
        merge: Add new habits and entries, skip existing ones
        replace: Replace existing habits with imported data
        append: Add all data, potentially creating duplicates
    
    Examples:
        habits import backup.json
        habits import data.csv --mode replace --preview
        habits import export.json --no-backup
    """
    try:
        # Validate file exists
        if not Path(file_path).exists():
            print_error(f"File not found: {file_path}")
            raise typer.Exit(1)
        
        console.print(f"[bold blue]Importing data from: {file_path}[/bold blue]")
        
        # Perform import
        result = ImportService.import_data(
            file_path=file_path,
            format_type=format_type,
            mode=mode,
            create_backup=backup,
            preview=preview
        )
        
        if preview:
            _show_import_preview(result)
        else:
            _show_import_results(result)
            
    except ImportValidationError as e:
        print_error(f"Import validation failed: {str(e)}")
        raise typer.Exit(1)
    except ImportError as e:
        print_error(f"Import failed: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error during import: {str(e)}")
        raise typer.Exit(1)


def _show_import_preview(result: Dict[str, Any]) -> None:
    """Show import preview information."""
    validation = result["validation"]
    import_data = result["import_data"]
    
    # Show validation status
    if validation["valid"]:
        console.print("\n[bold green]✅ Import data validation passed[/bold green]")
    else:
        console.print("\n[bold red]❌ Import data validation failed[/bold red]")
        
        for error in validation["errors"]:
            console.print(f"  [red]• {error}[/red]")
    
    if validation["warnings"]:
        console.print("\n[bold yellow]⚠️  Validation warnings:[/bold yellow]")
        for warning in validation["warnings"]:
            console.print(f"  [yellow]• {warning}[/yellow]")
    
    # Show statistics
    stats = validation["statistics"]
    table = Table(title="Import Preview", show_header=True, header_style="bold magenta")
    table.add_column("Data Type", style="cyan")
    table.add_column("Count", justify="right", style="green")
    
    table.add_row("Habits", str(stats["habits"]))
    table.add_row("Tracking Entries", str(stats["tracking_entries"]))
    table.add_row("Categories", str(stats["categories"]))
    table.add_row("History Entries", str(stats["history"]))
    
    console.print("\n")
    console.print(table)
    
    # Show import mode
    console.print(f"\n[bold cyan]Import Mode:[/bold cyan] {result['mode']}")
    
    if not validation["valid"]:
        print_error("Cannot proceed with import due to validation errors")
        return
    
    # Show what would happen
    mode_descriptions = {
        "merge": "Add new items, skip existing ones",
        "replace": "Update existing items with new data",
        "append": "Add all items, potentially creating duplicates"
    }
    
    console.print(f"[bold blue]Action:[/bold blue] {mode_descriptions.get(result['mode'], 'Unknown mode')}")


def _show_import_results(result: Dict[str, Any]) -> None:
    """Show import results."""
    # Show backup info
    if result.get("backup_path"):
        print_info(f"Backup created: {result['backup_path']}")
    
    # Show results table
    table = Table(title="Import Results", show_header=True, header_style="bold magenta")
    table.add_column("Data Type", style="cyan")
    table.add_column("Created", justify="right", style="green")
    table.add_column("Updated", justify="right", style="yellow")
    table.add_column("Skipped", justify="right", style="blue")
    
    for data_type in ["habits", "tracking_entries", "categories"]:
        table.add_row(
            data_type.replace("_", " ").title(),
            str(result["created"][data_type]),
            str(result["updated"][data_type]),
            str(result["skipped"][data_type])
        )
    
    console.print("\n")
    console.print(table)
    
    # Show errors if any
    if result["errors"]:
        console.print(f"\n[bold red]⚠️  {len(result['errors'])} errors occurred during import:[/bold red]")
        for error in result["errors"][:5]:  # Show first 5 errors
            console.print(f"  [red]• {error}[/red]")
        
        if len(result["errors"]) > 5:
            console.print(f"  [red]... and {len(result['errors']) - 5} more errors[/red]")
    else:
        print_success("Import completed successfully!")
    
    # Show totals
    total_created = sum(result["created"].values())
    total_updated = sum(result["updated"].values())
    total_skipped = sum(result["skipped"].values())
    
    console.print(f"\n[bold]Summary:[/bold] {total_created} created, {total_updated} updated, {total_skipped} skipped")


def backup_database(
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Backup file path (default: ~/.habits/backup_YYYYMMDD_HHMMSS.db)"
    ),
    compress: bool = typer.Option(
        False,
        "--compress",
        "-c",
        help="Compress the backup file"
    ),
    verify: bool = typer.Option(
        True,
        "--verify/--no-verify",
        help="Verify backup integrity after creation"
    )
) -> None:
    """Create a complete backup of the habits database.
    
    Creates a full backup of all habit data including tracking entries,
    categories, history, and configuration.
    
    Examples:
        habits backup
        habits backup --output my_backup.db --compress
        habits backup --no-verify --compress
    """
    try:
        console.print("[bold blue]Creating database backup...[/bold blue]")
        
        backup_info = BackupService.create_backup(
            output_path=output,
            compress=compress,
            verify=verify
        )
        
        _show_backup_info(backup_info)
        
    except BackupError as e:
        print_error(f"Backup failed: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error during backup: {str(e)}")
        raise typer.Exit(1)


def restore_database(
    backup_file: str = typer.Argument(..., help="Path to backup file to restore"),
    verify: bool = typer.Option(
        True,
        "--verify/--no-verify",
        help="Verify backup integrity before restoring"
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help="Force restore without confirmation"
    ),
    backup: bool = typer.Option(
        True,
        "--backup/--no-backup",
        help="Create backup of current database before restoring"
    )
) -> None:
    """Restore database from backup file.
    
    Restores the complete database from a backup file. This will replace
    all current data with the backup data.
    
    Examples:
        habits restore backup_20250101_120000.db
        habits restore old_backup.db --no-verify --force
        habits restore backup.db --no-backup
    """
    try:
        # Confirm destructive operation
        if not force:
            console.print("[bold yellow]⚠️  WARNING: This will replace all current data![/bold yellow]")
            if not Confirm.ask("Are you sure you want to restore from backup?"):
                print_info("Restore cancelled")
                return
        
        console.print(f"[bold blue]Restoring database from: {backup_file}[/bold blue]")
        
        restore_info = BackupService.restore_backup(
            backup_path=backup_file,
            verify=verify,
            create_backup=backup
        )
        
        _show_restore_info(restore_info)
        
    except RestoreError as e:
        print_error(f"Restore failed: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error during restore: {str(e)}")
        raise typer.Exit(1)


def _show_backup_info(backup_info: Dict[str, Any]) -> None:
    """Show backup creation information."""
    print_success(f"Backup created successfully!")
    
    # Create info table
    table = Table(title="Backup Information", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Backup Path", backup_info["backup_path"])
    table.add_row("File Size", f"{backup_info['backup_size']:,} bytes")
    table.add_row("Compressed", "Yes" if backup_info["compressed"] else "No")
    table.add_row("Created At", backup_info["created_at"])
    
    if backup_info.get("database_stats"):
        stats = backup_info["database_stats"]
        if "total_habits" in stats:
            table.add_row("Habits Backed Up", str(stats["total_habits"]))
        if "total_entries" in stats:
            table.add_row("Entries Backed Up", str(stats["total_entries"]))
    
    console.print("\n")
    console.print(table)
    
    # Show verification results
    if backup_info.get("verification"):
        verification = backup_info["verification"]
        if verification["valid"]:
            print_success("Backup verification passed")
        else:
            print_warning(f"Backup verification failed: {verification.get('error', 'Unknown error')}")


def _show_restore_info(restore_info: Dict[str, Any]) -> None:
    """Show restore operation information."""
    print_success("Database restored successfully!")
    
    # Create info table
    table = Table(title="Restore Information", show_header=True, header_style="bold magenta")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Backup File", restore_info["backup_path"])
    table.add_row("Restored To", restore_info["restored_to"])
    table.add_row("Restored At", restore_info["restored_at"])
    
    if restore_info.get("pre_restore_backup"):
        table.add_row("Pre-restore Backup", restore_info["pre_restore_backup"])
    
    if restore_info.get("database_stats"):
        stats = restore_info["database_stats"]
        if "total_habits" in stats:
            table.add_row("Habits Restored", str(stats["total_habits"]))
        if "total_entries" in stats:
            table.add_row("Entries Restored", str(stats["total_entries"]))
    
    console.print("\n")
    console.print(table)
    
    # Show verification results
    if restore_info.get("verification"):
        verification = restore_info["verification"]
        if verification["valid"]:
            print_info("Backup verification passed before restore")
        else:
            print_warning(f"Backup verification: {verification.get('error', 'Unknown error')}")


def list_backups(
    backup_dir: Optional[str] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Backup directory to list (default: ~/.habits/backups)"
    )
) -> None:
    """List available backup files.
    
    Shows all backup files in the backup directory with their details.
    
    Examples:
        habits list-backups
        habits list-backups --dir /custom/backup/path
    """
    try:
        backups = BackupService.list_backups(backup_dir)
        
        if not backups:
            print_info("No backup files found")
            if backup_dir:
                print_info(f"Searched in: {backup_dir}")
            else:
                print_info("Searched in: ~/.habits/backups")
            return
        
        # Create backups table
        table = Table(title="Available Backups", show_header=True, header_style="bold magenta")
        table.add_column("Name", style="cyan")
        table.add_column("Size", justify="right", style="green")
        table.add_column("Compressed", justify="center", style="yellow")
        table.add_column("Created", style="blue")
        
        for backup in backups:
            size_str = f"{backup['size']:,} bytes"
            compressed_str = "Yes" if backup["compressed"] else "No"
            # Format timestamp for display
            created_str = backup["created_at"][:19].replace("T", " ")
            
            table.add_row(
                backup["name"],
                size_str,
                compressed_str,
                created_str
            )
        
        console.print("\n")
        console.print(table)
        console.print(f"\n[bold]Total backups found:[/bold] {len(backups)}")
        
    except Exception as e:
        print_error(f"Failed to list backups: {str(e)}")
        raise typer.Exit(1)