import hashlib
import os
import streamlit as st
import database as db


def _hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(32).hex()
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return hashed, salt


def signup(username, password):
    password_hash, salt = _hash_password(password)
    user_id = db.create_user(username, password_hash, salt)
    return user_id


def login(username, password):
    user = db.get_user_by_username(username)
    if user is None:
        return None
    hashed, _ = _hash_password(password, user["salt"])
    if hashed == user["password_hash"]:
        return user
    return None


def get_current_user_id():
    return st.session_state.get("user_id")


def is_logged_in():
    return "user_id" in st.session_state


def logout():
    for key in ["user_id", "username"]:
        st.session_state.pop(key, None)


def render_auth_page():
    st.markdown(
        "<h1 style='text-align:center;'>⚔️ RPG Life</h1>"
        "<p style='text-align:center;'>Gamify your productivity</p>",
        unsafe_allow_html=True,
    )

    tab_login, tab_signup = st.tabs(["Login", "Sign Up"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.error("Please fill in all fields.")
                else:
                    user = login(username, password)
                    if user:
                        st.session_state["user_id"] = user["id"]
                        st.session_state["username"] = user["username"]
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

    with tab_signup:
        with st.form("signup_form"):
            username = st.text_input("Username", key="signup_user")
            password = st.text_input("Password", type="password", key="signup_pass")
            confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
            submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                if not username or not password:
                    st.error("Please fill in all fields.")
                elif len(password) < 4:
                    st.error("Password must be at least 4 characters.")
                elif password != confirm:
                    st.error("Passwords do not match.")
                else:
                    user_id = signup(username, password)
                    if user_id:
                        st.session_state["user_id"] = user_id
                        st.session_state["username"] = username
                        st.rerun()
                    else:
                        st.error("Username already taken.")
