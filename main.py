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
    .stChatMessage { border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- Logic Class ---
class DolphinWebAI:
    def __init__(self):
        # ⚠️ အရေးကြီး: သင်ရလာတဲ့ Link အသစ်ကို ဒီနေရာမှာ အစားထိုးလိုက်ပါပြီ
        self.ollama_url = "https://lvijx-204-157-172-165.a.free.pinggy.link/api/generate" 
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
        # Tunnel Warning တွေကို ကျော်ဖြတ်ဖို့ Headers
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
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
            # AI ဆီသို့ တိုက်ရိုက် Request ပို့ခြင်း
            response = requests.post(self.ollama_url, json=payload, headers=headers, timeout=150)
            
            if response.status_code == 200:
                answer = response.json().get("response", "No response from AI.")
                self.cursor.execute("INSERT INTO brain VALUES (?, ?)", (prompt, answer))
                self.conn.commit()
                return answer
            else:
                return f"Server Error: {response.status_code}. ကျေးဇူးပြု၍ Browser မှာ Link ကိုဖွင့်ပြီး 'Proceed' နှိပ်ပေးပါ။"
        except Exception as e:
            return f"Connection Error: {str(e)}. သင့်စက်ထဲက Terminal ပိတ်သွားပြီလား စစ်ဆေးပေးပါ။"

# --- Streamlit UI ---
st.title("🐬 Dolphin-Llama3 Private Online AI")

if 'ai' not in st.session_state:
    st.session_state.ai = DolphinWebAI()

if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar
st.sidebar.title("AI Settings")
uploaded_file = st.sidebar.file_uploader("Upload PDF for Context", type="pdf")
pdf_text = ""
if uploaded_file:
    reader = PyPDF2.PdfReader(uploaded_file)
    for page in reader.pages[:3]:
        pdf_text += page.extract_text()
    st.sidebar.success("PDF Context Loaded!")

# Chat Interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is on your mind?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = st.session_state.ai.ask(prompt, pdf_text)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            if st.sidebar.checkbox("Enable Voice"):
                try:
                    tts = gTTS(text=response[:200], lang='en')
                    tts.save("reply.mp3")
                    st.audio("reply.mp3")
                except: pass
