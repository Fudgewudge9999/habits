"""Date and time utility functions for HabitsTracker."""

from datetime import datetime, date, timedelta
from typing import Optional, Union
import re

from dateutil import parser
from dateutil.tz import tzlocal


def get_today() -> date:
    """Get today's date in local timezone."""
    return datetime.now(tzlocal()).date()


def get_now() -> datetime:
    """Get current datetime in local timezone."""
    return datetime.now(tzlocal())


def parse_date(date_str: str) -> date:
    """Parse a date string into a date object with error handling.
    
    Supports various formats:
    - YYYY-MM-DD (ISO format)
    - MM/DD/YYYY
    - MM-DD-YYYY
    - Relative dates: today, yesterday, tomorrow
    - Relative offsets: -1d, +7d, etc.
    
    Args:
        date_str: String representation of date
        
    Returns:
        Parsed date object
        
    Raises:
        ValueError: If date string cannot be parsed
    """
    result = parse_date_string(date_str)
    if result is None:
        raise ValueError(f"Unable to parse date: '{date_str}'. Use formats like 'YYYY-MM-DD', 'today', 'yesterday', or '-1d'")
    return result


def parse_date_string(date_str: str) -> Optional[date]:
    """Parse a date string into a date object.
    
    Supports various formats:
    - YYYY-MM-DD (ISO format)
    - MM/DD/YYYY
    - MM-DD-YYYY
    - DD/MM/YYYY (when day > 12)
    - Relative dates: today, yesterday, tomorrow
    - Relative offsets: +1, -1, +7, -30 (days from today)
    
    Args:
        date_str: String representation of date
        
    Returns:
        Parsed date object or None if parsing fails
    """
    if not date_str or not date_str.strip():
        return None
    
    date_str = date_str.strip().lower()
    
    # Handle relative dates
    if date_str in ["today", "now"]:
        return get_today()
    elif date_str == "yesterday":
        return get_today() - timedelta(days=1)
    elif date_str == "tomorrow":
        return get_today() + timedelta(days=1)
    
    # Handle relative day offsets (+N, -N, +Nd, -Nd)
    offset_match = re.match(r'^([+-]?\d+)d?$', date_str)
    if offset_match:
        try:
            offset = int(offset_match.group(1))
            return get_today() + timedelta(days=offset)
        except ValueError:
            pass
    
    # Try to parse with dateutil
    try:
        parsed_dt = parser.parse(date_str, fuzzy=False)
        return parsed_dt.date()
    except (ValueError, parser.ParserError):
        pass
    
    # Try common formats manually
    date_formats = [
        "%Y-%m-%d",      # 2025-07-11
        "%m/%d/%Y",      # 07/11/2025
        "%m-%d-%Y",      # 07-11-2025
        "%d/%m/%Y",      # 11/07/2025
        "%d-%m-%Y",      # 11-07-2025
        "%Y/%m/%d",      # 2025/07/11
        "%m/%d/%y",      # 07/11/25
        "%d/%m/%y",      # 11/07/25
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    
    return None


def format_date(date_obj: Union[date, datetime], format_type: str = "iso") -> str:
    """Format a date object as a string.
    
    Args:
        date_obj: Date or datetime object to format
        format_type: Format style ("iso", "short", "long", "relative")
        
    Returns:
        Formatted date string
    """
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    if format_type == "iso":
        return date_obj.strftime("%Y-%m-%d")
    elif format_type == "short":
        return date_obj.strftime("%m/%d/%Y")
    elif format_type == "long":
        return date_obj.strftime("%B %d, %Y")
    elif format_type == "relative":
        return format_relative_date(date_obj)
    else:
        return date_obj.strftime("%Y-%m-%d")


def format_relative_date(date_obj: Union[date, datetime]) -> str:
    """Format a date relative to today.
    
    Args:
        date_obj: Date to format
        
    Returns:
        Relative date string (e.g., "today", "yesterday", "3 days ago")
    """
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
    
    today = get_today()
    delta = (date_obj - today).days
    
    if delta == 0:
        return "today"
    elif delta == 1:
        return "tomorrow"
    elif delta == -1:
        return "yesterday"
    elif delta > 1:
        if delta <= 7:
            return f"in {delta} days"
        else:
            return f"in {delta // 7} weeks" if delta < 30 else format_date(date_obj, "short")
    else:  # delta < -1
        abs_delta = abs(delta)
        if abs_delta <= 7:
            return f"{abs_delta} days ago"
        elif abs_delta <= 30:
            weeks = abs_delta // 7
            return f"{weeks} week{'s' if weeks > 1 else ''} ago"
        else:
            return format_date(date_obj, "short")


def get_week_range(date_obj: Optional[date] = None) -> tuple[date, date]:
    """Get the start and end dates of the week containing the given date.
    
    Args:
        date_obj: Date to find week for (defaults to today)
        
    Returns:
        Tuple of (week_start, week_end) where week starts on Monday
    """
    if date_obj is None:
        date_obj = get_today()
    
    # Find Monday of the week (weekday() returns 0 for Monday)
    days_since_monday = date_obj.weekday()
    week_start = date_obj - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    return week_start, week_end


def get_month_range(date_obj: Optional[date] = None) -> tuple[date, date]:
    """Get the start and end dates of the month containing the given date.
    
    Args:
        date_obj: Date to find month for (defaults to today)
        
    Returns:
        Tuple of (month_start, month_end)
    """
    if date_obj is None:
        date_obj = get_today()
    
    # First day of the month
    month_start = date_obj.replace(day=1)
    
    # Last day of the month
    if date_obj.month == 12:
        next_month_start = date_obj.replace(year=date_obj.year + 1, month=1, day=1)
    else:
        next_month_start = date_obj.replace(month=date_obj.month + 1, day=1)
    
    month_end = next_month_start - timedelta(days=1)
    
    return month_start, month_end


def get_year_range(date_obj: Optional[date] = None) -> tuple[date, date]:
    """Get the start and end dates of the year containing the given date.
    
    Args:
        date_obj: Date to find year for (defaults to today)
        
    Returns:
        Tuple of (year_start, year_end)
    """
    if date_obj is None:
        date_obj = get_today()
    
    year_start = date_obj.replace(month=1, day=1)
    year_end = date_obj.replace(month=12, day=31)
    
    return year_start, year_end


def date_range(start_date: date, end_date: date) -> list[date]:
    """Generate a list of dates between start_date and end_date (inclusive).
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        List of date objects
    """
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    return dates


def is_valid_date_range(start_date: date, end_date: date) -> bool:
    """Check if a date range is valid (start <= end).
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        True if valid range
    """
    return start_date <= end_date


def days_between(start_date: date, end_date: date) -> int:
    """Calculate number of days between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of days (positive if end_date > start_date)
    """
    return (end_date - start_date).days