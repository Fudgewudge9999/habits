"""Analytics commands for habit statistics and insights."""

from datetime import date
from typing import Optional, List, Dict, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

from ...core.services.analytics_service import AnalyticsService
from ...core.services.visualization_service import VisualizationService
from ...utils.display import create_success_panel, create_error_panel, create_info_panel
from ...utils.date_utils import format_date

console = Console()


def show_stats(
    habit_name: Optional[str] = typer.Option(
        None, 
        "--habit", 
        "-h", 
        help="Show stats for specific habit (leave blank for overall stats)"
    ),
    period: str = typer.Option(
        "all", 
        "--period", 
        "-p", 
        help="Time period: week (last 7 days), month (last 30 days), year (last 365 days), all (all-time)",
        show_default=True
    )
) -> None:
    """Show detailed habit statistics and performance analytics.
    
    Display comprehensive statistics including streaks, completion rates,
    and performance insights. View overall statistics for all habits or
    focus on a specific habit's performance over different time periods.
    
    Examples:
        habits stats                           # Overall stats for all habits
        habits stats --habit "Exercise"        # Stats for specific habit
        habits stats --period week             # Weekly overview
        habits stats --habit "Read" --period month  # Monthly stats for reading
        habits stats -h "Gym" -p year          # Yearly gym statistics
    """
    
    # Validate period
    valid_periods = ["week", "month", "year", "all"]
    if period not in valid_periods:
        console.print(create_error_panel(
            "Invalid Period",
            f"Period '{period}' is not valid",
            f"Valid periods: {', '.join(valid_periods)}\n" +
            "• week: last 7 days\n" +
            "• month: last 30 days\n" +
            "• year: last 365 days\n" +
            "• all: all-time statistics"
        ))
        raise typer.Exit(1)
    
    if habit_name:
        # Show stats for specific habit
        _show_habit_stats(habit_name, period)
    else:
        # Show overall stats for all habits
        _show_overall_stats(period)


def _show_habit_stats(habit_name: str, period: str) -> None:
    """Show statistics for a specific habit."""
    
    result = AnalyticsService.calculate_habit_stats(habit_name, period)
    
    if not result["success"]:
        console.print(create_error_panel(
            "Habit Not Found",
            result["error"],
            "Use 'habits list --filter all' to see all available habits"
        ))
        raise typer.Exit(1)
    
    stats = result["statistics"]
    
    # Header with habit name and period
    period_display = period.title() if period != "all" else "All Time"
    console.print(f"\n[bold blue]📊 Statistics for '{habit_name}' - {period_display}[/bold blue]\n")
    
    # Main statistics panel
    main_stats_content = _format_main_stats(stats)
    console.print(Panel(
        main_stats_content,
        title="📈 Key Metrics",
        border_style="blue"
    ))
    
    # Recent activity if we have entries
    if result["recent_entries"]:
        console.print("\n[bold]📅 Recent Activity (Last 10 entries)[/bold]\n")
        
        activity_table = Table(show_header=True, header_style="bold magenta")
        activity_table.add_column("Date", style="cyan", min_width=12)
        activity_table.add_column("Notes", style="dim italic", overflow="fold")
        
        for entry in reversed(result["recent_entries"]):  # Show most recent first
            date_str = format_date(entry["date"])
            notes = entry["notes"] or "—"
            activity_table.add_row(date_str, notes)
        
        console.print(activity_table)
    
    # Motivational message based on performance
    completion_rate = stats["completion_rate"]
    current_streak = stats["current_streak"]
    
    if completion_rate >= 90:
        motivation = "🏆 Outstanding consistency! You're a habit champion!"
    elif completion_rate >= 75:
        motivation = "⭐ Great job! You're building strong habits."
    elif completion_rate >= 50:
        motivation = "👍 Good progress! Keep building momentum."
    elif completion_rate >= 25:
        motivation = "💪 You're getting started! Focus on consistency."
    else:
        motivation = "🌱 Every journey begins with a single step. You've got this!"
    
    if current_streak > 0:
        motivation += f" Current streak: {current_streak} day{'s' if current_streak != 1 else ''}! 🔥"
    
    console.print(f"\n[dim]{motivation}[/dim]")


