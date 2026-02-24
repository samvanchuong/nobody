import os

import streamlit as st

from auth.face_auth import register_face_by_upload
from auth.register import USERS_DB, hash_password, is_valid_email


def render_account_settings(username: str, user: dict) -> None:
    st.markdown("#### Account Settings")

    with st.form("account_email_form", clear_on_submit=False):
        new_email = st.text_input("New Email", value=user.get("email", ""), key="account_new_email")
        save_email = st.form_submit_button("Save Email", use_container_width=True)

    if save_email:
        email = new_email.strip()
        if not is_valid_email(email):
            st.error("Please enter a valid email address")
        else:
            users = USERS_DB.load()
            if username not in users:
                st.error("User not found")
                return
            users[username]["email"] = email
            USERS_DB.save(users)
            st.success("Email updated successfully")

    with st.form("account_password_form", clear_on_submit=True):
        current_password = st.text_input("Current Password", type="password", key="account_current_password")
        new_password = st.text_input("New Password", type="password", key="account_new_password")
        confirm_password = st.text_input("Confirm New Password", type="password", key="account_confirm_password")
        save_password = st.form_submit_button("Save Password", use_container_width=True)

    if save_password:
        if hash_password(current_password) != user.get("password_hash"):
            st.error("Current password is incorrect")
        elif not new_password:
            st.error("New password is required")
        elif new_password != confirm_password:
            st.error("New password and confirmation do not match")
        else:
            users = USERS_DB.load()
            if username not in users:
                st.error("User not found")
                return
            users[username]["password_hash"] = hash_password(new_password)
            USERS_DB.save(users)
            st.success("Password updated successfully")


def render_account(username: str) -> None:
    st.title("Account")
    users = USERS_DB.load()
    user = users.get(username, {})

    profile_path = os.path.join("storage", "users", username, "face", "profile.jpg")

    col1, col2 = st.columns([2, 1], gap="medium")
    with col1:
        st.markdown("### Profile")
        st.markdown(f"**Username:** {username}")
        st.markdown(f"**Email:** {user.get('email', 'Not set')}")
        st.markdown(f"**Total predictions:** {len(user.get('history', []))}")

    with col2:
        if os.path.exists(profile_path):
            st.image(profile_path, caption="Profile face", width=220)
        else:
            st.info("No profile face registered")

    st.divider()
    tab1, tab2 = st.tabs(["Account Settings", "Upload Image"])

    with tab1:
        render_account_settings(username, user)

    with tab2:
        st.markdown("#### Update Face Registration")
        register_face_by_upload(username)
