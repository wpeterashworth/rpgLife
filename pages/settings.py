import streamlit as st
import database as db
import models


def render(user_id):
    stats = db.get_user_stats(user_id)
    username = st.session_state.get("username", "")

    st.header("⚙️ Settings")

    st.subheader("Profile")
    st.markdown(f"**Username:** {username}")
    st.markdown(f"**Account created:** {_get_created_at(user_id)}")

    st.divider()
    st.subheader("Stats Overview")
    total_completions = db.get_total_completions(user_id)
    redemptions = db.get_redemption_count(user_id)

    col1, col2, col3 = st.columns(3)
    col1.metric("Tasks Completed", total_completions)
    col2.metric("Rewards Redeemed", redemptions)
    col3.metric("Longest Streak", f"{stats['longest_streak']} days")

    st.divider()
    st.subheader("Feature Unlocks")
    for feature, req_level in sorted(models.FEATURE_UNLOCKS.items(), key=lambda x: x[1]):
        label = feature.replace("_", " ").title()
        unlocked = stats["level"] >= req_level
        icon = "✅" if unlocked else "🔒"
        st.markdown(f"{icon} **{label}** — Level {req_level}")

    st.divider()
    st.subheader("Point Multiplier")
    mult = models.level_multiplier(stats["level"])
    st.markdown(f"Current multiplier: **{mult:.1f}x** (Level {stats['level']})")
    st.caption("Earn 10% more base points per level.")

    st.divider()
    st.subheader("Level Progression")
    for lvl in range(stats["level"], min(stats["level"] + 5, 51)):
        xp_needed = models.xp_for_level(lvl + 1)
        st.caption(f"Level {lvl} → {lvl + 1}: {xp_needed:,} XP")


def _get_created_at(user_id):
    conn = db.get_connection()
    row = conn.execute("SELECT created_at FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row["created_at"][:10] if row else "Unknown"
