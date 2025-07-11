# 🎯 HabitsTracker CLI - Usage Examples & Workflows

Comprehensive examples and real-world workflows to help you get the most out of HabitsTracker CLI.

## 🌅 Getting Started: Your First Week

### Day 1: Setting Up Your First Habits

```bash
# Install HabitsTracker CLI
pip install habits-tracker

# Add your core habits
habits add "Exercise" --frequency daily --description "30 minutes of physical activity"
habits add "Read" --frequency daily --description "Read for 20 minutes"
habits add "Meditate" --frequency daily --description "10 minutes mindfulness"
habits add "Water" --frequency daily --description "Drink 8 glasses of water"

# Check your habits
habits list
```

**Expected Output:**
```
✅ Habit 'Exercise' added successfully!
🎯 Track it today with: habits track "Exercise"

✅ Habit 'Read' added successfully!
🎯 Track it today with: habits track "Read"

✅ Habit 'Meditate' added successfully!
🎯 Track it today with: habits track "Meditate"

✅ Habit 'Water' added successfully!
🎯 Track it today with: habits track "Water"
```

### Day 1 Evening: Track Your Progress

```bash
# Track what you accomplished today
habits track "Exercise" --note "30 min run in the park"
habits track "Read" --note "Read 2 chapters of Python book"
habits track "Water" --note "Actually drank 10 glasses!"

# See today's progress
habits today
```

**Expected Output:**
```
🌅 Today's Habits - Monday, July 11, 2024

┌────────────┬────────┬─────────────────────────┐
│ Habit      │ Status │ Notes                   │
├────────────┼────────┼─────────────────────────┤
│ Exercise   │ ✅ Done │ 30 min run in the park  │
│ Read       │ ✅ Done │ Read 2 chapters         │
│ Meditate   │ ⏳ Todo │                         │
│ Water      │ ✅ Done │ Actually drank 10!      │
└────────────┴────────┴─────────────────────────┘

📊 Progress: 3/4 completed (75%)
🎉 Great start! You're building momentum!
```

### Day 7: First Week Review

```bash
# Review your week
habits stats --period week

# Check individual habit performance
habits stats --habit "Exercise" --period week
habits stats --habit "Read" --period week
```

---

## 💪 Real-World Workflows

### 🌅 Morning Routine Optimization

**Goal**: Create and track a consistent morning routine.

```bash
# Setup morning habits (do this once)
habits add "Wake Up Early" --frequency daily --description "Wake up at 6:00 AM"
habits add "Morning Exercise" --frequency daily --description "20 min yoga or workout"
habits add "Meditation" --frequency daily --description "10 min mindfulness"
habits add "Healthy Breakfast" --frequency daily --description "Nutritious breakfast"
habits add "Plan Day" --frequency daily --description "Review calendar and priorities"

# Daily tracking (every morning)
habits track "Wake Up Early" --note "6:05 AM - close enough!"
habits track "Morning Exercise" --note "20 min yoga flow"
habits track "Meditation" --note "Felt very centered today"
habits track "Healthy Breakfast" --note "Oatmeal with berries"
habits track "Plan Day" --note "Reviewed 3 key priorities"

# Quick check
habits today
```

**Weekly Review Workflow:**
```bash
# Every Sunday morning
habits stats --period week
habits list

# Archive habits that didn't work
habits remove "Wake Up Early"  # If you kept snoozing

# Adjust and add new habits
habits add "Gentle Wake Up" --description "Wake up at 6:30 AM with gradual alarm"
```

---

### 📚 Learning & Development Tracking

**Goal**: Track programming learning and skill development.

```bash
# Setup learning habits
habits add "Code Practice" --frequency daily --description "Write code for 1 hour"
habits add "Read Tech Articles" --frequency daily --description "Read 2-3 tech articles"
habits add "Algorithm Practice" --frequency daily --description "Solve 1 coding problem"
habits add "Side Project" --frequency daily --description "Work on personal project"
habits add "Learn New Framework" --frequency weekly --description "Study new technology"

# Track with detailed notes for reflection
habits track "Code Practice" --note "Worked on Python web scraper - learned BeautifulSoup"
habits track "Algorithm Practice" --note "Solved binary tree problem on LeetCode"
habits track "Read Tech Articles" --note "Article on microservices, FastAPI tutorial"
habits track "Side Project" --note "Added user authentication to habit tracker"

# Weekly skill review
habits stats --habit "Code Practice" --period week
habits stats --habit "Algorithm Practice" --period week
```

