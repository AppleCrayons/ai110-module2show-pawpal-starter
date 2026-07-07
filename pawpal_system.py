"""PawPal+ system implementation.

Core domain + scheduling logic for a daily pet-care planner.

Design notes:
- Times are stored on tasks as strings ("08:00") so the UI can pass them
  straight through; scheduling converts them to `datetime.time` internally.
- The Scheduler is the "brain": it gathers every pet's open tasks, ranks
  them, drops what won't fit the owner's time budget, and lays the rest out
  into non-overlapping slots (honoring fixed-time tasks first).

The original class skeleton is preserved in pawpal_system_skeleton.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import time
from enum import Enum, IntEnum
from itertools import combinations


DAY_START = time(8, 0)  # default clock time the planned day begins at


def _parse_time(value: str) -> time | None:
    """Parse an 'HH:MM' string into a time, or None if empty/invalid."""
    if not value:
        return None
    try:
        hours, minutes = value.split(":")
        return time(int(hours), int(minutes))
    except (ValueError, AttributeError):
        return None


def _to_minutes(t: time) -> int:
    """Minutes since midnight for a time."""
    return t.hour * 60 + t.minute


def _from_minutes(minutes: int) -> time:
    """Convert minutes-since-midnight back to a time (clamped to a 24h day)."""
    minutes = max(0, min(minutes, 24 * 60 - 1))
    return time(minutes // 60, minutes % 60)


class Priority(IntEnum):
    """Task priority. IntEnum so members sort/compare directly as numbers."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Recurrence(str, Enum):
    """How often a task repeats. str-based so it prints/serializes cleanly."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"

    @property
    def days(self) -> int:
        """Days until the next occurrence (0 for a one-off task)."""
        return {"none": 0, "daily": 1, "weekly": 7}[self.value]


def _next_occurrence_id(task_id: str) -> str:
    """Derive the id for a task's next occurrence, e.g. 't1' -> 't1#2'.

    An existing '#N' suffix is incremented so repeated completions stay unique.
    """
    base, sep, num = task_id.partition("#")
    n = int(num) + 1 if sep and num.isdigit() else 2
    return f"{base}#{n}"


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    id: str = ""
    pet_id: str = ""  # back-reference: which Pet this task belongs to
    category: str = "other"
    preferred_time: str = ""  # e.g. "08:00"; "" means flexible
    fixed_time: bool = False  # True = must run at preferred_time
    recurrence: Recurrence = Recurrence.NONE  # daily/weekly tasks respawn
    completed: bool = False

    @property
    def is_recurring(self) -> bool:
        """True if this task repeats (daily or weekly)."""
        return self.recurrence is not Recurrence.NONE

    def fits_in(self, minutes: int) -> bool:
        """Return True if this task fits within the remaining time budget."""
        return self.duration_minutes <= minutes

    def conflicts_with(self, other: "Task") -> bool:
        """Return True if this task's time window overlaps with another's.

        Only meaningful for tasks with a concrete `preferred_time`; a flexible
        task (no preferred_time) has no fixed window and never conflicts here.
        """
        start_a = _parse_time(self.preferred_time)
        start_b = _parse_time(other.preferred_time)
        if start_a is None or start_b is None:
            return False
        a0 = _to_minutes(start_a)
        a1 = a0 + self.duration_minutes
        b0 = _to_minutes(start_b)
        b1 = b0 + other.duration_minutes
        return a0 < b1 and b0 < a1  # half-open intervals overlap

    def urgency_score(self) -> float:
        """Blend priority and overdue-ness into a single rankable score.

        Higher = more urgent. Priority dominates; an open (not-completed)
        recurring task that's fixed to a clock time gets small nudges so it
        wins ties against a flexible, lower-stakes task of the same priority.
        """
        score = float(self.priority) * 10.0
        if not self.completed:
            score += 5.0  # still outstanding -> "overdue" pressure
        if self.is_recurring:
            score += 2.0  # daily needs shouldn't slip
        if self.fixed_time:
            score += 1.0  # anchored to a time, harder to reschedule
        return score

    def summary(self) -> str:
        """One-line label, e.g. 'Morning walk (20 min) [HIGH]'."""
        return f"{self.title} ({self.duration_minutes} min) [{self.priority.name}]"

    def next_occurrence(self) -> "Task | None":
        """Return a fresh, uncompleted instance of this task for its next run.

        Returns None for a one-off (non-recurring) task. The copy keeps the
        same title/duration/time-of-day but gets a new id and is not completed.
        (Times here are clock times only; `Recurrence.days` records how far out
        the next run is for callers that track dates.)
        """
        if self.recurrence is Recurrence.NONE:
            return None
        return replace(
            self,
            id=_next_occurrence_id(self.id),
            completed=False,
        )

    def mark_complete(self) -> "Task | None":
        """Mark this task done; return its next occurrence if it recurs.

        A daily/weekly task yields a fresh instance for the next run (which the
        owning Pet appends via `complete_task`); a one-off returns None.
        """
        self.completed = True
        return self.next_occurrence()


@dataclass
class ScheduledItem:
    """A task placed at a concrete time slot in the day's plan."""

    task: Task
    start: time
    end: time  # derived from start + task.duration_minutes


