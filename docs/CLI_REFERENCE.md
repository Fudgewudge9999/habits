# 📚 HabitsTracker CLI Command Reference

Complete reference guide for all HabitsTracker CLI commands, options, and usage patterns.

## 🏁 Getting Started

### Basic Command Structure
```bash
habits <command> [arguments] [options]
```

### Global Options
| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-v` | Show version information |
| `--debug` | | Enable debug mode with detailed logging |
| `--help` | | Show help for any command |

### Getting Help
```bash
# General help
habits --help

# Command-specific help
habits add --help
habits track --help
habits stats --help
```

## 🎯 Habit Management Commands

### `habits add` - Create New Habits

Add a new habit to your tracking system.

**Syntax:**
```bash
habits add <name> [options]
```

**Arguments:**
- `name` (required): Name of the habit to add

**Options:**
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--frequency` | `-f` | string | `daily` | Habit frequency (daily, weekly, custom) |
| `--description` | `-d` | string | None | Optional description (max 500 chars) |

**Examples:**
```bash
# Basic habit
habits add "Exercise"

# With frequency
habits add "Gym" --frequency weekly

# With description
habits add "Read" --description "Read for 30 minutes each day"

# Using short options
habits add "Meditate" -f daily -d "10 minutes mindfulness practice"

# Complex habit
habits add "Learn Python" -f daily -d "Study Python for 1 hour - focus on data structures"
```

**Behavior:**
- If a habit with the same name was previously archived, it will be restored instead of creating a duplicate
- Habit names must be unique (case-insensitive)
- Names are limited to 100 characters
- Descriptions are limited to 500 characters
- Invalid frequencies will show available options

**Success Output:**
```
✅ Habit 'Exercise' added successfully!
🎯 Track it today with: habits track "Exercise"
```

---

### `habits list` - View Your Habits

Display all habits with their status, streaks, and details.

**Syntax:**
```bash
habits list [options]
```

**Options:**
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--filter` | | string | `active` | Filter habits: active, archived, all |

**Examples:**
```bash
# Show active habits (default)
habits list

# Show all habits
habits list --filter all

# Show only archived habits
habits list --filter archived
```

**Output Format:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                        📋 Your Habits                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌────────────┬──────────┬─────────┬───────────┬─────────────────┐
│ Habit      │ Status   │ Streak  │ Frequency │ Description     │
├────────────┼──────────┼─────────┼───────────┼─────────────────┤
│ Exercise   │ ✅ Active │ 🔥 7d   │ daily     │ 30 min workout  │
│ Read       │ ✅ Active │ ⭐ 15d  │ daily     │ Read for 20 min │
│ Meditate   │ 📦 Archived │ 🏆 30d  │ daily     │ 10 min mindful  │
└────────────┴──────────┴─────────┴───────────┴─────────────────┘
```

**Streak Icons:**
- 🔥 1-14 days: Building momentum
- ⭐ 15-29 days: Strong habit forming
- 🏆 30+ days: Mastery level

---

### `habits remove` - Archive Habits

Soft delete (archive) a habit. Can be restored later.

**Syntax:**
```bash
habits remove <name>
```

**Arguments:**
- `name` (required): Name of the habit to archive

**Examples:**
```bash
habits remove "Exercise"
habits remove "Old Habit I Don't Do Anymore"
```

**Behavior:**
- Habit is archived, not permanently deleted
- Tracking history is preserved
- Archived habits don't appear in default list view
- Can be restored with `habits restore`

**Success Output:**
```
📦 Habit 'Exercise' has been archived
💡 Restore it anytime with: habits restore "Exercise"
```

---

### `habits restore` - Restore Archived Habits

Restore a previously archived habit back to active status.

**Syntax:**
```bash
habits restore <name>
```

**Arguments:**
- `name` (required): Name of the archived habit to restore

**Examples:**
```bash
habits restore "Exercise"
habits restore "Meditation"
```

**Behavior:**
- Only works on archived habits
- Restores habit to active status
- All tracking history is preserved
- Habit appears in default list view again

**Success Output:**
```
✅ Habit 'Exercise' has been restored!
🎯 Track it today with: habits track "Exercise"
```

---

### `habits delete` - Permanently Delete Habits

Permanently delete a habit and all its tracking data. **This cannot be undone.**

**Syntax:**
```bash
habits delete <name> --confirm
```

**Arguments:**
- `name` (required): Name of the habit to delete

