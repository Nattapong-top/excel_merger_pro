import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import threading
import subprocess
import platform
import gc  # ใช้สำหรับคืนแรม
from datetime import datetime

# --- Import DDD Modules ---
from src.domain.value_objects import FilePath, SheetName
from src.domain.entities import SourceFile
from src.infrastructure.excel_reader import PandasSheetReader
from src.infrastructure.gui_logger import GuiLogger
from src.application.services import MergeService
from src.ui.dialogs import SheetSelectionDialog
from src.application.interfaces import ILogger

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# สร้าง Logger ตัวปลอมที่มีใบรับรองถูกต้อง
class DummyLogger(ILogger):
    def info(self, message: str):
        print(f"[LOG] {message}")  # พิมพ์ลง Console เฉยๆ

    def error(self, message: str):
        print(f"[ERR] {message}")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Data & Config ---
        self.source_files = [] 
        self.last_save_path = ""
        self.lang_code = "en"
        
        # --- Backend Setup ---
        self.reader = PandasSheetReader()
        # เริ่มต้นใช้ Logger ปลอมไปก่อน (เพราะยังไม่มีการ merge)
        self.dummy_logger = DummyLogger()
        self.service = MergeService(logger=self.dummy_logger, reader=self.reader)

        # --- Language Dictionary ---
        self.texts = {
            "en": {
                "title": "Merge Excel Pro - By Paa Top IT",
                "add_file": "Add Files", "add_folder": "Add Folder", "clear": "Clear List",
                "merge": "MERGE FILES", "open_dir": "Open Folder",
                "status_ready": "Ready...", "status_done": "Done! Saved at:", "status_processing": "Processing...",
                "msg_no_file": "Please select files first!", "msg_success": "Success!",
                "lang_label": "Language:"
            },
            "th": {
                "title": "โปรแกรมรวมไฟล์ Excel Pro - By Paa Top IT ",
                "add_file": "เพิ่มไฟล์", "add_folder": "เพิ่มโฟลเดอร์", "clear": "ล้างรายการ",
                "merge": "เริ่มรวมไฟล์", "open_dir": "เปิดที่เก็บไฟล์",
                "status_ready": "พร้อมทำงาน...", "status_done": "เรียบร้อย! บันทึกที่:", "status_processing": "กำลังทำงาน...",
                "msg_no_file": "กรุณาเลือกไฟล์ก่อนครับ!", "msg_success": "เรียบร้อย!",
                "lang_label": "ภาษา:"
            },
            "cn": { "title": "Merge Excel Pro", "add_file": "Add", "add_folder": "Folder", "clear": "Clear", "merge": "Merge", "open_dir": "Open", "status_ready": "Ready", "status_done": "Done", "status_processing": "Processing", "msg_no_file": "No File", "msg_success": "Success", "lang_label": "Lang" }
        }

        # --- UI Layout ---
        self.title("Merge Excel Pro - By Paa Top IT")
        self.geometry("750x600")
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.create_widgets()
        self.update_language_ui()

    def create_widgets(self):
        # 1. Header
        self.header_frame = ctk.CTkFrame(self, corner_radius=0)
        self.header_frame.grid(row=0, column=0, sticky="ew")
        
        self.logo_label = ctk.CTkLabel(self.header_frame, text="Merger Pro", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(side="left", padx=20, pady=15)

        self.lang_option = ctk.CTkOptionMenu(self.header_frame, values=["English", "ไทย", "中文"], command=self.change_language_event, width=100)
        self.lang_option.pack(side="right", padx=20, pady=10)
        self.lang_label_ui = ctk.CTkLabel(self.header_frame, text="Language:")
        self.lang_label_ui.pack(side="right", padx=5)

        # 2. Main Content
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1) 
        self.main_frame.grid_columnconfigure(1, weight=0) 
        self.main_frame.grid_rowconfigure(0, weight=1)

        # 3. File List / Log Display (จอแสดงผลหลัก)
        self.file_list_display = ctk.CTkTextbox(self.main_frame, font=("Consolas", 14))
        self.file_list_display.grid(row=0, column=0, sticky="nsew", padx=(0, 15))
        self.file_list_display.insert("0.0", "Please add files...\n")
        self.file_list_display.configure(state="disabled")

        # 4. Buttons Zone
        self.btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btn_frame.grid(row=0, column=1, sticky="ns")

        self.btn_add_file = ctk.CTkButton(self.btn_frame, text="Add Files", command=self.add_files_action)
        self.btn_add_file.pack(pady=(0, 10), fill="x")

        self.btn_add_folder = ctk.CTkButton(self.btn_frame, text="Add Folder", command=self.add_folder_action)
        self.btn_add_folder.pack(pady=(0, 10), fill="x")

        self.btn_clear = ctk.CTkButton(self.btn_frame, text="Clear", fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"), command=self.clear_action)
        self.btn_clear.pack(pady=(0, 20), fill="x")

        self.btn_merge = ctk.CTkButton(self.btn_frame, text="MERGE", height=60, fg_color="#2CC985", hover_color="#FF0000", font=ctk.CTkFont(size=16, weight="bold"), command=self.merge_action)
        self.btn_merge.pack(side="bottom", fill="x", pady=(10, 0))

        self.btn_open_folder = ctk.CTkButton(self.btn_frame, text="Open Folder", fg_color="#3B8ED0", command=self.open_folder_action)
        self.btn_open_folder.pack(side="bottom", fill="x", pady=(0, 10)) 
        self.btn_open_folder.configure(state="disabled")

        # 5. Status Bar
        self.status_label = ctk.CTkLabel(self, text="Ready...", anchor="w", text_color="gray")
        self.status_label.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

    # --- UI Logic ---
    def update_file_list_ui(self):
        """อัปเดตหน้าจอเพื่อแสดงรายชื่อไฟล์"""
        self.file_list_display.configure(state="normal")
        self.file_list_display.delete("0.0", "end")
        
        if not self.source_files:
            self.file_list_display.insert("0.0", "No files selected...\n")
        else:
            for idx, file in enumerate(self.source_files, 1):
                file_name = os.path.basename(file.path.value)
                sheet_count = len(file.selected_sheets)
                total_sheet = len(file.available_sheets)
                
                text = f"[{idx}] 📄 {file_name} (Selected {sheet_count}/{total_sheet} sheets)\n"
                self.file_list_display.insert("end", text)
                
                selected_names = ", ".join([s.value for s in file.selected_sheets])
                self.file_list_display.insert("end", f"      ↳ {selected_names}\n\n")

        self.file_list_display.configure(state="disabled")

    def add_files_action(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Excel Files", "*.xlsx *.xls")])
        if not file_paths: return

        def load_files():
            self.status_label.configure(text="Scanning files...")
            for path_str in file_paths:
                try:
                    path = FilePath(path_str)
                    sheets = self.reader.get_sheet_names(path)
                    
                    # กลับไป Main Thread เพื่อเปิด Dialog
                    self.after(0, lambda p=path_str, s=sheets: self.show_selection_dialog(p, s))
                except Exception as e:
                    print(f"Error: {e}")
            self.after(0, lambda: self.status_label.configure(text="Ready..."))

        threading.Thread(target=load_files, daemon=True).start()

    def show_selection_dialog(self, path_str, sheets):
        dialog = SheetSelectionDialog(self, os.path.basename(path_str), sheets)
        selected = dialog.get_selected()
        
        if selected:
            source_file = SourceFile(FilePath(path_str), sheets)
            for s in selected:
                source_file.select_sheet(s)
            self.source_files.append(source_file)
            self.update_file_list_ui()

    def add_folder_action(self):
        messagebox.showinfo("Info", "Coming soon in next update!")

    def clear_action(self):
        self.source_files = []
        self.last_save_path = ""
        self.btn_open_folder.configure(state="disabled")
        self.update_file_list_ui() # รีเซ็ตหน้าจอกลับมาเป็นรายชื่อไฟล์

    def merge_action(self):
        t = self.texts[self.lang_code]
        if not self.source_files:
            messagebox.showwarning("Warning", t["msg_no_file"])
            return

        # 1. ตั้งชื่อไฟล์อัตโนมัติ
        first_file_name = os.path.basename(self.source_files[0].path.value).split('.')[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"merge_{first_file_name}_{timestamp}.xlsx"

        # 2. ถามที่เซฟ
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile=default_name
        )
        if not save_path: return

        # 3. เตรียมหน้าจอสำหรับ Log (เคลียร์รายชื่อไฟล์ออก)
        self.file_list_display.configure(state="normal")
        self.file_list_display.delete("0.0", "end")
        self.file_list_display.insert("0.0", "--- STARTING MERGE PROCESS ---\n\n")
        self.file_list_display.configure(state="disabled")

        self.btn_merge.configure(state="disabled", text="Processing...")
        self.status_label.configure(text=t["status_processing"])

        # 4. Thread ทำงาน
        def run():
            try:
                # *** สร้าง Logger จริง เสียบเข้าหน้าจอ ***
                real_logger = GuiLogger(self.file_list_display)
                self.service.logger = real_logger
                
                # เริ่มรวมไฟล์
                result_df = self.service.merge(self.source_files)
                
                if not result_df.empty:
                    result_df.to_excel(save_path, index=False)
                    
                    # *** Cleaning Up Memory ***
                    real_logger.info("Cleaning up memory (Garbage Collection)...")
                    del result_df
                    gc.collect() 
                    
                    self.after(0, lambda: self.finish_merge(save_path, True, None))
                else:
                    self.after(0, lambda: self.finish_merge(save_path, False, "No data to merge"))
            except Exception as e:
                self.after(0, lambda: self.finish_merge(save_path, False, str(e)))

        threading.Thread(target=run, daemon=True).start()

    def finish_merge(self, save_path, success, error_msg):
        t = self.texts[self.lang_code]
        self.btn_merge.configure(state="normal", text=t["merge"])
        
        if success:
            self.last_save_path = save_path
            self.btn_open_folder.configure(state="normal")
            self.status_label.configure(text=f"{t['status_done']} {os.path.basename(save_path)}")
            messagebox.showinfo(t["msg_success"], f"Saved to:\n{save_path}")
        else:
            self.status_label.configure(text=f"Error: {error_msg}")
            messagebox.showerror("Error", error_msg)

    def open_folder_action(self):
        if self.last_save_path and os.path.exists(self.last_save_path):
            folder_path = os.path.dirname(self.last_save_path)
            if platform.system() == "Windows": os.startfile(folder_path)
            else: subprocess.Popen(["open" if platform.system() == "Darwin" else "xdg-open", folder_path])

    def change_language_event(self, new_lang):
        if new_lang == "English": self.lang_code = "en"
        elif new_lang == "ไทย": self.lang_code = "th"
        elif new_lang == "中文": self.lang_code = "cn"
        self.update_language_ui()

    def update_language_ui(self):
        t = self.texts[self.lang_code]
        self.logo_label.configure(text=t["title"])
        self.lang_label_ui.configure(text=t["lang_label"])
        self.btn_add_file.configure(text=t["add_file"])
        self.btn_add_folder.configure(text=t["add_folder"])
        self.btn_clear.configure(text=t["clear"])
        self.btn_merge.configure(text=t["merge"])
        self.btn_open_folder.configure(text=t["open_dir"])