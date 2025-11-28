import streamlit as st
from ultralytics import YOLO
import tempfile
import os
from gtts import gTTS
import requests
from datetime import datetime
import cv2

# ========================
#  CONFIGURATION
# ========================

# Load Telegram token from Streamlit Cloud secrets
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]

# Replace these with your real chat IDs later
CHAT_IDS = [
    "5455011626",
    #"CHAT_ID_2",
    #"CHAT_ID_3"
]

# Hardcoded South-South Nigeria coordinates
LOCATION_COORDS = "Latitude: 4.8156, Longitude: 7.0498 (Port Harcourt, Nigeria)"

# YOLO model filename
MODEL_PATH = "yolov8_trained.pt"


# ========================
#  TELEGRAM SEND FUNCTION
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
#  STREAMLIT UI
# ========================

st.title("🔫 Weapon Detection MVP (YOLO + Streamlit + Telegram)")
st.write("Upload an image or video. If a weapon is detected, Telegram alerts will be triggered.")

uploaded_file = st.file_uploader("Upload Image or Video", type=["jpg", "png", "jpeg", "mp4", "avi"])

# Load YOLO model
model = YOLO(MODEL_PATH)

if uploaded_file:
    file_ext = uploaded_file.name.split(".")[-1].lower()
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}")
    temp_file.write(uploaded_file.read())
    temp_file_path = temp_file.name

    st.write("### Input Preview")
    if file_ext in ["jpg", "png", "jpeg"]:
        st.image(temp_file_path)

    # ========================
    # PROCESS IMAGE
    # ========================
    if file_ext in ["jpg", "png", "jpeg"]:
        results = model(temp_file_path)
        st.write("### Detection Result")
        st.image(results[0].plot())

        # Check for weapon
        detected = False
        for box in results[0].boxes:
            cls = int(box.cls[0])
            class_name = results[0].names[cls]
            if class_name.lower() == "weapon":
                detected = True

        if detected:
            st.error("⚠️ Weapon Detected!")
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Save annotated output
            output_img = f"detected_{timestamp}.jpg".replace(" ", "_").replace(":", "-")
            cv2.imwrite(output_img, results[0].plot())

            # Send alert to Telegram
            alert_text = f"🚨 WEAPON DETECTED!\nTime: {timestamp}\nLocation: {LOCATION_COORDS}"
            send_telegram_message(alert_text, image_path=output_img)

            # ========================
            # Generate gTTS alert audio
            # ========================
            tts = gTTS("Warning. Weapon detected. Please take cover immediately.")
            audio_path = "alert.mp3"
            tts.save(audio_path)

            st.audio(audio_path)

        else:
            st.success("No weapon detected.")

    # ========================
    # PROCESS VIDEO
    # ========================
    elif file_ext in ["mp4", "avi"]:
        st.video(temp_file_path)

        cap = cv2.VideoCapture(temp_file_path)
        detected = False
        frame_saved = None

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
            st.error("⚠️ Weapon Detected in Video!")

            img_path = "video_detection.jpg"
            cv2.imwrite(img_path, frame_saved)

            st.image(img_path)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            alert_text = f"🚨 WEAPON DETECTED IN VIDEO!\nTime: {timestamp}\nLocation: {LOCATION_COORDS}"
            send_telegram_message(alert_text, image_path=img_path)

            # gTTS voice alert
            tts = gTTS("Warning. Weapon detected in video. Please take cover immediately.")
            audio_path = "alert_video.mp3"
            tts.save(audio_path)

            st.audio(audio_path)
        else:
            st.success("No weapon detected in the video.")
