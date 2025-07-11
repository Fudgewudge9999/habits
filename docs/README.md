# 📚 HabitsTracker CLI Documentation

Welcome to the comprehensive documentation for HabitsTracker CLI - a lightweight, fast, and intuitive command-line habit tracker designed specifically for macOS.

## 📖 Documentation Overview

### 🚀 Getting Started
- **[Main README](../README.md)** - Quick start guide, installation, and feature overview
- **[CLI Reference](CLI_REFERENCE.md)** - Complete command reference with all options and examples
- **[Usage Examples](USAGE_EXAMPLES.md)** - Real-world workflows, tips, and best practices

### 📋 Quick Navigation

| Document | Description | Best For |
|----------|-------------|----------|
| [README.md](../README.md) | Installation, features, quick start | New users, overview |
| [CLI_REFERENCE.md](CLI_REFERENCE.md) | Complete command documentation | Reference, troubleshooting |
| [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) | Workflows, examples, tips | Learning patterns, optimization |

## 🎯 Quick Start

1. **Install**: `pip install habits-tracker`
2. **Add a habit**: `habits add "Exercise"`
3. **Track it**: `habits track "Exercise"`
4. **Check progress**: `habits today`
5. **View stats**: `habits stats`

## 📚 Documentation Sections

### 🏁 Installation & Setup
- [Installation methods](../README.md#installation) (pip, Homebrew, source)
- [System requirements](../README.md#installation) (macOS 10.15+, Python 3.9+)
- [Configuration options](../README.md#configuration)

### 🎯 Core Features
- [Habit Management](CLI_REFERENCE.md#habit-management-commands) - Add, list, remove, restore habits
- [Tracking System](CLI_REFERENCE.md#tracking-commands) - Track progress, view daily status
- [Analytics](CLI_REFERENCE.md#analytics-commands) - Statistics, streaks, insights

### 💡 Usage Patterns
- [Daily Workflows](USAGE_EXAMPLES.md#daily-review-routine) - Morning/evening routines
- [Weekly Reviews](USAGE_EXAMPLES.md#weekly-deep-dive) - Progress analysis
- [Advanced Patterns](USAGE_EXAMPLES.md#advanced-tracking-patterns) - Power user techniques

### 🔧 Advanced Features
- [Performance Monitoring](CLI_REFERENCE.md#performance-commands) - Profile, benchmark, analyze
- [Data Management](USAGE_EXAMPLES.md#data-management) - Backup, migration, cleanup
- [Troubleshooting](CLI_REFERENCE.md#error-messages-and-troubleshooting) - Common issues, solutions

## 🎨 Command Categories

### Essential Commands
```bash
habits add "Exercise"           # Add new habit
habits list                     # View all habits  
habits track "Exercise"         # Track completion
habits today                    # Daily overview
habits stats                    # View statistics
```

### Management Commands
```bash
habits remove "Old Habit"      # Archive habit
habits restore "Old Habit"     # Restore archived habit
habits delete "Bad Habit" --confirm  # Permanent deletion
```

### Analytics Commands
```bash
habits stats --period week     # Weekly statistics
habits stats --habit "Exercise"  # Specific habit stats
habits stats --period month    # Monthly overview
```

### Performance Commands
```bash
habits profile                 # Performance profiling
habits benchmark               # Run benchmarks
habits db-analyze              # Database analysis
habits memory                  # Memory usage
```

## 🎯 Use Cases & Workflows

### 🌅 Morning Routine
Perfect for developers who want to track their daily habits alongside their coding workflow:
- [Morning Planning](USAGE_EXAMPLES.md#morning-routine-optimization)
- [Daily Development](USAGE_EXAMPLES.md#learning--development-tracking)
- [Evening Review](USAGE_EXAMPLES.md#daily-review-routine)

### 📊 Analytics & Insights
Track progress and optimize your habits:
- [Performance Analysis](USAGE_EXAMPLES.md#weekly-deep-dive)
- [Trend Identification](USAGE_EXAMPLES.md#monthly-optimization)
- [Goal Adjustment](USAGE_EXAMPLES.md#quarterly-planning)

### 🏃‍♀️ Fitness & Health
Build and maintain healthy lifestyle habits:
- [Fitness Tracking](USAGE_EXAMPLES.md#fitness--health-journey)
- [Wellness Monitoring](USAGE_EXAMPLES.md#mental-health--wellness)
- [Progress Measurement](USAGE_EXAMPLES.md#progress-tracking-tips)

### 🎨 Creative & Learning
Support creative work and skill development:
- [Learning Routines](USAGE_EXAMPLES.md#learning--development-tracking)
- [Creative Practice](USAGE_EXAMPLES.md#creative--personal-development)
- [Skill Building](USAGE_EXAMPLES.md#example-1-the-consistent-developer)

## 🔍 Finding What You Need

### I want to...
- **Learn the basics** → [README.md](../README.md)
- **See all commands** → [CLI_REFERENCE.md](CLI_REFERENCE.md)
- **Learn workflows** → [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
- **Troubleshoot issues** → [CLI_REFERENCE.md#error-messages-and-troubleshooting](CLI_REFERENCE.md#error-messages-and-troubleshooting)
- **Optimize performance** → [CLI_REFERENCE.md#performance-commands](CLI_REFERENCE.md#performance-commands)
- **See examples** → [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)

### Common Questions
- **How do I start?** → [Quick Start](../README.md#quick-start)
- **What commands are available?** → [Command Reference](CLI_REFERENCE.md#quick-reference-card)
- **How do I track habits efficiently?** → [Daily Workflows](USAGE_EXAMPLES.md#real-world-workflows)
- **How do I analyze my progress?** → [Analytics Examples](USAGE_EXAMPLES.md#analytics--review-workflows)
- **How do I fix errors?** → [Troubleshooting Guide](CLI_REFERENCE.md#error-messages-and-troubleshooting)

## 🎉 Success Stories

Learn from others who have built successful habits:
- [The Consistent Developer](USAGE_EXAMPLES.md#example-1-the-consistent-developer) - Daily coding practice
- [The Wellness Warrior](USAGE_EXAMPLES.md#example-2-the-wellness-warrior) - Health transformation
- [The Creative Professional](USAGE_EXAMPLES.md#example-3-the-creative-professional) - Creative discipline

## 🚀 Performance & Features

### ⚡ Speed
- All commands execute in <100ms
- Optimized database queries
- Intelligent caching system
- Minimal startup overhead

### 🎨 User Experience  
- Beautiful Rich terminal output
- Color-coded status indicators
- Helpful error messages
- Intuitive command structure

### 🔒 Privacy & Security
- Local-only data storage
- No cloud synchronization
- Secure file permissions
- No telemetry or tracking

### 🍎 macOS Integration
- Native macOS file conventions
- Optimized for Terminal.app
- Homebrew distribution ready
- System notification support

## 📞 Support & Community

### Getting Help
- **Documentation**: You're reading it! 📚
- **GitHub Issues**: [Report bugs or request features](https://github.com/habitstracker/habits-tracker/issues)
- **GitHub Discussions**: [Community discussions](https://github.com/habitstracker/habits-tracker/discussions)

### Contributing
- **Contributing Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Development Setup**: [README.md#development](../README.md#development)
- **Code Quality**: Black, mypy, ruff, pytest

## 🎯 What's Next?

1. **Start Small**: Begin with 1-2 habits
2. **Build Consistency**: Focus on daily tracking
3. **Use Analytics**: Review weekly progress
4. **Optimize**: Adjust based on data
5. **Expand**: Add more habits gradually

---

**Ready to build better habits?** Start with the [Quick Start Guide](../README.md#quick-start) and begin your journey to consistent habit building! 🎯

*Made with ❤️ for productivity enthusiasts and terminal lovers*