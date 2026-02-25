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
        if st.button("Start Face Login", use_container_width=True):
            ok, msg, username = authenticate_face_login()
            if ok:
                st.success(msg)
                st.session_state.page = "Dashboard"
                st.session_state.username = username
                st.rerun()
            else:
                st.error(msg)


def authenticate_face_login() -> tuple[bool, str, str | None]:
    try:
        import cv2
        from utils.face_encoding import extract_single_face_encoding, is_face_match
    except Exception:
        return False, "Camera support is unavailable in this environment.", None

    capture = cv2.VideoCapture(0)
    if not capture.isOpened():
        return False, "Unable to access camera. Please check camera permissions.", None

    try:
        frame = None
        for _ in range(20):
            ok, grabbed = capture.read()
            if not ok:
                continue
            frame = grabbed
            break

        if frame is None:
            return False, "Could not capture image from camera.", None

        try:
            candidate_encoding, _ = extract_single_face_encoding(frame)
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
    finally:
        capture.release()
