# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Running `python main.py` produces the daily schedule below:

```
Today's Schedule
========================================
  08:00  Morning meds (Mochi) [HIGH]
  08:05  Litter change (Biscuit) [MEDIUM]
  08:30  Morning walk (Mochi) [HIGH]
  09:00  Enrichment play (Mochi) [LOW]
  12:00  Feeding (Biscuit) [HIGH]
```

## 🧪 Testing PawPal+ (at bottom)

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

Beyond the core `build_plan()` pass, PawPal+ implements four "smarter scheduling"
features. Each is summarized below and documented in full in the method docstrings
in [`pawpal_system.py`](pawpal_system.py).

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()` | Order tasks by clock time; flexible tasks last |
| Filtering | `Owner.filter_tasks()` | Filter by completion status and/or pet name |
| Conflict detection | `Scheduler.find_conflicts()`, `Scheduler.conflict_warning()`, `DailyPlan.conflict_warning()` | Overlapping time slots (same or different pets) |
| Recurring tasks | `Task.mark_complete()`, `Task.next_occurrence()`, `Pet.complete_task()` | Daily/weekly tasks respawn on completion |

### Sorting behavior — `Scheduler.sort_by_time()`

Returns tasks ordered by their preferred clock time, earliest first. A `Task`'s
time is its `preferred_time` string (`"HH:MM"`), parsed to minutes-since-midnight
for comparison. Flexible tasks with no `preferred_time` are sorted to the end; the
sort is stable, so they keep their original relative order. The input list is not
mutated — a new list is returned.

### Filtering behavior — `Owner.filter_tasks()`

Returns the owner's tasks filtered by **completion status**, **pet name**, or both
(keyword-only args, so calls read clearly):

```python
owner.filter_tasks(completed=False)      # only open tasks
owner.filter_tasks(pet_name="Mochi")     # only that pet's tasks (case-insensitive)
owner.filter_tasks(completed=True, pet_name="Biscuit")
owner.filter_tasks()                      # every task across all pets
```

Pet-name filtering lives on `Owner` because a `Task` only stores `pet_id`; the
owner is what resolves a name back to its pet and tasks. Each filter defaults to
`None`, meaning "don't filter on this."

### Conflict detection — `Scheduler.find_conflicts()` / `conflict_warning()`

`find_conflicts(items)` compares every pair of scheduled items and returns those
whose slots overlap, using **half-open intervals** (`a0 < b1 and b0 < a1`) so it
catches partial overlaps — not just identical start times — and a task ending
exactly when another begins is *not* a conflict. Because it works over the whole
plan, it flags collisions whether the two tasks belong to the **same pet or
different pets** (e.g. two `fixed_time` tasks anchored at the same clock time).

`conflict_warning(items)` is the **lightweight** variant: it returns a
human-readable, multi-line warning string (or `""` when the plan is clean) and
**never raises**, so callers can print it and carry on. `DailyPlan.conflict_warning()`
is a convenience wrapper that runs the check against the plan's own scheduled items.
This is detection only — conflicts are reported, not auto-resolved.

### Recurring task logic — `Task.mark_complete()` / `Pet.complete_task()`

Recurrence is modeled by the `Recurrence` enum (`NONE` / `DAILY` / `WEEKLY`;
`Recurrence.days` → `0`/`1`/`7`). When a recurring task is completed, a fresh
instance is created automatically for the next occurrence:

- `Task.next_occurrence()` — returns a fresh, uncompleted copy with a new unique id
  (`t4` → `t4#2` → `t4#3`), or `None` for a one-off task.
- `Task.mark_complete()` — marks the task done and returns its next occurrence
  (or `None`).
- `Pet.complete_task(task_id)` — marks the task done **and** appends the new
  instance to the pet, so the respawn is automatic at the collection level.

## 📸 Demo Walkthrough

Follow these numbered steps to see PawPal+ end to end. Each step names the UI feature you use and the action you take:

