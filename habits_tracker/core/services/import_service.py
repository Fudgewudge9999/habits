"""Service layer for data import operations."""

import json
import csv
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path
from io import StringIO
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models import Habit, TrackingEntry, Category, HabitHistory
from ..database import get_session
from ...utils.date_utils import parse_date_string


class ImportError(Exception):
    """Raised when import operation fails."""
    pass


class ImportValidationError(Exception):
    """Raised when import data validation fails."""
    pass


class ImportService:
    """Service for importing habit data from various formats."""
    
    SUPPORTED_FORMATS = ["json", "csv"]
    SUPPORTED_MODES = ["merge", "replace", "append"]
    
    @classmethod
    def import_data(
        cls,
        file_path: str,
        format_type: Optional[str] = None,
        mode: str = "merge",
        create_backup: bool = True,
        preview: bool = False
    ) -> Dict[str, Any]:
        """Import habit data from file.
        
        Args:
            file_path: Path to file to import
            format_type: Import format (json, csv) - auto-detected if None
            mode: Import mode (merge, replace, append)
            create_backup: Whether to create backup before importing
            preview: Show preview without importing
            
        Returns:
            Import results dictionary
            
        Raises:
            ImportError: If import fails
            ImportValidationError: If data validation fails
        """
        if mode not in cls.SUPPORTED_MODES:
            raise ImportError(f"Unsupported import mode: {mode}. Supported modes: {cls.SUPPORTED_MODES}")
        
        # Validate file exists
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise ImportError(f"File not found: {file_path}")
        
        # Auto-detect format if not specified
        if format_type is None:
            format_type = cls._detect_format(file_path_obj)
        
        if format_type not in cls.SUPPORTED_FORMATS:
            raise ImportError(f"Unsupported format: {format_type}. Supported formats: {cls.SUPPORTED_FORMATS}")
        
        try:
            # Parse the file
            if format_type == "json":
                import_data = cls._parse_json_file(file_path)
            elif format_type == "csv":
                import_data = cls._parse_csv_file(file_path)
            else:
                raise ImportError(f"Format handler not implemented: {format_type}")
            
            # Validate the imported data
            validation_result = cls._validate_import_data(import_data)
            
            if preview:
                return {
                    "preview": True,
                    "validation": validation_result,
                    "import_data": import_data,
                    "mode": mode
                }
            
            # Create backup if requested
            backup_path = None
            if create_backup:
                from ..database import db_manager
                backup_path = db_manager.create_backup("pre_import")
            
            # Perform the import
            result = cls._perform_import(import_data, mode)
            result["backup_path"] = backup_path
            
            return result
            
        except Exception as e:
            raise ImportError(f"Import failed: {str(e)}")
    
    @classmethod
    def _detect_format(cls, file_path: Path) -> str:
        """Auto-detect file format based on extension and content."""
        extension = file_path.suffix.lower()
        
        if extension == ".json":
            return "json"
        elif extension == ".csv":
            return "csv"
        else:
            # Try to detect by content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line.startswith('{'):
                        return "json"
                    elif ',' in first_line:
                        return "csv"
            except Exception:
                pass
        
        raise ImportError(f"Cannot detect format for file: {file_path}")
    
    @classmethod
    def _parse_json_file(cls, file_path: str) -> Dict[str, Any]:
        """Parse JSON file and return structured data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate basic structure
            if not isinstance(data, dict):
                raise ImportValidationError("JSON file must contain a dictionary at root level")
            
            # Ensure required sections exist with defaults
            if "habits" not in data:
                data["habits"] = []
            if "tracking_entries" not in data:
                data["tracking_entries"] = []
            if "categories" not in data:
                data["categories"] = []
            if "history" not in data:
                data["history"] = []
            
            return data
            
        except json.JSONDecodeError as e:
            raise ImportValidationError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ImportError(f"Failed to read JSON file: {str(e)}")
    
    @classmethod
    def _parse_csv_file(cls, file_path: str) -> Dict[str, Any]:
        """Parse CSV file and return structured data."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split content by sections - handle both first section and subsequent sections
            sections = content.split('\n# ')
            if content.startswith('# '):
                # Handle the first section that starts with '# '
                first_section = content.split('\n# ', 1)[0][2:]  # Remove leading '# '
                sections = [first_section] + sections[1:]
            
            data = {
                "habits": [],
                "tracking_entries": [],
                "categories": [],
                "history": []
            }
            
            for section in sections:
                if section.startswith('HABITS'):
                    data["habits"] = cls._parse_csv_section(section, "HABITS")
                elif section.startswith('TRACKING_ENTRIES'):
                    data["tracking_entries"] = cls._parse_csv_section(section, "TRACKING_ENTRIES")
                elif section.startswith('CATEGORIES'):
                    data["categories"] = cls._parse_csv_section(section, "CATEGORIES")
                elif section.startswith('HISTORY'):
                    data["history"] = cls._parse_csv_section(section, "HISTORY")
            
            return data
            
        except Exception as e:
            raise ImportError(f"Failed to parse CSV file: {str(e)}")
    
    @classmethod
    def _parse_csv_section(cls, section_content: str, section_name: str) -> List[Dict[str, Any]]:
        """Parse a CSV section and return list of dictionaries."""
        lines = section_content.strip().split('\n')
        if len(lines) < 2:  # Need at least header and one data row
            return []
        
        # Remove section header
        if lines[0].startswith(section_name):
            lines = lines[1:]
        
        if not lines:
            return []
        
        # Parse CSV data
        csv_reader = csv.DictReader(lines)
        results = []
        
        for row in csv_reader:
            # Convert empty strings to None
            processed_row = {}
            for key, value in row.items():
                if value == '':
                    processed_row[key] = None
                elif key in ['id', 'habit_id']:
                    processed_row[key] = int(value) if value else None
                elif key in ['active', 'completed', 'is_predefined']:
                    processed_row[key] = value.lower() == 'true' if value else False
                elif key == 'categories' and value:
                    # Convert comma-separated string back to list
                    processed_row[key] = [cat.strip() for cat in value.split(',')]
                else:
                    processed_row[key] = value
            
            results.append(processed_row)
        
        return results
    
    @classmethod
    def _validate_import_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate imported data structure and content."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {
                "habits": len(data.get("habits", [])),
                "tracking_entries": len(data.get("tracking_entries", [])),
                "categories": len(data.get("categories", [])),
                "history": len(data.get("history", []))
            }
        }
        
        # Validate habits
        habit_names = set()
        for i, habit in enumerate(data.get("habits", [])):
            if not isinstance(habit, dict):
                validation_result["errors"].append(f"Habit {i}: Must be a dictionary")
                continue
            
            # Check required fields
            if "name" not in habit or not habit["name"]:
                validation_result["errors"].append(f"Habit {i}: Missing required field 'name'")
            else:
                name = habit["name"]
                if name in habit_names:
                    validation_result["errors"].append(f"Habit {i}: Duplicate name '{name}'")
                habit_names.add(name)
            
            # Check frequency
            if "frequency" in habit and habit["frequency"] not in ["daily", "weekly", "custom"]:
                validation_result["warnings"].append(f"Habit {i}: Invalid frequency '{habit['frequency']}'")
        
        # Validate tracking entries
        for i, entry in enumerate(data.get("tracking_entries", [])):
            if not isinstance(entry, dict):
                validation_result["errors"].append(f"Tracking entry {i}: Must be a dictionary")
                continue
            
            # Check required fields
            if "habit_id" not in entry:
                validation_result["errors"].append(f"Tracking entry {i}: Missing required field 'habit_id'")
            
            if "date" not in entry:
                validation_result["errors"].append(f"Tracking entry {i}: Missing required field 'date'")
            else:
                # Validate date format
                try:
                    if isinstance(entry["date"], str):
                        datetime.fromisoformat(entry["date"])
                except ValueError:
                    validation_result["errors"].append(f"Tracking entry {i}: Invalid date format '{entry['date']}'")
        
        # Validate categories
        category_names = set()
        for i, category in enumerate(data.get("categories", [])):
            if not isinstance(category, dict):
                validation_result["errors"].append(f"Category {i}: Must be a dictionary")
                continue
            
            if "name" not in category or not category["name"]:
                validation_result["errors"].append(f"Category {i}: Missing required field 'name'")
            else:
                name = category["name"]
                if name in category_names:
                    validation_result["errors"].append(f"Category {i}: Duplicate name '{name}'")
                category_names.add(name)
        
        validation_result["valid"] = len(validation_result["errors"]) == 0
        
        return validation_result
    
    @classmethod
    def _perform_import(cls, data: Dict[str, Any], mode: str) -> Dict[str, Any]:
        """Perform the actual import operation."""
        result = {
            "mode": mode,
            "created": {"habits": 0, "tracking_entries": 0, "categories": 0},
            "updated": {"habits": 0, "tracking_entries": 0, "categories": 0},
            "skipped": {"habits": 0, "tracking_entries": 0, "categories": 0},
            "errors": []
        }
        
        try:
            with get_session() as session:
                # Import categories first
                category_mapping = cls._import_categories(session, data.get("categories", []), mode, result)
                
                # Import habits
                habit_mapping = cls._import_habits(session, data.get("habits", []), mode, result, category_mapping)
                
                # Import tracking entries
                cls._import_tracking_entries(session, data.get("tracking_entries", []), mode, result, habit_mapping)
                
                # Commit the transaction
                session.commit()
                
        except Exception as e:
            result["errors"].append(f"Import transaction failed: {str(e)}")
            raise ImportError(f"Import failed: {str(e)}")
        
        return result
    
    @classmethod
    def _import_categories(
        cls, 
        session: Session, 
        categories: List[Dict[str, Any]], 
        mode: str, 
        result: Dict[str, Any]
    ) -> Dict[str, int]:
        """Import categories and return name-to-id mapping."""
        category_mapping = {}
        
        for category_data in categories:
            try:
                name = category_data["name"]
                
                # Check if category exists
                existing_category = session.query(Category).filter(Category.name == name).first()
                
                if existing_category:
                    if mode == "replace":
                        # Update existing category
                        if category_data.get("description"):
                            existing_category.description = category_data["description"]
                        if category_data.get("color"):
                            existing_category.color = category_data["color"]
                        result["updated"]["categories"] += 1
                    else:
                        # Skip existing
                        result["skipped"]["categories"] += 1
                    
                    category_mapping[name] = existing_category.id
                else:
                    # Create new category
                    new_category = Category(
                        name=name,
                        description=category_data.get("description"),
                        color=category_data.get("color")
                    )
                    session.add(new_category)
                    session.flush()  # Get the ID
                    
                    category_mapping[name] = new_category.id
                    result["created"]["categories"] += 1
                    
            except Exception as e:
                result["errors"].append(f"Failed to import category '{category_data.get('name', 'unknown')}': {str(e)}")
        
        return category_mapping
    
    @classmethod
    def _import_habits(
        cls, 
        session: Session, 
        habits: List[Dict[str, Any]], 
        mode: str, 
        result: Dict[str, Any],
        category_mapping: Dict[str, int]
    ) -> Dict[int, int]:
        """Import habits and return old-id-to-new-id mapping."""
        habit_mapping = {}
        
        for habit_data in habits:
            try:
                name = habit_data["name"]
                
                # Check if habit exists
                existing_habit = session.query(Habit).filter(Habit.name == name).first()
                
                if existing_habit:
                    if mode == "replace":
                        # Update existing habit
                        existing_habit.description = habit_data.get("description")
                        existing_habit.frequency = habit_data.get("frequency", "daily")
                        existing_habit.frequency_details = habit_data.get("frequency_details")
                        existing_habit.active = habit_data.get("active", True)
                        
                        # Update categories
                        cls._update_habit_categories(session, existing_habit, habit_data.get("categories", []), category_mapping)
                        
                        result["updated"]["habits"] += 1
                    else:
                        # Skip existing
                        result["skipped"]["habits"] += 1
                    
                    if habit_data.get("id"):
                        habit_mapping[habit_data["id"]] = existing_habit.id
                else:
                    # Create new habit
                    new_habit = Habit(
                        name=name,
                        description=habit_data.get("description"),
                        frequency=habit_data.get("frequency", "daily"),
                        frequency_details=habit_data.get("frequency_details"),
                        active=habit_data.get("active", True)
                    )
                    session.add(new_habit)
                    session.flush()  # Get the ID
                    
                    # Assign categories
                    cls._update_habit_categories(session, new_habit, habit_data.get("categories", []), category_mapping)
                    
                    if habit_data.get("id"):
                        habit_mapping[habit_data["id"]] = new_habit.id
                    
                    result["created"]["habits"] += 1
                    
            except Exception as e:
                result["errors"].append(f"Failed to import habit '{habit_data.get('name', 'unknown')}': {str(e)}")
        
        return habit_mapping
    
    @classmethod
    def _update_habit_categories(
        cls, 
        session: Session, 
        habit: Habit, 
        category_names: List[str], 
        category_mapping: Dict[str, int]
    ) -> None:
        """Update habit categories."""
        # Clear existing categories
        habit.categories.clear()
        
        # Add new categories
        for category_name in category_names:
            if category_name in category_mapping:
                category = session.query(Category).filter(Category.id == category_mapping[category_name]).first()
                if category:
                    habit.categories.append(category)
    
    @classmethod
    def _import_tracking_entries(
        cls, 
        session: Session, 
        entries: List[Dict[str, Any]], 
        mode: str, 
        result: Dict[str, Any],
        habit_mapping: Dict[int, int]
    ) -> None:
        """Import tracking entries."""
        for entry_data in entries:
            try:
                old_habit_id = entry_data["habit_id"]
                
                # Map to new habit ID
                if old_habit_id not in habit_mapping:
                    result["errors"].append(f"Tracking entry for unknown habit_id {old_habit_id}")
                    continue
                
                new_habit_id = habit_mapping[old_habit_id]
                entry_date = datetime.fromisoformat(entry_data["date"]).date()
                
                # Check if entry exists
                existing_entry = session.query(TrackingEntry).filter(
                    TrackingEntry.habit_id == new_habit_id,
                    TrackingEntry.date == entry_date
                ).first()
                
                if existing_entry:
                    if mode == "replace":
                        # Update existing entry
                        existing_entry.completed = entry_data.get("completed", True)
                        existing_entry.notes = entry_data.get("notes")
                        result["updated"]["tracking_entries"] += 1
                    else:
                        # Skip existing
                        result["skipped"]["tracking_entries"] += 1
                else:
                    # Create new entry
                    new_entry = TrackingEntry(
                        habit_id=new_habit_id,
                        date=entry_date,
                        completed=entry_data.get("completed", True),
                        notes=entry_data.get("notes")
                    )
                    session.add(new_entry)
                    result["created"]["tracking_entries"] += 1
                    
            except Exception as e:
                result["errors"].append(f"Failed to import tracking entry: {str(e)}")
    
    @classmethod
    def get_import_preview(cls, file_path: str, format_type: Optional[str] = None) -> Dict[str, Any]:
        """Get preview of what would be imported without importing.
        
        Args:
            file_path: Path to file to preview
            format_type: Import format (auto-detected if None)
            
        Returns:
            Preview information
        """
        try:
            return cls.import_data(file_path, format_type, mode="merge", preview=True)
        except Exception as e:
            raise ImportError(f"Preview generation failed: {str(e)}")