**Monthly Skills Assessment:**
```bash
# First of every month
habits stats --period month

# Review and adjust
habits remove "Learn New Framework"  # If too ambitious
habits add "Weekly Code Review" --frequency weekly --description "Review and refactor old code"
```

---

### 🏃‍♀️ Fitness & Health Journey

**Goal**: Build a comprehensive fitness routine.

```bash
# Fitness foundation
habits add "Daily Steps" --frequency daily --description "Walk 10,000 steps"
habits add "Strength Training" --frequency weekly --description "Full body workout"
habits add "Cardio Session" --frequency daily --description "20 min cardio activity"
habits add "Stretching" --frequency daily --description "10 min flexibility work"
habits add "Hydration" --frequency daily --description "Drink 3L water"
habits add "Sleep Tracking" --frequency daily --description "8 hours quality sleep"

# Track workouts with details
habits track "Strength Training" --note "Upper body: chest, shoulders, triceps - felt strong!"
habits track "Cardio Session" --note "5K run in 25 minutes - new PR!"
habits track "Daily Steps" --note "12,847 steps - walked to coffee shop"
habits track "Stretching" --note "Hip flexors and hamstrings - much needed"
habits track "Hydration" --note "3.2L - stayed ahead of thirst"

# Weekly fitness review
habits stats --habit "Strength Training" --period week
habits stats --habit "Cardio Session" --period week
```

**Progress Tracking Tips:**
```bash
# Track rest days too
habits track "Strength Training" --date yesterday --note "Rest day - active recovery walk"

# Backdate missed entries
habits track "Stretching" --date -2d --note "Did evening yoga before bed"

# Use stats to adjust intensity
habits stats --habit "Daily Steps" --period month  # See if 10K is realistic
```

---

### 🧘‍♀️ Mental Health & Wellness

**Goal**: Maintain emotional well-being and stress management.

```bash
# Mental wellness habits
habits add "Morning Meditation" --frequency daily --description "10 min mindfulness"
habits add "Gratitude Journal" --frequency daily --description "Write 3 things I'm grateful for"
habits add "Evening Reflection" --frequency daily --description "Reflect on the day"
habits add "Social Connection" --frequency daily --description "Meaningful conversation with someone"
habits add "Digital Detox" --frequency daily --description "1 hour phone-free time"
habits add "Nature Time" --frequency daily --description "Spend time outdoors"

# Track with mindful notes
habits track "Morning Meditation" --note "Focused on breath - mind was calm"
habits track "Gratitude Journal" --note "Grateful for: health, family, sunny weather"
habits track "Social Connection" --note "Long phone call with mom - really connected"
habits track "Digital Detox" --note "Read book instead of scrolling - felt peaceful"
habits track "Nature Time" --note "20 min walk in park - saw beautiful flowers"

# Weekly mental health check-in
habits stats --period week
```

---

### 🎨 Creative & Personal Development

**Goal**: Nurture creativity and personal growth.

```bash
# Creative habits
habits add "Creative Writing" --frequency daily --description "Write for 30 minutes"
habits add "Art Practice" --frequency daily --description "Sketch or paint for 20 minutes"
habits add "Music Practice" --frequency daily --description "Practice guitar for 30 minutes"
habits add "Photography" --frequency daily --description "Take and edit photos"
habits add "Language Learning" --frequency daily --description "Study Spanish for 20 minutes"
habits add "Personal Reading" --frequency daily --description "Read non-work books"

# Track creative sessions
habits track "Creative Writing" --note "Wrote 500 words for short story - good flow today"
habits track "Art Practice" --note "Watercolor landscape - experimenting with wet-on-wet"
habits track "Music Practice" --note "Learned 3 new chords - fingers getting stronger"
habits track "Language Learning" --note "Completed lesson on past tense - getting easier"

# Monthly creative review
habits stats --period month
```

---

## 🔄 Advanced Tracking Patterns

### Backfilling Missed Days

```bash
# Catch up on tracking when you've been away
habits track "Exercise" --date -1d --note "Gym session yesterday"
habits track "Exercise" --date -2d --note "Home workout Tuesday"
habits track "Read" --date -3d --note "Finished chapter 5 Monday"

# Quick backfill for multiple habits
habits track "Meditation" --date yesterday
habits track "Water" --date yesterday
habits track "Steps" --date yesterday
```