def _show_overall_stats(period: str) -> None:
    """Show overall statistics across all habits."""
    
    result = AnalyticsService.calculate_overall_stats(period)
    
    if not result["success"]:
        console.print(create_error_panel(
            "Error Loading Statistics",
            "Failed to retrieve habit statistics",
            "Please check your database connection"
        ))
        raise typer.Exit(1)
    
    if not result["habits"]:
        console.print(create_info_panel(
            "No Habits Found",
            "No habits available for statistics",
            "Use 'habits add' to create your first habit"
        ))
        return
    
    summary = result["summary"]
    period_display = period.title() if period != "all" else "All Time"
    
    # Header
    console.print(f"\n[bold blue]📊 Overall Statistics - {period_display}[/bold blue]\n")
    
    # Summary panel
    summary_content = _format_overall_summary(summary)
    console.print(Panel(
        summary_content,
        title="📈 Summary",
        border_style="blue"
    ))
    
    # Habits breakdown table
    console.print("\n[bold]📋 Habit Breakdown[/bold]\n")
    
    habits_table = Table(show_header=True, header_style="bold magenta")
    habits_table.add_column("Habit", style="cyan", no_wrap=True, min_width=20)
    habits_table.add_column("Status", justify="center", min_width=8)
    habits_table.add_column("Completions", justify="center", min_width=12)
    habits_table.add_column("Rate", justify="center", min_width=8)
    habits_table.add_column("Streak", justify="center", min_width=8)
    
    # Sort habits by completion rate (descending)
    sorted_habits = sorted(result["habits"], key=lambda x: x["completion_rate"], reverse=True)
    
    for habit in sorted_habits:
        # Status indicator
        status = "✅" if habit["active"] else "📦"
        
        # Completion rate with color coding
        rate = habit["completion_rate"]
        if rate >= 75:
            rate_display = f"[green]{rate}%[/green]"
        elif rate >= 50:
            rate_display = f"[yellow]{rate}%[/yellow]"
        else:
            rate_display = f"[red]{rate}%[/red]"
        
        # Streak with emoji
        streak = habit["current_streak"]
        if streak == 0:
            streak_display = "0"
        elif streak < 7:
            streak_display = f"🔥 {streak}"
        elif streak < 30:
            streak_display = f"⭐ {streak}"
        else:
            streak_display = f"🏆 {streak}"
        
        habits_table.add_row(
            habit["name"],
            status,
            str(habit["completions"]),
            rate_display,
            streak_display
        )
    
    console.print(habits_table)
    
    # Performance insights
    _show_performance_insights(summary, sorted_habits)


def _format_main_stats(stats: dict) -> str:
    """Format main statistics for a habit."""
    
    # Format dates
    created_date = format_date(stats["created_at"])
    
    # Status emoji
    status_emoji = "✅" if stats["is_active"] else "📦"
    
    content = f"""[bold]Status:[/bold] {status_emoji} {'Active' if stats['is_active'] else 'Archived'}
[bold]Created:[/bold] {created_date}

[bold]📊 Performance Metrics[/bold]
━━━━━━━━━━━━━━━━━━━━━━
[bold]Total Completions:[/bold] {stats['total_completions']}
[bold]Completion Rate:[/bold] {stats['completion_rate']}%
[bold]Current Streak:[/bold] {stats['current_streak']} day{'s' if stats['current_streak'] != 1 else ''}
[bold]Longest Streak:[/bold] {stats['longest_streak']} day{'s' if stats['longest_streak'] != 1 else ''}"""
    
    return content


def _format_overall_summary(summary: dict) -> str:
    """Format overall summary statistics."""
    
    content = f"""[bold]📋 Habit Overview[/bold]
━━━━━━━━━━━━━━━━━━━━━━
[bold]Total Habits:[/bold] {summary['total_habits']}
[bold]Active Habits:[/bold] {summary['active_habits']}
[bold]Archived Habits:[/bold] {summary['total_habits'] - summary['active_habits']}

[bold]📈 Performance Overview[/bold]
━━━━━━━━━━━━━━━━━━━━━━
[bold]Total Completions:[/bold] {summary['total_completions']}
[bold]Average Completion Rate:[/bold] {summary['average_completion_rate']}%"""
    
    return content


