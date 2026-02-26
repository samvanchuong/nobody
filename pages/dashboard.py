import streamlit as st


def render_dashboard(username: str) -> None:
    st.title("Dashboard")
    st.write(f"Welcome, **{username}**!")
    st.info("You can use the sidebar to run predictions, manage your account, and view your history.")
