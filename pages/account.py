import os

import streamlit as st

from auth.face_auth import register_face_by_upload
from auth.register import USERS_DB, hash_password, is_valid_email


def render_account_settings(username: str, user: dict) -> None:
    st.markdown("### Account Settings")

    st.markdown("##### Change Email")
    new_email = st.text_input("New Email", value=user.get("email", ""), key="account_new_email")
    if st.button("Save Email", use_container_width=True, key="save_email_button"):
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

    st.markdown("##### Change Password")
    current_password = st.text_input("Current Password", type="password", key="account_current_password")
    new_password = st.text_input("New Password", type="password", key="account_new_password")
    confirm_password = st.text_input("Confirm New Password", type="password", key="account_confirm_password")

    if st.button("Save Password", use_container_width=True, key="save_password_button"):
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
    st.markdown(
        """
        <style>
            div[data-baseweb="tab"] p {
                font-size: 1.05rem;
                font-weight: 600;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    users = USERS_DB.load()
    user = users.get(username, {})

    profile_path = os.path.join("storage", "users", username, "face", "profile.jpg")

    col_image, col_info = st.columns([1, 4], gap="small")
    with col_image:
        if os.path.exists(profile_path):
            st.image(profile_path, caption="Profile face", width=150)
        else:
            st.info("No profile face registered")

    with col_info:
        st.markdown("### Profile")
        st.markdown(f"**Username:** {username}")
        st.markdown(f"**Email:** {user.get('email', 'Not set')}")
        st.markdown(f"**Total predictions:** {len(user.get('history', []))}")

    st.divider()
    tab1, tab2 = st.tabs(["Account Settings", "Upload Image"])

    with tab1:
        render_account_settings(username, user)

    with tab2:
        st.markdown("### Upload Image")
        st.markdown("#### Update Face Registration")
        upload_success = register_face_by_upload(username)
        if upload_success and os.path.exists(profile_path):
            st.image(profile_path, caption="Updated profile preview", width=180)

