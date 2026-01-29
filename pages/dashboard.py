import streamlit as st
import database as db
import models
from components.charts import xp_over_time_chart, category_distribution_chart, weekly_completions_chart


def render(user_id):
    stats = db.get_user_stats(user_id)

    st.header("📊 Dashboard")

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Level", stats["level"])
    col2.metric("Total XP", f"{stats['total_xp']:,}")
    col3.metric("Available Points", f"{stats['available_points']:,}")
    col4.metric("Current Streak", f"{stats['current_streak']} days")

    # XP Progress
    progress = models.xp_progress(stats["total_xp"], stats["level"])
    next_xp = models.xp_for_level(stats["level"] + 1)
    st.subheader(f"Level {stats['level']} → {stats['level'] + 1}")
    st.progress(progress, text=f"{stats['total_xp']:,} / {next_xp:,} XP")

    # Streak info
    st.markdown(f"**Longest Streak:** {stats['longest_streak']} days")

    # Convert points to XP
    if stats["available_points"] > 0:
        st.divider()
        st.subheader("Convert Points to XP")
        max_pts = stats["available_points"]
        amount = st.number_input("Points to convert (1 point = 1 XP)", min_value=1, max_value=max_pts, value=min(10, max_pts))
        if st.button("Convert to XP", type="primary"):
            if models.spend_points_on_xp(user_id, amount):
                newly_unlocked = models.check_achievements(user_id)
                st.success(f"Converted {amount} points to {amount} XP!")
                for ach in newly_unlocked:
                    st.toast(f"🏆 Achievement unlocked: {ach['name']}")
                st.rerun()

    # Charts
    st.divider()
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        fig = category_distribution_chart(user_id)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete some tasks to see category breakdown.")

    with chart_col2:
        fig = weekly_completions_chart(user_id)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Complete some tasks to see weekly trends.")

    fig = xp_over_time_chart(user_id)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    # Recent activity
    st.divider()
    st.subheader("Recent Activity")
    completions = db.get_task_completions(user_id, limit=10)
    if completions:
        for c in completions:
            st.markdown(
                f"{c['category_icon']} **{c['task_name']}** — "
                f"+{c['points_earned']} pts — {c['completed_at'][:16]}"
            )
    else:
        st.info("No activity yet. Go complete some tasks!")
