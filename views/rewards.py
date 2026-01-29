import streamlit as st
import database as db
import models


def render(user_id):
    stats = db.get_user_stats(user_id)
    st.header("🎁 Rewards")
    st.metric("Available Points", f"{stats['available_points']:,}")

    # Form reset counter
    if "reward_form_counter" not in st.session_state:
        st.session_state.reward_form_counter = 0
    rc = st.session_state.reward_form_counter

    # Create reward
    with st.expander("➕ Create New Reward"):
        name = st.text_input("Reward Name", key=f"new_reward_name_{rc}")
        description = st.text_area("Description (optional)", height=68, key=f"new_reward_desc_{rc}")
        value = st.select_slider(
            "Value Tier",
            options=[1, 2, 3, 4, 5],
            format_func=lambda v: f"Tier {v} — {models.reward_cost(v)} pts",
            value=1,
            key=f"new_reward_value_{rc}",
        )

        cost = models.reward_cost(value)
        st.info(f"This reward will cost **{cost} points** to redeem.")

        if st.button("Create Reward", use_container_width=True, key=f"create_reward_btn_{rc}"):
            if not name.strip():
                st.error("Reward name is required.")
            else:
                db.create_reward(user_id, name.strip(), description.strip(), value, cost)
                st.success("Reward created!")
                st.session_state.reward_form_counter += 1
                st.rerun()

    # Reward shop
    st.divider()
    st.subheader("Reward Shop")
    rewards = db.get_rewards(user_id)

    if not rewards:
        st.info("No rewards yet. Create one above!")
    else:
        for reward in rewards:
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 2, 2])
                with col1:
                    st.markdown(f"**{reward['name']}**")
                    if reward["description"]:
                        st.caption(reward["description"])
                    stars = "⭐" * reward["value"]
                    st.markdown(f"Tier {reward['value']} {stars}")
                with col2:
                    st.markdown(f"**{reward['point_cost']:,} pts**")
                    can_afford = stats["available_points"] >= reward["point_cost"]
                    if can_afford:
                        st.caption("✅ Affordable")
                    else:
                        needed = reward["point_cost"] - stats["available_points"]
                        st.caption(f"Need {needed:,} more")
                with col3:
                    if st.button("🛒 Redeem", key=f"redeem_{reward['id']}",
                                 disabled=not can_afford, use_container_width=True):
                        if models.spend_points_on_reward(user_id, reward["id"], reward["point_cost"]):
                            newly_unlocked = models.check_achievements(user_id)
                            st.success(f"Redeemed: {reward['name']}!")
                            for ach in newly_unlocked:
                                st.toast(f"🏆 Achievement unlocked: {ach['name']}")
                            st.rerun()
                    if st.button("🗑️", key=f"del_reward_{reward['id']}", use_container_width=True):
                        db.delete_reward(reward["id"], user_id)
                        st.rerun()

    # Redemption history
    st.divider()
    st.subheader("Redemption History")
    history = db.get_redemption_history(user_id)
    if history:
        for h in history:
            st.markdown(
                f"⭐ **{h['reward_name']}** — {h['points_spent']:,} pts — {h['redeemed_at'][:16]}"
            )
    else:
        st.info("No redemptions yet.")
