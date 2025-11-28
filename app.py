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
import numpy as np
import random
import json

# ========================
#  PAGE CONFIGURATION
# ========================
st.set_page_config(
    page_title="Vision Guard AI",
    page_icon="🛡️",
    layout="wide"
)

# ========================
#  CONFIGURATION
# ========================

# Load Telegram token from Streamlit Cloud secrets
TELEGRAM_TOKEN = st.secrets["TELEGRAM_TOKEN"]

# Multiple recipients for professional setup
CHAT_IDS = [
    "5455011626",
    "5636140286",
    "SECURITY_TEAM_3"
]

# YOLO model filename
MODEL_PATH = "yolov8_trained.pt"

# South-South Nigeria States Bounding Boxes
SOUTH_SOUTH_STATES = {
    "Rivers": {"lat_range": (4.4, 5.5), "lon_range": (6.8, 7.4)},
    "Akwa Ibom": {"lat_range": (4.5, 5.3), "lon_range": (7.5, 8.5)},
    "Cross River": {"lat_range": (4.7, 6.0), "lon_range": (8.0, 9.0)},
    "Bayelsa": {"lat_range": (4.5, 5.0), "lon_range": (6.0, 6.5)},
    "Edo": {"lat_range": (5.5, 7.0), "lon_range": (5.5, 6.5)},
    "Delta": {"lat_range": (5.0, 6.0), "lon_range": (5.5, 6.5)}
}

# Initialize session state for logging
if "log_df" not in st.session_state:
    st.session_state.log_df = pd.DataFrame(columns=["Timestamp", "Event", "Details", "Threat Level"])

# ========================
#  FUNCTIONS
# ========================
def generate_random_coordinates():
    """Generate random coordinates within South-South Nigeria states"""
    state_name = random.choice(list(SOUTH_SOUTH_STATES.keys()))
    state_data = SOUTH_SOUTH_STATES[state_name]
    
    latitude = round(random.uniform(state_data["lat_range"][0], state_data["lat_range"][1]), 4)
    longitude = round(random.uniform(state_data["lon_range"][0], state_data["lon_range"][1]), 4)
    
    return state_name, latitude, longitude

def get_map_links(latitude, longitude):
    """Generate Google Maps and OpenStreetMap links"""
    google_maps_link = f"https://www.google.com/maps?q={latitude},{longitude}"
    openstreetmap_link = f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}&zoom=16"
    return google_maps_link, openstreetmap_link

def send_telegram_message_with_confirmation(text, image_path=None, incident_id=""):
    """Send professional alert messages to Telegram with confirmation buttons"""
    for i, chat_id in enumerate(CHAT_IDS):
        if i == 0:  # First chat ID gets interactive buttons
            # Send message with inline keyboard for confirmation
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            
            # Create inline keyboard with Yes/No buttons
            keyboard = {
                "inline_keyboard": [[
                    {"text": "✅ CONFIRM WEAPON", "callback_data": f"confirm_{incident_id}"},
                    {"text": "❌ FALSE ALARM", "callback_data": f"deny_{incident_id}"}
                ]]
            }
            
            payload = {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": json.dumps(keyboard)
            }
            
            response = requests.post(url, data=payload)
            
            # Send image separately if available
            if image_path and response.status_code == 200:
                url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
                with open(image_path, "rb") as img:
                    photo_payload = {
                        "chat_id": chat_id,
                        "caption": "📸 Detection Evidence - Please confirm above"
                    }
                    requests.post(url_photo, data=photo_payload, files={"photo": img})
                    
        else:
            # Other recipients get regular message without buttons
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            requests.post(url, data=payload)

            if image_path:
                url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
                with open(image_path, "rb") as img:
                    requests.post(url_photo, data={"chat_id": chat_id}, files={"photo": img})

def send_telegram_message(text, image_path=None):
    """Regular Telegram message without buttons (for non-alert messages)"""
    for chat_id in CHAT_IDS:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}
        requests.post(url, data=payload)

        if image_path:
            url_photo = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
            with open(image_path, "rb") as img:
                requests.post(url_photo, data={"chat_id": chat_id}, files={"photo": img})