**Options:**
| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--confirm` | flag | Yes | Required confirmation for safety |

**Examples:**
```bash
habits delete "Old Habit" --confirm
```

**Behavior:**
- Requires `--confirm` flag for safety
- Shows confirmation prompt before deletion
- Permanently removes habit and all tracking entries
- **Cannot be undone** - use `habits remove` for reversible archiving

**Confirmation Prompt:**
```
⚠️  WARNING: This will permanently delete 'Old Habit' and ALL tracking data.
This action cannot be undone.

Are you absolutely sure? (y/N):
```

---

## 📅 Tracking Commands

### `habits track` - Record Habit Completion

Mark a habit as completed for a specific date.

**Syntax:**
```bash
habits track <name> [options]
```

**Arguments:**
- `name` (required): Name of the habit to track

**Options:**
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--date` | | string | today | Date to track (flexible formats) |
| `--note` | | string | None | Optional note (max 500 chars) |

**Date Formats:**
- `today` (default)
- `yesterday`
- `YYYY-MM-DD` (e.g., `2024-07-10`)
- Relative: `-1d`, `-2d`, `-7d` (days ago)
- `YYYY-MM-DD` format

**Examples:**
```bash
# Track for today (default)
habits track "Exercise"

# Track for yesterday
habits track "Exercise" --date yesterday

# Track for specific date
habits track "Exercise" --date 2024-07-10

# Track with relative date
habits track "Exercise" --date -1d

# Track with note
habits track "Exercise" --note "Great 5k run in the park!"

# Track past date with note
habits track "Read" --date yesterday --note "Finished chapter 3 of Python book"
```

**Behavior:**
- Only one tracking entry per habit per date
- Attempting to track the same habit/date shows existing entry
- Notes are optional but helpful for reflection
- Updates existing entry if tracking same date again

**Success Output:**
```
✅ 'Exercise' tracked for today!
🔥 Current streak: 7 days
📝 Note: Great 5k run in the park!
```

---

### `habits untrack` - Remove Tracking Entry

Remove a tracking entry for a specific date.

**Syntax:**
```bash
habits untrack <name> [options]
```

**Arguments:**
- `name` (required): Name of the habit to untrack

**Options:**
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--date` | | string | today | Date to untrack (same formats as track) |

**Examples:**
```bash
# Untrack today (default)
habits untrack "Exercise"

# Untrack specific date
habits untrack "Exercise" --date 2024-07-10

# Untrack yesterday
habits untrack "Exercise" --date yesterday
```

**Behavior:**
- Removes tracking entry for specified date
- Affects streak calculations
- Shows confirmation of removal

**Success Output:**
```
🗑️  Tracking removed for 'Exercise' on today
📊 Updated streak: 6 days
```

---

### `habits today` - Daily Overview

Show today's habits and completion status.

**Syntax:**
```bash
habits today
```

**No options or arguments.**

**Example Output:**
```
🌅 Today's Habits - Friday, July 11, 2024

┌────────────┬────────┬─────────────────────────┐
│ Habit      │ Status │ Notes                   │
├────────────┼────────┼─────────────────────────┤
│ Exercise   │ ✅ Done │ Great 5k run            │
│ Read       │ ✅ Done │ Finished chapter 3      │
│ Meditate   │ ⏳ Todo │                         │
│ Journal    │ ⏳ Todo │                         │
└────────────┴────────┴─────────────────────────┘

📊 Progress: 2/4 completed (50%)
🎯 Keep going! You're doing great!

💡 Track remaining habits:
   habits track "Meditate"
   habits track "Journal"
```

**Behavior:**
- Shows only active habits
- Displays completion status for today
- Shows notes if present
- Provides helpful next-step suggestions
- Updates in real-time as you track habits

---

## 📊 Analytics Commands

### `habits stats` - View Statistics

Display detailed statistics and analytics for your habits.

**Syntax:**
```bash
habits stats [options]
```

**Options:**
| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--habit` | | string | None | Show stats for specific habit |
| `--period` | | string | `all` | Time period: week, month, year, all |

**Period Options:**
- `week`: Last 7 days
- `month`: Last 30 days  
- `year`: Last 365 days
- `all`: All-time statistics (default)

**Examples:**
```bash
# Overall statistics for all habits
habits stats

# Statistics for specific habit
habits stats --habit "Exercise"

# Weekly overview
habits stats --period week

# Monthly review for specific habit
habits stats --habit "Read" --period month

# Yearly summary
habits stats --period year
```

