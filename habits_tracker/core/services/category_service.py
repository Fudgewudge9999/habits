"""Service layer for category management and habit categorization."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, or_, func

from ..models import Category, Habit, habit_categories
from ..database import get_session
from .habit_service import HabitService, HabitValidationError, HabitNotFoundError
from ...utils.performance import performance_target, profile_query
from ...utils.cache import invalidate_habit_caches


class CategoryValidationError(Exception):
    """Raised when category validation fails."""
    pass


class CategoryNotFoundError(Exception):
    """Raised when a category is not found."""
    pass


class CategoryService:
    """Service for managing categories and habit categorization."""
    
    MAX_CATEGORY_NAME_LENGTH = 100
    MAX_CATEGORY_DESCRIPTION_LENGTH = 500
    VALID_COLOR_PATTERN = r'^#[0-9A-Fa-f]{6}$'
    
    @classmethod
    def validate_category_name(cls, name: str) -> str:
        """Validate and normalize category name.
        
        Args:
            name: Raw category name
            
        Returns:
            Normalized category name
            
        Raises:
            CategoryValidationError: If name is invalid
        """
        if not name or not name.strip():
            raise CategoryValidationError("Category name cannot be empty")
        
        name = name.strip()
        
        if len(name) > cls.MAX_CATEGORY_NAME_LENGTH:
            raise CategoryValidationError(f"Category name too long (max {cls.MAX_CATEGORY_NAME_LENGTH} characters)")
        
        # Check for invalid characters
        invalid_chars = ['\n', '\r', '\t']
        if any(char in name for char in invalid_chars):
            raise CategoryValidationError("Category name cannot contain newlines or tabs")
        
        return name
    
    @classmethod
    def validate_category_color(cls, color: Optional[str]) -> Optional[str]:
        """Validate category color.
        
        Args:
            color: Color hex code (e.g., #FF0000)
            
        Returns:
            Validated color or None
            
        Raises:
            CategoryValidationError: If color is invalid
        """
        if not color:
            return None
        
        color = color.strip()
        
        import re
        if not re.match(cls.VALID_COLOR_PATTERN, color):
            raise CategoryValidationError("Color must be a valid hex code (e.g., #FF0000)")
        
        return color.upper()
    
    @classmethod
    def validate_category_description(cls, description: Optional[str]) -> Optional[str]:
        """Validate category description.
        
        Args:
            description: Optional description
            
        Returns:
            Normalized description or None
            
        Raises:
            CategoryValidationError: If description is invalid
        """
        if not description:
            return None
        
        description = description.strip()
        
        if len(description) > cls.MAX_CATEGORY_DESCRIPTION_LENGTH:
            raise CategoryValidationError(f"Description too long (max {cls.MAX_CATEGORY_DESCRIPTION_LENGTH} characters)")
        
        return description if description else None
    
    @classmethod
    @performance_target(50)  # 50ms target for category creation
    @profile_query("category_creation")
    def create_category(
        cls,
        name: str,
        color: Optional[str] = None,
        description: Optional[str] = None
    ) -> Category:
        """Create a new category.
        
        Args:
            name: Category name
            color: Optional color hex code
            description: Optional description
            
        Returns:
            Created Category object
            
        Raises:
            CategoryValidationError: If validation fails
        """
        # Validate inputs
        name = cls.validate_category_name(name)
        color = cls.validate_category_color(color)
        description = cls.validate_category_description(description)
        
        try:
            with get_session() as session:
                # Check if category already exists
                existing = session.query(Category).filter(Category.name == name).first()
                if existing:
                    raise CategoryValidationError(f"Category '{name}' already exists")
                
                # Create new category
                category = Category(
                    name=name,
                    color=color,
                    description=description
                )
                
                session.add(category)
                session.commit()
                session.refresh(category)
                
                return category
                
        except IntegrityError as e:
            raise CategoryValidationError(f"Database constraint violation: {str(e)}")
        except SQLAlchemyError as e:
            raise CategoryValidationError(f"Database error: {str(e)}")
    
    @classmethod
    def get_category_by_name(cls, name: str) -> Optional[Category]:
        """Get a category by name.
        
        Args:
            name: Category name
            
        Returns:
            Category object or None if not found
        """
        try:
            with get_session() as session:
                return session.query(Category).filter(Category.name == name).first()
        except SQLAlchemyError:
            return None
    
    @classmethod
    @performance_target(100)  # 100ms target for listing categories
    @profile_query("category_listing")
    def list_categories(cls, include_stats: bool = True) -> List[Dict[str, Any]]:
        """List all categories with optional statistics.
        
        Args:
            include_stats: Whether to include habit count statistics
            
        Returns:
            List of category dictionaries with statistics
        """
        try:
            with get_session() as session:
                categories = session.query(Category).order_by(Category.created_at.desc()).all()
                
                result = []
                for category in categories:
                    category_dict = {
                        "id": category.id,
                        "name": category.name,
                        "color": category.color,
                        "description": category.description,
                        "created_at": category.created_at,
                    }
                    
                    if include_stats:
                        # Count habits in this category
                        habit_count = session.query(func.count(habit_categories.c.habit_id)).filter(
                            habit_categories.c.category_id == category.id
                        ).scalar() or 0
                        
                        active_habit_count = session.query(func.count(habit_categories.c.habit_id)).join(
                            Habit, Habit.id == habit_categories.c.habit_id
                        ).filter(
                            and_(
                                habit_categories.c.category_id == category.id,
                                Habit.active == True
                            )
                        ).scalar() or 0
                        
                        category_dict.update({
                            "total_habits": habit_count,
                            "active_habits": active_habit_count
                        })
                    
                    result.append(category_dict)
                
                return result
                
        except SQLAlchemyError:
            return []
    
    @classmethod
    def update_category(
        cls,
        name: str,
        new_name: Optional[str] = None,
        color: Optional[str] = None,
        description: Optional[str] = None
    ) -> bool:
        """Update an existing category.
        
        Args:
            name: Current category name
            new_name: New name for the category (optional)
            color: New color for the category (optional)
            description: New description for the category (optional)
            
        Returns:
            True if successful, False if category not found
            
        Raises:
            CategoryValidationError: If validation fails
        """
        try:
            with get_session() as session:
                category = session.query(Category).filter(Category.name == name).first()
                if not category:
                    return False
                
                # Validate and apply changes
                if new_name is not None:
                    new_name = cls.validate_category_name(new_name)
                    # Check for name conflicts
                    if new_name != category.name:
                        existing = session.query(Category).filter(Category.name == new_name).first()
                        if existing:
                            raise CategoryValidationError(f"Category '{new_name}' already exists")
                        category.name = new_name
                
                if color is not None:
                    category.color = cls.validate_category_color(color)
                
                if description is not None:
                    category.description = cls.validate_category_description(description)
                
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            raise CategoryValidationError(f"Database error during update: {str(e)}")
    
    @classmethod
    def delete_category(cls, name: str, force: bool = False) -> bool:
        """Delete a category.
        
        Args:
            name: Category name
            force: If True, remove category from all habits first
            
        Returns:
            True if successful, False if category not found
            
        Raises:
            CategoryValidationError: If category is in use and force=False
        """
        try:
            with get_session() as session:
                category = session.query(Category).filter(Category.name == name).first()
                if not category:
                    return False
                
                # Check if category is in use
                habit_count = session.query(func.count(habit_categories.c.habit_id)).filter(
                    habit_categories.c.category_id == category.id
                ).scalar() or 0
                
                if habit_count > 0 and not force:
                    raise CategoryValidationError(
                        f"Category '{name}' is assigned to {habit_count} habit(s). "
                        "Use force=True to remove it from all habits first."
                    )
                
                # Remove category assignments if force=True
                if force and habit_count > 0:
                    session.execute(
                        habit_categories.delete().where(habit_categories.c.category_id == category.id)
                    )
                
                # Delete the category
                session.delete(category)
                session.commit()
                return True
                
        except SQLAlchemyError as e:
            raise CategoryValidationError(f"Database error during deletion: {str(e)}")
    
    @classmethod
    def assign_category_to_habit(cls, habit_name: str, category_name: str) -> bool:
        """Assign a category to a habit.
        
        Args:
            habit_name: Name of the habit
            category_name: Name of the category
            
        Returns:
            True if successful
            
        Raises:
            HabitNotFoundError: If habit doesn't exist
            CategoryNotFoundError: If category doesn't exist
            CategoryValidationError: If assignment fails
        """
        try:
            with get_session() as session:
                # Get habit and category
                habit = session.query(Habit).filter(Habit.name == habit_name).first()
                if not habit:
                    raise HabitNotFoundError(f"Habit '{habit_name}' not found")
                
                category = session.query(Category).filter(Category.name == category_name).first()
                if not category:
                    raise CategoryNotFoundError(f"Category '{category_name}' not found")
                
                # Check if already assigned
                existing = session.execute(
                    habit_categories.select().where(
                        and_(
                            habit_categories.c.habit_id == habit.id,
                            habit_categories.c.category_id == category.id
                        )
                    )
                ).first()
                
                if existing:
                    raise CategoryValidationError(f"Habit '{habit_name}' is already in category '{category_name}'")
                
                # Add assignment
                session.execute(
                    habit_categories.insert().values(
                        habit_id=habit.id,
                        category_id=category.id
                    )
                )
                session.commit()
                
                # Invalidate caches
                invalidate_habit_caches(habit_name)
                
                return True
                
        except SQLAlchemyError as e:
            raise CategoryValidationError(f"Database error during assignment: {str(e)}")
    
    @classmethod
    def remove_category_from_habit(cls, habit_name: str, category_name: str) -> bool:
        """Remove a category from a habit.
        
        Args:
            habit_name: Name of the habit
            category_name: Name of the category
            
        Returns:
            True if successful, False if not assigned
            
        Raises:
            HabitNotFoundError: If habit doesn't exist
            CategoryNotFoundError: If category doesn't exist
        """
        try:
            with get_session() as session:
                # Get habit and category
                habit = session.query(Habit).filter(Habit.name == habit_name).first()
                if not habit:
                    raise HabitNotFoundError(f"Habit '{habit_name}' not found")
                
                category = session.query(Category).filter(Category.name == category_name).first()
                if not category:
                    raise CategoryNotFoundError(f"Category '{category_name}' not found")
                
                # Remove assignment
                result = session.execute(
                    habit_categories.delete().where(
                        and_(
                            habit_categories.c.habit_id == habit.id,
                            habit_categories.c.category_id == category.id
                        )
                    )
                )
                
                session.commit()
                
                # Invalidate caches
                invalidate_habit_caches(habit_name)
                
                return result.rowcount > 0
                
        except SQLAlchemyError as e:
            raise CategoryValidationError(f"Database error during removal: {str(e)}")
    
    @classmethod
    def get_habit_categories(cls, habit_name: str) -> List[Dict[str, Any]]:
        """Get all categories assigned to a habit.
        
        Args:
            habit_name: Name of the habit
            
        Returns:
            List of category dictionaries
            
        Raises:
            HabitNotFoundError: If habit doesn't exist
        """
        try:
            with get_session() as session:
                habit = session.query(Habit).filter(Habit.name == habit_name).first()
                if not habit:
                    raise HabitNotFoundError(f"Habit '{habit_name}' not found")
                
                categories = session.query(Category).join(
                    habit_categories, Category.id == habit_categories.c.category_id
                ).filter(habit_categories.c.habit_id == habit.id).all()
                
                return [
                    {
                        "id": category.id,
                        "name": category.name,
                        "color": category.color,
                        "description": category.description
                    }
                    for category in categories
                ]
                
        except SQLAlchemyError as e:
            raise CategoryValidationError(f"Database error retrieving categories: {str(e)}")
    
    @classmethod
    def get_habits_by_category(cls, category_name: str, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get all habits in a specific category.
        
        Args:
            category_name: Name of the category
            active_only: Whether to include only active habits
            
        Returns:
            List of habit dictionaries
            
        Raises:
            CategoryNotFoundError: If category doesn't exist
        """
        try:
            with get_session() as session:
                category = session.query(Category).filter(Category.name == category_name).first()
                if not category:
                    raise CategoryNotFoundError(f"Category '{category_name}' not found")
                
                query = session.query(Habit).join(
                    habit_categories, Habit.id == habit_categories.c.habit_id
                ).filter(habit_categories.c.category_id == category.id)
                
                if active_only:
                    query = query.filter(Habit.active == True)
                
                habits = query.all()
                
                return [
                    {
                        "id": habit.id,
                        "name": habit.name,
                        "description": habit.description,
                        "frequency": habit.frequency,
                        "active": habit.active,
                        "created_at": habit.created_at
                    }
                    for habit in habits
                ]
                
        except SQLAlchemyError as e:
            raise CategoryValidationError(f"Database error retrieving habits: {str(e)}")
    
    @classmethod
    def batch_assign_category(cls, habit_names: List[str], category_name: str) -> Dict[str, Any]:
        """Assign a category to multiple habits.
        
        Args:
            habit_names: List of habit names
            category_name: Name of the category
            
        Returns:
            Dictionary with batch operation results
            
        Raises:
            CategoryNotFoundError: If category doesn't exist
        """
        results = {
            "successful": [],
            "failed": [],
            "already_assigned": [],
            "not_found": []
        }
        
        try:
            with get_session() as session:
                # Check if category exists
                category = session.query(Category).filter(Category.name == category_name).first()
                if not category:
                    raise CategoryNotFoundError(f"Category '{category_name}' not found")
                
                for habit_name in habit_names:
                    try:
                        success = cls.assign_category_to_habit(habit_name, category_name)
                        if success:
                            results["successful"].append(habit_name)
                    except HabitNotFoundError:
                        results["not_found"].append(habit_name)
                    except CategoryValidationError as e:
                        if "already in category" in str(e):
                            results["already_assigned"].append(habit_name)
                        else:
                            results["failed"].append({"habit": habit_name, "error": str(e)})
                
        except SQLAlchemyError as e:
            raise CategoryValidationError(f"Database error during batch assignment: {str(e)}")
        
        return results