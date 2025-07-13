"""Service layer for habit editing operations with audit trail."""

from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_

from ..models import Habit, HabitHistory, Category
from ..database import get_session
from .habit_service import HabitService, HabitValidationError, HabitNotFoundError
from ...utils.performance import performance_target, profile_query
from ...utils.cache import invalidate_habit_caches


class EditValidationError(Exception):
    """Raised when edit validation fails."""
    pass


class EditConflictError(Exception):
    """Raised when edit operation conflicts with existing data."""
    pass


class EditingService:
    """Service for habit editing operations with comprehensive validation and audit trail."""
    
    @classmethod
    def _log_change(
        cls, 
        session: Session, 
        habit_id: int, 
        field_name: str, 
        old_value: Any, 
        new_value: Any,
        change_type: str = "update"
    ) -> None:
        """Log a change to the habit history table.
        
        Args:
            session: Database session
            habit_id: Habit ID
            field_name: Name of the field that changed
            old_value: Previous value
            new_value: New value
            change_type: Type of change (update, create, delete, archive, restore)
        """
        history_entry = HabitHistory(
            habit_id=habit_id,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            change_type=change_type
        )
        session.add(history_entry)
    
    @classmethod
    def _validate_name_change(cls, session: Session, habit: Habit, new_name: str) -> str:
        """Validate a habit name change.
        
        Args:
            session: Database session
            habit: Current habit object
            new_name: Proposed new name
            
        Returns:
            Validated and normalized new name
            
        Raises:
            EditValidationError: If validation fails
            EditConflictError: If name conflicts with existing habit
        """
        # Use existing validation from HabitService
        new_name = HabitService.validate_habit_name(new_name)
        
        # Check if new name is different from current
        if new_name == habit.name:
            raise EditValidationError("New name is the same as current name")
        
        # Check for conflicts with other habits
        existing = session.query(Habit).filter(
            and_(Habit.name == new_name, Habit.id != habit.id)
        ).first()
        
        if existing:
            if existing.active:
                raise EditConflictError(f"Habit '{new_name}' already exists and is active")
            else:
                # Suggest restoring the archived habit instead
                raise EditConflictError(
                    f"Habit '{new_name}' exists but is archived. "
                    f"Consider restoring it with: habits restore \"{new_name}\""
                )
        
        return new_name
    
    @classmethod
    def _validate_frequency_change(cls, habit: Habit, new_frequency: str) -> str:
        """Validate a habit frequency change.
        
        Args:
            habit: Current habit object
            new_frequency: Proposed new frequency
            
        Returns:
            Validated and normalized new frequency
            
        Raises:
            EditValidationError: If validation fails
        """
        # Use existing validation from HabitService
        new_frequency = HabitService.validate_frequency(new_frequency)
        
        # Check if new frequency is different from current
        if new_frequency == habit.frequency:
            raise EditValidationError("New frequency is the same as current frequency")
        
        return new_frequency
    
    @classmethod
    def _validate_description_change(cls, habit: Habit, new_description: Optional[str]) -> Optional[str]:
        """Validate a habit description change.
        
        Args:
            habit: Current habit object
            new_description: Proposed new description
            
        Returns:
            Validated and normalized new description
            
        Raises:
            EditValidationError: If validation fails
        """
        # Use existing validation from HabitService
        new_description = HabitService.validate_description(new_description)
        
        # Check if new description is different from current
        current_desc = habit.description or ""
        new_desc = new_description or ""
        
        if new_desc == current_desc:
            raise EditValidationError("New description is the same as current description")
        
        return new_description
    
    @classmethod
    @performance_target(100)  # 100ms target for edit operations
    @profile_query("habit_editing")
    def edit_habit(
        cls,
        habit_name: str,
        name: Optional[str] = None,
        frequency: Optional[str] = None,
        description: Optional[str] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Edit a habit with comprehensive validation and audit trail.
        
        Args:
            habit_name: Current name of the habit to edit
            name: New name for the habit (optional)
            frequency: New frequency for the habit (optional)
            description: New description for the habit (optional)
            categories: New list of category names (optional)
            
        Returns:
            Dictionary with edit results and changes made
            
        Raises:
            HabitNotFoundError: If habit doesn't exist
            EditValidationError: If validation fails
            EditConflictError: If edit conflicts with existing data
        """
        changes = {}
        
        try:
            with get_session() as session:
                # Get the habit
                habit = session.query(Habit).filter(Habit.name == habit_name).first()
                if not habit:
                    raise HabitNotFoundError(f"Habit '{habit_name}' not found")
                
                if not habit.active:
                    raise EditValidationError(f"Cannot edit archived habit '{habit_name}'. Restore it first.")
                
                # Validate and apply changes
                if name is not None:
                    new_name = cls._validate_name_change(session, habit, name)
                    old_name = habit.name
                    habit.name = new_name
                    changes["name"] = {"old": old_name, "new": new_name}
                    cls._log_change(session, habit.id, "name", old_name, new_name)
                
                if frequency is not None:
                    new_frequency = cls._validate_frequency_change(habit, frequency)
                    old_frequency = habit.frequency
                    habit.frequency = new_frequency
                    changes["frequency"] = {"old": old_frequency, "new": new_frequency}
                    cls._log_change(session, habit.id, "frequency", old_frequency, new_frequency)
                
                if description is not None:
                    new_description = cls._validate_description_change(habit, description)
                    old_description = habit.description
                    habit.description = new_description
                    changes["description"] = {"old": old_description, "new": new_description}
                    cls._log_change(session, habit.id, "description", old_description, new_description)
                
                if categories is not None:
                    # Handle category changes (will be implemented when CategoryService is ready)
                    # For now, just log that this feature is coming
                    changes["categories"] = {"message": "Category editing will be available after CategoryService implementation"}
                
                # Check if any changes were made
                if not changes:
                    raise EditValidationError("No changes specified. At least one field must be provided.")
                
                # Commit all changes
                session.commit()
                session.refresh(habit)
                
                # Invalidate caches
                invalidate_habit_caches(habit_name)
                if "name" in changes:
                    invalidate_habit_caches(changes["name"]["new"])
                
                return {
                    "success": True,
                    "habit": {
                        "id": habit.id,
                        "name": habit.name,
                        "frequency": habit.frequency,
                        "description": habit.description,
                        "active": habit.active
                    },
                    "changes": changes,
                    "message": f"Successfully updated habit '{habit.name}'"
                }
                
        except (EditValidationError, EditConflictError, HabitNotFoundError):
            # Re-raise validation and conflict errors as-is
            raise
        except IntegrityError as e:
            raise EditValidationError(f"Database constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            raise EditValidationError(f"Database error during edit: {str(e)}")
    
    @classmethod
    def get_edit_preview(
        cls,
        habit_name: str,
        name: Optional[str] = None,
        frequency: Optional[str] = None,
        description: Optional[str] = None,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Preview changes before applying them.
        
        Args:
            habit_name: Current name of the habit
            name: Proposed new name
            frequency: Proposed new frequency
            description: Proposed new description
            categories: Proposed new categories
            
        Returns:
            Dictionary with preview of changes and validation results
        """
        preview = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "changes": {},
            "current": {},
            "proposed": {}
        }
        
        try:
            with get_session() as session:
                # Get current habit
                habit = session.query(Habit).filter(Habit.name == habit_name).first()
                if not habit:
                    preview["valid"] = False
                    preview["errors"].append(f"Habit '{habit_name}' not found")
                    return preview
                
                if not habit.active:
                    preview["valid"] = False
                    preview["errors"].append(f"Cannot edit archived habit '{habit_name}'. Restore it first.")
                    return preview
                
                # Store current values
                preview["current"] = {
                    "name": habit.name,
                    "frequency": habit.frequency,
                    "description": habit.description or ""
                }
                
                # Validate proposed changes
                proposed = preview["current"].copy()
                
                if name is not None:
                    try:
                        new_name = cls._validate_name_change(session, habit, name)
                        proposed["name"] = new_name
                        preview["changes"]["name"] = {"from": habit.name, "to": new_name}
                    except (EditValidationError, EditConflictError) as e:
                        preview["valid"] = False
                        preview["errors"].append(f"Name change error: {str(e)}")
                
                if frequency is not None:
                    try:
                        new_frequency = cls._validate_frequency_change(habit, frequency)
                        proposed["frequency"] = new_frequency
                        preview["changes"]["frequency"] = {"from": habit.frequency, "to": new_frequency}
                        
                        # Add warning about frequency change impact
                        if habit.frequency != new_frequency:
                            preview["warnings"].append(
                                "Changing frequency may affect streak calculations and statistics"
                            )
                    except EditValidationError as e:
                        preview["valid"] = False
                        preview["errors"].append(f"Frequency change error: {str(e)}")
                
                if description is not None:
                    try:
                        new_description = cls._validate_description_change(habit, description)
                        proposed["description"] = new_description or ""
                        preview["changes"]["description"] = {
                            "from": habit.description or "", 
                            "to": new_description or ""
                        }
                    except EditValidationError as e:
                        preview["valid"] = False
                        preview["errors"].append(f"Description change error: {str(e)}")
                
                preview["proposed"] = proposed
                
                # Check if any changes were actually proposed
                if not preview["changes"] and preview["valid"]:
                    preview["valid"] = False
                    preview["errors"].append("No changes specified. At least one field must be provided.")
                
        except SQLAlchemyError as e:
            preview["valid"] = False
            preview["errors"].append(f"Database error: {str(e)}")
        
        return preview
    
    @classmethod
    def get_habit_history(cls, habit_name: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get edit history for a habit.
        
        Args:
            habit_name: Name of the habit
            limit: Maximum number of history entries to return
            
        Returns:
            List of history entries
            
        Raises:
            HabitNotFoundError: If habit doesn't exist
        """
        try:
            with get_session() as session:
                habit = session.query(Habit).filter(Habit.name == habit_name).first()
                if not habit:
                    raise HabitNotFoundError(f"Habit '{habit_name}' not found")
                
                history_entries = session.query(HabitHistory).filter(
                    HabitHistory.habit_id == habit.id
                ).order_by(HabitHistory.changed_at.desc()).limit(limit).all()
                
                return [
                    {
                        "id": entry.id,
                        "field_name": entry.field_name,
                        "old_value": entry.old_value,
                        "new_value": entry.new_value,
                        "change_type": entry.change_type,
                        "changed_at": entry.changed_at
                    }
                    for entry in history_entries
                ]
                
        except SQLAlchemyError as e:
            raise EditValidationError(f"Database error retrieving history: {str(e)}")