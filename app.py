import streamlit as st
from ultralytics import YOLO
import tempfile
import os
from gtts import gTTS
import requests
from datetime import datetime
import cv2
import time
import pandas as pd

# ========================
# CONFIGURATION
# ========================

# Load Telegram token from Streamlit Cloud secrets
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]

# Replace these with your real chat IDs later
CHAT_IDS = [
    "5455011626",
    "CHAT_ID_2",
    "CHAT_ID_3"
]

# Hardcoded South-South Nigeria coordinates
LOCATION_COORDS = "Latitude: 4.8156, Longitude: 7.0498 (Port Harcourt, Nigeria)"

# YOLO model filename
MODEL_PATH = "yolov8_trained.pt"

# ========================
# TELEGRAM SEND FUNCTION
# ========================
def send_telegram_message(text, image_path=None):
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        requests.post(url, data=payload)

        # Send image if available
        if image_path:
            url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            with open(image_path, "rb") as img:
                requests.post(url_photo, data={"chat_id": chat_id}, files={"photo": img})

# ========================
# STREAMLIT UI
# ========================

# Sidebar
st.sidebar.title("System Information")
st.sidebar.write("**Model Version:** YOLO v9")
st.sidebar.write("**Current Mode:** MVP / Demo")
st.sidebar.write("**Human-in-the-Loop:** Simulated")
st.sidebar.write("**Alert Recipients:**")
for idx, chat_id in enumerate(CHAT_IDS, 1):
    st.sidebar.write(f"{idx}. {chat_id} (placeholder)")

# Title & Subtitle
st.title("Weapon Detection & Alert System")
st.subheader("AI-Powered Security Monitoring")

# Upload file
uploaded_file = st.file_uploader("Upload Image or Video", type=["jpg", "png", "jpeg", "mp4", "avi"])

# Load YOLO model
model = YOLO(MODEL_PATH)

# Initialize log DataFrame
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=["Time", "Event", "Details"])

# Function to append log
def log_event(event, details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.log_df.loc[len(st.session_state.log_df)] = [timestamp, event, details]

# Display logs
st.write("### Event Log")
st.dataframe(st.session_state.log_df)

# ========================
# PROCESS UPLOADED FILE
# ========================
if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}")
    temp_file.write(uploaded_file.read())
    temp_file_path = temp_file.name

    st.write("### Input Preview")
    if file_ext in ["jpg", "png", "jpeg"]:
        st.image(temp_file_path)
    elif file_ext in ["mp4", "avi"]:
        st.video(temp_file_path)

    detected = False
    frame_saved = None

    # ========================
    # IMAGE DETECTION
    # ========================
    if file_ext in ["jpg", "png", "jpeg"]:
        results = model(temp_file_path)
        st.write("### Detection Result")
        st.image(results[0].plot())

        # Check for weapon
        for box in results[0].boxes:
            cls = int(box.cls[0])
            class_name = results[0].names[cls]
            if class_name.lower() == "weapon":
                detected = True

        if detected:
            st.error("⚠️ Threat Level: High — Weapon Confirmed")
            log_event("Detection", "Weapon detected in image")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Save annotated output
            output_img = f"detected_{timestamp}.jpg".replace(" ", "_").replace(":", "-")
            cv2.imwrite(output_img, results[0].plot())
            log_event("Annotated Image", output_img)

            # Send alert to Telegram
            alert_text = f"🚨 WEAPON DETECTED!\nTime: {timestamp}\nLocation: {LOCATION_COORDS}"
            send_telegram_message(alert_text, image_path=output_img)
            log_event("Telegram Alert Sent", f"Recipients: {len(CHAT_IDS)}")

            # ========================
            # Simulated Human-in-the-Loop (5 seconds)
            # ========================
            st.info("Human-in-the-Loop: Awaiting confirmation...")
            time.sleep(5)  # simulate delay
            st.success("Confirmation received: YES")
            log_event("Human-in-the-Loop", "Simulated confirmation: YES")

            # Generate gTTS alert audio
            tts = gTTS("Warning. Weapon detected. Please take cover immediately.")
            audio_path = "alert.mp3"
            tts.save(audio_path)
            st.audio(audio_path)
            log_event("TTS Played", "Alert audio played")
        else:
            st.success("No weapon detected.")
            log_event("Detection", "No weapon detected in image")

    # ========================
    # VIDEO DETECTION
    # ========================
    elif file_ext in ["mp4", "avi"]:
        cap = cv2.VideoCapture(temp_file_path)
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            results = model(frame)
            for box in results[0].boxes:
                cls = int(box.cls[0])
                class_name = results[0].names[cls]
                if class_name.lower() == "weapon":
                    detected = True
                    frame_saved = results[0].plot()
                    break
            if detected:
                break
        cap.release()

        if detected:
            st.error("⚠️ Threat Level: High — Weapon Confirmed in Video")
            log_event("Detection", "Weapon detected in video")
            img_path = "video_detection.jpg"
            cv2.imwrite(img_path, frame_saved)
            st.image(img_path)
            log_event("Annotated Image", img_path)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert_text = f"🚨 WEAPON DETECTED IN VIDEO!\nTime: {timestamp}\nLocation: {LOCATION_COORDS}"
            send_telegram_message(alert_text, image_path=img_path)
            log_event("Telegram Alert Sent", f"Recipients: {len(CHAT_IDS)}")

            # Simulated Human-in-the-Loop
            st.info("Human-in-the-Loop: Awaiting confirmation...")
            time.sleep(5)
            st.success("Confirmation received: YES")
            log_event("Human-in-the-Loop", "Simulated confirmation: YES")

            # gTTS voice alert
            tts = gTTS("Warning. Weapon detected in video. Please take cover immediately.")
            audio_path = "alert_video.mp3"
            tts.save(audio_path)
            st.audio(audio_path)
            log_event("TTS Played", "Alert audio played")
        else:
            st.success("No weapon detected in the video.")
            log_event("Detection", "No weapon detected in video")
