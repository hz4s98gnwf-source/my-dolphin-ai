import customtkinter as ctk
import sqlite3
import requests
import threading
import wikipediaapi
import PyPDF2
from gtts import gTTS
from pygame import mixer
import os

# --- Super Intelligence Engine ---
class SuperBrain:
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "dolphin-llama3:latest"
        
        # Wikipedia Setup with Proper User Agent
        self.wiki = wikipediaapi.Wikipedia(
            language='en',
            extract_format=wikipediaapi.ExtractFormat.WIKI,
            user_agent='MyEvolvingAI/1.2 (contact: dev@example.com)'
        )
        
        mixer.init()
        
        # Database for Auto-Learning Memory
        self.conn = sqlite3.connect('super_ai_memory.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS brain (topic TEXT, info TEXT)')
        self.conn.commit()

    # 1. Voice Output Logic
    def speak(self, text):
        def play():
            try:
                # အရှည်ကြီးဆိုရင် ပထမစာကြောင်း ၂ ကြောင်းလောက်ပဲ ဖတ်မယ်
                clean_text = text.split('.')[0] + "." + text.split('.')[1] if '.' in text else text
                tts = gTTS(text=clean_text[:300], lang='en')
                tts.save("speech.mp3")
                mixer.music.load("speech.mp3")
                mixer.music.play()
            except: pass
        threading.Thread(target=play, daemon=True).start()

    # 2. PDF Context Extractor
    def read_pdf(self, file_path):
        text = ""
        try:
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                # ပထမ ၃ မျက်နှာကို context အဖြစ် ယူမယ်
                for page in reader.pages[:3]:
                    text += page.extract_text()
            return text[:1000] # စာလုံးရေ ၁၀၀၀ ထိ context ယူမယ်
        except Exception as e:
            return f"PDF Error: {str(e)}"

    # 3. Web Search Engine (Wikipedia)
    def web_search(self, topic):
        try:
            page = self.wiki.page(topic.strip())
            if page.exists():
                return page.summary[:600]
            return None
        except: return None

    # 4. Main Intelligence Logic
    def ask(self, prompt, pdf_context=""):
        search_data = ""
        
        # "Search" ပါရင် အင်တာနက်မှာ အရင်ရှာမယ်
        if "search" in prompt.lower():
            topic = prompt.lower().replace("search", "").strip()
            search_results = self.web_search(topic)
            if search_results:
                search_data = f"\nWeb Knowledge found: {search_results}\n"
        
        # Dolphin ဆီပို့မယ့် Prompt ကို Context တွေနဲ့ ပေါင်းစပ်ခြင်း
        full_context = f"PDF Info: {pdf_context}\n{search_data}"
        final_prompt = f"System Context: {full_context}\nUser: {prompt}\nAI Answer:"
        
        payload = {
            "model": self.model,
            "prompt": final_prompt,
            "stream": False
        }
        
        try:
            response = requests.post(self.ollama_url, json=payload, timeout=120)
            ans = response.json().get("response", "No response from model.")
            
            # Auto-Learning: Database ထဲ သိမ်းဆည်းခြင်း
            self.cursor.execute("INSERT INTO brain (topic, info) VALUES (?, ?)", (prompt, ans))
            self.conn.commit()
            return ans
        except Exception as e:
            return f"Ollama Connection Error: {str(e)}"

# --- UI Interface ---
class SuperAIApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Dolphin Pro - All-in-One AI")
        self.geometry("1000x700")
        ctk.set_appearance_mode("dark")
        
        self.brain = SuperBrain()
        self.current_pdf_context = ""
        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=220, fg_color="#1a1a1a", corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="🧠 AI CORE", font=("Orbitron", 22, "bold"), text_color="#00d4ff").pack(pady=30)
        
        ctk.CTkButton(self.sidebar, text="📁 Upload PDF", command=self.upload_pdf, fg_color="#333", hover_color="#444").pack(pady=15, padx=20)
        
        self.voice_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self.sidebar, text="Voice Output", variable=self.voice_var, text_color="#00d4ff").pack(pady=15)
        
        self.status_label = ctk.CTkLabel(self.sidebar, text="Status: Ready", text_color="gray")
        self.status_label.pack(side="bottom", pady=20)

        # Chat Area
        self.chat_display = ctk.CTkTextbox(self, fg_color="#0d1117", font=("Arial", 14), border_width=0)
        self.chat_display.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        # Input Area
        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="ew")
        
        self.entry = ctk.CTkEntry(self.input_frame, placeholder_text="Ask, Search, or Discuss PDF...", height=50, corner_radius=25)
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry.bind("<Return>", lambda e: self.handle_send())

        self.send_btn = ctk.CTkButton(self.input_frame, text="EVOLVE", width=100, height=50, corner_radius=25, fg_color="#00d4ff", text_color="black", command=self.handle_send)
        self.send_btn.pack(side="right")

    def upload_pdf(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.status_label.configure(text="Status: Reading PDF...", text_color="yellow")
            self.current_pdf_context = self.brain.read_pdf(file_path)
            self.chat_display.insert("end", f"\n[System]: PDF '{os.path.basename(file_path)}' has been analyzed. You can now ask questions about it.\n")
            self.status_label.configure(text="Status: PDF Loaded", text_color="#00ff88")

    def handle_send(self):
        msg = self.entry.get().strip()
        if not msg: return
        
        self.chat_display.insert("end", f"\nUSER: {msg}\n")
        self.entry.delete(0, 'end')
        self.status_label.configure(text="Status: AI Thinking...", text_color="orange")
        
        threading.Thread(target=self.run_logic, args=(msg,), daemon=True).start()

    def run_logic(self, msg):
        response = self.brain.ask(msg, self.current_pdf_context)
        
        self.chat_display.insert("end", f"AI: {response}\n\n" + "-"*40 + "\n")
        self.chat_display.see("end")
        self.status_label.configure(text="Status: Ready", text_color="#00ff88")
        
        if self.voice_var.get():
            self.brain.speak(response)

if __name__ == "__main__":
    app = SuperAIApp()
    app.mainloop()
    