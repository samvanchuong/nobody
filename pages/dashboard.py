import streamlit as st


def render_dashboard(username: str) -> None:
    st.title("🧠 Brain Tumor AI Dashboard")
    st.write(f"Welcome, **{username}**")
    st.info("Use sidebar to run predictions, manage your account, and review history.")
