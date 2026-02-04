import customtkinter as ctk
from typing import List
from src.domain.value_objects import SheetName

class SheetSelectionDialog(ctk.CTkToplevel):
    def __init__(self, parent, filename: str, sheet_names: List[SheetName]):
        super().__init__(parent)
        self.title(f"Select Sheets")
        self.geometry("400x600")
        
        # ทำให้เป็นหน้าต่างหลัก (กดอย่างอื่นไม่ได้)
        self.grab_set()
        self.focus_force()

        self.selected_sheets = [] 
        self.checkboxes = []

        # Header
        lbl = ctk.CTkLabel(self, text=f"File: {filename}", font=("Arial", 14, "bold"))
        lbl.pack(pady=(15, 5))
        
        lbl_hint = ctk.CTkLabel(self, text="Select sheets to merge:")
        lbl_hint.pack(pady=5)

        # --- เพิ่มปุ่ม Select All / Unselect All ตรงนี้ครับ ---
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=5, fill="x", padx=20)

        btn_select_all = ctk.CTkButton(action_frame, text="Select All", 
                                       width=100, height=25,
                                       fg_color="#3B8ED0",
                                       command=self.select_all_action)
        btn_select_all.pack(side="left", padx=5, expand=True)

        btn_deselect_all = ctk.CTkButton(action_frame, text="Unselect All", 
                                         width=100, height=25,
                                         fg_color="gray",
                                         command=self.deselect_all_action)
        btn_deselect_all.pack(side="right", padx=5, expand=True)
        # ------------------------------------------------

        # Scrollable Area
        scroll_frame = ctk.CTkScrollableFrame(self, width=350, height=350)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Checkboxes
        for sheet in sheet_names:
            var = ctk.StringVar(value=sheet.value) 
            chk = ctk.CTkCheckBox(scroll_frame, text=sheet.value, variable=var, 
                                  onvalue=sheet.value, offvalue="")
            chk.pack(anchor="w", pady=5, padx=10)
            self.checkboxes.append(chk)

        # Confirm Button
        btn_ok = ctk.CTkButton(self, text="Confirm", command=self.on_confirm, height=40, font=("Arial", 14, "bold"))
        btn_ok.pack(pady=20, padx=20, fill="x")

    def select_all_action(self):
        for chk in self.checkboxes: chk.select()

    def deselect_all_action(self):
        for chk in self.checkboxes: chk.deselect()

    def on_confirm(self):
        self.selected_sheets = []
        for chk in self.checkboxes:
            val = chk.get()
            if val != "": 
                self.selected_sheets.append(SheetName(val))
        self.destroy()

    def get_selected(self) -> List[SheetName]:
        self.wait_window()
        return self.selected_sheets