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

## 🧪 Testing PawPal+

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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
