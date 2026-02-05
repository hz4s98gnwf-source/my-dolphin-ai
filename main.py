import streamlit as st
import requests
import sqlite3
import wikipediaapi
import PyPDF2
from gtts import gTTS
import os

# --- Page Configuration ---
st.set_page_config(page_title="Dolphin Online AI", page_icon="🐬", layout="wide")

# --- CSS for Styling ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stTextInput>div>div>input { color: #00d4ff; }
    </style>
    """, unsafe_allow_html=True)

# --- Logic Class ---
class DolphinWebAI:
    def __init__(self):
        # အောက်က Link ကို သင့်ရဲ့ လက်ရှိ LocalTunnel Link နဲ့ အမြဲလဲပေးပါ
        self.ollama_url = "https://fifty-dingos-add.loca.lt/api/generate" 
        self.model = "dolphin-llama3:latest"
        self.wiki = wikipediaapi.Wikipedia(
            language='en',
            user_agent='MyEvolvingAI/1.2 (dev@example.com)'
        )
        
        # Database Setup
        self.conn = sqlite3.connect('online_memory.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS brain (q TEXT, a TEXT)')
        self.conn.commit()

    def web_search(self, topic):
        try:
            page = self.wiki.page(topic)
            return page.summary[:500] if page.exists() else None
        except: return None

    def ask(self, prompt, context=""):
        # LocalTunnel 403 Error ကျော်ဖို့ Header ထည့်ခြင်း
        headers = {
            "Bypass-Tunnel-Reminder": "true",
            "User-Agent": "Mozilla/5.0"
        }

        # Search logic
        search_info = ""
        if "search" in prompt.lower():
            topic = prompt.lower().replace("search", "").strip()
            web_data = self.web_search(topic)
            if web_data: search_info = f"\nWeb Data: {web_data}"

        full_prompt = f"Context: {context}\n{search_info}\nUser: {prompt}\nAI:"
        
        payload = {"model": self.model, "prompt": full_prompt, "stream": False}
        
        try:
            # headers=headers ကို ဒီမှာ သုံးထားပါတယ်
            response = requests.post(self.ollama_url, json=payload, headers=headers, timeout=120)
            if response.status_code == 200:
                answer = response.json().get("response", "No response from AI.")
                # Save to Memory
                self.cursor.execute("INSERT INTO brain VALUES (?, ?)", (prompt, answer))
                self.conn.commit()
                return answer
            else:
                return f"Error: Server returned status {response.status_code}. Make sure you verified your IP in the browser."
        except Exception as e:
            return f"Connection Error: {str(e)}. Please check if your LocalTunnel is still running."

# --- Streamlit UI ---
st.title("🐬 Dolphin-Llama3 Private Online AI")

if 'ai' not in st.session_state:
    st.session_state.ai = DolphinWebAI()

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar PDF Upload
st.sidebar.title("AI Settings")
uploaded_file = st.sidebar.file_uploader("Upload PDF for Context", type="pdf")
pdf_text = ""
if uploaded_file:
    reader = PyPDF2.PdfReader(uploaded_file)
    for
