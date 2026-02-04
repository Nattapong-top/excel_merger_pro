import customtkinter as ctk
from typing import List
from src.domain.value_objects import SheetName

class SheetSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, filename: str, sheet_names: List[SheetName]):
        super().__init__(parent)
        self.title(f"Select Sheets: {filename}")
        self.geometry("400x500")
        
        # ทำให้เป็น Modal Window (กดหน้าอื่นไม่ได้จนกว่าจะปิดหน้านี้)
        self.grab_set()
        self.focus_force()

        self.selected_sheets = [] # เก็บผลลัพธ์ที่ User เลือก
        self.checkboxes = []

        # 1. Header
        lbl = ctk.CTkLabel(self, text=f"File: {filename}", font=("Arial", 14, "bold"))
        lbl.pack(pady=10)
        
        lbl_hint = ctk.CTkLabel(self, text="Select sheets to merge:")
        lbl_hint.pack(pady=5)

        # 2. Scrollable Frame (เผื่อ Sheet เยอะ)
        scroll_frame = ctk.CTkScrollableFrame(self, width=350, height=300)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # 3. สร้าง Checkbox ตามจำนวน Sheet
        for sheet in sheet_names:
            var = ctk.StringVar(value=sheet.value) # ติ๊กถูกไว้ก่อน (value=ชื่อ คือติ๊ก)
            chk = ctk.CTkCheckBox(scroll_frame, text=sheet.value, variable=var, 
                                  onvalue=sheet.value, offvalue="")
            chk.pack(anchor="w", pady=5, padx=10)
            self.checkboxes.append(chk)

        # 4. ปุ่ม OK
        btn_ok = ctk.CTkButton(self, text="Confirm", command=self.on_confirm)
        btn_ok.pack(pady=20)

    def on_confirm(self):
        # วนลูปดูว่าอันไหนถูกติ๊กบ้าง
        self.selected_sheets = []
        for chk in self.checkboxes:
            val = chk.get()
            if val != "": # ถ้าไม่ว่าง แปลว่าติ๊กถูก
                self.selected_sheets.append(SheetName(val))
        
        self.destroy() # ปิดหน้าต่าง

    def get_selected(self) -> List[SheetName]:
        # รอจนกว่าหน้าต่างจะปิด
        self.wait_window()
        return self.selected_sheets