import streamlit as st
import database as db
import auth
from components.sidebar import render_sidebar
from views import dashboard, tasks, rewards, achievements, categories, settings

st.set_page_config(
    page_title="RPG Life",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize database
db.init_db()

# Auth gate
if not auth.is_logged_in():
    auth.render_auth_page()
else:
    user_id = auth.get_current_user_id()
    current_page = render_sidebar(user_id)

    page_map = {
        "dashboard": dashboard.render,
        "tasks": tasks.render,
        "rewards": rewards.render,
        "achievements": achievements.render,
        "categories": categories.render,
        "settings": settings.render,
    }

    render_fn = page_map.get(current_page, dashboard.render)
    render_fn(user_id)
