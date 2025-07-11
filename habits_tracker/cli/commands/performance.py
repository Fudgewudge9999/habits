"""Performance monitoring and profiling CLI commands."""

import typer
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ...core.database import get_session
from ...utils.performance import (
    profiler, monitor, memory_monitor,
    analyze_query_performance, get_performance_recommendations
)

console = Console()


def performance_profile(
    enable: bool = typer.Option(
        False,
        "--enable/--disable",
        help="Enable or disable performance profiling"
    ),
    clear: bool = typer.Option(
        False,
        "--clear",
        help="Clear existing performance data"
    ),
    report: bool = typer.Option(
        False,
        "--report",
        help="Show performance report"
    )
) -> None:
    """Monitor and profile HabitsTracker command performance.
    
    Profile command execution times to identify performance bottlenecks and
    ensure all operations complete within the <100ms target. Useful for
    development and optimization.
    
    Examples:
        habits profile                    # Show current profiler status
        habits profile --enable           # Enable performance profiling
        habits profile --report           # View performance report
        habits profile --clear            # Clear performance data
        habits profile --disable          # Disable profiling
    """
    
    if clear:
        profiler.clear()
        monitor.clear()
        console.print("[green]Performance data cleared[/green]")
        return
    
    if enable:
        profiler.enable()
        console.print("[green]Performance profiling enabled[/green]")
        console.print("Run commands to collect performance data, then use --report to view results")
        return
    
    if not enable:
        profiler.disable()
        console.print("[yellow]Performance profiling disabled[/yellow]")
        return
    
    if report:
        _show_performance_report()
        return
    
    # Default: show current status
    _show_profiler_status()


