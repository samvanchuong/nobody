import streamlit as st

from auth.register import USERS_DB, hash_password
from auth.session_manager import create_session


def authenticate(username: str, password: str) -> tuple[bool, str]:
    users = USERS_DB.load()
    user = users.get(username)
    if not user:
        return False, "Invalid username/password"

    if user.get("password_hash") != hash_password(password):
        return False, "Invalid username/password"

    create_session(username)
    return True, "Login successful"


def render_login_page() -> None:
    st.subheader("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login", use_container_width=True):
        ok, msg = authenticate(username, password)
        if ok:
            st.success(msg)
            st.session_state.page = "Dashboard"
            st.rerun()
        else:
            st.error(msg)
