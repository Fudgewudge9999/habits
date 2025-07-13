"""Service layer for habit template management operations."""

import json
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from ..models import Template, Habit, Category
from ..database import get_session
from .habit_service import HabitService
from .category_service import CategoryService


class TemplateError(Exception):
    """Raised when template operation fails."""
    pass


class TemplateNotFoundError(Exception):
    """Raised when a template is not found."""
    pass


class TemplateValidationError(Exception):
    """Raised when template validation fails."""
    pass


class TemplateService:
    """Service for managing habit templates."""
    
    MAX_NAME_LENGTH = 100
    MAX_DESCRIPTION_LENGTH = 500
    
    # Pre-defined template collections
    PREDEFINED_TEMPLATES = {
        "health": [
            {
                "name": "Daily Exercise",
                "description": "30 minutes of physical activity",
                "habits": [
                    {"name": "Morning Workout", "description": "30 min exercise routine", "frequency": "daily"},
                    {"name": "10k Steps", "description": "Walk 10,000 steps daily", "frequency": "daily"},
                    {"name": "Stretch", "description": "10 min stretching routine", "frequency": "daily"}
                ]
            },
            {
                "name": "Healthy Eating",
                "description": "Nutritious eating habits",
                "habits": [
                    {"name": "Drink Water", "description": "8 glasses of water daily", "frequency": "daily"},
                    {"name": "Eat Vegetables", "description": "5 servings of vegetables", "frequency": "daily"},
                    {"name": "No Processed Food", "description": "Avoid processed foods", "frequency": "daily"}
                ]
            },
            {
                "name": "Sleep Hygiene",
                "description": "Better sleep habits",
                "habits": [
                    {"name": "Bedtime Routine", "description": "Consistent bedtime routine", "frequency": "daily"},
                    {"name": "No Screens Before Bed", "description": "No devices 1 hour before sleep", "frequency": "daily"},
                    {"name": "8 Hours Sleep", "description": "Get 8 hours of quality sleep", "frequency": "daily"}
                ]
            }
        ],
        "productivity": [
            {
                "name": "Deep Work",
                "description": "Focused productivity habits",
                "habits": [
                    {"name": "Deep Work Block", "description": "2 hours of focused work", "frequency": "daily"},
                    {"name": "No Social Media", "description": "No social media during work", "frequency": "daily"},
                    {"name": "Review Goals", "description": "Review daily/weekly goals", "frequency": "daily"}
                ]
            },
            {
                "name": "Learning & Growth",
                "description": "Continuous learning habits",
                "habits": [
                    {"name": "Read", "description": "Read for 30 minutes", "frequency": "daily"},
                    {"name": "Online Course", "description": "Study online course material", "frequency": "daily"},
                    {"name": "Practice Skills", "description": "Practice new skills", "frequency": "daily"}
                ]
            },
            {
                "name": "Task Management",
                "description": "Effective task management",
                "habits": [
                    {"name": "Plan Tomorrow", "description": "Plan next day tasks", "frequency": "daily"},
                    {"name": "Review Today", "description": "Review completed tasks", "frequency": "daily"},
                    {"name": "Weekly Review", "description": "Weekly productivity review", "frequency": "weekly"}
                ]
            }
        ],
        "personal": [
            {
                "name": "Mindfulness",
                "description": "Mental wellness and mindfulness",
                "habits": [
                    {"name": "Meditation", "description": "10 minutes of meditation", "frequency": "daily"},
                    {"name": "Gratitude Journal", "description": "Write 3 things you're grateful for", "frequency": "daily"},
                    {"name": "Mindful Walking", "description": "10 minutes of mindful walking", "frequency": "daily"}
                ]
            },
            {
                "name": "Self-Care",
                "description": "Personal care and wellness",
                "habits": [
                    {"name": "Skincare Routine", "description": "Morning and evening skincare", "frequency": "daily"},
                    {"name": "Personal Time", "description": "30 minutes of personal time", "frequency": "daily"},
                    {"name": "Connect with Friends", "description": "Call or text a friend", "frequency": "daily"}
                ]
            },
            {
                "name": "Creativity",
                "description": "Creative expression habits",
                "habits": [
                    {"name": "Write", "description": "Creative writing or journaling", "frequency": "daily"},
                    {"name": "Draw/Sketch", "description": "Artistic expression", "frequency": "daily"},
                    {"name": "Music Practice", "description": "Practice musical instrument", "frequency": "daily"}
                ]
            }
        ],
        "wellness": [
            {
                "name": "Mental Health",
                "description": "Mental health and emotional wellness",
                "habits": [
                    {"name": "Mood Check-in", "description": "Check in with your emotions", "frequency": "daily"},
                    {"name": "Stress Management", "description": "Practice stress relief technique", "frequency": "daily"},
                    {"name": "Positive Affirmations", "description": "Practice self-affirmations", "frequency": "daily"}
                ]
            },
            {
                "name": "Social Connection",
                "description": "Building and maintaining relationships",
                "habits": [
                    {"name": "Call Family", "description": "Connect with family members", "frequency": "weekly"},
                    {"name": "Social Activity", "description": "Engage in social activities", "frequency": "weekly"},
                    {"name": "Help Others", "description": "Do something kind for others", "frequency": "daily"}
                ]
            }
        ]
    }
    
    @classmethod
    def create_template(
        cls,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        habits: Optional[List[Dict[str, Any]]] = None
    ) -> Template:
        """Create a new habit template.
        
        Args:
            name: Template name
            description: Optional template description
            category: Optional template category
            habits: List of habit definitions
            
        Returns:
            Created template
            
        Raises:
            TemplateValidationError: If validation fails
            TemplateError: If creation fails
        """
        # Validate template data
        name = cls._validate_template_name(name)
        if description:
            description = cls._validate_template_description(description)
        
        if habits is None:
            habits = []
        
        # Validate habits data
        for i, habit in enumerate(habits):
            if not isinstance(habit, dict):
                raise TemplateValidationError(f"Habit {i}: Must be a dictionary")
            
            if "name" not in habit:
                raise TemplateValidationError(f"Habit {i}: Missing required field 'name'")
            
            # Validate habit fields using HabitService validation
            try:
                HabitService.validate_habit_name(habit["name"])
                if habit.get("frequency"):
                    HabitService.validate_frequency(habit["frequency"])
                if habit.get("description"):
                    HabitService.validate_description(habit["description"])
            except Exception as e:
                raise TemplateValidationError(f"Habit {i} validation failed: {str(e)}")
        
        try:
            with get_session() as session:
                # Check if template name already exists
                existing = session.query(Template).filter(Template.name == name).first()
                if existing:
                    raise TemplateValidationError(f"Template with name '{name}' already exists")
                
                # Create template
                template_data = json.dumps(habits, ensure_ascii=False)
                
                template = Template(
                    name=name,
                    description=description,
                    category=category,
                    template_data=template_data,
                    is_predefined=False
                )
                
                session.add(template)
                session.commit()
                session.refresh(template)
                
                return template
                
        except IntegrityError:
            raise TemplateValidationError(f"Template with name '{name}' already exists")
        except Exception as e:
            raise TemplateError(f"Failed to create template: {str(e)}")
    
    @classmethod
    def list_templates(
        cls,
        category: Optional[str] = None,
        include_predefined: bool = True,
        include_user: bool = True
    ) -> List[Template]:
        """List available templates.
        
        Args:
            category: Optional category filter
            include_predefined: Whether to include predefined templates
            include_user: Whether to include user-created templates
            
        Returns:
            List of templates
        """
        try:
            with get_session() as session:
                query = session.query(Template)
                
                # Apply filters
                if category:
                    query = query.filter(Template.category == category)
                
                if not include_predefined and not include_user:
                    return []
                elif not include_predefined:
                    query = query.filter(Template.is_predefined == False)
                elif not include_user:
                    query = query.filter(Template.is_predefined == True)
                
                return query.order_by(Template.is_predefined.desc(), Template.name).all()
                
        except Exception as e:
            raise TemplateError(f"Failed to list templates: {str(e)}")
    
    @classmethod
    def get_template(cls, name: str) -> Template:
        """Get template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template object
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        try:
            with get_session() as session:
                template = session.query(Template).filter(Template.name == name).first()
                if not template:
                    raise TemplateNotFoundError(f"Template '{name}' not found")
                
                return template
                
        except TemplateNotFoundError:
            raise
        except Exception as e:
            raise TemplateError(f"Failed to get template: {str(e)}")
    
    @classmethod
    def delete_template(cls, name: str) -> Template:
        """Delete template by name.
        
        Args:
            name: Template name
            
        Returns:
            Deleted template
            
        Raises:
            TemplateNotFoundError: If template not found
            TemplateError: If deletion fails
        """
        try:
            with get_session() as session:
                template = session.query(Template).filter(Template.name == name).first()
                if not template:
                    raise TemplateNotFoundError(f"Template '{name}' not found")
                
                if template.is_predefined:
                    raise TemplateError("Cannot delete predefined templates")
                
                session.delete(template)
                session.commit()
                
                return template
                
        except (TemplateNotFoundError, TemplateError):
            raise
        except Exception as e:
            raise TemplateError(f"Failed to delete template: {str(e)}")
    
    @classmethod
    def apply_template(
        cls,
        template_name: str,
        category_name: Optional[str] = None,
        skip_existing: bool = True
    ) -> Dict[str, Any]:
        """Apply template to create habits.
        
        Args:
            template_name: Name of template to apply
            category_name: Optional category to assign to created habits
            skip_existing: Whether to skip habits that already exist
            
        Returns:
            Application result dictionary
            
        Raises:
            TemplateNotFoundError: If template not found
            TemplateError: If application fails
        """
        try:
            # Get template
            template = cls.get_template(template_name)
            
            # Parse template data
            try:
                habits_data = json.loads(template.template_data)
            except json.JSONDecodeError as e:
                raise TemplateError(f"Invalid template data format: {str(e)}")
            
            result = {
                "template_name": template_name,
                "created": [],
                "skipped": [],
                "errors": []
            }
            
            # Get or create category if specified
            category = None
            if category_name:
                try:
                    category = CategoryService.get_category_by_name(category_name)
                except:
                    # Create category if it doesn't exist
                    category = CategoryService.create_category(category_name)
            
            with get_session() as session:
                for habit_data in habits_data:
                    try:
                        habit_name = habit_data["name"]
                        
                        # Check if habit already exists
                        existing_habit = session.query(Habit).filter(Habit.name == habit_name).first()
                        
                        if existing_habit:
                            if skip_existing:
                                result["skipped"].append(habit_name)
                                continue
                            else:
                                result["errors"].append(f"Habit '{habit_name}' already exists")
                                continue
                        
                        # Create new habit
                        new_habit = Habit(
                            name=habit_name,
                            description=habit_data.get("description"),
                            frequency=habit_data.get("frequency", "daily"),
                            frequency_details=habit_data.get("frequency_details")
                        )
                        
                        session.add(new_habit)
                        session.flush()  # Get the ID
                        
                        # Assign category if specified
                        if category:
                            new_habit.categories.append(category)
                        
                        result["created"].append(habit_name)
                        
                    except Exception as e:
                        result["errors"].append(f"Failed to create habit '{habit_data.get('name', 'unknown')}': {str(e)}")
                
                session.commit()
            
            return result
            
        except (TemplateNotFoundError, TemplateError):
            raise
        except Exception as e:
            raise TemplateError(f"Failed to apply template: {str(e)}")
    
    @classmethod
    def create_template_from_habits(
        cls,
        template_name: str,
        habit_names: List[str],
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> Template:
        """Create template from existing habits.
        
        Args:
            template_name: Name for the new template
            habit_names: List of habit names to include
            description: Optional template description
            category: Optional template category
            
        Returns:
            Created template
            
        Raises:
            TemplateValidationError: If validation fails
            TemplateError: If creation fails
        """
        try:
            with get_session() as session:
                # Get existing habits
                habits = session.query(Habit).filter(Habit.name.in_(habit_names)).all()
                
                found_names = {habit.name for habit in habits}
                missing_names = set(habit_names) - found_names
                
                if missing_names:
                    raise TemplateValidationError(f"Habits not found: {', '.join(missing_names)}")
                
                # Create habits data for template
                habits_data = []
                for habit in habits:
                    habit_data = {
                        "name": habit.name,
                        "description": habit.description,
                        "frequency": habit.frequency,
                    }
                    if habit.frequency_details:
                        habit_data["frequency_details"] = habit.frequency_details
                    
                    habits_data.append(habit_data)
                
                # Create template
                return cls.create_template(
                    name=template_name,
                    description=description,
                    category=category,
                    habits=habits_data
                )
                
        except (TemplateValidationError, TemplateError):
            raise
        except Exception as e:
            raise TemplateError(f"Failed to create template from habits: {str(e)}")
    
    @classmethod
    def initialize_predefined_templates(cls) -> Dict[str, Any]:
        """Initialize predefined template collections in the database.
        
        Returns:
            Initialization result dictionary
        """
        result = {
            "created": [],
            "skipped": [],
            "errors": []
        }
        
        try:
            with get_session() as session:
                for category, templates in cls.PREDEFINED_TEMPLATES.items():
                    for template_data in templates:
                        try:
                            template_name = template_data["name"]
                            
                            # Check if template already exists
                            existing = session.query(Template).filter(Template.name == template_name).first()
                            if existing:
                                result["skipped"].append(template_name)
                                continue
                            
                            # Create predefined template
                            template_json = json.dumps(template_data["habits"], ensure_ascii=False)
                            
                            template = Template(
                                name=template_name,
                                description=template_data["description"],
                                category=category,
                                template_data=template_json,
                                is_predefined=True
                            )
                            
                            session.add(template)
                            result["created"].append(template_name)
                            
                        except Exception as e:
                            result["errors"].append(f"Failed to create template '{template_data.get('name', 'unknown')}': {str(e)}")
                
                session.commit()
                
        except Exception as e:
            raise TemplateError(f"Failed to initialize predefined templates: {str(e)}")
        
        return result
    
    @classmethod
    def get_template_preview(cls, template_name: str) -> Dict[str, Any]:
        """Get preview of template contents.
        
        Args:
            template_name: Name of template to preview
            
        Returns:
            Template preview information
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        template = cls.get_template(template_name)
        
        try:
            habits_data = json.loads(template.template_data)
        except json.JSONDecodeError as e:
            raise TemplateError(f"Invalid template data format: {str(e)}")
        
        return {
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "is_predefined": template.is_predefined,
            "habit_count": len(habits_data),
            "habits": habits_data,
            "created_at": template.created_at.isoformat()
        }
    
    @classmethod
    def _validate_template_name(cls, name: str) -> str:
        """Validate and normalize template name."""
        if not name or not name.strip():
            raise TemplateValidationError("Template name cannot be empty")
        
        name = name.strip()
        
        if len(name) > cls.MAX_NAME_LENGTH:
            raise TemplateValidationError(f"Template name too long (max {cls.MAX_NAME_LENGTH} characters)")
        
        return name
    
    @classmethod
    def _validate_template_description(cls, description: str) -> str:
        """Validate and normalize template description."""
        description = description.strip()
        
        if len(description) > cls.MAX_DESCRIPTION_LENGTH:
            raise TemplateValidationError(f"Template description too long (max {cls.MAX_DESCRIPTION_LENGTH} characters)")
        
        return description