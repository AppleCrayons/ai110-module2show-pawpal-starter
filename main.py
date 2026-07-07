"""PawPal+ command-line demo.

Builds an owner with pets and tasks, then prints today's schedule.
Run with:

    python main.py
"""

from __future__ import annotations

from pawpal_system import Owner, Pet, Priority, Recurrence, Scheduler, Task


def build_owner() -> Owner:
    """Create an owner with two pets and several care tasks.

    Tasks are intentionally added *out of time order* so the sorting and
    filtering demos below have something to actually reorder.
    """
    owner = Owner(name="Jordan", available_minutes=120)

    # Pet 1 -- note the deliberately jumbled times (12:00-ish evening, then 08:00).
    mochi = Pet(name="Mochi", species="dog", age=3, id="p1")
    mochi.add_task(
        Task("Evening walk", 30, Priority.HIGH, id="t2",
             preferred_time="18:30", fixed_time=True, recurrence=Recurrence.DAILY)
    )
    mochi.add_task(Task("Enrichment play", 25, Priority.LOW, id="t3"))  # flexible
    mochi.add_task(
        Task("Morning meds", 5, Priority.HIGH, id="t1",
             preferred_time="08:00", fixed_time=True, recurrence=Recurrence.DAILY,
             completed=True)  # already done today
    )

    # Pet 2 -- also out of order.
    biscuit = Pet(name="Biscuit", species="cat", age=6, id="p2")
    biscuit.add_task(Task("Litter change", 10, Priority.MEDIUM, id="t5"))  # flexible
    biscuit.add_task(
        Task("Feeding", 10, Priority.HIGH, id="t4",
             preferred_time="12:00", fixed_time=True, recurrence=Recurrence.WEEKLY)
    )
    # Deliberately clashes with Feeding at 12:00 to exercise conflict detection.
    biscuit.add_task(
        Task("Nail trim", 15, Priority.MEDIUM, id="t6",
             preferred_time="12:00", fixed_time=True)
    )

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

    # --- Lightweight conflict detection: warn, don't crash ---
    warning = plan.conflict_warning()
    if warning:
        print("\n" + warning)
    else:
        print("\nNo scheduling conflicts.")

    # --- Demo: sorting and filtering methods ---
    scheduler = Scheduler()
    all_tasks = owner.filter_tasks()  # every task across all pets

    print("\nTasks as added (unsorted):")
    for task in all_tasks:
        print(f"  {task.preferred_time or '--:--'}  {task.title}")

    print("\nSorted by time (Scheduler.sort_by_time):")
    for task in scheduler.sort_by_time(all_tasks):
        print(f"  {task.preferred_time or '--:--'}  {task.title}")

    print("\nOpen tasks only (filter_tasks completed=False):")
    for task in owner.filter_tasks(completed=False):
        print(f"  - {task.title}")

    print("\nMochi's tasks (filter_tasks pet_name='Mochi'):")
    for task in owner.filter_tasks(pet_name="Mochi"):
        status = "done" if task.completed else "open"
        print(f"  - {task.title} ({status})")

    # --- Demo: recurring tasks respawn on completion ---
    biscuit = owner.get_pet("p2")
    print("\nBiscuit's tasks before completing 'Feeding' (weekly):")
    for task in biscuit.list_tasks():
        print(f"  - {task.id}: {task.title} "
              f"({task.recurrence.value}, {'done' if task.completed else 'open'})")

    upcoming = biscuit.complete_task("t4")  # weekly -> should respawn
    print(f"\nCompleted 't4'. Auto-created next occurrence: "
          f"{upcoming.id if upcoming else None}")

    print("Biscuit's tasks after completing 'Feeding':")
    for task in biscuit.list_tasks():
        print(f"  - {task.id}: {task.title} "
              f"({task.recurrence.value}, {'done' if task.completed else 'open'})")


if __name__ == "__main__":
    main()