@dataclass
class Pet:
    """A pet that owns a list of care tasks."""

    name: str
    species: str
    age: int = 0
    id: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet (and stamp task.pet_id)."""
        task.pet_id = self.id
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task by id."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def complete_task(self, task_id: str) -> "Task | None":
        """Mark a task complete and auto-add its next occurrence if it recurs.

        Returns the newly created next-occurrence Task (already appended to this
        pet), or None for a one-off task. Raises KeyError if no task matches.
        """
        for task in self.tasks:
            if task.id == task_id:
                upcoming = task.mark_complete()
                if upcoming is not None:
                    self.add_task(upcoming)
                return upcoming
        raise KeyError(f"No task with id {task_id!r}")

    def list_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return list(self.tasks)

    def total_task_time(self) -> int:
        """Sum of all task durations in minutes."""
        return sum(t.duration_minutes for t in self.tasks)

    def tasks_by_priority(self) -> list[Task]:
        """Return tasks sorted high to low priority."""
        return sorted(self.tasks, key=lambda t: t.priority, reverse=True)

    def care_load(self) -> int:
        """Total daily minutes of care this pet demands (open tasks only)."""
        return sum(t.duration_minutes for t in self.tasks if not t.completed)

    def needs_attention(self, available_minutes: int | None = None) -> bool:
        """True if this pet's care can't comfortably fit the available time.

        With `available_minutes` given, compares against the open care load.
        Without it, falls back to a simpler heuristic: the pet has an open,
        high-priority task waiting.
        """
        if available_minutes is not None:
            return self.care_load() > available_minutes
        return any(
            not t.completed and t.priority == Priority.HIGH for t in self.tasks
        )


@dataclass
class Owner:
    """A pet owner with pets, preferences, and a daily time budget."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    available_minutes: int = 0

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet by id."""
        self.pets = [p for p in self.pets if p.id != pet_id]

    def get_pet(self, pet_id: str) -> Pet:
        """Look up a single pet by id (resolves a Task.pet_id back to a Pet)."""
        for pet in self.pets:
            if pet.id == pet_id:
                return pet
        raise KeyError(f"No pet with id {pet_id!r}")

    def list_pets(self) -> list[Pet]:
        """Return all pets owned."""
        return list(self.pets)

    def filter_tasks(
        self,
        *,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return this owner's tasks filtered by completion status and/or pet.

        - `completed`: keep only tasks whose `completed` flag matches (True or
          False). Left as None means "don't filter on completion".
        - `pet_name`: keep only tasks belonging to the pet with this name
          (case-insensitive). None means "any pet".

        With no arguments, returns every task across all pets.
        """
        wanted = pet_name.casefold() if pet_name is not None else None
        result: list[Task] = []
        for pet in self.pets:
            if wanted is not None and pet.name.casefold() != wanted:
                continue
            for task in pet.tasks:
                if completed is not None and task.completed != completed:
                    continue
                result.append(task)
        return result

    def busiest_pet(self) -> Pet:
        """Return the pet that consumes the most care time."""
        if not self.pets:
            raise ValueError("Owner has no pets")
        return max(self.pets, key=lambda p: p.care_load())

    def time_deficit(self) -> int:
        """Minutes short: total care needed minus available time.

        Positive = short by that many minutes; <= 0 = the day fits.
        """
        total_care = sum(p.care_load() for p in self.pets)
        return total_care - self.available_minutes


