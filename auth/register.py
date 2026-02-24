import hashlib
import re

import streamlit as st

from utils.json_db import JsonDB


USERS_DB = JsonDB("database/users.json", default_data={})
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_PATTERN.match(email.strip()))


def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    username = username.strip()
    email = email.strip()
    if not username or not email or not password:
        return False, "Username, email, and password are required"
    if not is_valid_email(email):
        return False, "Invalid email format"

    users = USERS_DB.load()
    if username in users:
        return False, "Username already exists"

    users[username] = {
        "email": email,
        "password_hash": hash_password(password),
        "face_encoding": [],
        "history": [],
    }
    USERS_DB.save(users)
    return True, "User created. Please register face data in Account page."


def render_register_page() -> None:
    st.subheader("Create Account")
    username = st.text_input("Username", key="register_username")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_password")
    confirm = st.text_input("Confirm Password", type="password", key="register_confirm")

    if st.button("Register", use_container_width=True):
        if password != confirm:
            st.error("Passwords do not match")
            return
        ok, msg = register_user(username, email, password)
        if ok:
            st.success(msg)
            st.session_state.page = "Login"
        else:
            st.error(msg)