def performance_benchmark(
    operations: int = typer.Option(
        10,
        "--operations",
        "-n",
        help="Number of operations to benchmark"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed timing for each operation"
    )
) -> None:
    """Run comprehensive performance benchmarks on core operations.
    
    Execute multiple iterations of key HabitsTracker operations to measure
    performance and ensure they meet the <100ms target. Useful for validating
    optimizations and detecting performance regressions.
    
    Examples:
        habits benchmark                   # Run standard benchmark (10 operations)
        habits benchmark --operations 50   # Run 50 operations for more accurate results
        habits benchmark --verbose         # Show timing for each individual operation
        habits benchmark -n 100 -v         # Run 100 operations with detailed output
    """
    
    import time
    from ...core.services.habit_service import HabitService
    from ...core.services.tracking_service import TrackingService
    from ...core.services.analytics_service import AnalyticsService
    
    console.print(f"[bold blue]Running performance benchmark with {operations} operations...[/bold blue]")
    
    # Enable profiling for benchmark
    profiler.enable()
    monitor.clear()
    
    benchmark_results = {}
    
    # Benchmark habit listing
    console.print("Benchmarking habit listing...")
    times = []
    for i in range(operations):
        start = time.time()
        HabitService.list_habits("active", include_stats=True)
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        if verbose:
            console.print(f"  Operation {i+1}: {elapsed:.1f}ms")
    
    benchmark_results["habit_listing"] = {
        "avg": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
        "target": 100
    }
    
    # Benchmark today status
    console.print("Benchmarking today status...")
    times = []
    for i in range(operations):
        start = time.time()
        TrackingService.get_today_status()
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        if verbose:
            console.print(f"  Operation {i+1}: {elapsed:.1f}ms")
    
    benchmark_results["today_status"] = {
        "avg": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
        "target": 100
    }
    
    # Benchmark analytics
    console.print("Benchmarking analytics...")
    times = []
    for i in range(operations // 2):  # Analytics is slower, run fewer
        start = time.time()
        AnalyticsService.calculate_overall_stats("all")
        elapsed = (time.time() - start) * 1000
        times.append(elapsed)
        if verbose:
            console.print(f"  Operation {i+1}: {elapsed:.1f}ms")
    
    benchmark_results["analytics"] = {
        "avg": sum(times) / len(times),
        "min": min(times),
        "max": max(times),
        "target": 200
    }
    
    # Display results
    _show_benchmark_results(benchmark_results)


def database_analyze() -> None:
    """Analyze database performance and provide optimization recommendations.
    
    Examine database structure, query performance, index usage, and storage
    efficiency. Provides actionable suggestions for improving database performance
    and identifying potential bottlenecks.
    
    Examples:
        habits db-analyze                  # Full database performance analysis
    """
    
    console.print("[bold blue]Analyzing database performance...[/bold blue]")
    
    with get_session() as session:
        db_stats = analyze_query_performance(session)
        
        if "error" in db_stats:
            console.print(f"[red]Error analyzing database: {db_stats['error']}[/red]")
            return
        
        # Create database stats table
        table = Table(title="Database Performance Analysis")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_column("Status", style="green")
        
        # Database size
        size_mb = db_stats.get('database_size_mb', 0)
        size_status = "✅ Good" if size_mb < 100 else "⚠️ Large" if size_mb < 500 else "❌ Very Large"
        table.add_row("Database Size", f"{size_mb:.2f} MB", size_status)
        
        # Cache size
        cache_pages = db_stats.get('cache_size_pages', 0)
        cache_mb = cache_pages * 4 / 1024  # Assuming 4KB pages
        cache_status = "✅ Good" if cache_mb >= 16 else "⚠️ Small"
        table.add_row("Cache Size", f"{cache_pages:,} pages ({cache_mb:.1f} MB)", cache_status)
        
        # Journal mode
        journal_mode = db_stats.get('journal_mode', 'unknown')
        journal_status = "✅ Optimal" if journal_mode == "wal" else "⚠️ Suboptimal"
        table.add_row("Journal Mode", journal_mode.upper(), journal_status)
        
        # Integrity
        integrity = db_stats.get('integrity', 'unknown')
        integrity_status = "✅ OK" if integrity == "ok" else "❌ Issues"
        table.add_row("Integrity Check", integrity, integrity_status)
        
        console.print(table)
        
        # Provide recommendations
        recommendations = []
        if size_mb > 100:
            recommendations.append("Consider archiving old tracking data")
        if cache_mb < 16:
            recommendations.append("Increase SQLite cache size for better performance")
        if journal_mode != "wal":
            recommendations.append("Enable WAL mode for better concurrency")
        
        if recommendations:
            console.print("\n[bold yellow]Recommendations:[/bold yellow]")
            for rec in recommendations:
                console.print(f"💡 {rec}")
        else:
            console.print("\n[green]✅ Database performance looks good![/green]")


def memory_usage() -> None:
    """Show current memory usage and optimization status.
    
    Display detailed memory usage statistics including application memory,
    cache usage, and memory efficiency metrics. Helps monitor resource
    consumption and ensure the application stays within the <50MB target.
    
    Examples:
        habits memory                      # Show current memory usage
    """
    
    memory_stats = memory_monitor.get_memory_usage()
    
    if "error" in memory_stats:
        console.print(f"[red]Error getting memory stats: {memory_stats['error']}[/red]")
        console.print("Install psutil for memory monitoring: pip install psutil")
        return
    
    # Create memory stats panel
    memory_text = Text()
    memory_text.append(f"RSS (Resident Set Size): ", style="cyan")
    memory_text.append(f"{memory_stats['rss_mb']:.1f} MB\n", style="bright_white")
    
    memory_text.append(f"VMS (Virtual Memory): ", style="cyan")
    memory_text.append(f"{memory_stats['vms_mb']:.1f} MB\n", style="bright_white")
    
    memory_text.append(f"Memory Percentage: ", style="cyan")
    memory_text.append(f"{memory_stats['percent']:.1f}%", style="bright_white")
    
    # Determine status
    rss_mb = memory_stats['rss_mb']
    if rss_mb < 50:
        status = "[green]✅ Excellent[/green]"
    elif rss_mb < 100:
        status = "[yellow]⚠️ Moderate[/yellow]"
    else:
        status = "[red]❌ High[/red]"
    
    panel = Panel(
        memory_text,
        title=f"Memory Usage {status}",
        border_style="blue"
    )
    
    console.print(panel)


def _show_profiler_status():
    """Show current profiler status."""
    status = "Enabled" if profiler.enabled else "Disabled"
    color = "green" if profiler.enabled else "yellow"
    
    console.print(f"Performance profiling: [{color}]{status}[/{color}]")
    
    if profiler.query_times:
        console.print(f"Collected data for {len(profiler.query_times)} query types")
    else:
        console.print("No performance data collected yet")


def _show_performance_report():
    """Show detailed performance report."""
    performance_data = monitor.get_performance_report()
    
    if not performance_data["operations"] and not performance_data["query_stats"]:
        console.print("[yellow]No performance data available. Enable profiling first.[/yellow]")
        return
    
    # Operations table
    if performance_data["operations"]:
        ops_table = Table(title="Operation Performance")
        ops_table.add_column("Operation", style="cyan")
        ops_table.add_column("Avg Time (ms)", style="magenta")
        ops_table.add_column("Min/Max (ms)", style="white")
        ops_table.add_column("Count", style="blue")
        ops_table.add_column("Status", style="green")
        
        for operation, stats in performance_data["operations"].items():
            avg_time = stats["avg_time_ms"]
            status = "✅" if avg_time < 100 else "⚠️" if avg_time < 200 else "❌"
            
            ops_table.add_row(
                operation.split('.')[-1],  # Show just function name
                f"{avg_time:.1f}",
                f"{stats['min_time_ms']:.1f} / {stats['max_time_ms']:.1f}",
                str(stats["count"]),
                status
            )
        
        console.print(ops_table)
    
    # Query table
    if performance_data["query_stats"]:
        query_table = Table(title="Query Performance")
        query_table.add_column("Query Type", style="cyan")
        query_table.add_column("Avg Time (ms)", style="magenta")
        query_table.add_column("Total Time (ms)", style="white")
        query_table.add_column("Count", style="blue")
        query_table.add_column("Status", style="green")
        
        for query, stats in performance_data["query_stats"].items():
            avg_time = stats["avg_time"]
            status = "✅" if avg_time < 50 else "⚠️" if avg_time < 100 else "❌"
            
            query_table.add_row(
                query,
                f"{avg_time:.1f}",
                f"{stats['total_time']:.1f}",
                str(stats["count"]),
                status
            )
        
        console.print(query_table)
    
    # Warnings
    if performance_data["warnings"]:
        console.print("\n[bold red]Performance Warnings:[/bold red]")
        for warning in performance_data["warnings"]:
            console.print(f"⚠️  {warning}")
    
    # Recommendations
    recommendations = get_performance_recommendations(performance_data)
    console.print("\n[bold yellow]Recommendations:[/bold yellow]")
    for rec in recommendations:
        console.print(f"💡 {rec}")


def _show_benchmark_results(results):
    """Show benchmark results table."""
    table = Table(title="Performance Benchmark Results")
    table.add_column("Operation", style="cyan")
    table.add_column("Avg Time (ms)", style="magenta")
    table.add_column("Min/Max (ms)", style="white")
    table.add_column("Target (ms)", style="blue")
    table.add_column("Status", style="green")
    
    for operation, stats in results.items():
        avg_time = stats["avg"]
        target = stats["target"]
        status = "✅" if avg_time < target else "⚠️" if avg_time < target * 1.5 else "❌"
        
        table.add_row(
            operation.replace("_", " ").title(),
            f"{avg_time:.1f}",
            f"{stats['min']:.1f} / {stats['max']:.1f}",
            str(target),
            status
        )
    
    console.print(table)
    
    # Overall assessment
    all_good = all(stats["avg"] < stats["target"] for stats in results.values())
    if all_good:
        console.print("\n[green]🎉 All operations meet performance targets![/green]")
    else:
        slow_ops = [op for op, stats in results.items() if stats["avg"] >= stats["target"]]
        console.print(f"\n[yellow]⚠️ Operations needing optimization: {', '.join(slow_ops)}[/yellow]")