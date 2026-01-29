import streamlit as st
import database as db
import models


def render(user_id):
    st.header("🏆 Achievements")

    all_achievements = db.get_all_achievements()
    unlocked = db.get_user_achievements(user_id)
    progress_fn = models.get_achievement_progress(user_id)

    unlocked_count = len(unlocked)
    total_count = len(all_achievements)
    st.progress(unlocked_count / total_count if total_count else 0,
                text=f"{unlocked_count} / {total_count} unlocked")

    # Group by category
    categories = {}
    for ach in all_achievements:
        cat = ach["category"]
        categories.setdefault(cat, []).append(ach)

    category_labels = {
        "consistency": "🔥 Consistency",
        "intensity": "⚡ Intensity",
        "specialization": "🎯 Specialization",
        "leveling": "⭐ Leveling",
        "economy": "💰 Economy",
    }

    for cat_key, achs in categories.items():
        st.subheader(category_labels.get(cat_key, cat_key.title()))
        cols = st.columns(min(len(achs), 3))
        for i, ach in enumerate(achs):
            is_unlocked = ach["id"] in unlocked
            col = cols[i % len(cols)]
            with col:
                with st.container(border=True):
                    if is_unlocked:
                        st.markdown(f"### {ach['icon']} {ach['name']}")
                        st.caption(ach["description"])
                        st.success(f"Unlocked: {unlocked[ach['id']][:10]}")
                    else:
                        st.markdown(f"### 🔒 {ach['name']}")
                        st.caption(ach["description"])
                        prog = progress_fn(ach["requirement_type"], ach["requirement_value"])
                        st.progress(prog, text=f"{int(prog * 100)}%")