def log_event(event, details, threat_level="INFO"):
    """Log events with timestamp and threat level"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.log_df.loc[len(st.session_state.log_df)] = [timestamp, event, details, threat_level]

def simulate_human_verification(confidence):
    """Simulate human-in-the-loop verification with probability based on confidence"""
    st.info("🔍 Human-in-the-Loop: Awaiting security team verification...")
    
    # Simulate verification delay
    with st.spinner("Security team reviewing detection..."):
        time.sleep(5)
    
    # Higher confidence = higher probability of confirmation
    confirmation_probability = min(confidence / 100, 0.9)  # Cap at 90% max
    is_confirmed = np.random.random() < confirmation_probability
    
    if is_confirmed:
        st.success(f"✅ Verification: CONFIRMED (Confidence: {confidence:.1f}%)")
        log_event("Human Verification", f"Confirmed - Confidence: {confidence:.1f}%", "SUCCESS")
        return True
    else:
        st.warning(f"⚠️ Verification: INCONCLUSIVE (Confidence: {confidence:.1f}%)")
        log_event("Human Verification", f"Inconclusive - Confidence: {confidence:.1f}%", "WARNING")
        return False

def get_threat_level(confidence):
    """Determine threat level based on confidence score"""
    if confidence >= 80:
        return "HIGH", "🔴"
    elif confidence >= 60:
        return "MEDIUM", "🟡"
    else:
        return "LOW", "🟢"


# ========================
#  SIDEBAR - SYSTEM INFORMATION
# ========================
with st.sidebar:
    st.title("🛡️ System Dashboard")
    
    # System Status
    st.subheader("System Status")
    st.success("🟢 All Systems Operational")
    
    # Model Information
    st.subheader("Model Information")
    st.write("**AI Engine:** YOLOv9 Architecture")
    st.write("**Model Version:** 1.0.0")
    st.write("**Operation Mode:** MVP Demo")
    
    # Alert Configuration
    st.subheader("Alert Configuration")
    st.write("**Recipients Configured:** 3")
    st.write("**Coverage Area:** South-South Nigeria")
    st.write("**Response Protocol:** Active")
    
    # Telegram Features
    st.subheader("Telegram Features")
    st.write("**Interactive Alerts:** ✅ Enabled")
    st.write("**Primary Contact:** Interactive buttons")
    st.write("**Secondary Contacts:** Read-only alerts")
    
    # Location Information
    st.subheader("📍 Coverage Area")
    st.write("**States Covered:**")
    for state in SOUTH_SOUTH_STATES.keys():
        st.write(f"• {state}")
    
    # Event Log Preview
    st.subheader("Recent Events")
    if not st.session_state.log_df.empty:
        recent_events = st.session_state.log_df.tail(3)
        for _, event in recent_events.iterrows():
            st.write(f"{event['Timestamp'][11:]} - {event['Event']}")

    # ========================
    # TEAM INFORMATION
    # ========================
    st.markdown("---")
    st.subheader("🏆 Hackathon Information")
    st.write("**Event:** 3MTT/Deeptech")
    st.write("**Hackathon:** Build with AI Hackathon 2025")
    st.write("**Track:** Health & Public Safety")
    st.write("**Sector:** Public Safety & Security")
    
    st.subheader("👥 Team Members")
    
    # Team Member 1
    with st.expander("Ayoola Mujib Ayodel", expanded=True):
        st.write("**Learning Track:** Data Science and Machine Learning")
        st.write("**Fellow ID:** FE/23/89361170")
        st.write("**Role:** AI/ML Engineer & Team Lead")
    
    # Team Member 2 (Placeholder)
    with st.expander("Edidiong Ime Moses", expanded=False):
        st.write("**Learning Track:** Data Science and Machine Learning")
        st.write("**Fellow ID:** FE/23/96831838")
        st.write("**Role:** Machine Learning Engineer")
        #st.write("**Email:** [email@example.com]")
    
    # Team Member 3 (Placeholder)
    with st.expander("Samuel Ekong", expanded=False):
        st.write("**Learning Track:** Geospatial Data Science")
        st.write("**Fellow ID:** FE/2388939683")
        st.write("**Role:** Geospatial Data Scientist")
        #st.write("**Email:** [email@example.com]")
    
    st.markdown("---")
    st.caption("Built for 3MTT Build with AI Hackathon 2025")
# ========================
#  MAIN CONTENT AREA
# ========================

# Centralized Title Section
st.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='margin-bottom: 10px;'>Weapon Detection & Alert System</h1>
    <h3 style='color: #666; margin-top: 0;'>AI-Powered Security Monitoring Platform</h3>
</div>
""", unsafe_allow_html=True)

# Professional file upload section
st.markdown("---")
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Media Analysis")
    uploaded_file = st.file_uploader(
        "Upload Image or Video for Threat Assessment", 
        type=["jpg", "png", "jpeg", "mp4", "avi"],
        help="Supported formats: JPG, PNG, JPEG, MP4, AVI"
    )

with col2:
    st.subheader("Quick Stats")
    total_scans = len(st.session_state.log_df[st.session_state.log_df['Event'].str.contains('Detection')])
    threats_detected = len(st.session_state.log_df[st.session_state.log_df['Threat Level'] == 'HIGH'])
    
    st.metric("Total Scans", total_scans)
    st.metric("Threats Detected", threats_detected)
    st.metric("System Uptime", "100%", "Stable")

