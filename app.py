import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
from prompt import PROMPT_WORKAW
from prompt2 import PROMPT_PRODUCT
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# -------------------- UI Custom Style --------------------
st.set_page_config(page_title="Workaw AI Chatbot", page_icon="💬", layout="wide")
st.markdown("""
    <style>
    body {
        background-color: #f4f4f4;
    }
    .css-1d391kg {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 1rem;
    }
    .css-1kyxreq {
        font-family: 'Segoe UI', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------- Sidebar --------------------
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/4140/4140048.png", width=100)
st.sidebar.title("🤖 Workaw Assistant")
def reset_inputs():
    for key in st.session_state.keys():
        del st.session_state[key]


# สร้าง Sidebar radio และจับ event การเลือกใหม่
if "selected_prompt" not in st.session_state:
    st.session_state.selected_prompt = "💼 ประกัน (Workaw)"
selected_prompt = st.sidebar.radio(
    "🔍 เลือกประเภทคำแนะนำที่ต้องการ",
    ("💼 ประกัน (Workaw)", "🛍️ สินค้า/บริการ (Product)"),
    index=("💼 ประกัน (Workaw)", "🛍️ สินค้า/บริการ (Product)").index(st.session_state.selected_prompt),
    key="selected_prompt_radio"
)
# ตรวจจับการเปลี่ยนแปลง และล้างข้อมูลเดิม
if selected_prompt != st.session_state.selected_prompt:
    reset_inputs()
    st.session_state.selected_prompt = selected_prompt
# ตั้งค่าระบบ prompt
selected_system_prompt = PROMPT_WORKAW if selected_prompt == "💼 ประกัน (Workaw)" else PROMPT_PRODUCT


if st.sidebar.button("🧹 ล้างประวัติการสนทนา"):
    st.session_state["messages"] = [{
        "role": "model",
        "content": "Workaw สวัสดีค่ะ คุณลูกค้า สอบถามข้อมูลการคุ้มครองแรงงาน สิทธิและสวัสดิการเรื่องใดคะ"
    }]
    st.rerun()

# -------------------- Model Setup --------------------
genai.configure(api_key="AIzaSyCB_vnuDX-qiF9J-mRIGQUOHZsrIIM-YQo")
generation_config = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 1024,
    "response_mime_type": "text/plain",
}

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    safety_settings=SAFETY_SETTINGS,
    generation_config=generation_config,
    system_instruction=selected_system_prompt,
)

# -------------------- Title --------------------
st.title("💬 Workaw AI Chatbot")
st.caption("เวอร์ชันที่ปรึกษาด้านแรงงานและข้อมูลสินค้า 🧠")

# -------------------- Load Excel Data --------------------
file1_path = "getgo_data.xlsx"
file2_path = "jorakay_products.xlsx"

def load_file(file_path):
    try:
        df = pd.read_excel(file_path)
        return df.to_string(index=False)
    except Exception as e:
        st.error(f"🚫 Error reading file: {file_path} - {e}")
        return ""

file1_content = load_file(file1_path)
file2_content = load_file(file2_path)
combined_file_content = file1_content + "\n" + file2_content

# -------------------- Initial Chat --------------------
if "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "model",
        "content": "👩‍💼 สวัสดีค่ะ Workaw ยินดีให้คำปรึกษาแรงงานและสินค้า ถามข้อมูลที่ต้องการได้เลยค่ะ"
    }]

# -------------------- Show Chat History --------------------
for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

# -------------------- Handle User Input --------------------
if prompt := st.chat_input("พิมพ์ข้อความที่นี่..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    def generate_response():
        history = [
            {"role": msg["role"], "parts": [{"text": msg["content"]}]}
            for msg in st.session_state["messages"]
        ]

        if prompt.lower().startswith("add") or prompt.lower().endswith("add"):
            response_text = "📌 ขอบคุณสำหรับคำแนะนำค่ะ"
        else:
            history.insert(1, {"role": "user", "parts": [{"text": combined_file_content}]})
            chat_session = model.start_chat(history=history)
            response = chat_session.send_message(prompt)
            response_text = response.text

        st.chat_message("model").write(response_text)
        st.session_state["messages"].append({"role": "model", "content": response_text})

    generate_response()
