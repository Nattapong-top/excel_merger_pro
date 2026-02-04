import customtkinter as ctk
from src.application.interfaces import ILogger

class GuiLogger(ILogger):
    def __init__(self, textbox: ctk.CTkTextbox):
        self.textbox = textbox

    def info(self, message: str):
        # ใช้ .after เพื่อความปลอดภัยเมื่อเรียกจาก Thread อื่น
        self.textbox.after(0, self._append_text, f"[INFO] {message}\n")

    def error(self, message: str):
        self.textbox.after(0, self._append_text, f"[ERROR] {message}\n")

    def _append_text(self, text):
        self.textbox.insert("end", text)
        self.textbox.see("end") # เลื่อน Scrollbar ลงล่างสุดอัตโนมัติ