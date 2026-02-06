import customtkinter as ctk
from typing import List, Dict
from src.domain.value_objects import SheetName, FilePath
import os

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


class MultiFileSheetSelectionDialog(ctk.CTkToplevel):
    """Dialog สำหรับเลือก Sheet จากหลายไฟล์พร้อมกัน"""
    
    def __init__(self, parent, files_data: Dict[str, List[SheetName]]):
        """
        files_data: Dict[file_path, List[SheetName]]
        """
        super().__init__(parent)
        self.title(f"Select Sheets from {len(files_data)} Files")
        self.geometry("600x700")
        
        self.grab_set()
        self.focus_force()

        self.files_data = files_data
        self.file_checkboxes = {}  # {file_path: [checkbox1, checkbox2, ...]}
        self.selected_data = {}  # {file_path: [SheetName1, SheetName2, ...]}

        # Header
        lbl = ctk.CTkLabel(self, text=f"Found {len(files_data)} Excel files", 
                          font=("Arial", 16, "bold"))
        lbl.pack(pady=(15, 5))
        
        lbl_hint = ctk.CTkLabel(self, text="Select sheets to merge from each file:")
        lbl_hint.pack(pady=5)

        # Global Actions
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=5, fill="x", padx=20)

        btn_select_all = ctk.CTkButton(action_frame, text="Select All", 
                                       width=120, height=30,
                                       fg_color="#3B8ED0",
                                       command=self.select_all_action)
        btn_select_all.pack(side="left", padx=5, expand=True)

        btn_deselect_all = ctk.CTkButton(action_frame, text="Unselect All", 
                                         width=120, height=30,
                                         fg_color="gray",
                                         command=self.deselect_all_action)
        btn_deselect_all.pack(side="right", padx=5, expand=True)

        # Scrollable Area
        scroll_frame = ctk.CTkScrollableFrame(self, width=550, height=450)
        scroll_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # สร้าง UI สำหรับแต่ละไฟล์
        for file_path, sheet_names in files_data.items():
            self.create_file_section(scroll_frame, file_path, sheet_names)

        # Confirm Button
        btn_ok = ctk.CTkButton(self, text="Confirm Selection", 
                              command=self.on_confirm, 
                              height=45, 
                              font=("Arial", 15, "bold"),
                              fg_color="#2CC985")
        btn_ok.pack(pady=20, padx=20, fill="x")

    def create_file_section(self, parent, file_path: str, sheet_names: List[SheetName]):
        """สร้างส่วนแสดงไฟล์และ Sheet ของมัน"""
        # Frame สำหรับไฟล์นี้
        file_frame = ctk.CTkFrame(parent, fg_color=("#E0E0E0", "#2B2B2B"), corner_radius=8)
        file_frame.pack(pady=8, padx=5, fill="x")

        # Header ของไฟล์ (ชื่อไฟล์ + ปุ่ม Select/Unselect)
        header_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=8)

        file_name = os.path.basename(file_path)
        lbl_file = ctk.CTkLabel(header_frame, text=f"📄 {file_name}", 
                               font=("Arial", 13, "bold"),
                               anchor="w")
        lbl_file.pack(side="left", fill="x", expand=True)

        # ปุ่มเล็กๆ สำหรับไฟล์นี้
        btn_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        btn_frame.pack(side="right")

        btn_sel = ctk.CTkButton(btn_frame, text="All", width=50, height=25,
                               command=lambda fp=file_path: self.select_file_sheets(fp))
        btn_sel.pack(side="left", padx=2)

        btn_unsel = ctk.CTkButton(btn_frame, text="None", width=50, height=25,
                                 fg_color="gray",
                                 command=lambda fp=file_path: self.deselect_file_sheets(fp))
        btn_unsel.pack(side="left", padx=2)

        # Checkboxes สำหรับ Sheets
        self.file_checkboxes[file_path] = []
        for sheet in sheet_names:
            var = ctk.StringVar(value=sheet.value)
            chk = ctk.CTkCheckBox(file_frame, text=f"  ↳ {sheet.value}", 
                                 variable=var,
                                 onvalue=sheet.value, 
                                 offvalue="")
            chk.pack(anchor="w", pady=3, padx=25)
            chk.select()  # เลือกทุก Sheet ตั้งแต่แรก
            self.file_checkboxes[file_path].append(chk)

    def select_all_action(self):
        """เลือกทุก Sheet ของทุกไฟล์"""
        for checkboxes in self.file_checkboxes.values():
            for chk in checkboxes:
                chk.select()

    def deselect_all_action(self):
        """ยกเลิกทุก Sheet ของทุกไฟล์"""
        for checkboxes in self.file_checkboxes.values():
            for chk in checkboxes:
                chk.deselect()

    def select_file_sheets(self, file_path: str):
        """เลือกทุก Sheet ของไฟล์นี้"""
        for chk in self.file_checkboxes[file_path]:
            chk.select()

    def deselect_file_sheets(self, file_path: str):
        """ยกเลิกทุก Sheet ของไฟล์นี้"""
        for chk in self.file_checkboxes[file_path]:
            chk.deselect()

    def on_confirm(self):
        """เก็บข้อมูลที่เลือกและปิด Dialog"""
        self.selected_data = {}
        
        for file_path, checkboxes in self.file_checkboxes.items():
            selected_sheets = []
            for chk in checkboxes:
                val = chk.get()
                if val != "":
                    selected_sheets.append(SheetName(val))
            
            if selected_sheets:  # เก็บเฉพาะไฟล์ที่มีการเลือก Sheet
                self.selected_data[file_path] = selected_sheets
        
        self.destroy()

    def get_selected(self) -> Dict[str, List[SheetName]]:
        """
        Returns: Dict[file_path, List[SheetName]]
        """
        self.wait_window()
        return self.selected_data