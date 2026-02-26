import hashlib
import re

import streamlit as st

from utils.json_db import JsonDB


USERS_DB = JsonDB("database/users.json", default_data={})


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def is_valid_email(email: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()))


def register_user(username: str, password: str, email: str, confirm: str) -> tuple[bool, str]:
    username = username.strip()
    email = email.strip()
    if not username or not password or not email:
        return False, "Please complete all required information."

    if not is_valid_email(email):
        return False, "Please enter a valid email address."

    if password != confirm:
        return False, "Passwords do not match."

    users = USERS_DB.load()
    if username in users:
        return False, "This username already exists."

    users[username] = {
        "password_hash": hash_password(password),
        "email": email,
        "face_registration": False,
        "face_encoding": [],
        "history": [],
    }
    USERS_DB.save(users)
    return True, "Account created successfully. Please register your facial data on the Account page."


def render_register_page() -> None:
    st.title("Register")
    username = st.text_input("Username", key="register_username")
    email = st.text_input("Email", key="register_email")
    password = st.text_input("Password", type="password", key="register_password")
    confirm = st.text_input("Confirm Password", type="password", key="register_confirm")

    if st.button("Register", use_container_width=True):
        ok, msg = register_user(username, password, email, confirm)
        if ok:
            st.success(msg)
            st.session_state.page = "Login"
        else:
            st.warning(msg)
