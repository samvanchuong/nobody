import os

import streamlit as st

from auth.login import render_login_page
from auth.register import render_register_page
from auth.session_manager import logout, restore_session
from pages.account import render_account
from pages.dashboard import render_dashboard
from pages.history import render_history
from pages.predict import render_predict
from utils.json_db import JsonDB
from utils.storage_manager import ensure_user_dirs


st.set_page_config(page_icon="🧠", page_title="Brain Tumor Detection", layout="wide")


# Initialize required files/folders
JsonDB("database/users.json", default_data={})
JsonDB("database/sessions.json", default_data={})
os.makedirs(os.path.join("storage", "users"), exist_ok=True)

restore_session()

if "page" not in st.session_state:
    st.session_state.page = "Dashboard" if st.session_state.get("authenticated") else "Login"

is_authenticated = st.session_state.get("authenticated", False)
username = st.session_state.get("username")

with st.sidebar:
    st.title("Navigation")
    if not is_authenticated:
        if st.button("Login", use_container_width=True):
            st.session_state.page = "Login"
        if st.button("Register", use_container_width=True):
            st.session_state.page = "Register"
    else:
        ensure_user_dirs(username)
        for page in ["Dashboard", "Predict Image", "History", "Account"]:
            if st.button(page, use_container_width=True):
                st.session_state.page = page
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

page = st.session_state.page

if not is_authenticated:
    if page == "Register":
        render_register_page()
    else:
        render_login_page()
else:
    if page == "Dashboard":
        render_dashboard(username)
    elif page == "Predict Image":
        render_predict(username)
    elif page == "History":
        render_history(username)
    elif page == "Account":
        render_account(username)
    else:
        render_dashboard(username)
