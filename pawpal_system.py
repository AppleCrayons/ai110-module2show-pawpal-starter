"""PawPal+ system skeleton.

Class stubs generated from diagrams/uml.mmd. No logic yet — just names,
attributes, and empty method bodies to fill in as you implement scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single pet care task (walk, feeding, meds, etc.)."""

    title: str
    duration_minutes: int
    priority: str  # "low" | "medium" | "high"
    id: str = ""
    category: str = "other"
    preferred_time: str = ""
    is_recurring: bool = False
    completed: bool = False

    def priority_rank(self) -> int:
        """Map priority string to a sortable number (higher = more urgent)."""
        raise NotImplementedError

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
        """One-line label, e.g. 'Morning walk (20 min) [high]'."""
        raise NotImplementedError


@dataclass
class Pet:
    """A pet that owns a list of care tasks."""

    name: str
    species: str
    age: int = 0
    id: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        raise NotImplementedError

    def remove_task(self, title: str) -> None:
        """Remove a task by title."""
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
        """Look up a single pet by id."""
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
    """The result of scheduling: which tasks made it in, which were skipped."""

    scheduled: list[Task] = field(default_factory=list)
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

    def build_plan(self, pets: list[Pet], available_minutes: int) -> DailyPlan:
        """Pick and order tasks under the time constraint into a DailyPlan."""
        raise NotImplementedError

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority/duration for scheduling."""
        raise NotImplementedError

    def _filter_to_budget(self, tasks: list[Task], minutes: int) -> list[Task]:
        """Drop tasks once the time budget runs out."""
        raise NotImplementedError
