from __future__ import annotations

import json
import os
import shutil

import streamlit as st

from auth.register import USERS_DB


def _safe_user_file(username: str, path: str) -> str:
    user_root = os.path.abspath(os.path.join("storage", "users", username))
    file_abs = os.path.abspath(path)
    if not file_abs.startswith(user_root):
        raise ValueError("Unauthorized file path")
    return file_abs


def _safe_prediction_folder(username: str, prediction_id: str) -> str:
    user_prediction_root = os.path.abspath(os.path.join("storage", "users", username, "predictions"))
    prediction_folder = os.path.abspath(os.path.join(user_prediction_root, prediction_id))
    if not prediction_folder.startswith(user_prediction_root):
        raise ValueError("Unauthorized prediction folder")
    return prediction_folder


def render_history(username: str) -> None:
    st.title("Prediction History")
    users = USERS_DB.load()
    history = users.get(username, {}).get("history", [])

    if not history:
        st.info("No predictions yet.")
        return

    history_list = list(reversed(history))

    for idx, item in enumerate(history_list):
        original_idx = len(history) - 1 - idx
        prediction_id = item["prediction_id"]
        pred_folder = os.path.join("storage", "users", username, "predictions", prediction_id)
        input_path = os.path.join(pred_folder, "input.jpg")
        processed_path = os.path.join(pred_folder, "processed.jpg")
        metadata_path = os.path.join(pred_folder, "metadata.json")

        try:
            input_safe = _safe_user_file(username, input_path)
            processed_safe = _safe_user_file(username, processed_path)
            metadata_safe = _safe_user_file(username, metadata_path)
        except ValueError:
            st.error(f"Skipped unauthorized entry {prediction_id}")
            continue

        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if os.path.exists(input_safe):
                st.image(input_safe, caption="Input", use_container_width=True)
        with col2:
            if os.path.exists(processed_safe):
                st.image(processed_safe, caption="Processed", use_container_width=True)
        with col3:
            st.write(f"**Time:** {item.get('time', 'N/A')}")
            st.write(f"**Summary:** {item.get('summary', 'N/A')}")

            labels = []
            if os.path.exists(metadata_safe):
                with open(metadata_safe, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                labels = metadata.get("labels", [])
            st.write(f"**Labels:** {', '.join(labels) if labels else 'None'}")

            toggle_key = f"show_detail_{prediction_id}"
            show_detail = st.toggle(
                "View Details",
                key=toggle_key,
            )

            if st.button("Delete", key=f"delete_{prediction_id}_{original_idx}"):
                users[username].setdefault("history", []).pop(original_idx)
                USERS_DB.save(users)
                try:
                    pred_folder_safe = _safe_prediction_folder(username, prediction_id)
                    if os.path.isdir(pred_folder_safe):
                        shutil.rmtree(pred_folder_safe)
                except ValueError:
                    st.warning(f"Skipped deleting unauthorized prediction folder for {prediction_id}")
                st.rerun()

        if show_detail and os.path.exists(metadata_safe):
            with open(metadata_safe, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            st.image(processed_safe, caption="Full Annotated Image", use_container_width=True)
            st.write("Confidence Table")
            table_data = {"Label": [], "Confidence": [], "Box": [], "Width (px)": [], "Height (px)": []}
            for label, conf, box in zip(
                metadata.get("labels", []), metadata.get("confidences", []), metadata.get("boxes", [])
            ):
                x1, y1, x2, y2 = box
                width = int(x2) - int(x1)
                height = int(y2) - int(y1)

                table_data["Label"].append(label)
                table_data["Confidence"].append(f"{float(conf):.2f}")
                table_data["Box"].append(f"({int(x1)}, {int(y1)}, {int(x2)}, {int(y2)})")
                table_data["Width (px)"].append(width)
                table_data["Height (px)"].append(height)
            st.table(table_data)
        st.divider()
