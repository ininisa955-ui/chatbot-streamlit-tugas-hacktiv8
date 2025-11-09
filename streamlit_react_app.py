import streamlit as st
import openai
import json
import os
from datetime import datetime

# --- 1. Page Configuration and Title ---
st.set_page_config(page_title="GiziBoost Chatbot", page_icon="🍽", layout="wide")
st.title("🍽 GiziBoost – Chatbot Konsultasi Gizi")

# --- 2. Sidebar for Settings ---
with st.sidebar:
    st.header("Pengaturan Input Awal")
    tinggi = st.number_input("Tinggi badan (cm)", min_value=50.0, max_value=250.0, step=0.1)
    berat = st.number_input("Berat badan (kg)", min_value=20.0, max_value=250.0, step=0.1)
    umur = st.number_input("Umur (tahun)", min_value=5, max_value=120, step=1)
    aktivitas = st.selectbox("Aktivitas harian", ["Banyak duduk", "Cukup aktif", "Aktif", "Sangat aktif"])
    makanan_suka = st.text_input("Makanan disukai")
    makanan_tidak_suka = st.text_input("Makanan tidak disukai")

    st.header("API Key")
    api_key = st.text_input("Masukkan OpenAI API Key", type="password")

# --- 3. API Key and Agent Initialization ---
if api_key:
    openai.api_key = api_key
    agent_initialized = True
else:
    agent_initialized = False

# --- 4. Chat History Management + File Storage ---
HISTORY_FILE = "chat_history.json"

if "history" not in st.session_state:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            st.session_state.history = json.load(f)
    else:
        st.session_state.history = []

def save_history():
    with open(HISTORY_FILE, "w") as f:
        json.dump(st.session_state.history, f, indent=2)

def add_message(role, content):
    st.session_state.history.append({"role": role, "content": content, "time": str(datetime.now())})
    save_history()

# --- Chat Bubble UI ---
st.subheader("Percakapan")
for m in st.session_state.history:
    if m["role"] == "user":
        st.markdown(f"<div style='background:#DCF8C6;padding:10px;border-radius:10px;margin-bottom:5px;text-align:right'> {m['content']} </div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background:#F1F0F0;padding:10px;border-radius:10px;margin-bottom:5px;text-align:left'> {m['content']} </div>", unsafe_allow_html=True)

# --- 6. Handle User Input and Agent Communication ---
user_input = st.text_input("Ketik pesan...")

if st.button("Kirim"):
    if not agent_initialized:
        st.error("Masukkan API Key terlebih dahulu.")
    else:
        add_message("user", user_input)

        system_prompt = f"Anda adalah GiziBoost, chatbot gizi yang memberi saran berdasarkan data berikut: \nTinggi: {tinggi} cm, Berat: {berat} kg, Umur: {umur}, Aktivitas: {aktivitas}, Suka: {makanan_suka}, Tidak suka: {makanan_tidak_suka}."

        messages = [
            {"role": "system", "content": system_prompt}
        ] + [
            {"role": m["role"], "content": m["content"]} for m in st.session_state.history
        ]

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )

        bot_reply = response.choices[0].message["content"]
        add_message("assistant", bot_reply)
        st.rerun()

# Pelacak progres
st.subheader("Pelacak Progres Berat Badan")
berat_mingguan = st.number_input("Input berat minggu ini", min_value=20.0, max_value=250.0, step=0.1)
if berat_mingguan:
    st.line_chart({"Berat Badan": [berat, berat_mingguan]})