@dataclass
class DailyPlan:
    """The result of scheduling: which tasks were placed, which were skipped."""

    scheduled: list[ScheduledItem] = field(default_factory=list)
    skipped: list[Task] = field(default_factory=list)
    # Back-references so what_if() can re-plan; excluded from repr/equality.
    owner: "Owner | None" = field(default=None, repr=False, compare=False)
    scheduler: "Scheduler | None" = field(default=None, repr=False, compare=False)

    def explain(self) -> str:
        """Human-readable reasoning for why each task was chosen or skipped."""
        lines: list[str] = []
        if self.scheduled:
            lines.append("Scheduled:")
            for item in self.scheduled:
                start = item.start.strftime("%H:%M")
                end = item.end.strftime("%H:%M")
                lines.append(f"  {start}-{end}  {item.task.summary()}")
        else:
            lines.append("Scheduled: (nothing)")
        if self.skipped:
            lines.append("Skipped (out of time, lowest urgency first):")
            for task in self.skipped:
                lines.append(f"  - {task.summary()}")
        return "\n".join(lines)

    def conflicts(self) -> list[tuple[ScheduledItem, ScheduledItem]]:
        """Overlapping pairs in this plan (see Scheduler.find_conflicts)."""
        if self.scheduler is None:
            raise ValueError("Plan has no scheduler to check conflicts with")
        return self.scheduler.find_conflicts(self.scheduled)

    def conflict_warning(self) -> str:
        """Lightweight warning string for this plan's conflicts ('' if none)."""
        if self.scheduler is None:
            return ""
        return self.scheduler.conflict_warning(self.scheduled)

    def score_plan(self) -> float:
        """Rate plan quality: fraction of total urgency actually scheduled.

        1.0 means every outstanding task got placed; lower means high-value
        tasks were skipped. Weighted by urgency so dropping a HIGH task hurts
        more than dropping a LOW one.
        """
        scheduled_weight = sum(i.task.urgency_score() for i in self.scheduled)
        skipped_weight = sum(t.urgency_score() for t in self.skipped)
        total = scheduled_weight + skipped_weight
        if total == 0:
            return 1.0
        return scheduled_weight / total

    def what_if(self, extra_minutes: int) -> "DailyPlan":
        """Re-plan as if the owner had extra_minutes more time."""
        if self.owner is None or self.scheduler is None:
            raise ValueError("Plan has no owner/scheduler to re-plan from")
        hypothetical = Owner(
            name=self.owner.name,
            pets=self.owner.pets,
            preferences=self.owner.preferences,
            available_minutes=self.owner.available_minutes + extra_minutes,
        )
        return self.scheduler.build_plan(hypothetical)


