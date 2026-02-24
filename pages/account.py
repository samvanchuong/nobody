import os

import streamlit as st

from auth.face_auth import register_face_by_camera, register_face_by_upload
from auth.register import USERS_DB


def render_account(username: str) -> None:
    st.title("Account")
    users = USERS_DB.load()
    user = users.get(username, {})

    st.write(f"**Username:** {username}")
    st.write(f"**Total predictions:** {len(user.get('history', []))}")

    profile_path = os.path.join("storage", "users", username, "face", "profile.jpg")
    if os.path.exists(profile_path):
        st.image(profile_path, caption="Profile face", width=220)
    else:
        st.warning("No profile face registered.")

    st.markdown("### Update Face Registration")
    tab1, tab2 = st.tabs(["Camera Auto Capture", "Upload Image"])

    with tab1:
        register_face_by_camera(username)

    with tab2:
        register_face_by_upload(username)