**Overall Statistics Output:**
```
📊 Overall Habit Statistics - All Time

┌─────────────────┬─────────┐
│ Metric          │ Value   │
├─────────────────┼─────────┤
│ Active Habits   │ 4       │
│ Total Entries   │ 156     │
│ Avg Success     │ 78.5%   │
│ Best Streak     │ 🏆 45d  │
│ Active Streaks  │ 3       │
└─────────────────┴─────────┘

🏆 Top Performers:
┌────────────┬─────────┬─────────────┐
│ Habit      │ Success │ Current     │
├────────────┼─────────┼─────────────┤
│ Meditate   │ 92.3%   │ 🏆 30d      │
│ Read       │ 85.7%   │ ⭐ 15d      │
│ Exercise   │ 78.9%   │ 🔥 7d       │
│ Journal    │ 65.4%   │ 🔥 3d       │
└────────────┴─────────┴─────────────┘
```

**Individual Habit Statistics:**
```bash
habits stats --habit "Exercise"
```

```
📊 Habit Statistics - Exercise

┌─────────────────┬─────────┐
│ Metric          │ Value   │
├─────────────────┼─────────┤
│ Current Streak  │ 🔥 7d   │
│ Longest Streak  │ 🏆 21d  │
│ This Week       │ 6/7     │
│ This Month      │ 28/31   │
│ All Time        │ 145/180 │
│ Success Rate    │ 80.6%   │
└─────────────────┴─────────┘

📈 Recent Activity:
┌────────────┬────────┬─────────────────────────┐
│ Date       │ Status │ Notes                   │
├────────────┼────────┼─────────────────────────┤
│ 2024-07-11 │ ✅     │ Great 5k run            │
│ 2024-07-10 │ ✅     │ Gym session             │
│ 2024-07-09 │ ✅     │ Morning yoga            │
│ 2024-07-08 │ ✅     │ Swimming                │
│ 2024-07-07 │ ❌     │                         │
└────────────┴────────┴─────────────────────────┘

🎉 Excellent! You're in the top 20% of performers
💪 Keep up the momentum - you're on a great streak!
```

---

## 🔧 Performance Commands

### `habits profile` - Performance Profiling

Profile command execution times for performance analysis.

**Syntax:**
```bash
habits profile
```

**Example Output:**
```
⚡ Performance Profile

Command Execution Times:
┌──────────────┬─────────────┬────────────┐
│ Command      │ Avg Time    │ Status     │
├──────────────┼─────────────┼────────────┤
│ habits list  │ 23.4ms      │ ✅ Optimal │
│ habits add   │ 31.2ms      │ ✅ Optimal │
│ habits track │ 18.7ms      │ ✅ Optimal │
│ habits stats │ 67.8ms      │ ✅ Good    │
└──────────────┴─────────────┴────────────┘

🎯 Target: <100ms ✅ All commands meeting performance goals
```

---

### `habits benchmark` - Performance Benchmarking

Run comprehensive performance benchmarks.

**Syntax:**
```bash
habits benchmark
```

**Example Output:**
```
🏁 Performance Benchmark Results

Database Operations:
┌─────────────────────┬─────────────┬─────────────┐
│ Operation           │ Time        │ Throughput  │
├─────────────────────┼─────────────┼─────────────┤
│ Create habit        │ 1.2ms       │ 833 ops/sec │
│ Track habit         │ 0.8ms       │ 1250 ops/sec│
│ List habits         │ 3.4ms       │ 294 ops/sec │
│ Calculate streaks   │ 12.1ms      │ 83 ops/sec  │
└─────────────────────┴─────────────┴─────────────┘

Memory Usage: 12.3MB
Database Size: 2.1MB
Cache Hit Rate: 94.7%
```

---

### `habits db-analyze` - Database Analysis

Analyze database performance and optimization opportunities.

**Syntax:**
```bash
habits db-analyze
```

**Example Output:**
```
🔍 Database Analysis Report

Database Information:
┌─────────────────┬─────────────┐
│ Metric          │ Value       │
├─────────────────┼─────────────┤
│ Database Size   │ 2.1MB       │
│ Total Records   │ 1,247       │
│ Habits          │ 12          │
│ Tracking Entries│ 1,235       │
│ Fragmentation   │ 3.2%        │
└─────────────────┴─────────────┘

Index Usage:
┌─────────────────────┬─────────────┬─────────────┐
│ Index               │ Usage       │ Efficiency  │
├─────────────────────┼─────────────┼─────────────┤
│ idx_habit_active    │ 94.7%       │ ✅ Optimal  │
│ idx_tracking_date   │ 89.3%       │ ✅ Good     │
│ idx_completed_date  │ 76.8%       │ ✅ Good     │
└─────────────────────┴─────────────┴─────────────┘

💡 All indexes performing well - no optimization needed
```

