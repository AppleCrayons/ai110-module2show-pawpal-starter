import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# Map the UI's lowercase priority strings to the Priority enum from the backend.
PRIORITY_MAP = {"low": Priority.LOW, "medium": Priority.MEDIUM, "high": Priority.HIGH}

# The Owner lives in the session "vault" so pets/tasks persist across reruns.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)
owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)
owner.available_minutes = int(
    st.number_input(
        "Available minutes today",
        min_value=0,
        max_value=1440,
        value=owner.available_minutes,
    )
)

st.divider()

# --- Adding a Pet: calls Owner.add_pet() ---
st.subheader("Add a Pet")
pcol1, pcol2, pcol3 = st.columns(3)
with pcol1:
    pet_name = st.text_input("Pet name", value="Mochi")
with pcol2:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with pcol3:
    age = st.number_input("Age", min_value=0, max_value=40, value=1)

if st.button("Add pet"):
    new_pet = Pet(
        name=pet_name,
        species=species,
        age=int(age),
        id=f"p{len(owner.pets) + 1}",
    )
    owner.add_pet(new_pet)
    st.success(f"Added {new_pet.name} the {new_pet.species}.")

if owner.list_pets():
    st.write("Pets:", ", ".join(f"{p.name} ({p.species})" for p in owner.list_pets()))
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Scheduling a Task: calls Pet.add_task() ---
st.subheader("Add a Task")
if not owner.list_pets():
    st.info("Add a pet first, then you can give it tasks.")
else:
    pet_choices = {f"{p.name} ({p.species})": p for p in owner.list_pets()}
    chosen_label = st.selectbox("For which pet?", list(pet_choices))

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    col4, col5 = st.columns(2)
    with col4:
        preferred_time = st.text_input("Preferred time (HH:MM, optional)", value="")
    with col5:
        fixed_time = st.checkbox("Must run at that exact time")

    if st.button("Add task"):
        pet = pet_choices[chosen_label]
        total_tasks = sum(len(p.tasks) for p in owner.list_pets())
        pet.add_task(
            Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=PRIORITY_MAP[priority],
                id=f"t{total_tasks + 1}",
                preferred_time=preferred_time.strip(),
                fixed_time=bool(fixed_time) and bool(preferred_time.strip()),
            )
        )
        st.success(f"Added '{task_title}' to {pet.name}.")

# --- Show current tasks: filtered (Owner.filter_tasks) + sorted chronologically
# (Scheduler.sort_by_time) so the data reads like a real daily agenda. ---
scheduler = Scheduler()

if any(pet.list_tasks() for pet in owner.list_pets()):
    st.markdown("#### Current tasks")
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        status_filter = st.selectbox(
            "Show", ["All", "Open only", "Completed only"], index=0
        )
    with fcol2:
        sort_by_time = st.checkbox("Sort by time of day", value=True)

    completed_flag = {"All": None, "Open only": False, "Completed only": True}[
        status_filter
    ]

    for pet in owner.list_pets():
        tasks = owner.filter_tasks(completed=completed_flag, pet_name=pet.name)
        if not tasks:
            continue
        if sort_by_time:
            tasks = scheduler.sort_by_time(tasks)
        st.write(f"**{pet.name}** — {pet.care_load()} min of open care:")
        st.table(
            [
                {
                    "task": t.title,
                    "min": t.duration_minutes,
                    "priority": t.priority.name,
                    "time": t.preferred_time or "flexible",
                    "status": "done" if t.completed else "open",
                }
                for t in tasks
            ]
        )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# --- Build Schedule: calls Scheduler.build_plan() ---
st.subheader("Build Schedule")
st.caption("Ranks tasks by urgency, drops what won't fit the time budget, and slots the rest.")

if st.button("Generate schedule"):
    plan = scheduler.build_plan(owner)

    if plan.scheduled:
        st.markdown("### Today's Schedule")
        st.table(
            [
                {
                    "start": item.start.strftime("%H:%M"),
                    "end": item.end.strftime("%H:%M"),
                    "task": item.task.title,
                    "pet": owner.get_pet(item.task.pet_id).name,
                    "priority": item.task.priority.name,
                }
                for item in plan.scheduled
            ]
        )

        # Surface time-slot collisions via the Scheduler's conflict methods.
        warning = plan.conflict_warning()
        if warning:
            st.warning(warning)
        else:
            st.success("No scheduling conflicts — every task has a clear slot. ✅")
    else:
        st.info("Nothing scheduled — add some tasks and time budget first.")

    if plan.skipped:
        st.warning("Skipped (ran out of time): " + ", ".join(t.title for t in plan.skipped))

    mcol1, mcol2 = st.columns(2)
    mcol1.metric("Plan quality", f"{plan.score_plan():.0%}")
    mcol2.metric("Time deficit", f"{owner.time_deficit()} min")

    with st.expander("Why this plan?"):
        st.text(plan.explain())