### Flexible Date Tracking

```bash
# Various date formats for convenience
habits track "Exercise" --date today
habits track "Read" --date yesterday  
habits track "Gym" --date 2024-07-10
habits track "Run" --date -1d
habits track "Yoga" --date -7d

# Useful for irregular schedules
habits track "Weekly Planning" --date -3d --note "Sunday planning session"
```

### Detailed Note-Taking Strategies

```bash
# Performance tracking
habits track "Exercise" --note "5K run - 24:30, felt strong, good pace"

# Emotional tracking  
habits track "Meditation" --note "Struggled to focus today, mind was busy"

# Progress tracking
habits track "Guitar" --note "Finally nailed the F chord! Muscle memory building"

# Context tracking
habits track "Reading" --note "Chapter 3 of Atomic Habits - insights on habit stacking"

# Challenge tracking
habits track "Diet" --note "Resisted office cookies - getting easier to say no"
```

---

## 📊 Analytics & Review Workflows

### Daily Review Routine

```bash
# Every evening (5 minutes)
habits today                    # See what's done
habits track "Remaining Habit"  # Complete tracking
habits stats --period week     # Quick weekly check
```

### Weekly Deep Dive

```bash
# Sunday morning routine (15 minutes)
habits stats --period week              # Weekly overview
habits stats --habit "Exercise" --period week  # Deep dive on key habits
habits stats --habit "Reading" --period week
habits list --filter all               # Review all habits

# Identify patterns and make adjustments
habits remove "Unrealistic Habit"      # Archive what's not working
habits add "Better Alternative"        # Add improved version
```

### Monthly Optimization

```bash
# First Sunday of the month (30 minutes)
habits stats --period month            # Full month review
habits stats --period year             # Year-to-date progress

# Performance analysis for each major habit
habits stats --habit "Exercise" --period month
habits stats --habit "Learning" --period month
habits stats --habit "Wellness" --period month

# Strategic adjustments
habits list --filter archived          # Review archived habits
habits restore "Seasonal Habit"        # Bring back relevant habits
habits add "New Monthly Goal"          # Add new challenges
```

### Quarterly Planning

```bash
# Every 3 months - major review and reset
habits stats --period year             # Full year perspective
habits list --filter all              # Complete habit inventory

# Major habit lifecycle management
habits delete "Old Habit" --confirm   # Permanently remove outdated habits
habits add "Quarterly Goal" --description "90-day focused challenge"
```

---

## 🎯 Troubleshooting Common Scenarios

### Scenario 1: Inconsistent Tracking

**Problem**: You forget to track habits regularly.

**Solution**:
```bash
# Set up simple daily habits first
habits add "Track Habits" --description "Update habit tracker each evening"

# Use notes to build the habit
habits track "Track Habits" --note "Tracked 3/4 habits today - getting better"

# Weekly catch-up sessions
habits track "Exercise" --date -1d
habits track "Exercise" --date -2d
habits track "Reading" --date -3d
```

### Scenario 2: Too Many Habits

**Problem**: You added too many habits and feel overwhelmed.

**Solution**:
```bash
# Review current habits
habits list

# Archive non-essential habits
habits remove "Nice-to-Have Habit"
habits remove "Overwhelming Habit"

# Focus on 3-4 core habits
habits stats --period week  # See which ones you're actually doing
```

### Scenario 3: Losing Motivation

**Problem**: You're not seeing progress and losing motivation.

**Solution**:
```bash
# Look at your wins
habits stats --period month     # See your overall progress
habits stats --habit "Exercise" --period year  # Long-term view

# Celebrate small wins with detailed notes
habits track "Small Win" --note "Even 10 minutes counts - building momentum!"

# Adjust expectations
habits remove "Perfectionist Habit"
habits add "Realistic Habit" --description "Progress over perfection"
```

### Scenario 4: Streaks Breaking

**Problem**: You missed a day and broke your streak.

**Solution**:
```bash
# Don't let perfect be the enemy of good
habits track "Exercise" --note "Missed yesterday but back today - that's what matters"

# Focus on overall trends, not perfect streaks
habits stats --habit "Exercise" --period month  # 25/30 days is still amazing!

# Use the two-day rule: never miss twice in a row
habits track "Recovery Day" --note "Back on track after one miss"
```

---

## 🚀 Power User Tips

### Efficient Command Combinations

