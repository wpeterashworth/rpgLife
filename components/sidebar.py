import streamlit as st
import database as db
import models


def render_sidebar(user_id):
    stats = db.get_user_stats(user_id)
    username = st.session_state.get("username", "Adventurer")

    with st.sidebar:
        st.markdown(f"### ⚔️ {username}")
        st.markdown(f"**Level {stats['level']}**")

        progress = models.xp_progress(stats["total_xp"], stats["level"])
        next_xp = models.xp_for_level(stats["level"] + 1)
        st.progress(progress, text=f"XP: {stats['total_xp']:,} / {next_xp:,}")

        col1, col2 = st.columns(2)
        col1.metric("Points", f"{stats['available_points']:,}")
        col2.metric("Streak", f"{stats['current_streak']}🔥")

        st.divider()

        pages = {
            "📊 Dashboard": "dashboard",
            "📋 Tasks": "tasks",
            "🎁 Rewards": "rewards",
            "🏆 Achievements": "achievements",
            "📁 Categories": "categories",
            "⚙️ Settings": "settings",
        }

        current = st.session_state.get("current_page", "dashboard")
        for label, page_key in pages.items():
            if st.button(label, use_container_width=True, key=f"nav_{page_key}",
                         type="primary" if current == page_key else "secondary"):
                st.session_state["current_page"] = page_key
                st.rerun()

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            from auth import logout
            logout()
            st.rerun()

    return st.session_state.get("current_page", "dashboard")