class Scheduler:
    """Builds a DailyPlan from pets and a time budget. Holds the decision logic."""

    def __init__(self, day_start: time = DAY_START) -> None:
        """Create a scheduler that lays out the day starting at day_start."""
        self.day_start = day_start

    def build_plan(self, owner: Owner) -> DailyPlan:
        """Pick, order, and time-slot tasks under the owner's time budget."""
        open_tasks = [
            task
            for pet in owner.pets
            for task in pet.tasks
            if not task.completed
        ]
        ranked = self._sort_tasks(open_tasks)
        chosen = self._filter_to_budget(ranked, owner.available_minutes)
        chosen_ids = {id(t) for t in chosen}
        skipped = [t for t in ranked if id(t) not in chosen_ids]
        scheduled = self._place_in_slots(chosen)
        return DailyPlan(
            scheduled=scheduled,
            skipped=skipped,
            owner=owner,
            scheduler=self,
        )

    def find_conflicts(
        self, items: list[ScheduledItem]
    ) -> list[tuple[ScheduledItem, ScheduledItem]]:
        """Return every pair of scheduled items whose time slots overlap.

        Works across the whole plan, so it catches collisions whether the two
        tasks belong to the same pet or to different pets (e.g. two fixed-time
        tasks anchored at the same clock time). Uses half-open intervals: a task
        ending exactly when another starts is not a conflict.
        """
        conflicts: list[tuple[ScheduledItem, ScheduledItem]] = []
        ordered = sorted(items, key=lambda i: i.start)
        for a, b in combinations(ordered, 2):
            a0, a1 = _to_minutes(a.start), _to_minutes(a.end)
            b0, b1 = _to_minutes(b.start), _to_minutes(b.end)
            if a0 < b1 and b0 < a1:  # half-open intervals overlap
                conflicts.append((a, b))
        return conflicts

    def conflict_warning(self, items: list[ScheduledItem]) -> str:
        """Lightweight conflict check: return a warning message, never raise.

        Returns an empty string when the plan is clean, or a human-readable,
        multi-line warning listing each overlapping pair. Callers can print it
        as-is and carry on -- nothing here crashes the program.
        """
        conflicts = self.find_conflicts(items)
        if not conflicts:
            return ""
        lines = [f"WARNING: {len(conflicts)} scheduling conflict(s) detected:"]
        for a, b in conflicts:
            same_pet = a.task.pet_id == b.task.pet_id and a.task.pet_id
            scope = "same pet" if same_pet else "different pets"
            lines.append(
                f"  - {a.task.title} ({a.start:%H:%M}-{a.end:%H:%M}) overlaps "
                f"{b.task.title} ({b.start:%H:%M}-{b.end:%H:%M}) [{scope}]"
            )
        return "\n".join(lines)

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by their preferred clock time (earliest first).

        A Task's time is its `preferred_time` ("HH:MM"); flexible tasks with no
        preferred_time are sorted to the end, keeping their relative order.
        """
        return sorted(
            tasks,
            key=lambda t: _to_minutes(_parse_time(t.preferred_time))
            if _parse_time(t.preferred_time) is not None
            else 24 * 60,
        )

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by urgency (desc), then shorter duration first."""
        return sorted(
            tasks,
            key=lambda t: (-t.urgency_score(), t.duration_minutes),
        )

    def _filter_to_budget(self, tasks: list[Task], minutes: int) -> list[Task]:
        """Greedily keep tasks (already ranked) until the budget runs out."""
        remaining = minutes
        kept: list[Task] = []
        for task in tasks:
            if task.fits_in(remaining):
                kept.append(task)
                remaining -= task.duration_minutes
        return kept

    def _place_in_slots(self, tasks: list[Task]) -> list[ScheduledItem]:
        """Assign non-overlapping time slots, honoring fixed_time tasks.

        Fixed-time tasks are anchored at their preferred_time first; flexible
        tasks then fill the earliest gap that doesn't collide with an
        already-placed slot.
        """
        placed: list[ScheduledItem] = []
        occupied: list[tuple[int, int]] = []  # (start_min, end_min) intervals

        def reserve(start_min: int, task: Task) -> None:
            end_min = start_min + task.duration_minutes
            occupied.append((start_min, end_min))
            placed.append(
                ScheduledItem(
                    task=task,
                    start=_from_minutes(start_min),
                    end=_from_minutes(end_min),
                )
            )

        fixed = [t for t in tasks if t.fixed_time and _parse_time(t.preferred_time)]
        flexible = [t for t in tasks if t not in fixed]

        # Anchor fixed-time tasks at their requested clock time.
        for task in fixed:
            start_min = _to_minutes(_parse_time(task.preferred_time))
            reserve(start_min, task)

        # Fill flexible tasks into the earliest non-conflicting gap.
        for task in flexible:
            start_min = self._earliest_free_slot(
                task.duration_minutes, occupied
            )
            reserve(start_min, task)

        placed.sort(key=lambda item: item.start)
        return placed

    def _earliest_free_slot(
        self, duration: int, occupied: list[tuple[int, int]]
    ) -> int:
        """First start-minute at/after day_start where `duration` fits free."""
        candidate = _to_minutes(self.day_start)
        for start, end in sorted(occupied):
            if candidate + duration <= start:
                return candidate  # fits before this occupied block
            candidate = max(candidate, end)
        return candidate