# Load YOLO model
model = YOLO(MODEL_PATH)

if uploaded_file:
    # Generate random coordinates for this detection
    state_name, latitude, longitude = generate_random_coordinates()
    google_maps_link, openstreetmap_link = get_map_links(latitude, longitude)
    location_coords = f"Latitude: {latitude}, Longitude: {longitude} ({state_name} State)"
    
    # File processing section
    st.markdown("---")
    st.subheader("Analysis in Progress")
    
    with st.spinner("🔍 Processing media content for threat assessment..."):
        time.sleep(2)
        
        file_ext = uploaded_file.name.split(".")[-1].lower()
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}")
        temp_file.write(uploaded_file.read())
        temp_file_path = temp_file.name

        # Display input preview
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### Input Media")
            if file_ext in ["jpg", "png", "jpeg"]:
                st.image(temp_file_path, use_column_width=True)
            elif file_ext in ["mp4", "avi"]:
                st.video(temp_file_path)

        # ========================
        # PROCESS IMAGE
        # ========================
        if file_ext in ["jpg", "png", "jpeg"]:
            results = model(temp_file_path)
            
            with col2:
                st.write("#### Threat Assessment Result")
                st.image(results[0].plot(), use_column_width=True)

            # Check for weapon and get confidence
            detected = False
            max_confidence = 0.0
            for box in results[0].boxes:
                cls = int(box.cls[0])
                class_name = results[0].names[cls]
                if class_name.lower() == "weapon":
                    detected = True
                    confidence = float(box.conf[0]) * 100
                    max_confidence = max(max_confidence, confidence)

            if detected:
                threat_level, threat_icon = get_threat_level(max_confidence)
                st.error(f"{threat_icon} THREAT LEVEL: {threat_level} - WEAPON DETECTED")
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                incident_id = timestamp.replace(' ', '').replace(':', '').replace('-', '')
                log_event("Weapon Detection", f"Confidence: {max_confidence:.1f}% - Location: {state_name}", "HIGH")

                # Save annotated output
                output_img = f"detected_{timestamp}.jpg".replace(" ", "_").replace(":", "-")
                cv2.imwrite(output_img, results[0].plot())
                log_event("Evidence Saved", output_img, "INFO")

                # Professional alert message with dynamic map links
                alert_text = f"""🚨 SECURITY ALERT - WEAPON DETECTED

📍 Location: {location_coords}
🕒 Time: {timestamp}
🎯 Confidence: {max_confidence:.1f}%
⚠️ Threat Level: {threat_level}
📊 Status: AWAITING CONFIRMATION

🗺️ NAVIGATION LINKS:
Google Maps: {google_maps_link}
OpenStreetMap: {openstreetmap_link}

Action Required: Please confirm weapon presence
Safety Protocol: Standby for confirmation

Incident ID: {incident_id}
"""
                # Send interactive alert to primary contact, regular alerts to others
                send_telegram_message_with_confirmation(alert_text, image_path=output_img, incident_id=incident_id)
                log_event("Interactive Alert Sent", f"Primary: Interactive - Others: Read-only - Incident: {incident_id}", "HIGH")

                # Human verification simulation
                is_confirmed = simulate_human_verification(max_confidence)
                
                if is_confirmed:
                    # Public safety evacuation announcement
                    st.warning("🔊 PUBLIC SAFETY ANNOUNCEMENT - EVACUATION ALERT")
                    tts = gTTS("Emergency! Emergency! Weapon detected around building. Immediate evacuation required. All occupants move calmly to nearest exits. Follow directions of staff and security personnel.", lang='en', slow=False)
                    audio_path = "evacuation_alert.mp3"
                    tts.save(audio_path)
                    st.audio(audio_path)
                    log_event("Evacuation Alert", "Public safety announcement activated", "HIGH")
                    
                    # Send confirmation update
                    confirmation_text = f"✅ WEAPON CONFIRMED - Incident {incident_id}\nEvacuation procedures ACTIVATED"
                    send_telegram_message(confirmation_text)
                    
                else:
                    st.info("🟡 Alert escalation paused pending further review")
                    # Send update about inconclusive verification
                    update_text = f"🟡 VERIFICATION INCONCLUSIVE - Incident {incident_id}\nManual review required"
                    send_telegram_message(update_text)

                # Incident report
                st.markdown("---")
                st.subheader("📋 Incident Report")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Threat Level", threat_level, f"Confidence: {max_confidence:.1f}%")
                with col2:
                    st.metric("Human Verify", "CONFIRMED" if is_confirmed else "PENDING", "")
                with col3:
                    st.metric("Location", state_name, "State")
                with col4:
                    st.write("**📍 Navigation Links:**")
                    st.write(f"[Google Maps]({google_maps_link})")
                    st.write(f"[OpenStreetMap]({openstreetmap_link})")
                    st.write(f"**Coordinates:** {latitude}, {longitude}")
                    
                st.info("💡 **Primary security contact received interactive alert with confirmation buttons**")

            else:
                st.success("✅ THREAT ASSESSMENT: CLEAR")
                log_event("Clear Scan", "No weapons detected", "INFO")
                st.info("No weapons detected. Area secured.")

        # ========================
        # PROCESS VIDEO
        # ========================
        elif file_ext in ["mp4", "avi"]:
            cap = cv2.VideoCapture(temp_file_path)
            detected = False
            frame_saved = None
            max_confidence = 0.0

            progress_bar = st.progress(0)
            status_text = st.empty()

            frame_count = 0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                progress = int((frame_count / total_frames) * 100)
                progress_bar.progress(min(progress, 100))
                status_text.text(f"Analyzing frame {frame_count}/{total_frames}")

                results = model(frame)

                for box in results[0].boxes:
                    cls = int(box.cls[0])
                    class_name = results[0].names[cls]
                    if class_name.lower() == "weapon":
                        detected = True
                        confidence = float(box.conf[0]) * 100
                        max_confidence = max(max_confidence, confidence)
                        frame_saved = results[0].plot()
                        break

                if detected:
                    break

            cap.release()
            progress_bar.empty()
            status_text.empty()

            if detected:
                threat_level, threat_icon = get_threat_level(max_confidence)
                st.error(f"{threat_icon} THREAT LEVEL: {threat_level} - WEAPON IN VIDEO")

                with col2:
                    st.write("#### Threat Frame Analysis")
                    img_path = "video_threat_detection.jpg"
                    cv2.imwrite(img_path, frame_saved)
                    st.image(img_path, use_column_width=True)

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                incident_id = f"VID{timestamp.replace(' ', '').replace(':', '').replace('-', '')}"
                log_event("Video Weapon Detection", f"Confidence: {max_confidence:.1f}% - Location: {state_name}", "HIGH")
                
                # Professional video alert message with dynamic map links
                alert_text = f"""🚨 SECURITY ALERT - WEAPON DETECTED IN VIDEO

📍 Location: {location_coords}
🕒 Time: {timestamp}
🎯 Confidence: {max_confidence:.1f}%
⚠️ Threat Level: {threat_level}
📹 Source: Video Surveillance
📊 Status: AWAITING CONFIRMATION

🗺️ NAVIGATION LINKS:
Google Maps: {google_maps_link}
OpenStreetMap: {openstreetmap_link}

Action Required: Please confirm weapon presence in video
Safety Protocol: Standby for confirmation

Incident ID: {incident_id}
"""
                send_telegram_message_with_confirmation(alert_text, image_path=img_path, incident_id=incident_id)
                log_event("Video Interactive Alert", f"Primary: Interactive - Others: Read-only - Incident: {incident_id}", "HIGH")

                # Human verification for video
                is_confirmed = simulate_human_verification(max_confidence)
                
                if is_confirmed:
                    st.warning("🔊 PUBLIC SAFETY ANNOUNCEMENT - EVACUATION ALERT")
                    tts = gTTS("Emergency! Emergency! Weapon detected around building. Immediate evacuation required. All occupants move calmly to nearest exits. Follow directions of staff and security personnel.", lang='en', slow=False)
                    audio_path = "video_evacuation_alert.mp3"
                    tts.save(audio_path)
                    st.audio(audio_path)
                    log_event("Video Evacuation Alert", "Public safety announcement activated", "HIGH")
                    
                    # Send confirmation update
                    confirmation_text = f"✅ VIDEO WEAPON CONFIRMED - Incident {incident_id}\nEvacuation procedures ACTIVATED"
                    send_telegram_message(confirmation_text)
                else:
                    st.info("🟡 Video alert escalation paused pending further review")
                    update_text = f"🟡 VIDEO VERIFICATION INCONCLUSIVE - Incident {incident_id}\nManual review required"
                    send_telegram_message(update_text)
                    
                st.info("💡 **Primary security contact received interactive alert with confirmation buttons**")

            else:
                st.success("✅ VIDEO ANALYSIS COMPLETE: NO THREATS DETECTED")
                log_event("Video Clear", "No weapons detected in video", "INFO")
                st.info("Video surveillance analysis completed. No weapons identified.")

# Event Log Section
st.markdown("---")
st.subheader("📊 System Event Log")
if not st.session_state.log_df.empty:
    st.dataframe(st.session_state.log_df.sort_values("Timestamp", ascending=False))
else:
    st.info("No events logged yet. Upload media to begin analysis.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Weapon Detection & Alert System v1.0 | AI-Powered Security Platform | Interactive Telegram Alerts"
    "</div>", 
    unsafe_allow_html=True
)
