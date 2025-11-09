# Import the necessary libraries
import os
from typing import List, Dict, Any

# Flag ketersediaan dependensi agar tidak error di sandbox
HAVE_STREAMLIT = True
try:
    import streamlit as st  # For creating the web app interface
except Exception:
    HAVE_STREAMLIT = False

HAVE_LANG = True
try:
    from langchain_google_genai import ChatGoogleGenerativeAI  # For interacting with Google Gemini via LangChain
    from langgraph.prebuilt import create_react_agent  # For creating a ReAct agent
    from langchain_core.messages import HumanMessage, AIMessage  # For message formatting
    from langchain.tools import tool
except Exception:
    HAVE_LANG = False

# --------------------
# Tools: Rekomendasi
# --------------------
if HAVE_LANG:
    @tool("recommend_workout", return_direct=False)
    def recommend_workout(goal: str, days_per_week: int = 3, equipment: str = "bodyweight") -> str:
        """Buat rekomendasi program latihan mingguan berdasarkan `goal` (bulking/cutting/kebugaran/strength),
        jumlah hari latihan per minggu (`days_per_week`), dan ketersediaan alat (`equipment`)."""
        days_per_week = max(2, min(6, int(days_per_week)))
        split = {
            2: ["Full-body A", "Full-body B"],
            3: ["Push+Quads", "Pull+Hinge", "Full-body+Core"],
            4: ["Upper", "Lower", "Upper", "Lower"],
            5: ["Push", "Pull", "Legs", "Upper", "Full-body"],
            6: ["Push", "Pull", "Legs", "Push", "Pull", "Legs"],
        }[days_per_week]
        focus = {
            "bulking": "prioritaskan progressive overload, 6–12 reps, 8–16 set/otot/minggu",
            "cutting": "pertahankan beban, kurangi volume sedikit, tambah kardio ringan",
            "kebugaran": "kombinasi resistance + kardio zona 2, mobilitas",
            "strength": "fokus compound 3–6 reps, istirahat lebih panjang"
        }
        f = focus.get(goal.lower(), "seimbangkan compound & isolasi, progres bertahap")
        eq = "Tanpa alat (bodyweight)" if equipment.lower() == "bodyweight" else f"Dengan alat: {equipment}"
        template = [
            f"Goal: {goal} | Hari/minggu: {days_per_week} | {eq}",
            f"Fokus: {f}",
            "Rangka contoh:",
        ]
        for i, d in enumerate(split, 1):
            if "Full-body" in d:
                blk = "Squat/hinge, Push, Pull, Core, Carry"
            elif d in ("Upper", "Push", "Pull"):
                blk = "Bench/Overhead, Row/Pull-up, Accessory, Core"
            else:
                blk = "Squat/Deadlift, Lunge/Hinge, Calves/Glutes, Core"
            template.append(f"{i}. {d}: {blk}")
        template.append("Catatan: progres 1–2 repetisi/pekan atau +2.5–5% beban bila mampu.")
        return "\n".join(template)

    @tool("recommend_meal_plan", return_direct=False)
    def recommend_meal_plan(goal: str, body_weight_kg: float = 70.0, diet_pref: str = "flexible") -> str:
        """Buat rekomendasi pola makan harian (kalori & makro) berdasarkan `goal` (bulking/cutting/kebugaran),
        berat badan `body_weight_kg`, dan preferensi diet (`diet_pref`: halal/vegetarian/vegan/flexible)."""
        bw = max(35.0, min(200.0, float(body_weight_kg)))
        if goal.lower() == "bulking":
            kcal = bw * 33 + 250
            p = bw * 1.8
            c = bw * 4.0
            f = (kcal - (p*4 + c*4)) / 9
        elif goal.lower() == "cutting":
            kcal = bw * 30 - 350
            p = bw * 2.0
            c = bw * 2.5
            f = (kcal - (p*4 + c*4)) / 9
        else:
            kcal = bw * 31
            p = bw * 1.6
            c = bw * 3.0
            f = (kcal - (p*4 + c*4)) / 9
        kcal = max(1200, round(kcal))
        p, c, f = round(p), round(c), max(20, round(f))
        meal = [
            f"Goal: {goal} | BB: {bw:.1f} kg | Estimasi Kalori: {kcal} kkal",
            f"Makro: Protein {p}g | Karbo {c}g | Lemak {f}g",
            f"Preferensi: {diet_pref}",
            "Contoh pembagian 4x makan:",
            "- Sarapan: Protein cepat serap + karbo kompleks + lemak sehat",
            "- Makan siang: Sumber protein utama + sayur berserat + karbo",
            "- Snack: Greek yogurt/kedelai + buah/kacang",
            "- Makan malam: Protein lean + sayur + karbo (cutting: kurangi)",
            "Minum 30–35 ml/kg BB/hari; serat 20–35 g/hari.",
        ]
        if diet_pref.lower() in ("vegetarian", "vegan"):
            meal.append("Catatan: pastikan kombinasi asam amino lengkap & B12.")
        if diet_pref.lower() == "halal":
            meal.append("Catatan: pastikan sumber protein & suplemen bersertifikat halal.")
        return "\n".join(meal)

