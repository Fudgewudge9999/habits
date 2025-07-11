# 🎯 HabitsTracker CLI

A lightweight, fast, and intuitive command-line habit tracker designed specifically for macOS. Perfect for developers and power users who prefer terminal interfaces over GUI applications.

![HabitsTracker CLI Demo](https://via.placeholder.com/800x400/1a1a1a/00d4aa?text=HabitsTracker+CLI+Demo)

## ✨ Features

- **⚡ Lightning Fast**: All commands execute in under 100ms
- **🍎 macOS Native**: Optimized for macOS with native notifications and file system integration
- **🎨 Beautiful Output**: Rich terminal UI with colors, tables, and progress indicators
- **📊 Smart Analytics**: Track streaks, completion rates, and progress over time
- **🔒 Privacy First**: All data stored locally in SQLite database
- **💾 Minimal Footprint**: Under 50MB memory usage, minimal dependencies
- **🧪 Well Tested**: >90% test coverage with comprehensive error handling

## 🚀 Quick Start

### Installation

**Requirements**: macOS 10.15+ (Catalina or newer), Python 3.9+

#### Via pip (Recommended)
```bash
pip install habits-tracker
```

#### Via Homebrew (Coming Soon)
```bash
brew install habits-tracker
```

#### From Source
```bash
git clone https://github.com/habitstracker/habits-tracker.git
cd habits-tracker
pip install -e .
```

### Your First Habit

```bash
# Add your first habit
habits add "Exercise" --frequency daily --description "30 minutes of exercise"

# Track it for today
habits track "Exercise"

# See your progress
habits today
habits stats
```

## 📖 Usage Guide

### 🎯 Managing Habits

#### Add a New Habit
```bash
# Basic habit
habits add "Read"

# With frequency and description
habits add "Meditate" --frequency daily --description "10 minutes mindfulness"

# Short form
habits add "Gym" -f weekly -d "Strength training session"
```

#### List Your Habits
```bash
# Show active habits
habits list

# Show all habits (including archived)
habits list --filter all

# Show only archived habits
habits list --filter archived
```

#### Remove or Delete Habits
```bash
# Soft delete (archive) - can be restored
habits remove "Exercise"

# Restore an archived habit
habits restore "Exercise"

# Permanently delete (requires confirmation)
habits delete "Exercise" --confirm
```

### 📅 Tracking Progress

#### Track Habits
```bash
# Track for today
habits track "Exercise"

# Track for a specific date
habits track "Exercise" --date 2024-07-10
habits track "Exercise" --date yesterday
habits track "Exercise" --date -1d

# Track with notes
habits track "Exercise" --note "Great 5k run in the park!"
```

#### Untrack Habits
```bash
# Remove today's tracking
habits untrack "Exercise"

# Remove tracking for specific date
habits untrack "Exercise" --date 2024-07-10
```

#### Daily Overview
```bash
# See today's habits and completion status
habits today
```

### 📊 Analytics & Progress

#### View Statistics
```bash
# Overall statistics for all habits
habits stats

# Statistics for a specific habit
habits stats --habit "Exercise"

# Statistics for a time period
habits stats --period week
habits stats --period month
habits stats --period year
habits stats --period all
```

### 🔧 Advanced Features

#### Performance Monitoring
```bash
# Profile command performance
habits profile

# Run performance benchmarks
habits benchmark

# Analyze database performance
habits db-analyze

# Check memory usage
habits memory
```

## 🎨 Example Workflows

### Morning Routine Setup
```bash
# Set up your morning habits
habits add "Exercise" -f daily -d "30 min workout"
habits add "Meditate" -f daily -d "10 min mindfulness"
habits add "Journal" -f daily -d "Gratitude journaling"
habits add "Read" -f daily -d "Read for 20 minutes"

# Track your morning routine
habits track "Exercise" --note "Great yoga session"
habits track "Meditate" --note "Felt very focused"
habits track "Journal"
habits track "Read" --note "Finished chapter 3"

# Check your progress
habits today
habits stats --period week
```

### Weekly Review
```bash
# Review your weekly progress
habits stats --period week

# Check specific habits that need attention
habits stats --habit "Exercise" --period week
habits stats --habit "Reading" --period week

# See overall trends
habits stats --period month
```

### Data Management
```bash
# View all habits (active and archived)
habits list --filter all

# Clean up old habits you no longer track
habits remove "Old Habit"

# Restore a habit you want to start again
habits restore "Yoga"
```

## 🎯 Command Reference

### Habit Management
| Command | Description | Options |
|---------|-------------|---------|
| `habits add <name>` | Add a new habit | `--frequency`, `--description` |
| `habits list` | List habits | `--filter` (active/archived/all) |
| `habits remove <name>` | Archive a habit | - |
| `habits delete <name>` | Permanently delete | `--confirm` |
| `habits restore <name>` | Restore archived habit | - |

### Tracking
| Command | Description | Options |
|---------|-------------|---------|
| `habits track <name>` | Track habit completion | `--date`, `--note` |
| `habits untrack <name>` | Remove tracking entry | `--date` |
| `habits today` | Show today's progress | - |

### Analytics
| Command | Description | Options |
|---------|-------------|---------|
| `habits stats` | Show statistics | `--habit`, `--period` |

### Performance
| Command | Description | Purpose |
|---------|-------------|---------|
| `habits profile` | Profile performance | Development/debugging |
| `habits benchmark` | Run benchmarks | Performance testing |
| `habits db-analyze` | Database analysis | Optimization |
| `habits memory` | Memory usage report | Resource monitoring |

## 🎨 Output Examples

### Beautiful Terminal Output
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                        📋 Your Habits                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌────────────┬──────────┬─────────┬───────────┬─────────────────┐
│ Habit      │ Status   │ Streak  │ Frequency │ Description     │
├────────────┼──────────┼─────────┼───────────┼─────────────────┤
│ Exercise   │ ✅ Active │ 🔥 7d   │ daily     │ 30 min workout  │
│ Read       │ ✅ Active │ ⭐ 15d  │ daily     │ Read for 20 min │
│ Meditate   │ ✅ Active │ 🏆 30d  │ daily     │ 10 min mindful  │
└────────────┴──────────┴─────────┴───────────┴─────────────────┘
```

### Today's Progress
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
```

### Statistics Overview
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

🎉 Excellent! You're in the top 20% of performers
💪 Keep up the momentum - you're on a great streak!
```

## ⚙️ Configuration

### Data Storage
- **Database**: `~/.habits/habits.db` (SQLite)
- **Config**: `~/.config/habits/` (follows macOS conventions)
- **Backups**: Automatic backup before schema migrations

### File Permissions
The application automatically sets secure file permissions (0600) on your database to ensure privacy.

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `HABITS_DB_PATH` | Custom database location | `~/.habits/habits.db` |
| `HABITS_DEBUG` | Enable debug logging | `false` |

## 🔧 Development

### Setup Development Environment
```bash
# Clone the repository
git clone https://github.com/habitstracker/habits-tracker.git
cd habits-tracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=habits_tracker --cov-report=html
```

### Code Quality Tools
```bash
# Format code
black habits_tracker/ tests/

# Type checking
mypy habits_tracker/

# Linting
ruff habits_tracker/ tests/

# Run all checks
black . && mypy habits_tracker/ && ruff . && pytest
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest`)
6. Run code quality checks (`black . && mypy habits_tracker/ && ruff .`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

## 📊 Performance

HabitsTracker CLI is optimized for speed and efficiency:

- **Command Execution**: All commands complete in <100ms
- **Memory Usage**: <50MB during operation
- **Database**: Optimized for up to 10,000 tracking entries
- **Startup Time**: Minimal CLI startup overhead

## 🔒 Privacy & Security

- **Local Storage**: All data stored locally on your Mac
- **No Cloud Sync**: No data transmitted to external servers
- **Secure Permissions**: Database files protected with 0600 permissions
- **No Telemetry**: No usage tracking or analytics collection

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for the CLI framework
- Styled with [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- Data persistence with [SQLAlchemy](https://www.sqlalchemy.org/) and SQLite
- Inspired by the productivity and habit-tracking community

## 📞 Support

- **Documentation**: [habitstracker.readthedocs.io](https://habitstracker.readthedocs.io)
- **Issues**: [GitHub Issues](https://github.com/habitstracker/habits-tracker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/habitstracker/habits-tracker/discussions)

---

**Happy habit building! 🎯**

*Made with ❤️ for productivity enthusiasts and terminal lovers*