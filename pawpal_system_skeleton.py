"""PawPal+ system skeleton.

Class stubs generated from diagrams/uml.mmd. No logic yet — just names,
attributes, and empty method bodies to fill in as you implement scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from enum import IntEnum


class Priority(IntEnum):
    """Task priority. IntEnum so members sort/compare directly as numbers."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


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
    is_recurring: bool = False
    completed: bool = False

    def fits_in(self, minutes: int) -> bool:
        """Return True if this task fits within the remaining time budget."""
        raise NotImplementedError

    def conflicts_with(self, other: "Task") -> bool:
        """Return True if this task's time window overlaps with another's."""
        raise NotImplementedError

    def urgency_score(self) -> float:
        """Blend priority and overdue-ness into a single rankable score."""
        raise NotImplementedError

    def summary(self) -> str:
        """One-line label, e.g. 'Morning walk (20 min) [HIGH]'."""
        raise NotImplementedError


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
        raise NotImplementedError

    def remove_task(self, task_id: str) -> None:
        """Remove a task by id."""
        raise NotImplementedError

    def list_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        raise NotImplementedError

    def total_task_time(self) -> int:
        """Sum of all task durations in minutes."""
        raise NotImplementedError

    def tasks_by_priority(self) -> list[Task]:
        """Return tasks sorted high to low priority."""
        raise NotImplementedError

    def care_load(self) -> int:
        """Total daily minutes of care this pet demands."""
        raise NotImplementedError

    def needs_attention(self) -> bool:
        """True if this pet's tasks can't all fit the available time."""
        raise NotImplementedError


@dataclass
class Owner:
    """A pet owner with pets, preferences, and a daily time budget."""

    name: str
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)
    available_minutes: int = 0

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        raise NotImplementedError

    def remove_pet(self, pet_id: str) -> None:
        """Remove a pet by id."""
        raise NotImplementedError

    def get_pet(self, pet_id: str) -> Pet:
        """Look up a single pet by id (resolves a Task.pet_id back to a Pet)."""
        raise NotImplementedError

    def list_pets(self) -> list[Pet]:
        """Return all pets owned."""
        raise NotImplementedError

    def busiest_pet(self) -> Pet:
        """Return the pet that consumes the most care time."""
        raise NotImplementedError

    def time_deficit(self) -> int:
        """Minutes short: total care needed minus available time."""
        raise NotImplementedError


@dataclass
class DailyPlan:
    """The result of scheduling: which tasks were placed, which were skipped."""

    scheduled: list[ScheduledItem] = field(default_factory=list)
    skipped: list[Task] = field(default_factory=list)

    def explain(self) -> str:
        """Human-readable reasoning for why each task was chosen or skipped."""
        raise NotImplementedError

    def score_plan(self) -> float:
        """Rate plan quality (e.g. coverage of high-priority tasks)."""
        raise NotImplementedError

    def what_if(self, extra_minutes: int) -> "DailyPlan":
        """Re-plan as if the owner had extra_minutes more time."""
        raise NotImplementedError


class Scheduler:
    """Builds a DailyPlan from pets and a time budget. Holds the decision logic."""

    def build_plan(self, owner: Owner) -> DailyPlan:
        """Pick, order, and time-slot tasks under the owner's time budget."""
        raise NotImplementedError

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority/duration for scheduling."""
        raise NotImplementedError

    def _filter_to_budget(self, tasks: list[Task], minutes: int) -> list[Task]:
        """Drop tasks once the time budget runs out."""
        raise NotImplementedError

    def _place_in_slots(self, tasks: list[Task]) -> list[ScheduledItem]:
        """Assign non-overlapping time slots, honoring fixed_time tasks."""
        raise NotImplementedError