def _show_performance_insights(summary: dict, habits: list) -> None:
    """Show performance insights and recommendations."""
    
    console.print("\n[bold]🔍 Performance Insights[/bold]\n")
    
    insights = []
    
    # Best performing habit
    if habits:
        best_habit = habits[0]  # Already sorted by completion rate
        if best_habit["completion_rate"] > 0:
            insights.append(f"🏆 Your best habit is '{best_habit['name']}' with {best_habit['completion_rate']}% completion rate")
    
    # Habits needing attention
    struggling_habits = [h for h in habits if h["active"] and h["completion_rate"] < 50]
    if struggling_habits:
        habit_names = [f"'{h['name']}'" for h in struggling_habits[:3]]  # Show up to 3
        if len(struggling_habits) == 1:
            insights.append(f"💪 {habit_names[0]} could use more attention (below 50% completion)")
        else:
            names_str = ", ".join(habit_names)
            insights.append(f"💪 These habits could use more attention: {names_str}")
    
    # Overall performance assessment
    avg_rate = summary["average_completion_rate"]
    if avg_rate >= 80:
        insights.append("🎉 Excellent overall performance! You're crushing your goals!")
    elif avg_rate >= 60:
        insights.append("👍 Solid performance across your habits. Keep up the momentum!")
    elif avg_rate >= 40:
        insights.append("📈 Room for improvement. Focus on consistency with your most important habits.")
    else:
        insights.append("🌱 Building habits takes time. Start with just one habit and be consistent.")
    
    # Active vs total habits
    if summary["active_habits"] < summary["total_habits"]:
        archived_count = summary["total_habits"] - summary["active_habits"]
        insights.append(f"📦 You have {archived_count} archived habit{'s' if archived_count != 1 else ''}. Consider using 'habits restore' if you want to restart any.")
    
    # Display insights
    for insight in insights:
        console.print(f"• {insight}")
    
    # Suggestions
    if summary["active_habits"] > 0:
        console.print(f"\n[dim]💡 Use 'habits today' to see today's progress or 'habits stats --habit \"[habit_name]\"' for detailed habit analysis.[/dim]")


def show_chart(
    habit_name: str = typer.Argument(
        ...,
        help="Name of the habit to chart"
    ),
    period: str = typer.Option(
        "month",
        "--period",
        "-p",
        help="Time period: week (last 7 days), month (last 30 days), year (last 365 days)",
        show_default=True
    ),
    style: str = typer.Option(
        "calendar",
        "--style",
        "-s", 
        help="Chart style: calendar (calendar view), heatmap (GitHub-style), simple (basic symbols)",
        show_default=True
    )
) -> None:
    """Display visual chart for a habit's completion pattern.
    
    Generate beautiful ASCII charts showing habit completion patterns over time.
    Choose from calendar view, GitHub-style heatmap, or simple symbol display.
    
    Examples:
        habits chart "Exercise"                    # Monthly calendar view
        habits chart "Reading" --period week       # Weekly view  
        habits chart "Meditation" --style heatmap  # GitHub-style heatmap
        habits chart "Gym" -p year -s calendar     # Yearly calendar view
    """
    
    # Validate period
    valid_periods = ["week", "month", "year"]
    if period not in valid_periods:
        console.print(create_error_panel(
            "Invalid Period",
            f"Period '{period}' is not valid",
            f"Valid periods: {', '.join(valid_periods)}\n" +
            "• week: last 7 days\n" +
            "• month: last 30 days\n" +
            "• year: last 365 days"
        ))
        raise typer.Exit(1)
    
    # Validate style
    valid_styles = ["calendar", "heatmap", "simple"]
    if style not in valid_styles:
        console.print(create_error_panel(
            "Invalid Style",
            f"Style '{style}' is not valid",
            f"Valid styles: {', '.join(valid_styles)}\n" +
            "• calendar: calendar grid view\n" +
            "• heatmap: GitHub-style contribution graph\n" +
            "• simple: basic completion symbols"
        ))
        raise typer.Exit(1)
    
    # Get chart data
    chart_data = VisualizationService.get_chart_data(habit_name, period, style)
    
    if not chart_data:
        console.print(create_error_panel(
            "Habit Not Found",
            f"Habit '{habit_name}' not found",
            "Use 'habits list --filter all' to see all available habits"
        ))
        raise typer.Exit(1)
    
    # Generate appropriate chart
    try:
        if style == "heatmap":
            chart_output = VisualizationService.generate_heatmap_chart(chart_data)
        else:  # calendar or simple
            chart_output = VisualizationService.generate_calendar_chart(chart_data, style)
        
        console.print(f"\n{chart_output}")
        
        # Add trend analysis for longer periods
        if period in ["month", "year"] and len(chart_data.data_points) >= 7:
            console.print(f"\n{VisualizationService.generate_trend_analysis(chart_data)}")
        
    except Exception as e:
        console.print(create_error_panel(
            "Chart Generation Error",
            f"Failed to generate chart: {str(e)}",
            "Please try again or use a different style"
        ))
        raise typer.Exit(1)


