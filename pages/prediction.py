from __future__ import annotations

import time
from datetime import datetime

import cv2
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from PIL import Image
from rembg import remove
from ultralytics import YOLO

from auth.register import USERS_DB
from utils.storage_manager import save_prediction_artifacts

DETECTOR_PATH = "yolo11n.pt"
MRI_MODEL_PATH = "best.pt"


@st.cache_resource
def load_models() -> tuple[YOLO, YOLO]:
    return YOLO(DETECTOR_PATH), YOLO(MRI_MODEL_PATH)


def normalize_image(image: np.ndarray) -> np.ndarray:
    return image / 255.0


def resize_image(image: np.ndarray, size: tuple[int, int] = (640, 640)) -> np.ndarray:
    return cv2.resize(image, size)


def _build_results(boxes, model_names: dict) -> tuple[dict, list, list, list]:
    table_data = {"Label": [], "Confidence": [], "Box": [], "Width (px)": [], "Height (px)": []}
    labels: list[str] = []
    confidences: list[float] = []
    boxes_meta: list[list[int]] = []

    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        cls_id = int(box.cls[0])
        label = model_names[cls_id]
        w, h = x2 - x1, y2 - y1

        labels.append(label)
        confidences.append(conf)
        boxes_meta.append([int(x1), int(y1), int(x2), int(y2)])

        table_data["Label"].append(label)
        table_data["Confidence"].append(f"{conf:.2f}")
        table_data["Box"].append(f"({int(x1)}, {int(y1)}, {int(x2)}, {int(y2)})")
        table_data["Width (px)"].append(int(w))
        table_data["Height (px)"].append(int(h))

    return table_data, labels, confidences, boxes_meta


def render_predict(username: str) -> None:
    detector_model, mri_model = load_models()

    st.title("Predict Image")
    uploaded_file = st.file_uploader("Upload an image (JPG/PNG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is None:
        st.info("🚀 Please upload an image to get started.")
        return

    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, use_container_width=True)

    image_no_background = remove(image)
    image_white = Image.new("RGB", image_no_background.size, (255, 255, 255))
    image_white.paste(image_no_background, mask=image_no_background.split()[3])

    image_cv = cv2.cvtColor(np.array(image_white), cv2.COLOR_RGB2BGR)
    resized_image = resize_image(image_cv)
    normalized_image = normalize_image(resized_image)
    normalized_image_uint8 = (normalized_image * 255).astype(np.uint8)

    progress = st.progress(0)
    for i in range(100):
        time.sleep(0.01)
        progress.progress(i + 1)

    det_results = detector_model.predict(source=normalized_image_uint8, imgsz=640, conf=0.8, verbose=False)
    det_boxes = det_results[0].boxes

    if len(det_boxes) > 0:
        st.error("⚠️ Uploaded image is not a valid MRI. Please try again.")
        return

    st.success("✅ MRI analysis completed successfully!")
    results = mri_model.predict(source=normalized_image_uint8, imgsz=640, conf=0.1, verbose=False)
    boxes = results[0].boxes
    annotated_image = results[0].plot(line_width=2)
    annotated_rgb = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)

    fig = go.Figure()
    fig.add_trace(go.Image(z=annotated_rgb))

    table_data, labels, confidences, boxes_meta = _build_results(boxes, mri_model.names)

    for idx, coords in enumerate(boxes_meta):
        x1, y1, x2, y2 = coords
        conf = confidences[idx]
        label = labels[idx]
        w, h = x2 - x1, y2 - y1
        hover_text = (
            f"<b>Label:</b> {label}<br>"
            f"<b>Confidence:</b> {conf:.2f}<br>"
            f"<b>Box:</b> ({x1}, {y1}, {x2}, {y2})<br>"
            f"<b>Size:</b> {w}×{h}px"
        )
        fig.add_trace(
            go.Scatter(
                x=[(x1 + x2) / 2],
                y=[(y1 + y2) / 2],
                mode="markers",
                marker=dict(size=10, color="red", symbol="circle"),
                hovertext=hover_text,
                hoverinfo="text",
                showlegend=False,
            )
        )

    fig.update_layout(
        autosize=True,
        xaxis=dict(showgrid=False, visible=False),
        yaxis=dict(showgrid=False, visible=False),
        margin=dict(l=0, r=0, t=0, b=0, pad=0),
        dragmode=False,
        hovermode="closest",
        showlegend=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )
    if len(boxes) > 0:
        st.table(table_data)

    metadata = {
        "timestamp": datetime.utcnow().isoformat(),
        "labels": labels,
        "confidences": confidences,
        "boxes": boxes_meta,
    }
    artifacts = save_prediction_artifacts(username, normalized_image_uint8, annotated_image, metadata)

    users = USERS_DB.load()
    users[username].setdefault("history", []).append(
        {
            "prediction_id": artifacts["prediction_id"],
            "time": metadata["timestamp"],
            "result_path": artifacts["processed_path"],
            "summary": ", ".join(sorted(set(labels))) if labels else "No tumor detected",
        }
    )
    USERS_DB.save(users)
