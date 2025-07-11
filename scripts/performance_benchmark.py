#!/usr/bin/env python3
"""Performance benchmark script for HabitsTracker CLI."""

import sys
import os
import time
import tempfile
from datetime import date, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from habits_tracker.core.database import init_database
from habits_tracker.core.services.habit_service import HabitService
from habits_tracker.core.services.tracking_service import TrackingService
from habits_tracker.core.services.analytics_service import AnalyticsService
from habits_tracker.utils.performance import (
    profiler, monitor, memory_monitor, 
    analyze_query_performance, get_performance_recommendations
)


def setup_test_database():
    """Set up a temporary database with test data."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "benchmark_habits.db")
    
    # Patch database path
    import habits_tracker.core.database as db_module
    original_path = db_module.get_database_path
    db_module.get_database_path = lambda: db_path
    
    # Initialize database
    init_database()
    
    print(f"Created test database: {db_path}")
    return db_path, temp_dir, original_path


def create_test_data(num_habits=10, days_of_data=30):
    """Create test data for benchmarking."""
    print(f"Creating test data: {num_habits} habits, {days_of_data} days of tracking...")
    
    start_time = time.time()
    
    # Create habits
    habits = []
    for i in range(num_habits):
        habit = HabitService.create_habit(
            f"Habit_{i:02d}",
            frequency="daily",
            description=f"Test habit number {i} for performance benchmarking"
        )
        habits.append(habit.name)
    
    # Create tracking data
    today = date.today()
    for i in range(days_of_data):
        tracking_date = today - timedelta(days=i)
        
        # Track 70% of habits each day (realistic usage pattern)
        for j, habit_name in enumerate(habits):
            if (i + j) % 10 < 7:  # 70% tracking rate
                TrackingService.track_habit(habit_name, tracking_date=tracking_date)
    
    creation_time = time.time() - start_time
    print(f"Test data created in {creation_time:.2f}s")
    
    return habits


def benchmark_operations(habits):
    """Benchmark core operations."""
    print("\n=== BENCHMARKING CORE OPERATIONS ===")
    
    # Enable profiling
    profiler.enable()
    monitor.clear()
    
    results = {}
    
    # Benchmark habit creation
    print("Benchmarking habit creation...")
    start_time = time.time()
    for i in range(5):
        HabitService.create_habit(f"Benchmark_Habit_{i}")
    results["habit_creation"] = (time.time() - start_time) / 5 * 1000  # avg ms
    
    # Benchmark habit listing
    print("Benchmarking habit listing...")
    start_time = time.time()
    for _ in range(10):
        HabitService.list_habits("active", include_stats=True)
    results["habit_listing"] = (time.time() - start_time) / 10 * 1000  # avg ms
    
    # Benchmark tracking
    print("Benchmarking habit tracking...")
    start_time = time.time()
    for i, habit_name in enumerate(habits[:5]):
        tracking_date = date.today() - timedelta(days=i+50)  # Avoid conflicts
        TrackingService.track_habit(habit_name, tracking_date=tracking_date)
    results["habit_tracking"] = (time.time() - start_time) / 5 * 1000  # avg ms
    
    # Benchmark today status
    print("Benchmarking today status...")
    start_time = time.time()
    for _ in range(10):
        TrackingService.get_today_status()
    results["today_status"] = (time.time() - start_time) / 10 * 1000  # avg ms
    
    # Benchmark analytics
    print("Benchmarking analytics...")
    start_time = time.time()
    for _ in range(5):
        AnalyticsService.calculate_overall_stats("all")
    results["analytics"] = (time.time() - start_time) / 5 * 1000  # avg ms
    
    return results


def benchmark_scaling(habits):
    """Benchmark operations with different data sizes."""
    print("\n=== SCALING BENCHMARKS ===")
    
    scaling_results = {}
    
    # Test with different numbers of habits
    for filter_type in ["active", "all"]:
        start_time = time.time()
        result = HabitService.list_habits(filter_type, include_stats=True)
        execution_time = (time.time() - start_time) * 1000
        
        scaling_results[f"list_{filter_type}_{len(result)}_habits"] = execution_time
        print(f"List {filter_type} ({len(result)} habits): {execution_time:.2f}ms")
    
    # Test analytics with different periods
    for period in ["week", "month", "year", "all"]:
        start_time = time.time()
        AnalyticsService.calculate_overall_stats(period)
        execution_time = (time.time() - start_time) * 1000
        
        scaling_results[f"analytics_{period}"] = execution_time
        print(f"Analytics ({period}): {execution_time:.2f}ms")
    
    return scaling_results


def memory_benchmark():
    """Benchmark memory usage."""
    print("\n=== MEMORY BENCHMARK ===")
    
    start_memory = memory_monitor.get_memory_usage()
    print(f"Starting memory: {start_memory.get('rss_mb', 0):.1f}MB")
    
    # Create large dataset
    with memory_monitor.monitor_memory_usage("large_dataset_creation"):
        for i in range(50):
            HabitService.create_habit(f"Memory_Test_{i:03d}")
    
    # Generate analytics on large dataset
    with memory_monitor.monitor_memory_usage("large_dataset_analytics"):
        for _ in range(10):
            AnalyticsService.calculate_overall_stats("all")
    
    end_memory = memory_monitor.get_memory_usage()
    print(f"Ending memory: {end_memory.get('rss_mb', 0):.1f}MB")
    
    memory_increase = end_memory.get('rss_mb', 0) - start_memory.get('rss_mb', 0)
    print(f"Memory increase: {memory_increase:.1f}MB")
    
    return {
        "start_memory_mb": start_memory.get('rss_mb', 0),
        "end_memory_mb": end_memory.get('rss_mb', 0),
        "memory_increase_mb": memory_increase
    }


def print_performance_report():
    """Print comprehensive performance report."""
    print("\n=== PERFORMANCE REPORT ===")
    
    # Get performance data
    performance_data = monitor.get_performance_report()
    
    # Print operation timings
    if performance_data["operations"]:
        print("\nOperation Performance:")
        print("-" * 50)
        for operation, stats in performance_data["operations"].items():
            avg_time = stats["avg_time_ms"]
            status = "✅" if avg_time < 100 else "⚠️" if avg_time < 200 else "❌"
            
            print(f"{status} {operation}: {avg_time:.1f}ms avg "
                  f"(min: {stats['min_time_ms']:.1f}ms, max: {stats['max_time_ms']:.1f}ms)")
            
            if stats["over_100ms"] > 0:
                print(f"   └─ {stats['over_100ms']} executions over 100ms")
    
    # Print query statistics
    if performance_data["query_stats"]:
        print("\nQuery Performance:")
        print("-" * 50)
        for query, stats in performance_data["query_stats"].items():
            avg_time = stats["avg_time"]
            status = "✅" if avg_time < 50 else "⚠️" if avg_time < 100 else "❌"
            
            print(f"{status} {query}: {avg_time:.1f}ms avg "
                  f"({stats['count']} executions)")
    
    # Print warnings
    if performance_data["warnings"]:
        print("\nPerformance Warnings:")
        print("-" * 50)
        for warning in performance_data["warnings"]:
            print(f"⚠️  {warning}")
    
    # Print recommendations
    recommendations = get_performance_recommendations(performance_data)
    print("\nRecommendations:")
    print("-" * 50)
    for rec in recommendations:
        print(f"💡 {rec}")


def analyze_database_performance():
    """Analyze database-level performance."""
    print("\n=== DATABASE ANALYSIS ===")
    
    from habits_tracker.core.database import get_session
    
    with get_session() as session:
        db_stats = analyze_query_performance(session)
        
        if "error" not in db_stats:
            print(f"Database size: {db_stats.get('database_size_mb', 0):.2f}MB")
            print(f"Cache size: {db_stats.get('cache_size_pages', 0)} pages")
            print(f"Journal mode: {db_stats.get('journal_mode', 'unknown')}")
            print(f"Integrity: {db_stats.get('integrity', 'unknown')}")
        else:
            print(f"Database analysis error: {db_stats['error']}")


def main():
    """Run comprehensive performance benchmark."""
    print("HabitsTracker Performance Benchmark")
    print("=" * 50)
    
    # Setup
    db_path, temp_dir, original_path = setup_test_database()
    
    try:
        # Create test data
        habits = create_test_data(num_habits=20, days_of_data=60)
        
        # Run benchmarks
        operation_results = benchmark_operations(habits)
        scaling_results = benchmark_scaling(habits)
        memory_results = memory_benchmark()
        
        # Print detailed results
        print("\n=== BENCHMARK RESULTS ===")
        print("\nCore Operations (Target: <100ms):")
        for operation, avg_time in operation_results.items():
            status = "✅" if avg_time < 100 else "⚠️" if avg_time < 200 else "❌"
            print(f"{status} {operation}: {avg_time:.1f}ms")
        
        print("\nScaling Results:")
        for test, time_ms in scaling_results.items():
            status = "✅" if time_ms < 200 else "⚠️" if time_ms < 500 else "❌"
            print(f"{status} {test}: {time_ms:.1f}ms")
        
        print(f"\nMemory Usage:")
        print(f"Memory increase: {memory_results['memory_increase_mb']:.1f}MB")
        
        # Analyze database
        analyze_database_performance()
        
        # Print comprehensive report
        print_performance_report()
        
        # Overall assessment
        print("\n=== OVERALL ASSESSMENT ===")
        all_operations_fast = all(time < 100 for time in operation_results.values())
        memory_efficient = memory_results['memory_increase_mb'] < 20
        
        if all_operations_fast and memory_efficient:
            print("🎉 EXCELLENT: All performance targets met!")
        elif all_operations_fast:
            print("✅ GOOD: Performance targets met, monitor memory usage")
        else:
            print("⚠️  NEEDS OPTIMIZATION: Some operations exceed targets")
            slow_ops = [op for op, time in operation_results.items() if time >= 100]
            print(f"   Slow operations: {', '.join(slow_ops)}")
    
    finally:
        # Cleanup
        import habits_tracker.core.database as db_module
        db_module.get_database_path = original_path
        
        try:
            os.unlink(db_path)
            os.rmdir(temp_dir)
        except:
            pass
        
        print(f"\nCleaned up test database")


if __name__ == "__main__":
    main()