def show_progress(
    period: str = typer.Option(
        "month",
        "--period",
        "-p",
        help="Time period: week (last 7 days), month (last 30 days), year (last 365 days)",
        show_default=True
    ),
    habits: Optional[str] = typer.Option(
        None,
        "--habits",
        "-h",
        help="Comma-separated list of specific habits (leave blank for all active habits)"
    ),
    all_habits: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Include archived habits in the progress view"
    )
) -> None:
    """Display progress bars for habit completion rates.
    
    Show visual progress bars comparing completion rates across multiple habits.
    Includes streak indicators, trend analysis, and performance insights.
    
    Examples:
        habits progress                                    # All active habits, monthly view
        habits progress --period week                      # Weekly progress for all habits
        habits progress --habits "Exercise,Reading"        # Specific habits only
        habits progress --all --period year                # All habits including archived, yearly view
    """
    
    # Validate period
    valid_periods = ["week", "month", "year"]
    if period not in valid_periods:
        console.print(create_error_panel(
            "Invalid Period",
            f"Period '{period}' is not valid",
            f"Valid periods: {', '.join(valid_periods)}\n" +
            "• week: last 7 days\n" +
            "• month: last 30 days\n" +
            "• year: last 365 days"
        ))
        raise typer.Exit(1)
    
    # Parse habit names if provided
    habit_names = None
    if habits:
        habit_names = [name.strip() for name in habits.split(",") if name.strip()]
    
    try:
        # Get progress data
        if all_habits:
            # For all habits, we'll need to modify the service method to include archived
            # For now, use the existing method and filter later if needed
            progress_data = VisualizationService.get_multiple_habits_progress_data(period, habit_names)
        else:
            progress_data = VisualizationService.get_multiple_habits_progress_data(period, habit_names)
        
        if not progress_data:
            message = "No habits found"
            if habit_names:
                message = f"No matching habits found: {', '.join(habit_names)}"
            elif not all_habits:
                message = "No active habits found"
            
            console.print(create_info_panel(
                "No Data Available",
                message,
                "Use 'habits add' to create habits or 'habits list --filter all' to see all habits"
            ))
            return
        
        # Generate progress visualization
        progress_output = VisualizationService.generate_progress_bars(progress_data, period)
        console.print(f"\n{progress_output}")
        
        # Add performance insights for multiple habits
        if len(progress_data) > 1:
            _show_progress_insights(progress_data, period)
        
    except Exception as e:
        console.print(create_error_panel(
            "Progress Generation Error", 
            f"Failed to generate progress visualization: {str(e)}",
            "Please try again with different parameters"
        ))
        raise typer.Exit(1)