```bash
# Morning routine in one terminal session
habits today && habits track "Exercise" && habits track "Meditation" && habits today

# Evening review flow
habits track "Reading" --note "Great chapter on habits" && habits stats --period week

# Quick weekly review
habits stats --period week && habits list --filter archived
```

### Smart Habit Naming

```bash
# Use specific, action-oriented names
habits add "20min Morning Walk" --description "Walk around neighborhood"
habits add "3x Weekly Gym" --frequency weekly --description "Strength training session"
habits add "Daily Python Study" --description "Learn Python for 30 minutes"

# Time-based habits for clarity
habits add "Evening Reading" --description "Read before bed for 20 min"
habits add "Morning Pages" --description "Write 3 pages stream of consciousness"
```

### Note-Taking for Success

```bash
# Track intensity and enjoyment
habits track "Exercise" --note "5/10 intensity, 8/10 enjoyment - perfect balance"

# Note environmental factors
habits track "Reading" --note "Coffee shop was perfect - focus was great"

# Track obstacles and solutions
habits track "Meditation" --note "Kids were loud - used noise canceling headphones"

# Celebrate progress and insights
habits track "Learning" --note "Finally understood recursion! Clicked after 3rd example"
```

### Data Export and Backup Strategies

```bash
# Regular performance monitoring
habits profile              # Check command speed
habits memory               # Monitor resource usage
habits db-analyze           # Database health check

# Monthly data review
habits benchmark            # Performance trends
```

---

## 📱 Integration Ideas

### Terminal Workflow Integration

```bash
# Add to your shell's .bashrc or .zshrc
alias ht="habits today"
alias hts="habits stats --period week"
alias htl="habits list"

# Quick tracking aliases
alias track-exercise="habits track 'Exercise'"
alias track-reading="habits track 'Reading'"
alias track-meditation="habits track 'Meditation'"
```

### Daily Planning Integration

```bash
# Morning planning routine
echo "=== Morning Planning ===" && habits today && echo "=== Calendar ==="
# (Then check your calendar)

# Evening review routine  
echo "=== Evening Review ===" && habits stats --period week
```

---

## 🎉 Success Stories & Examples

### Example 1: The Consistent Developer

**Month 1 Setup:**
```bash
habits add "Code Daily" --description "Write code for 1 hour"
habits add "Learn New Tech" --description "Study new technology for 30 min"
habits add "Read Tech Blog" --description "Read 1-2 technical articles"
```

**Month 3 Results:**
```bash
habits stats --period month
# Code Daily: 28/30 days (93.3%)
# Learn New Tech: 25/30 days (83.3%) 
# Read Tech Blog: 30/30 days (100%)
```

**Success Notes:**
- Started small with achievable goals
- Used detailed notes to track learning
- Adjusted frequency based on actual performance

### Example 2: The Wellness Warrior

**Initial Setup:**
```bash
habits add "Morning Yoga" --description "15 min gentle yoga"
habits add "Healthy Lunch" --description "Nutritious homemade lunch"
habits add "Evening Walk" --description "20 min neighborhood walk"
habits add "Water Intake" --description "Drink 8 glasses water"
```

**6-Month Evolution:**
```bash
habits stats --period year
# Built incredible consistency
# Expanded to include meditation and strength training
# Lost 20 pounds and gained energy
```

### Example 3: The Creative Professional

**Creative Journey:**
```bash
habits add "Morning Pages" --description "Write 3 pages stream of consciousness"
habits add "Daily Sketch" --description "Draw for 20 minutes"
habits add "Photo Challenge" --description "Take and edit one photo"
```

**Impact:**
- Completed a novel draft in 6 months
- Improved artistic skills dramatically  
- Built a portfolio that led to freelance opportunities

---

## 🎯 Next Steps

### Week 1: Foundation
- Set up 3-4 core habits
- Focus on consistent tracking
- Use detailed notes

### Week 2-4: Refinement  
- Adjust habits based on performance
- Add notes to understand patterns
- Weekly reviews

### Month 2-3: Expansion
- Add new habits gradually
- Use analytics for optimization
- Develop personal workflows

### Ongoing: Mastery
- Regular reviews and adjustments
- Share your success stories
- Help others build great habits

---

*Ready to start your habit journey? Begin with one simple habit today!*

```bash
habits add "Daily Habit Tracking" --description "Use HabitsTracker CLI every day"
habits track "Daily Habit Tracking" --note "Started my journey to better habits!"
```