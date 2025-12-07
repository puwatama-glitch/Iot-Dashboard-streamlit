from pathlib import Path
import streamlit as st
import pandas as pd
import paho.mqtt.client as mqtt
from datetime import datetime
import json

# ===========================
# MQTT CONFIG
# ===========================
MQTT_BROKER = "broker.hivemq.com"
SENSOR_TOPIC = "DEVA/SMKN1BOYOLANGU/SENSOR"
OUTPUT_TOPIC = "DEVA/SMKN1BOYOLANGU/OUTPUT"

# ===========================
# CSV LOG SETUP
# ===========================
CSV_FILE = "iot_log.csv"

if not Path(CSV_FILE).exists():
    df = pd.DataFrame(columns=["timestamp", "temperature", "humidity", "prediction"])
    df.to_csv(CSV_FILE, index=False)

# ===========================
# STREAMLIT UI
# ===========================
st.set_page_config(page_title="IoT + ML Dashboard", layout="centered")

st.title("📡 IoT + Machine Learning Dashboard (ESP32 + MQTT)")
st.write("Realtime Monitoring • Prediction • Feedback Control")

if 'temp_box' not in st.session_state:
    st.session_state.temp_box = st.empty()
if 'hum_box' not in st.session_state:
    st.session_state.hum_box = st.empty()
if 'pred_box' not in st.session_state:
    st.session_state.pred_box = st.empty()
if 'alert_box' not in st.session_state:
    st.session_state.alert_box = st.empty()

temp_box = st.session_state.temp_box
hum_box = st.session_state.hum_box
pred_box = st.session_state.pred_box
alert_box = st.session_state.alert_box


# ===========================
# SIMPLE ML MODEL (contoh)
# ===========================
def predict(temp):
    if temp < 25:
        return "Dingin"
    elif temp < 30:
        return "Normal"
    else:
        return "Panas"


# ===========================
# MQTT CALLBACK
# ===========================
def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())

        temp = data["temp"]
        hum = data["hum"]

        prediction = predict(temp)

        # Update Dashboard
        temp_box.metric("🌡 Suhu", f"{temp} °C")
        hum_box.metric("💧 Kelembapan", f"{hum} %")
        pred_box.subheader(f"🔎 Prediksi ML: **{prediction}**")

        # Alert color + send MQTT feedback
        if prediction == "Panas":
            alert_box.error("🔥 ALERT: SUHU PANAS — ALERT_ON")
            client.publish(OUTPUT_TOPIC, "ALERT_ON")
        else:
            alert_box.success("✅ Suhu Normal / Dingin — ALERT_OFF")
            client.publish(OUTPUT_TOPIC, "ALERT_OFF")

        # Save to CSV
        df = pd.read_csv(CSV_FILE)
        df.loc[len(df)] = {
            "timestamp": datetime.now(),
            "temperature": temp,
            "humidity": hum,
            "prediction": prediction
        }
        df.to_csv(CSV_FILE, index=False)

    except Exception as e:
        st.error(f"Error: {e}")


# ===========================
# MQTT SUBSCRIBER START
# ===========================
if 'mqtt_client' not in st.session_state:
    st.session_state.mqtt_client = mqtt.Client()
    st.session_state.mqtt_client.on_message = on_message
    st.session_state.mqtt_client.connect(MQTT_BROKER, 1883)
    st.session_state.mqtt_client.subscribe(SENSOR_TOPIC)
    st.session_state.mqtt_client.loop_start()

st.info("🚀 MQTT Client Running... menunggu data dari ESP32...")