def generate_report(
    format_type: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Report format: table (console table), json (JSON output), csv (CSV format), markdown (Markdown format)",
        show_default=True
    ),
    output: Optional[str] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (prints to console if not specified)"
    ),
    period: str = typer.Option(
        "month",
        "--period",
        "-p",
        help="Time period: week, month, year, all",
        show_default=True
    ),
    habits: Optional[str] = typer.Option(
        None,
        "--habits",
        "-h",
        help="Comma-separated list of specific habits (leave blank for all habits)"
    ),
    include_archived: bool = typer.Option(
        False,
        "--include-archived",
        help="Include archived habits in the report"
    )
) -> None:
    """Generate comprehensive habit reports in multiple formats.
    
    Create detailed reports with analytics, trends, and insights. Export to
    various formats including JSON, CSV, and Markdown for external analysis.
    
    Examples:
        habits report                                      # Console table format
        habits report --format json --output report.json  # Export JSON report
        habits report --format csv --period year           # Yearly CSV report
        habits report --habits "Exercise,Reading" -f md    # Markdown for specific habits
    """
    
    # Validate format
    valid_formats = ["table", "json", "csv", "markdown", "md"]
    if format_type not in valid_formats:
        console.print(create_error_panel(
            "Invalid Format",
            f"Format '{format_type}' is not valid",
            f"Valid formats: {', '.join(valid_formats)}\n" +
            "• table: console table (default)\n" +
            "• json: JSON format\n" +
            "• csv: CSV format\n" +
            "• markdown/md: Markdown format"
        ))
        raise typer.Exit(1)
    
    # Validate period
    valid_periods = ["week", "month", "year", "all"]
    if period not in valid_periods:
        console.print(create_error_panel(
            "Invalid Period",
            f"Period '{period}' is not valid",
            f"Valid periods: {', '.join(valid_periods)}"
        ))
        raise typer.Exit(1)
    
    # Parse habit names if provided
    habit_names = None
    if habits:
        habit_names = [name.strip() for name in habits.split(",") if name.strip()]
    
    try:
        # Generate report data
        report_data = _generate_report_data(period, habit_names, include_archived)
        
        if not report_data["habits"]:
            console.print(create_info_panel(
                "No Data Available",
                "No habits found for report generation",
                "Use 'habits add' to create habits or adjust your filters"
            ))
            return
        
        # Format report based on type
        if format_type == "json":
            report_content = _format_json_report(report_data)
        elif format_type == "csv":
            report_content = _format_csv_report(report_data)
        elif format_type in ["markdown", "md"]:
            report_content = _format_markdown_report(report_data)
        else:  # table
            _display_table_report(report_data)
            return
        
        # Output to file or console
        if output:
            try:
                with open(output, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                console.print(create_success_panel(
                    "Report Generated",
                    f"Report saved to '{output}'",
                    f"Format: {format_type.upper()}"
                ))
            except Exception as e:
                console.print(create_error_panel(
                    "File Write Error",
                    f"Failed to write report to '{output}': {str(e)}",
                    "Check file permissions and path"
                ))
                raise typer.Exit(1)
        else:
            console.print(f"\n{report_content}")
    
    except Exception as e:
        console.print(create_error_panel(
            "Report Generation Error",
            f"Failed to generate report: {str(e)}",
            "Please try again with different parameters"
        ))
        raise typer.Exit(1)


def _show_progress_insights(progress_data: List[Dict[str, Any]], period: str) -> None:
    """Show additional insights for progress visualization."""
    
    console.print(f"\n[bold]🔍 Progress Insights - {period.title()}[/bold]\n")
    
    # Performance categories
    high_performers = [h for h in progress_data if h["completion_rate"] >= 80]
    struggling = [h for h in progress_data if h["completion_rate"] < 50]
    streak_leaders = sorted(progress_data, key=lambda x: x["current_streak"], reverse=True)[:3]
    
    insights = []
    
    if high_performers:
        names = [f"'{h['name']}'" for h in high_performers[:3]]
        insights.append(f"🏆 Top performers: {', '.join(names)}")
    
    if struggling:
        names = [f"'{h['name']}'" for h in struggling[:2]]
        insights.append(f"💪 Need attention: {', '.join(names)}")
    
    if streak_leaders[0]["current_streak"] > 0:
        leader = streak_leaders[0]
        insights.append(f"🔥 Streak leader: '{leader['name']}' ({leader['current_streak']} days)")
    
    # Overall assessment
    avg_rate = sum(h["completion_rate"] for h in progress_data) / len(progress_data)
    if avg_rate >= 75:
        insights.append("🎉 Excellent overall consistency across habits!")
    elif avg_rate >= 60:
        insights.append("👍 Good overall progress with room for optimization")
    else:
        insights.append("📈 Focus on building consistency with fewer habits")
    
    for insight in insights:
        console.print(f"• {insight}")
    
    console.print(f"\n[dim]💡 Use 'habits chart [habit_name]' for detailed visual analysis of individual habits.[/dim]")


def _generate_report_data(
    period: str,
    habit_names: Optional[List[str]] = None,
    include_archived: bool = False
) -> Dict[str, Any]:
    """Generate comprehensive report data."""
    
    # Get overall statistics
    overall_stats = AnalyticsService.calculate_overall_stats(period)
    
    if not overall_stats["success"]:
        raise Exception("Failed to calculate overall statistics")
    
    # Filter habits if specific names provided
    habits_data = overall_stats["habits"]
    if habit_names:
        habits_data = [h for h in habits_data if h["name"] in habit_names]
    
    if not include_archived:
        habits_data = [h for h in habits_data if h["active"]]
    
    # Get additional analytics for each habit
    enhanced_habits = []
    for habit in habits_data:
        habit_stats = AnalyticsService.calculate_habit_stats(habit["name"], period)
        if habit_stats["success"]:
            enhanced_habit = {
                **habit,
                "created_at": habit_stats["statistics"]["created_at"],
                "longest_streak": habit_stats["statistics"]["longest_streak"]
            }
            enhanced_habits.append(enhanced_habit)
    
    return {
        "period": period,
        "generated_at": format_date(AnalyticsService.get_today() if hasattr(AnalyticsService, 'get_today') else date.today()),
        "summary": overall_stats["summary"],
        "habits": enhanced_habits
    }


def _format_json_report(report_data: Dict[str, Any]) -> str:
    """Format report as JSON."""
    import json
    return json.dumps(report_data, indent=2, default=str)


def _format_csv_report(report_data: Dict[str, Any]) -> str:
    """Format report as CSV."""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Habit Name", "Status", "Completion Rate %", "Total Completions", 
        "Current Streak", "Longest Streak", "Created Date"
    ])
    
    # Data rows
    for habit in report_data["habits"]:
        writer.writerow([
            habit["name"],
            "Active" if habit["active"] else "Archived",
            habit["completion_rate"],
            habit["completions"],
            habit["current_streak"],
            habit.get("longest_streak", 0),
            habit.get("created_at", "Unknown")
        ])
    
    return output.getvalue()


