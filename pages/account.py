import os

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from auth.register import USERS_DB, hash_password, is_valid_email
from utils.face_encoding import extract_single_face_encoding
from utils.storage_manager import ensure_user_dirs


def _update_password(username: str, current_password: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    users = USERS_DB.load()
    user = users.get(username)
    if not user:
        return False, "User not found"

    if user.get("password_hash") != hash_password(current_password):
        return False, "Current password is incorrect"

    if not new_password:
        return False, "New password is required"

    if new_password != confirm_password:
        return False, "New passwords do not match"

    user["password_hash"] = hash_password(new_password)
    USERS_DB.save(users)
    return True, "Password updated successfully"


def _update_email(username: str, email: str) -> tuple[bool, str]:
    users = USERS_DB.load()
    user = users.get(username)
    if not user:
        return False, "User not found"

    email = email.strip()
    if not email:
        return False, "Email is required"
    if not is_valid_email(email):
        return False, "Please enter a valid email address"

    user["email"] = email
    USERS_DB.save(users)
    return True, "Email updated successfully"


def _save_avatar_upload(username: str, uploaded_file) -> tuple[bool, str]:
    if uploaded_file is None:
        return False, "Please select an image"

    pil_image = Image.open(uploaded_file).convert("RGB")
    image_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    try:
        encoding, _ = extract_single_face_encoding(image_bgr)
    except ValueError as e:
        return False, str(e)

    dirs = ensure_user_dirs(username)
    profile_path = os.path.join(dirs["face"], "profile.jpg")
    pil_image.save(profile_path, format="JPEG")

    users = USERS_DB.load()
    user = users.get(username)
    if not user:
        return False, "User not found"

    user["face_registration"] = True
    user["face_encoding"] = encoding.tolist()
    USERS_DB.save(users)

    return True, "Avatar uploaded and face registered successfully"


def render_account(username: str) -> None:
    st.title("Account")
    users = USERS_DB.load()
    user = users.get(username, {})

    dirs = ensure_user_dirs(username)
    profile_path = os.path.join(dirs["face"], "profile.jpg")

    avatar_col, info_col = st.columns([2, 3], vertical_alignment="top")
    with avatar_col:
        if os.path.exists(profile_path):
            avatar_image = Image.open(profile_path).convert("RGB")
            square_avatar = avatar_image.resize((200, 200))
            st.image(square_avatar, caption="Profile Avatar", width=200)
        else:
            st.warning("No profile avatar uploaded.")

    with info_col:
        st.write(f"**Username:** {username}")
        st.write(f"**Email:** {user.get('email', 'Not set')}")
        st.write(f"**Total predictions:** {len(user.get('history', []))}")

    tab_password, tab_avatar, tab_email = st.tabs(["Change Password", "Upload Avatar", "Change Email"])

    with tab_password:
        current_password = st.text_input("Current Password", type="password", key="account_current_password")
        new_password = st.text_input("New Password", type="password", key="account_new_password")
        confirm_password = st.text_input("Confirm New Password", type="password", key="account_confirm_new_password")
        if st.button("Update Password", key="account_update_password"):
            ok, msg = _update_password(username, current_password, new_password, confirm_password)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    with tab_avatar:
        upload_success = st.session_state.pop("account_avatar_upload_success", None)
        if upload_success:
            st.success(upload_success)

        uploaded = st.file_uploader("Upload avatar image", type=["jpg", "jpeg", "png"], key="account_avatar_upload")

        last_processed_name = st.session_state.get("account_avatar_processed_name")
        if uploaded is not None and uploaded.name != last_processed_name:
            ok, msg = _save_avatar_upload(username, uploaded)
            st.session_state["account_avatar_processed_name"] = uploaded.name
            if ok:
                st.session_state["account_avatar_upload_success"] = msg
                st.rerun()
            else:
                st.error(msg)

    with tab_email:
        new_email = st.text_input("New Email", value=user.get("email", ""), key="account_new_email")
        if st.button("Update Email", key="account_update_email"):
            ok, msg = _update_email(username, new_email)
            if ok:
                st.success(msg)
            else:
                st.error(msg)
