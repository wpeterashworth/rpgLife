import streamlit as st
import database as db
import models


def render(user_id):
    stats = db.get_user_stats(user_id)
    level = stats["level"]

    st.header("📁 Categories")

    categories = db.get_categories(user_id)

    # Default categories
    st.subheader("Default Categories")
    for cat in categories:
        if cat["is_default"]:
            st.markdown(f"{cat['icon']} **{cat['name']}**")

    # Custom categories
    st.divider()
    st.subheader("Custom Categories")

    if not models.is_feature_unlocked(level, "custom_categories"):
        st.warning(f"Custom categories unlock at level {models.FEATURE_UNLOCKS['custom_categories']}. "
                   f"You are level {level}.")
        return

    custom_cats = [c for c in categories if not c["is_default"]]
    if custom_cats:
        for cat in custom_cats:
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 1, 1])
                with col1:
                    st.markdown(f"{cat['icon']} **{cat['name']}**")
                    color = cat['color']
                    st.markdown(
                        f"<span style='display:inline-block;width:16px;height:16px;"
                        f"background:{color};border-radius:3px;'></span> {color}",
                        unsafe_allow_html=True,
                    )
                with col3:
                    if st.button("🗑️", key=f"del_cat_{cat['id']}"):
                        db.delete_category(cat["id"])
                        st.rerun()
    else:
        st.info("No custom categories yet.")

    # Add new
    with st.expander("➕ Add Custom Category"):
        with st.form("add_category"):
            name = st.text_input("Category Name")
            icon = st.text_input("Icon (emoji)", value="📌")
            color = st.color_picker("Color", value="#4A90D9")
            if st.form_submit_button("Add Category", use_container_width=True):
                if not name.strip():
                    st.error("Name is required.")
                else:
                    db.create_category(user_id, name.strip(), icon.strip(), color)
                    st.success(f"Category '{name}' created!")
                    st.rerun()
