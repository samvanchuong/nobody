from __future__ import annotations

import time

import cv2
import numpy as np
import streamlit as st
from PIL import Image

from auth.register import USERS_DB
from utils.face_encoding import extract_single_face_encoding
from utils.storage_manager import save_profile_face


def _save_user_face(username: str, encoding: np.ndarray, face_crop_bgr: np.ndarray) -> None:
    users = USERS_DB.load()
    users[username]["face_encoding"] = encoding.tolist()
    USERS_DB.save(users)
    save_profile_face(username, face_crop_bgr)


def register_face_by_upload(username: str) -> bool:
    st.markdown("#### Face registration by image upload")
    uploaded = st.file_uploader("Upload face image", type=["jpg", "jpeg", "png"], key="face_upload")
    if uploaded is None:
        return False

    pil_image = Image.open(uploaded).convert("RGB")
    image_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    try:
        encoding, (top, right, bottom, left) = extract_single_face_encoding(image_bgr)
        face_crop = image_bgr[top:bottom, left:right]
        _save_user_face(username, encoding, face_crop)
        st.success("Face registered from uploaded image")
        return True
    except ValueError as e:
        st.error(str(e))
        return False


def register_face_by_camera(username: str) -> None:
    st.markdown("#### Face registration by camera")
    if not st.button("Start camera auto-capture", key="start_camera_capture"):
        return

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Cannot access webcam")
        return

    placeholder = st.empty()
    status = st.empty()
    stable_start = None
    last_box = None

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                status.warning("No camera frame available")
                break

            display = frame.copy()
            try:
                _, (top, right, bottom, left) = extract_single_face_encoding(frame)
                curr_box = (top, right, bottom, left)
                cv2.rectangle(display, (left, top), (right, bottom), (0, 255, 0), 2)

                if last_box is None:
                    stable_start = time.time()
                else:
                    movement = sum(abs(a - b) for a, b in zip(curr_box, last_box))
                    if movement < 25:
                        stable_start = stable_start or time.time()
                    else:
                        stable_start = time.time()

                last_box = curr_box
                if stable_start and (time.time() - stable_start) >= 2.0:
                    encoding, _ = extract_single_face_encoding(frame)
                    face_crop = frame[top:bottom, left:right]
                    _save_user_face(username, encoding, face_crop)
                    status.success("Face auto-captured and registered")
                    break
                else:
                    remaining = max(0.0, 2.0 - (time.time() - (stable_start or time.time())))
                    status.info(f"Hold still... {remaining:.1f}s")

            except ValueError:
                stable_start = None
                last_box = None
                status.warning("Need exactly one face in frame")

            placeholder.image(cv2.cvtColor(display, cv2.COLOR_BGR2RGB), channels="RGB")

    finally:
        cap.release()