1. **Set the time budget** — in the *Owner* section, enter your name and the **available minutes** for the day (e.g. `120`). This is the budget the scheduler plans against.
2. **Add a pet** — in *Add a Pet*, enter a name, species, and age, then click **Add pet**. A green success banner confirms it; pets persist across reruns via session state.
3. **Add tasks** — in *Add a Task*, pick a pet and set title, duration, priority, an optional preferred time (`HH:MM`), and the "must run at that exact time" (fixed-time) flag. Add a few — mix flexible and fixed-time tasks.
4. **Filter and sort** — in *Current tasks*, use the **status filter** (All / Open only / Completed only, backed by `Owner.filter_tasks()`) and the **Sort by time of day** toggle (backed by `Scheduler.sort_by_time()`) to watch tasks reorder chronologically, with flexible tasks last.
5. **Generate the schedule** — in *Build Schedule*, click **Generate schedule** to run `Scheduler.build_plan()` and view today's timed plan, any skipped tasks, plan-quality/time-deficit metrics, and an expandable "Why this plan?" explanation.
6. **Watch the Scheduler behaviors** — the plan demonstrates: **urgency ranking + budget filtering** (tasks kept by `urgency_score()` until time runs out, the rest skipped), **sorting by time**, **conflict warnings** (`conflict_warning()` flags overlapping slots and labels them *same pet* / *different pets*; a clean plan shows a success banner), and **daily/weekly recurrence** (completing a recurring task spawns its next occurrence with a fresh id, `t4 → t4#2`).

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->

**Sample CLI output** — running `python main.py` seeds two pets with deliberately out-of-order and clashing tasks, then exercises scheduling, sorting, filtering, conflict detection, and recurrence:

```
Today's Schedule
========================================
  08:00  Litter change (Biscuit) [MEDIUM]
  08:10  Enrichment play (Mochi) [LOW]
  12:00  Feeding (Biscuit) [HIGH]
  12:00  Nail trim (Biscuit) [MEDIUM]
  18:30  Evening walk (Mochi) [HIGH]

WARNING: 1 scheduling conflict(s) detected:
  - Feeding (12:00-12:10) overlaps Nail trim (12:00-12:15) [same pet]

Tasks as added (unsorted):
  18:30  Evening walk
  --:--  Enrichment play
  08:00  Morning meds
  --:--  Litter change
  12:00  Feeding
  12:00  Nail trim

Sorted by time (Scheduler.sort_by_time):
  08:00  Morning meds
  12:00  Feeding
  12:00  Nail trim
  18:30  Evening walk
  --:--  Enrichment play
  --:--  Litter change

Open tasks only (filter_tasks completed=False):
  - Evening walk
  - Enrichment play
  - Litter change
  - Feeding
  - Nail trim

Mochi's tasks (filter_tasks pet_name='Mochi'):
  - Evening walk (open)
  - Enrichment play (open)
  - Morning meds (done)

Biscuit's tasks before completing 'Feeding' (weekly):
  - t5: Litter change (none, open)
  - t4: Feeding (weekly, open)
  - t6: Nail trim (none, open)

Completed 't4'. Auto-created next occurrence: t4#2
Biscuit's tasks after completing 'Feeding':
  - t5: Litter change (none, open)
  - t4: Feeding (weekly, done)
  - t6: Nail trim (none, open)
  - t4#2: Feeding (weekly, open)
```

## Testing PawPal+
"python -m pytest" will run the program
Tests cover tasks, how tasks will fit into the schedule, urgency ranking, summaries, pets and owners with adding tasks, inputting pet id's, and care loads. Scheduler is tested to test a list being properly formatted withn o overlap and ordered by urgency. Tests srting for chronological order of timed tasks, recurrence of tasks, and general conflict detection.

PS C:\Users\bonca\110 ai\ai110-module2show-pawpal-starter> python -m pytest
============================================================ test session starts =============================================================
platform win32 -- Python 3.14.6, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\bonca\110 ai\ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 26 items                                                                                                                            

tests\test_pawpal.py ..........................                                                                                         [100%]

============================================================= 26 passed in 0.06s =============================================================

All 26 tests passed first time, 5* confidence.