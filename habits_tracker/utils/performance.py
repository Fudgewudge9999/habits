"""Performance optimization utilities for HabitsTracker."""

import time
import functools
from typing import Callable, Any, Dict
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..core.database import get_session


class QueryProfiler:
    """Simple query profiler to monitor database performance."""
    
    def __init__(self):
        self.query_times: Dict[str, list] = {}
        self.enabled = False
    
    def enable(self):
        """Enable query profiling."""
        self.enabled = True
    
    def disable(self):
        """Disable query profiling."""
        self.enabled = False
    
    def record_query(self, query_name: str, execution_time: float):
        """Record a query execution time."""
        if not self.enabled:
            return
        
        if query_name not in self.query_times:
            self.query_times[query_name] = []
        
        self.query_times[query_name].append(execution_time)
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """Get query performance statistics."""
        stats = {}
        
        for query_name, times in self.query_times.items():
            if times:
                stats[query_name] = {
                    "count": len(times),
                    "total_time": sum(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                }
        
        return stats
    
    def clear(self):
        """Clear all recorded query times."""
        self.query_times.clear()


# Global profiler instance
profiler = QueryProfiler()


def profile_query(query_name: str):
    """Decorator to profile query execution time."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                execution_time = (time.time() - start_time) * 1000  # Convert to ms
                profiler.record_query(query_name, execution_time)
        return wrapper
    return decorator


@contextmanager
def optimized_session():
    """Context manager for database session with SQLite optimizations."""
    with get_session() as session:
        # Apply SQLite performance optimizations
        if "sqlite" in str(session.bind.url):
            # Set SQLite pragmas for better performance
            session.execute(text("PRAGMA journal_mode = WAL"))  # Write-Ahead Logging
            session.execute(text("PRAGMA synchronous = NORMAL"))  # Faster than FULL
            session.execute(text("PRAGMA cache_size = -64000"))  # 64MB cache
            session.execute(text("PRAGMA temp_store = MEMORY"))  # Use memory for temp tables
            session.execute(text("PRAGMA mmap_size = 268435456"))  # 256MB memory map
        
        yield session


class PerformanceMonitor:
    """Monitor and track performance of various operations."""
    
    def __init__(self):
        self.operation_times: Dict[str, list] = {}
        self.warnings: list = []
    
    @contextmanager
    def measure_operation(self, operation_name: str, warning_threshold_ms: float = 100):
        """Measure operation execution time with optional warning threshold."""
        start_time = time.time()
        try:
            yield
        finally:
            execution_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if operation_name not in self.operation_times:
                self.operation_times[operation_name] = []
            
            self.operation_times[operation_name].append(execution_time)
            
            if execution_time > warning_threshold_ms:
                warning = f"{operation_name} took {execution_time:.2f}ms (threshold: {warning_threshold_ms}ms)"
                self.warnings.append(warning)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get a comprehensive performance report."""
        report = {
            "operations": {},
            "warnings": self.warnings.copy(),
            "query_stats": profiler.get_stats()
        }
        
        for operation, times in self.operation_times.items():
            if times:
                report["operations"][operation] = {
                    "count": len(times),
                    "total_time_ms": sum(times),
                    "avg_time_ms": sum(times) / len(times),
                    "min_time_ms": min(times),
                    "max_time_ms": max(times),
                    "over_100ms": len([t for t in times if t > 100]),
                    "over_500ms": len([t for t in times if t > 500]),
                }
        
        return report
    
    def clear(self):
        """Clear all performance data."""
        self.operation_times.clear()
        self.warnings.clear()


# Global performance monitor
monitor = PerformanceMonitor()


def performance_target(target_ms: float = 100):
    """Decorator to ensure operations meet performance targets."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            operation_name = f"{func.__module__}.{func.__name__}"
            with monitor.measure_operation(operation_name, target_ms):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class MemoryMonitor:
    """Monitor memory usage patterns."""
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage statistics."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            
            return {
                "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
                "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
                "percent": process.memory_percent(),
            }
        except ImportError:
            return {"error": "psutil not available"}
    
    @contextmanager
    def monitor_memory_usage(self, operation_name: str):
        """Monitor memory usage during an operation."""
        start_memory = self.get_memory_usage()
        try:
            yield
        finally:
            end_memory = self.get_memory_usage()
            
            if "error" not in start_memory and "error" not in end_memory:
                memory_increase = end_memory["rss_mb"] - start_memory["rss_mb"]
                if memory_increase > 10:  # More than 10MB increase
                    warning = f"{operation_name} increased memory by {memory_increase:.2f}MB"
                    monitor.warnings.append(warning)


# Global memory monitor
memory_monitor = MemoryMonitor()


def optimize_sqlite_database(session: Session):
    """Apply comprehensive SQLite optimizations."""
    if "sqlite" not in str(session.bind.url):
        return
    
    # Performance optimizations
    optimizations = [
        "PRAGMA journal_mode = WAL",           # Write-Ahead Logging for better concurrency
        "PRAGMA synchronous = NORMAL",         # Balance between safety and speed
        "PRAGMA cache_size = -64000",          # 64MB cache
        "PRAGMA temp_store = MEMORY",          # Use memory for temporary tables
        "PRAGMA mmap_size = 268435456",        # 256MB memory mapping
        "PRAGMA page_size = 4096",             # Optimal page size for most systems
        "PRAGMA auto_vacuum = INCREMENTAL",    # Automatic space reclamation
        "PRAGMA foreign_keys = ON",            # Enable foreign key constraints
    ]
    
    for pragma in optimizations:
        try:
            session.execute(text(pragma))
        except Exception:
            # Some pragmas might not be supported in all SQLite versions
            pass


def analyze_query_performance(session: Session) -> Dict[str, Any]:
    """Analyze database query performance."""
    if "sqlite" not in str(session.bind.url):
        return {"error": "Only SQLite analysis supported"}
    
    try:
        # Get database statistics
        stats = {}
        
        # Page count and size
        page_count = session.execute(text("PRAGMA page_count")).scalar()
        page_size = session.execute(text("PRAGMA page_size")).scalar()
        stats["database_size_mb"] = (page_count * page_size) / (1024 * 1024)
        
        # Cache statistics
        cache_size = session.execute(text("PRAGMA cache_size")).scalar()
        stats["cache_size_pages"] = abs(cache_size)  # Negative values are in KB
        
        # Journal mode
        journal_mode = session.execute(text("PRAGMA journal_mode")).scalar()
        stats["journal_mode"] = journal_mode
        
        # Integrity check (quick)
        integrity = session.execute(text("PRAGMA quick_check")).scalar()
        stats["integrity"] = integrity
        
        return stats
        
    except Exception as e:
        return {"error": str(e)}


def get_performance_recommendations(report: Dict[str, Any]) -> list:
    """Generate performance recommendations based on monitoring data."""
    recommendations = []
    
    # Check for slow operations
    if "operations" in report:
        for operation, stats in report["operations"].items():
            if stats["avg_time_ms"] > 100:
                recommendations.append(
                    f"Consider optimizing {operation}: avg {stats['avg_time_ms']:.1f}ms"
                )
            
            if stats["over_500ms"] > 0:
                recommendations.append(
                    f"{operation} has {stats['over_500ms']} executions over 500ms"
                )
    
    # Check query patterns
    if "query_stats" in report:
        for query, stats in report["query_stats"].items():
            if stats["avg_time"] > 50:  # 50ms threshold for individual queries
                recommendations.append(
                    f"Query {query} averages {stats['avg_time']:.1f}ms - consider indexing"
                )
    
    # Check warnings
    if report.get("warnings"):
        recommendations.append(f"Address {len(report['warnings'])} performance warnings")
    
    if not recommendations:
        recommendations.append("Performance looks good! All operations under target thresholds.")
    
    return recommendations