---

### `habits memory` - Memory Usage Report

Display current memory usage and optimization status.

**Syntax:**
```bash
habits memory
```

**Example Output:**
```
💾 Memory Usage Report

Current Usage:
┌─────────────────┬─────────────┐
│ Component       │ Memory      │
├─────────────────┼─────────────┤
│ Application     │ 8.2MB       │
│ Database Cache  │ 3.1MB       │
│ Query Cache     │ 1.4MB       │
│ Display Buffer  │ 0.8MB       │
│ Total           │ 13.5MB      │
└─────────────────┴─────────────┘

Cache Statistics:
┌─────────────────┬─────────────┐
│ Cache           │ Hit Rate    │
├─────────────────┼─────────────┤
│ Habits Cache    │ 96.8%       │
│ Stats Cache     │ 87.3%       │
│ Query Cache     │ 92.1%       │
└─────────────────┴─────────────┘

🎯 Memory usage: 13.5MB / 50MB target ✅ Excellent
```

---

## 🎨 Output Formatting

### Color Codes
- ✅ **Green**: Success, completion, active status
- ❌ **Red**: Errors, failures, warnings
- 📦 **Blue**: Archived items, information
- ⏳ **Yellow**: Pending, todo items
- 🔥 **Orange**: Streaks 1-14 days
- ⭐ **Blue**: Streaks 15-29 days  
- 🏆 **Gold**: Streaks 30+ days

### Status Indicators
- ✅ **Done**: Habit completed for the day
- ⏳ **Todo**: Habit not yet completed
- 📦 **Archived**: Habit is archived
- ❌ **Failed**: Tracking failed or missed

### Progress Indicators
- 🔥 **Building** (1-14 days): Early momentum
- ⭐ **Strong** (15-29 days): Habit forming
- 🏆 **Mastery** (30+ days): Established habit

---

## 💡 Tips and Best Practices

### Efficient Workflows
```bash
# Morning routine
habits today                    # Check today's habits
habits track "Exercise"         # Track as you complete
habits track "Meditate" --note "10 min focused session"

# Weekly review
habits stats --period week     # Review weekly performance
habits list --filter all       # See all habits including archived

# Monthly planning
habits stats --period month    # Monthly analysis
habits remove "Old Habit"      # Archive habits you don't do
habits add "New Habit"          # Add new habits for the month
```

### Date Shortcuts
```bash
# Quick date references
habits track "Exercise" --date yesterday
habits track "Read" --date -1d      # Same as yesterday
habits track "Gym" --date -7d       # One week ago
```

### Habit Organization
```bash
# Use descriptive names
habits add "Morning Exercise" -d "30 min cardio or strength"
habits add "Evening Reading" -d "Read fiction or non-fiction for 20 min"

# Group related habits
habits add "Morning Meditation" -d "10 min mindfulness"
habits add "Evening Reflection" -d "5 min gratitude journaling"
```

---

## 🚨 Error Messages and Troubleshooting

### Common Errors

**Habit Not Found:**
```
❌ Error: Habit 'Exercice' not found
💡 Did you mean 'Exercise'? Use 'habits list' to see all habits
```

**Already Tracked:**
```
⚠️  'Exercise' is already tracked for today
📊 Current entry: ✅ Done (Great workout!)
💡 Use 'habits untrack "Exercise"' to remove, then track again
```

**Invalid Date Format:**
```
❌ Error: Unable to parse date '2024-13-01'
💡 Use formats like: today, yesterday, -1d, or YYYY-MM-DD
```

**Database Issues:**
```
❌ Error: Database connection failed
💡 Try: Check ~/.habits/habits.db permissions or run with --debug
```

### Getting Help
```bash
# Command-specific help
habits <command> --help

# Enable debug mode for detailed errors
habits --debug <command>

# Check database status
habits db-analyze
```

---

## 📋 Quick Reference Card

### Essential Commands
```bash
habits add "Habit Name"           # Add new habit
habits list                       # View all habits
habits track "Habit"              # Track today
habits today                      # Today's overview
habits stats                      # View statistics
```

### Common Options
```bash
--date yesterday                  # Yesterday
--date -1d                        # 1 day ago
--note "Some note"               # Add note
--filter all                     # Show all habits
--period week                    # Weekly stats
```

### Keyboard Shortcuts in Terminal
- `Ctrl+C`: Cancel current command
- `Tab`: Auto-complete habit names (if supported by shell)
- `↑/↓`: Navigate command history
- `Ctrl+R`: Search command history

---

*For more detailed information, see the main [README.md](../README.md) file.*