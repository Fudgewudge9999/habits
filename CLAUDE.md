# HabitsTracker CLI - Claude Context & Instructions

## 🎯 Project Overview
**HabitsTracker CLI** is a macOS-only command-line habits tracking application built in Python. This is a focused, minimalist tool for developers and power users who prefer terminal interfaces.

## 🍎 Platform Specifics
- **Target Platform:** macOS ONLY (10.15+ Catalina and newer)
- **Distribution:** PyPI + Homebrew formula for macOS
- **Integration:** Leverage macOS-specific features (notifications, file system conventions)
- **File Locations:** Follow macOS conventions (~/.config/habits/ for config, ~/.habits/ for data)

## 🏗️ Technical Stack & Architecture
- **Language:** Python 3.9+
- **CLI Framework:** Typer (type-safe, modern)
- **Database:** SQLite3 with SQLAlchemy ORM
- **Output:** Rich library for beautiful terminal output
- **Testing:** pytest with >90% coverage requirement
- **Packaging:** Modern Python packaging with pyproject.toml

## 📁 Project Structure
```
habits_tracker/
├── habits_tracker/           # Main package
│   ├── cli/                 # CLI commands and interface
│   ├── core/                # Models, database, business logic
│   └── utils/               # Utilities and helpers
├── tests/                   # Test suite
├── docs/                    # Documentation
├── TECHNICAL_IMPLEMENTATION_PLAN.md  # Living implementation plan
├── habits_tracker_prd.md    # Original requirements
└── pyproject.toml          # Modern Python packaging
```

## 🔄 Development Workflow & Instructions

### Before Starting ANY Task:
1. **Read this CLAUDE.md file completely**
2. **Check the current todo list status**
3. **Review relevant sections of TECHNICAL_IMPLEMENTATION_PLAN.md**
4. **Update todos to in_progress before starting work**

### After Completing ANY Task:
1. **Mark completed todos as completed immediately**
2. **Update TECHNICAL_IMPLEMENTATION_PLAN.md with:**
   - Mark completed items in development checklist
   - Add any implementation notes or decisions made
   - Update timelines if needed
   - Document any architectural changes or discoveries
3. **Add new todos if subtasks were discovered**
4. **Run tests if applicable**

### Key Development Principles:
- **macOS-First:** Design with macOS conventions and integrations in mind
- **Performance:** All commands must execute in <100ms
- **Minimalism:** Keep the tool focused and lightweight
- **Type Safety:** Use Python 3.9+ type hints throughout
- **Testing:** Maintain >90% test coverage
- **User Experience:** Follow Unix CLI conventions with helpful error messages

## 🎨 Code Style & Conventions
- **Formatting:** Use black for code formatting
- **Type Checking:** Use mypy for type checking
- **Imports:** Follow PEP8 import ordering
- **Docstrings:** Use Google-style docstrings
- **Error Handling:** Custom exception hierarchy with helpful messages
- **No Comments:** Code should be self-documenting unless absolutely necessary

## 📊 Database Design Notes
- **Local Storage:** SQLite database in `~/.habits/habits.db`
- **Schema:** habits, tracking_entries, config tables
- **Migrations:** Auto-migration on schema changes
- **Performance:** Indexed on habit_id, date, active columns
- **Backup:** Automatic backup before migrations

## 🧪 Testing Strategy
- **Unit Tests:** All services and core logic
- **Integration Tests:** CLI commands end-to-end
- **Performance Tests:** Command execution time validation
- **Coverage:** Target >90% code coverage
- **Database Tests:** Migration and data integrity testing

## 📈 Performance Requirements
- **Command Execution:** <100ms for typical operations
- **Memory Usage:** <50MB during operation
- **Database:** Optimized for up to 10,000 tracking entries
- **Startup Time:** Minimal CLI startup overhead

## 🔧 macOS-Specific Features to Leverage
- **Notifications:** Native macOS notifications for reminders
- **File System:** Use macOS standard directories (~/.config, ~/.local)
- **Terminal:** Rich output optimized for macOS Terminal.app
- **Distribution:** Homebrew formula for easy installation
- **Integration:** Potential future Calendar.app integration

## 📋 Key Commands to Implement (Priority Order)
1. **Core:** `habits add/list/remove/delete`
2. **Tracking:** `habits track/untrack/today`
3. **Analytics:** `habits stats`
4. **Advanced:** `habits config/export/import`

## ⚠️ Important Reminders
- **Always update TECHNICAL_IMPLEMENTATION_PLAN.md after completing tasks**
- **Mark todos as completed immediately upon finishing**
- **Focus on macOS-specific optimizations and conventions**
- **Maintain the minimalist philosophy - don't over-engineer**
- **Test performance regularly to meet <100ms requirement**
- **Keep dependencies minimal for fast startup**

## 🗂️ File References
- **Requirements:** `habits_tracker_prd.md`
- **Implementation Plan:** `TECHNICAL_IMPLEMENTATION_PLAN.md`
- **This Context:** `CLAUDE.md`

## 🛠️ Development Lessons Learned

### Critical Issues & Solutions from Phase 0-1A

#### 1. **Database Session Management**
- **Issue**: Never use `next(generator())` for context managers - causes integrity check failures
- **Solution**: Always use `@contextmanager` decorator with explicit try/finally cleanup
- **Code Pattern**: 
  ```python
  @contextmanager
  def get_session():
      session = SessionLocal()
      try:
          yield session
      finally:
          session.close()
  ```

#### 2. **macOS Development Environment**
- **Issue**: macOS Python environments are externally managed (PEP 668)
- **Solution**: Always use virtual environments: `python3 -m venv venv && source venv/bin/activate`
- **Testing**: Use `source venv/bin/activate` in separate terminals for testing

#### 3. **CLI Architecture Decisions**
- **Issue**: Nested vs flat command structure affects user experience
- **Solution**: Use flat structure (`habits add`) not nested (`habits habits add`)
- **Implementation**: Import functions directly and use `app.command("name")(function)`

#### 4. **Database Integrity Checks**
- **Issue**: Overly aggressive integrity checks cause unnecessary reinitializations
- **Solution**: Check for table existence AND connectivity, not just simple queries
- **Pattern**: Verify required tables exist before running test queries

#### 5. **Error Messages & UX**
- **Always** provide helpful error messages with suggested solutions
- **Always** add confirmation prompts for destructive operations
- **Always** show next-step suggestions after successful operations

### Testing Checklist
- [ ] Database persists between CLI sessions (no reinitializations)
- [ ] All commands work without Python tracebacks
- [ ] Rich formatting displays correctly
- [ ] Validation errors are clear and helpful
- [ ] Virtual environment setup works on fresh terminal

## 💡 Development Notes
- This is Phase 1 MVP development focused on core functionality
- Future phases will add advanced analytics, import/export, and notifications
- Architecture should support easy extension for Phase 2/3 features
- Keep the codebase clean and well-organized for future maintainability