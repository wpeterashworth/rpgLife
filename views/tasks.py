import streamlit as st
import database as db
import models


def render(user_id):
    stats = db.get_user_stats(user_id)
    level = stats["level"]

    st.header("📋 Tasks")

    active_tasks = db.get_active_tasks(user_id)
    max_slots = models.get_task_slots(level)
    slots_text = "Unlimited" if max_slots == -1 else f"{len(active_tasks)} / {max_slots}"
    st.caption(f"Active task slots: {slots_text}")

    # Create task form
    can_create = max_slots == -1 or len(active_tasks) < max_slots
    if can_create:
        with st.expander("➕ Create New Task", expanded=len(active_tasks) == 0):
            categories = db.get_categories(user_id)
            cat_options = {f"{c['icon']} {c['name']}": c["id"] for c in categories}

            name = st.text_input("Task Name", key="new_task_name")
            description = st.text_area("Description (optional)", height=68, key="new_task_desc")
            col1, col2 = st.columns(2)
            with col1:
                cat_label = st.selectbox("Category", list(cat_options.keys()))
            with col2:
                difficulty = st.select_slider(
                    "Difficulty",
                    options=[1, 2, 3, 4, 5],
                    format_func=lambda d: f"{d} - {models.DIFFICULTY_LABELS[d]}",
                    value=2,
                )

            is_recurring = False
            if models.is_feature_unlocked(level, "recurring_tasks"):
                is_recurring = st.checkbox("Recurring (reappears after completion)")

            preview_pts = models.calc_points_earned(difficulty, level)
            st.info(f"Completing this will earn **{preview_pts} points**")

            if st.button("Create Task", use_container_width=True, key="create_task_btn"):
                if not name.strip():
                    st.error("Task name is required.")
                else:
                    db.create_task(user_id, cat_options[cat_label], name.strip(),
                                   description.strip(), difficulty, is_recurring)
                    st.success("Task created!")
                    st.rerun()
    else:
        st.warning(f"You've reached your task slot limit ({max_slots}). Level up to unlock more!")

    # Active tasks list
    st.divider()
    if not active_tasks:
        st.info("No active tasks. Create one above!")
        return

    for task in active_tasks:
        diff_label = models.DIFFICULTY_LABELS[task["difficulty"]]
        diff_color = models.DIFFICULTY_COLORS[task["difficulty"]]
        pts = models.calc_points_earned(task["difficulty"], level)

        with st.container(border=True):
            col1, col2, col3 = st.columns([4, 2, 2])
            with col1:
                st.markdown(
                    f"**{task['category_icon']} {task['name']}**"
                )
                if task["description"]:
                    st.caption(task["description"])
                st.markdown(
                    f"<span style='color:{diff_color};font-weight:bold;'>"
                    f"{'★' * task['difficulty']}{'☆' * (5 - task['difficulty'])} {diff_label}</span>",
                    unsafe_allow_html=True,
                )
            with col2:
                st.markdown(f"**+{pts} pts**")
                if task["is_recurring"]:
                    st.caption("🔄 Recurring")
            with col3:
                if st.button("✅ Complete", key=f"complete_{task['id']}", use_container_width=True):
                    db.complete_task(task["id"], user_id, pts)
                    models.add_points(user_id, pts)
                    models.update_streak(user_id)
                    newly_unlocked = models.check_achievements(user_id)
                    st.success(f"+{pts} points earned!")
                    for ach in newly_unlocked:
                        st.toast(f"🏆 Achievement unlocked: {ach['name']}")
                    st.rerun()
                if st.button("🗑️", key=f"delete_{task['id']}", use_container_width=True):
                    db.delete_task(task["id"], user_id)
                    st.rerun()
