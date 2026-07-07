"""PawPal+ command-line demo.

Builds an owner with pets and tasks, then prints today's schedule.
Run with:

    python main.py
"""

from __future__ import annotations

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def build_owner() -> Owner:
    """Create an owner with two pets and several care tasks at different times."""
    owner = Owner(name="Jordan", available_minutes=120)

    # Pet 1
    mochi = Pet(name="Mochi", species="dog", age=3, id="p1")
    mochi.add_task(
        Task("Morning meds", 5, Priority.HIGH, id="t1",
             preferred_time="08:00", fixed_time=True, is_recurring=True)
    )
    mochi.add_task(
        Task("Morning walk", 30, Priority.HIGH, id="t2",
             preferred_time="08:30", fixed_time=True, is_recurring=True)
    )
    mochi.add_task(Task("Enrichment play", 25, Priority.LOW, id="t3"))

    # Pet 2
    biscuit = Pet(name="Biscuit", species="cat", age=6, id="p2")
    biscuit.add_task(
        Task("Feeding", 10, Priority.HIGH, id="t4",
             preferred_time="12:00", fixed_time=True, is_recurring=True)
    )
    biscuit.add_task(Task("Litter change", 10, Priority.MEDIUM, id="t5"))

    owner.add_pet(mochi)
    owner.add_pet(biscuit)
    return owner


def main() -> None:
    owner = build_owner()
    plan = Scheduler().build_plan(owner)

    print("Today's Schedule")
    print("=" * 40)
    for item in plan.scheduled:
        start = item.start.strftime("%H:%M")
        pet = owner.get_pet(item.task.pet_id)
        print(f"  {start}  {item.task.title} ({pet.name}) [{item.task.priority.name}]")

    if plan.skipped:
        print("\nNot scheduled (out of time):")
        for task in plan.skipped:
            print(f"  - {task.title}")


if __name__ == "__main__":
    main()
