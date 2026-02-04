import customtkinter as ctk
from src.application.interfaces import ILogger

class GuiLogger(ILogger):
    def __init__(self, textbox: ctk.CTkTextbox):
        self.textbox = textbox

    def info(self, message: str):
        # ส่งไปทำงานใน Main Thread (UI Update)
        self.textbox.after(0, self._append_text, f"[INFO] {message}\n")

    def error(self, message: str):
        self.textbox.after(0, self._append_text, f"[ERROR] {message}\n")

    def _append_text(self, text):
        # 1. ปลดล็อคกล่องข้อความ
        self.textbox.configure(state="normal")
        
        # 2. เขียนข้อความต่อท้าย
        self.textbox.insert("end", text)
        
        # 3. เลื่อน Scrollbar ลงล่างสุด
        self.textbox.see("end")
        
        # 4. ล็อคกลับเหมือนเดิม
        self.textbox.configure(state="disabled")