def _format_markdown_report(report_data: Dict[str, Any]) -> str:
    """Format report as Markdown."""
    
    lines = []
    lines.append(f"# Habits Report - {report_data['period'].title()}")
    lines.append(f"*Generated on {report_data['generated_at']}*")
    lines.append("")
    
    # Summary
    summary = report_data["summary"]
    lines.append("## Summary")
    lines.append(f"- **Total Habits:** {summary['total_habits']}")
    lines.append(f"- **Active Habits:** {summary['active_habits']}")
    lines.append(f"- **Total Completions:** {summary['total_completions']}")
    lines.append(f"- **Average Completion Rate:** {summary['average_completion_rate']}%")
    lines.append("")
    
    # Habits table
    lines.append("## Habit Details")
    lines.append("")
    lines.append("| Habit | Status | Completion Rate | Total Completions | Current Streak | Longest Streak |")
    lines.append("|-------|--------|-----------------|-------------------|----------------|----------------|")
    
    for habit in report_data["habits"]:
        status = "✅ Active" if habit["active"] else "📦 Archived"
        lines.append(
            f"| {habit['name']} | {status} | {habit['completion_rate']}% | "
            f"{habit['completions']} | {habit['current_streak']} | {habit.get('longest_streak', 0)} |"
        )
    
    return "\n".join(lines)


def _display_table_report(report_data: Dict[str, Any]) -> None:
    """Display report as console table."""
    
    # Summary panel
    summary = report_data["summary"]
    summary_content = f"""[bold]📊 Report Summary - {report_data['period'].title()}[/bold]
Generated: {report_data['generated_at']}

[bold]Overview:[/bold]
• Total Habits: {summary['total_habits']}
• Active Habits: {summary['active_habits']}
• Total Completions: {summary['total_completions']}
• Average Completion Rate: {summary['average_completion_rate']}%"""
    
    console.print(Panel(
        summary_content,
        title="📈 Comprehensive Habit Report",
        border_style="blue"
    ))
    
    # Detailed table
    if report_data["habits"]:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Habit", style="cyan", min_width=20)
        table.add_column("Status", justify="center", min_width=8)
        table.add_column("Rate", justify="center", min_width=8)
        table.add_column("Completions", justify="center", min_width=12)
        table.add_column("Current Streak", justify="center", min_width=14)
        table.add_column("Best Streak", justify="center", min_width=12)
        table.add_column("Created", justify="center", min_width=12)
        
        for habit in sorted(report_data["habits"], key=lambda x: x["completion_rate"], reverse=True):
            status = "✅" if habit["active"] else "📦"
            
            # Color-coded completion rate
            rate = habit["completion_rate"]
            if rate >= 75:
                rate_display = f"[green]{rate}%[/green]"
            elif rate >= 50:
                rate_display = f"[yellow]{rate}%[/yellow]"
            else:
                rate_display = f"[red]{rate}%[/red]"
            
            # Streak formatting
            current_streak = habit["current_streak"]
            streak_display = f"🔥 {current_streak}" if current_streak > 0 else "0"
            
            longest_streak = habit.get("longest_streak", 0)
            best_display = f"🏆 {longest_streak}" if longest_streak > 0 else "0"
            
            created_date = habit.get("created_at", "Unknown")
            if hasattr(created_date, 'strftime'):
                created_display = created_date.strftime("%Y-%m-%d")
            else:
                created_display = str(created_date)
            
            table.add_row(
                habit["name"],
                status,
                rate_display,
                str(habit["completions"]),
                streak_display,
                best_display,
                created_display
            )
        
        console.print(f"\n[bold]📋 Detailed Habit Analysis[/bold]\n")
        console.print(table)