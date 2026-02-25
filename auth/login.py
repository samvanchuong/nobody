import numpy as np
import streamlit as st
from PIL import Image

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

    tab_password, tab_face = st.tabs(["Password Login", "Face Login"])

    with tab_password:
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

    with tab_face:
        st.caption("Use your webcam to authenticate with your registered face.")
        captured_image = st.camera_input("Capture face", key="face_login_camera")

        if st.button("Start Face Login", use_container_width=True):
            ok, msg, username = authenticate_face_login(captured_image)
            if ok:
                st.success(msg)
                st.session_state.page = "Dashboard"
                st.session_state.username = username
                st.rerun()
            else:
                st.error(msg)


def authenticate_face_login(captured_image) -> tuple[bool, str, str | None]:
    if captured_image is None:
        return False, "Please capture a photo to continue.", None

    try:
        from utils.face_encoding import extract_single_face_encoding, is_face_match
    except Exception:
        return False, "Face authentication support is unavailable in this environment.", None

    try:
        image = Image.open(captured_image).convert("RGB")
    except Exception:
        return False, "Could not read captured image.", None

    image_bgr = np.array(image)[:, :, ::-1]

    try:
        candidate_encoding, _ = extract_single_face_encoding(image_bgr)
    except ValueError:
        return False, "Authentication failed: no detectable single face found.", None

    users = USERS_DB.load()
    for username, user in users.items():
        if not user.get("face_registration"):
            continue

        stored_encoding = user.get("face_encoding")
        if not stored_encoding:
            continue

        if is_face_match(stored_encoding, candidate_encoding, threshold=0.5):
            create_session(username)
            return True, "Face login successful", username

    return False, "Authentication failed: no matching face found.", None