# --------------------
# Helper untuk Agent
# --------------------

def build_agent(api_key: str, model_name: str, temperature: float):
    if not HAVE_LANG:
        return None
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=temperature)
    tools = [recommend_workout, recommend_meal_plan]
    agent = create_react_agent(llm, tools)
    return agent

# --- 1. Page Configuration and Title ---

def render_streamlit():
    st.set_page_config(page_title="Gym & Fitness Chatbot", page_icon="💪", layout="wide")
    st.title("Gym & Fitness Chatbot 💪")

    # --- 2. Sidebar for Settings ---
    st.sidebar.header("Settings")
    api_key = st.sidebar.text_input("Google Gemini API Key", type="password")
    model_name = st.sidebar.selectbox("Model", ["gemini-pro", "gemini-1.5-flash", "gemini-1.5-pro"], index=1)
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7)

    st.sidebar.subheader("Context Cepat (opsional)")
    goal = st.sidebar.selectbox("Goal", ["bulking", "cutting", "kebugaran", "strength"], index=2)
    days = st.sidebar.slider("Hari latihan/minggu", 2, 6, 3)
    equipment = st.sidebar.text_input("Alat (mis. bodyweight, dumbbell, barbell)", value="bodyweight")
    body_weight = st.sidebar.number_input("Berat Badan (kg)", 35.0, 200.0, 70.0)
    diet_pref = st.sidebar.selectbox("Preferensi makan", ["flexible", "halal", "vegetarian", "vegan"], index=0)

    # --- 3. API Key and Agent Initialization ---
    if not HAVE_LANG:
        st.warning("LangChain/LangGraph tidak terpasang. Pasang paket yang diperlukan untuk menggunakan agent.")
        agent = None
    else:
        agent = build_agent(api_key, model_name, temperature)

    # --- 4. Chat History Management ---
    if "messages" not in st.session_state:
        st.session_state["messages"] = []  # list[dict(role, content)]

    for msg in st.session_state.messages:
        st.chat_message("user" if msg["role"] == "user" else "assistant").write(msg["content"])

    # Tombol cepat (memicu tool lewat prompt natural language)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔧 Rekomendasi Latihan Cepat"):
            prompt = f"Buatkan program latihan: goal={goal}, days_per_week={days}, equipment={equipment}. Gunakan tool `recommend_workout`."
            st.session_state.messages.append({"role": "user", "content": prompt})
    with col2:
        if st.button("🍽️ Rekomendasi Pola Makan Cepat"):
            prompt = f"Buatkan pola makan: goal={goal}, body_weight_kg={body_weight}, diet_pref={diet_pref}. Gunakan tool `recommend_meal_plan`."
            st.session_state.messages.append({"role": "user", "content": prompt})

    # --- 6. Handle User Input and Agent Communication ---
    user_input = st.chat_input("Tanya seputar gym & nutrisi… (contoh: 'Saya ingin cutting 3x/minggu')")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

    # Proses turn terbaru jika ada input/tool button
    if agent and st.session_state.messages and (st.session_state.messages[-1]["role"] == "user"):
        try:
            # Convert pesan ke BaseMessage untuk LangGraph
            msg_objs = []
            for m in st.session_state.messages:
                if m["role"] == "user":
                    msg_objs.append(HumanMessage(content=m["content"]))
                else:
                    msg_objs.append(AIMessage(content=m["content"]))
            result = agent.invoke({"messages": msg_objs})
            # Hasil dari agent biasanya berupa dict dengan key "messages"
            out_messages = result.get("messages", [])
            if out_messages and hasattr(out_messages[-1], "content"):
                reply = out_messages[-1].content
            else:
                reply = str(result)
        except Exception as e:
            reply = f"Terjadi kesalahan saat memanggil agent: {e}"
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.chat_message("assistant").write(reply)

    # Peringatan informatif bila user menjalankan file ini dengan `python` (bukan `streamlit run`)
    st.sidebar.info("Jika aplikasi tidak tampil, jalankan dengan: `streamlit run nama_file.py`. ")

