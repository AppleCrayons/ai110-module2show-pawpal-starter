"""Tests for the PawPal+ scheduling logic."""

from datetime import time

from pawpal_system import DailyPlan, Owner, Pet, Priority, Scheduler, Task


def test_task_fits_in():
    task = Task("Walk", 30)
    assert task.fits_in(30)
    assert task.fits_in(45)
    assert not task.fits_in(20)


def test_task_summary():
    task = Task("Morning walk", 20, Priority.HIGH)
    assert task.summary() == "Morning walk (20 min) [HIGH]"


def test_higher_priority_is_more_urgent():
    high = Task("Meds", 5, Priority.HIGH)
    low = Task("Play", 5, Priority.LOW)
    assert high.urgency_score() > low.urgency_score()


def test_conflicts_with_overlapping_windows():
    a = Task("A", 30, preferred_time="08:00")
    b = Task("B", 30, preferred_time="08:15")  # overlaps 08:00-08:30
    c = Task("C", 30, preferred_time="09:00")  # no overlap
    assert a.conflicts_with(b)
    assert not a.conflicts_with(c)


def test_flexible_tasks_never_conflict():
    a = Task("A", 30)  # no preferred_time
    b = Task("B", 30, preferred_time="08:00")
    assert not a.conflicts_with(b)


def test_pet_add_task_stamps_pet_id():
    pet = Pet(name="Mochi", species="dog", id="p1")
    task = Task("Walk", 30, id="t1")
    pet.add_task(task)
    assert task.pet_id == "p1"
    assert pet.list_tasks() == [task]


def test_pet_care_load_ignores_completed():
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 30))
    pet.add_task(Task("Done", 10, completed=True))
    assert pet.care_load() == 30
    assert pet.total_task_time() == 40


def test_owner_busiest_pet():
    owner = Owner(name="Jordan")
    light = Pet(name="Light", species="cat", id="p1")
    light.add_task(Task("Feed", 10))
    heavy = Pet(name="Heavy", species="dog", id="p2")
    heavy.add_task(Task("Walk", 60))
    owner.add_pet(light)
    owner.add_pet(heavy)
    assert owner.busiest_pet().name == "Heavy"


def test_owner_time_deficit():
    owner = Owner(name="Jordan", available_minutes=30)
    pet = Pet(name="Mochi", species="dog")
    pet.add_task(Task("Walk", 50))
    owner.add_pet(pet)
    assert owner.time_deficit() == 20


def test_scheduler_skips_when_over_budget():
    owner = Owner(name="Jordan", available_minutes=40)
    pet = Pet(name="Mochi", species="dog", id="p1")
    pet.add_task(Task("Walk", 30, Priority.HIGH, id="t1"))
    pet.add_task(Task("Grooming", 40, Priority.LOW, id="t2"))
    owner.add_pet(pet)

    plan = Scheduler().build_plan(owner)
    scheduled_titles = [i.task.title for i in plan.scheduled]
    skipped_titles = [t.title for t in plan.skipped]
    assert "Walk" in scheduled_titles       # high priority fits
    assert "Grooming" in skipped_titles      # low priority dropped


def test_scheduler_honors_fixed_time():
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog", id="p1")
    pet.add_task(
        Task("Meds", 5, Priority.HIGH, id="t1",
             preferred_time="09:00", fixed_time=True)
    )
    owner.add_pet(pet)

    plan = Scheduler().build_plan(owner)
    meds = next(i for i in plan.scheduled if i.task.title == "Meds")
    assert meds.start == time(9, 0)


def test_scheduler_slots_are_non_overlapping():
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog", id="p1")
    pet.add_task(Task("A", 30, id="t1"))
    pet.add_task(Task("B", 30, id="t2"))
    pet.add_task(Task("C", 30, id="t3"))
    owner.add_pet(pet)

    plan = Scheduler().build_plan(owner)
    items = sorted(plan.scheduled, key=lambda i: i.start)
    for earlier, later in zip(items, items[1:]):
        assert earlier.end <= later.start


def test_completed_tasks_not_scheduled():
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog", id="p1")
    pet.add_task(Task("Done", 10, id="t1", completed=True))
    owner.add_pet(pet)

    plan = Scheduler().build_plan(owner)
    assert plan.scheduled == []


def test_what_if_adds_time():
    owner = Owner(name="Jordan", available_minutes=30)
    pet = Pet(name="Mochi", species="dog", id="p1")
    pet.add_task(Task("Walk", 30, Priority.HIGH, id="t1"))
    pet.add_task(Task("Grooming", 40, Priority.LOW, id="t2"))
    owner.add_pet(pet)

    plan = Scheduler().build_plan(owner)
    assert len(plan.skipped) == 1

    better = plan.what_if(60)
    assert better.skipped == []


def test_score_plan_full_when_everything_fits():
    owner = Owner(name="Jordan", available_minutes=120)
    pet = Pet(name="Mochi", species="dog", id="p1")
    pet.add_task(Task("Walk", 30, id="t1"))
    owner.add_pet(pet)

    plan = Scheduler().build_plan(owner)
    assert plan.score_plan() == 1.0


def test_mark_complete_changes_status():
    task = Task("Walk", 30)
    assert task.completed is False   # starts open
    task.mark_complete()
    assert task.completed is True    # status actually changed


def test_add_task_increases_pet_task_count():
    pet = Pet(name="Mochi", species="dog", id="p1")
    assert len(pet.list_tasks()) == 0
    pet.add_task(Task("Walk", 30, id="t1"))
    assert len(pet.list_tasks()) == 1
    pet.add_task(Task("Feed", 10, id="t2"))
    assert len(pet.list_tasks()) == 2
