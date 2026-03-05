import customtkinter as ctk
from datetime import datetime
from src.application.interfaces import ILogger

class GuiLogger(ILogger):
    def __init__(self, textbox: ctk.CTkTextbox):
        self.textbox = textbox

    def info(self, message: str):
        # เพิ่มเวลาใน log
        timestamp = datetime.now().strftime("%H:%M:%S")
        # ส่งไปทำงานใน Main Thread (UI Update)
        self.textbox.after(0, self._append_text, f"[{timestamp}] [INFO] {message}\n")

    def error(self, message: str):
        # เพิ่มเวลาใน log
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.textbox.after(0, self._append_text, f"[{timestamp}] [ERROR] {message}\n")

    def _append_text(self, text):
        # 1. ปลดล็อคกล่องข้อความชั่วคราว
        self.textbox.configure(state="normal")
        
        # 2. เขียนข้อความต่อท้าย
        self.textbox.insert("end", text)
        
        # 3. เลื่อน Scrollbar ลงล่างสุด
        self.textbox.see("end")
        
        # 4. ไม่ล็อคกลับ - ให้ copy ได้
        # แต่ปิดการแก้ไขด้วย binding
        # (ปล่อยให้เป็น normal เพื่อให้ copy ได้)