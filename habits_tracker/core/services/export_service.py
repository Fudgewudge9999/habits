"""Service layer for data export operations."""

import json
import csv
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Union
from io import StringIO
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models import Habit, TrackingEntry, Category, HabitHistory
from ..database import get_session
from ...utils.date_utils import parse_date_string


class ExportError(Exception):
    """Raised when export operation fails."""
    pass


class ExportService:
    """Service for exporting habit data in multiple formats."""
    
    SUPPORTED_FORMATS = ["json", "csv", "markdown"]
    
    @classmethod
    def export_data(
        cls,
        format_type: str,
        output_path: Optional[str] = None,
        habit_names: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_categories: bool = True,
        include_history: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """Export habit data in specified format.
        
        Args:
            format_type: Export format (json, csv, markdown)
            output_path: Optional file path to save export
            habit_names: Optional list of specific habits to export
            start_date: Optional start date for tracking data
            end_date: Optional end date for tracking data
            include_categories: Whether to include category information
            include_history: Whether to include modification history
            
        Returns:
            Exported data as string or dict
            
        Raises:
            ExportError: If export fails
        """
        if format_type not in cls.SUPPORTED_FORMATS:
            raise ExportError(f"Unsupported format: {format_type}. Supported formats: {cls.SUPPORTED_FORMATS}")
        
        try:
            with get_session() as session:
                # Collect data for export
                export_data = cls._collect_export_data(
                    session, habit_names, start_date, end_date, include_categories, include_history
                )
                
                # Format data based on requested format
                if format_type == "json":
                    result = cls._export_json(export_data)
                elif format_type == "csv":
                    result = cls._export_csv(export_data)
                elif format_type == "markdown":
                    result = cls._export_markdown(export_data)
                else:
                    raise ExportError(f"Format handler not implemented: {format_type}")
                
                # Save to file if output path provided
                if output_path:
                    cls._save_to_file(result, output_path)
                
                return result
                
        except Exception as e:
            raise ExportError(f"Export failed: {str(e)}")
    
    @classmethod
    def _collect_export_data(
        cls,
        session: Session,
        habit_names: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_categories: bool = True,
        include_history: bool = False
    ) -> Dict[str, Any]:
        """Collect data from database for export."""
        
        # Build habits query
        habits_query = session.query(Habit)
        if habit_names:
            habits_query = habits_query.filter(Habit.name.in_(habit_names))
        
        habits = habits_query.all()
        habit_ids = [habit.id for habit in habits]
        
        # Collect tracking entries
        entries_query = session.query(TrackingEntry).filter(TrackingEntry.habit_id.in_(habit_ids))
        if start_date:
            entries_query = entries_query.filter(TrackingEntry.date >= start_date)
        if end_date:
            entries_query = entries_query.filter(TrackingEntry.date <= end_date)
        
        tracking_entries = entries_query.all()
        
        # Collect categories if requested
        categories = []
        if include_categories:
            categories = session.query(Category).all()
        
        # Collect history if requested
        history_entries = []
        if include_history:
            history_entries = session.query(HabitHistory).filter(
                HabitHistory.habit_id.in_(habit_ids)
            ).all()
        
        # Build export data structure
        export_data = {
            "export_info": {
                "exported_at": datetime.utcnow().isoformat(),
                "format_version": "1.0",
                "total_habits": len(habits),
                "total_entries": len(tracking_entries),
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            },
            "habits": [cls._serialize_habit(habit, include_categories) for habit in habits],
            "tracking_entries": [cls._serialize_tracking_entry(entry) for entry in tracking_entries],
            "categories": [cls._serialize_category(category) for category in categories] if include_categories else [],
            "history": [cls._serialize_history_entry(entry) for entry in history_entries] if include_history else []
        }
        
        return export_data
    
    @classmethod
    def _serialize_habit(cls, habit: Habit, include_categories: bool = True) -> Dict[str, Any]:
        """Serialize habit to dictionary."""
        data = {
            "id": habit.id,
            "name": habit.name,
            "description": habit.description,
            "frequency": habit.frequency,
            "frequency_details": habit.frequency_details,
            "created_at": habit.created_at.isoformat(),
            "archived_at": habit.archived_at.isoformat() if habit.archived_at else None,
            "active": habit.active
        }
        
        if include_categories:
            data["categories"] = [category.name for category in habit.categories]
        
        return data
    
    @classmethod
    def _serialize_tracking_entry(cls, entry: TrackingEntry) -> Dict[str, Any]:
        """Serialize tracking entry to dictionary."""
        return {
            "habit_id": entry.habit_id,
            "date": entry.date.isoformat(),
            "completed": entry.completed,
            "notes": entry.notes,
            "tracked_at": entry.tracked_at.isoformat()
        }
    
    @classmethod
    def _serialize_category(cls, category: Category) -> Dict[str, Any]:
        """Serialize category to dictionary."""
        return {
            "id": category.id,
            "name": category.name,
            "color": category.color,
            "description": category.description,
            "created_at": category.created_at.isoformat()
        }
    
    @classmethod
    def _serialize_history_entry(cls, entry: HabitHistory) -> Dict[str, Any]:
        """Serialize history entry to dictionary."""
        return {
            "habit_id": entry.habit_id,
            "field_name": entry.field_name,
            "old_value": entry.old_value,
            "new_value": entry.new_value,
            "change_type": entry.change_type,
            "changed_at": entry.changed_at.isoformat()
        }
    
    @classmethod
    def _export_json(cls, data: Dict[str, Any]) -> str:
        """Export data as JSON format."""
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    @classmethod
    def _export_csv(cls, data: Dict[str, Any]) -> str:
        """Export data as CSV format with multiple sheets."""
        output = StringIO()
        
        # Write habits data
        output.write("# HABITS\n")
        if data["habits"]:
            habits_fieldnames = ["id", "name", "description", "frequency", "frequency_details", 
                               "created_at", "archived_at", "active", "categories"]
            habits_writer = csv.DictWriter(output, fieldnames=habits_fieldnames)
            habits_writer.writeheader()
            
            for habit in data["habits"]:
                # Convert categories list to comma-separated string
                habit_copy = habit.copy()
                if "categories" in habit_copy:
                    habit_copy["categories"] = ", ".join(habit_copy["categories"])
                habits_writer.writerow(habit_copy)
        
        output.write("\n# TRACKING_ENTRIES\n")
        if data["tracking_entries"]:
            entries_fieldnames = ["habit_id", "date", "completed", "notes", "tracked_at"]
            entries_writer = csv.DictWriter(output, fieldnames=entries_fieldnames)
            entries_writer.writeheader()
            entries_writer.writerows(data["tracking_entries"])
        
        if data["categories"]:
            output.write("\n# CATEGORIES\n")
            categories_fieldnames = ["id", "name", "color", "description", "created_at"]
            categories_writer = csv.DictWriter(output, fieldnames=categories_fieldnames)
            categories_writer.writeheader()
            categories_writer.writerows(data["categories"])
        
        if data["history"]:
            output.write("\n# HISTORY\n")
            history_fieldnames = ["habit_id", "field_name", "old_value", "new_value", "change_type", "changed_at"]
            history_writer = csv.DictWriter(output, fieldnames=history_fieldnames)
            history_writer.writeheader()
            history_writer.writerows(data["history"])
        
        return output.getvalue()
    
    @classmethod
    def _export_markdown(cls, data: Dict[str, Any]) -> str:
        """Export data as Markdown format."""
        lines = []
        
        # Header
        lines.append("# Habits Tracker Export")
        lines.append(f"**Exported:** {data['export_info']['exported_at']}")
        lines.append(f"**Total Habits:** {data['export_info']['total_habits']}")
        lines.append(f"**Total Entries:** {data['export_info']['total_entries']}")
        
        if data['export_info']['date_range']['start']:
            lines.append(f"**Date Range:** {data['export_info']['date_range']['start']} to {data['export_info']['date_range']['end']}")
        
        lines.append("")
        
        # Habits section
        if data["habits"]:
            lines.append("## Habits")
            lines.append("")
            for habit in data["habits"]:
                lines.append(f"### {habit['name']}")
                lines.append(f"- **Description:** {habit['description'] or 'None'}")
                lines.append(f"- **Frequency:** {habit['frequency']}")
                lines.append(f"- **Created:** {habit['created_at']}")
                lines.append(f"- **Status:** {'Active' if habit['active'] else 'Archived'}")
                if habit.get('categories'):
                    lines.append(f"- **Categories:** {', '.join(habit['categories'])}")
                lines.append("")
        
        # Categories section
        if data["categories"]:
            lines.append("## Categories")
            lines.append("")
            for category in data["categories"]:
                lines.append(f"- **{category['name']}**")
                if category['description']:
                    lines.append(f"  - {category['description']}")
                if category['color']:
                    lines.append(f"  - Color: {category['color']}")
                lines.append("")
        
        # Summary statistics
        if data["tracking_entries"]:
            lines.append("## Tracking Summary")
            lines.append("")
            
            # Group entries by habit
            habit_stats = {}
            for entry in data["tracking_entries"]:
                habit_id = entry["habit_id"]
                if habit_id not in habit_stats:
                    habit_stats[habit_id] = {"total": 0, "completed": 0}
                habit_stats[habit_id]["total"] += 1
                if entry["completed"]:
                    habit_stats[habit_id]["completed"] += 1
            
            # Find habit names
            habit_names = {habit["id"]: habit["name"] for habit in data["habits"]}
            
            for habit_id, stats in habit_stats.items():
                habit_name = habit_names.get(habit_id, f"Habit {habit_id}")
                completion_rate = (stats["completed"] / stats["total"]) * 100
                lines.append(f"- **{habit_name}:** {stats['completed']}/{stats['total']} ({completion_rate:.1f}%)")
            
            lines.append("")
        
        return "\n".join(lines)
    
    @classmethod
    def _save_to_file(cls, content: str, file_path: str) -> None:
        """Save content to file."""
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
                
        except IOError as e:
            raise ExportError(f"Failed to save file: {str(e)}")
    
    @classmethod
    def get_export_preview(
        cls,
        habit_names: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get preview of what would be exported.
        
        Args:
            habit_names: Optional list of specific habits
            start_date: Optional start date filter
            end_date: Optional end date filter
            
        Returns:
            Preview statistics
        """
        try:
            with get_session() as session:
                # Count habits
                habits_query = session.query(Habit)
                if habit_names:
                    habits_query = habits_query.filter(Habit.name.in_(habit_names))
                
                habit_count = habits_query.count()
                habits = habits_query.all()
                habit_ids = [habit.id for habit in habits]
                
                # Count tracking entries
                entries_query = session.query(TrackingEntry).filter(TrackingEntry.habit_id.in_(habit_ids))
                if start_date:
                    entries_query = entries_query.filter(TrackingEntry.date >= start_date)
                if end_date:
                    entries_query = entries_query.filter(TrackingEntry.date <= end_date)
                
                entry_count = entries_query.count()
                
                # Get date range
                date_range = None
                if entry_count > 0:
                    earliest = entries_query.order_by(TrackingEntry.date).first()
                    latest = entries_query.order_by(TrackingEntry.date.desc()).first()
                    if earliest and latest:
                        date_range = {
                            "earliest": earliest.date,
                            "latest": latest.date
                        }
                
                return {
                    "habit_count": habit_count,
                    "entry_count": entry_count,
                    "habit_names": [habit.name for habit in habits],
                    "date_range": date_range
                }
                
        except Exception as e:
            raise ExportError(f"Preview generation failed: {str(e)}")