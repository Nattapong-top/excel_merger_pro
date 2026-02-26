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
from src.ui.dialogs import SheetSelectionDialog, MultiFileSheetSelectionDialog
from src.ui.processing_options_dialog import ProcessingOptionsDialog
from src.ui.progress_dialog import ProgressDialog
from src.application.interfaces import ILogger
from src.infrastructure.progress_tracker import ThreadSafeProgressTracker
from src.domain.processing_options import ProcessingOptions

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
            "cn": {
                "title": "合并Excel专业版 - By Paa Top IT",
                "add_file": "添加文件", "add_folder": "添加文件夹", "clear": "清除列表",
                "merge": "合并文件", "open_dir": "打开文件夹",
                "status_ready": "准备就绪...", "status_done": "完成！保存在:", "status_processing": "处理中...",
                "msg_no_file": "请先选择文件！", "msg_success": "成功！",
                "lang_label": "语言:"
            }
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
            files_data = {}  # {file_path: [SheetName1, SheetName2, ...]}
            
            for path_str in file_paths:
                try:
                    path = FilePath(path_str)
                    sheets = self.reader.get_sheet_names(path)
                    files_data[path_str] = sheets
                except Exception as e:
                    print(f"Error: {e}")
            
            if files_data:
                # แสดง Dialog เดียวสำหรับทุกไฟล์
                self.after(0, lambda: self.show_multi_file_selection_dialog(files_data))
            
            self.after(0, lambda: self.status_label.configure(text="Ready..."))

        threading.Thread(target=load_files, daemon=True).start()

    def show_multi_file_selection_dialog(self, files_data):
        """แสดง Dialog สำหรับเลือก Sheet จากหลายไฟล์พร้อมกัน"""
        dialog = MultiFileSheetSelectionDialog(self, files_data, lang_code=self.lang_code)
        selected_data = dialog.get_selected()
        
        # เพิ่มไฟล์ที่เลือกเข้าไปใน source_files
        for file_path, selected_sheets in selected_data.items():
            path = FilePath(file_path)
            all_sheets = files_data[file_path]
            
            source_file = SourceFile(path, all_sheets)
            for sheet in selected_sheets:
                source_file.select_sheet(sheet)
            
            self.source_files.append(source_file)
        
        self.update_file_list_ui()

    def add_folder_action(self):
        folder_path = filedialog.askdirectory(title="Select Folder")
        if not folder_path: return

        def scan_folder():
            self.status_label.configure(text="Scanning folder...")
            files_data = {}  # {file_path: [SheetName1, SheetName2, ...]}
            
            # สแกนหาไฟล์ Excel ทั้งหมดในโฟลเดอร์ (รวม subfolder)
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.endswith(('.xlsx', '.xls')):
                        full_path = os.path.join(root, file)
                        try:
                            path = FilePath(full_path)
                            sheets = self.reader.get_sheet_names(path)
                            files_data[full_path] = sheets
                        except Exception as e:
                            print(f"Error loading {full_path}: {e}")
            
            if not files_data:
                self.after(0, lambda: messagebox.showinfo("Info", f"No Excel files found in:\n{folder_path}"))
                self.after(0, lambda: self.status_label.configure(text="Ready..."))
                return
            
            # แสดง Dialog เดียวสำหรับทุกไฟล์
            self.after(0, lambda: self.show_multi_file_selection_dialog(files_data))
            self.after(0, lambda: self.status_label.configure(text=f"Loaded {len(files_data)} files from folder"))

        threading.Thread(target=scan_folder, daemon=True).start()

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

        # 1. Read columns from first file's first sheet
        available_columns = []
        try:
            first_file = self.source_files[0]
            if first_file.selected_sheets:
                first_sheet = first_file.selected_sheets[0]
                # Read just the header (first row)
                import pandas as pd
                df_header = pd.read_excel(
                    first_file.path.value,
                    sheet_name=first_sheet.value,
                    nrows=0,  # Read only header
                    engine='openpyxl'
                )
                available_columns = list(df_header.columns)
        except Exception as e:
            print(f"Warning: Could not read columns from first file: {e}")
            available_columns = []

        # 2. Show processing options dialog with available columns
        options_dialog = ProcessingOptionsDialog(
            self, 
            available_columns=available_columns,
            lang_code=self.lang_code
        )
        self.wait_window(options_dialog)
        
        options = options_dialog.get_result()
        if options is None:
            # User cancelled
            return

        # 2. Auto-generate filename
        first_file_name = os.path.basename(self.source_files[0].path.value).split('.')[0]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        default_name = f"merge_{first_file_name}_{timestamp}.xlsx"

        # 3. Ask save location
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")],
            initialfile=default_name
        )
        if not save_path:
            return

        # 4. Prepare UI for processing
        self.file_list_display.configure(state="normal")
        self.file_list_display.delete("0.0", "end")
        self.file_list_display.insert("0.0", "--- STARTING MERGE PROCESS ---\n\n")
        self.file_list_display.configure(state="disabled")

        self.btn_merge.configure(state="disabled", text="Processing...")
        self.status_label.configure(text=t["status_processing"])

        # 5. Create progress tracker and dialog
        progress_tracker = ThreadSafeProgressTracker()
        progress_dialog = ProgressDialog(self, progress_tracker, title="Merging Files")

        # 6. Run merge in background thread
        def run():
            try:
                # Create GUI logger
                real_logger = GuiLogger(self.file_list_display)
                
                # Create service with progress tracking
                service = MergeService(
                    logger=real_logger,
                    reader=self.reader,
                    progress_callback=progress_tracker
                )
                
                # Start merge
                result_df = service.merge(self.source_files, options)
                
                if not result_df.empty:
                    result_df.to_excel(save_path, index=False)
                    
                    # Clean up memory
                    real_logger.info("Cleaning up memory (Garbage Collection)...")
                    del result_df
                    gc.collect()
                    
                    self.after(0, lambda: self._finish_merge_success(save_path, progress_dialog))
                else:
                    self.after(0, lambda: self._finish_merge_error(
                        save_path, "No data to merge", progress_dialog
                    ))
                    
            except Exception as e:
                error_msg = str(e)
                if 'cancel' in error_msg.lower():
                    self.after(0, lambda: self._finish_merge_cancelled(progress_dialog))
                else:
                    self.after(0, lambda: self._finish_merge_error(
                        save_path, error_msg, progress_dialog
                    ))

        threading.Thread(target=run, daemon=True).start()

    def _finish_merge_success(self, save_path, progress_dialog):
        """Handle successful merge completion"""
        t = self.texts[self.lang_code]
        
        # Close progress dialog
        progress_dialog.close_dialog()
        
        # Update UI
        self.btn_merge.configure(state="normal", text=t["merge"])
        self.last_save_path = save_path
        self.btn_open_folder.configure(state="normal")
        self.status_label.configure(text=f"{t['status_done']} {os.path.basename(save_path)}")
        
        messagebox.showinfo(t["msg_success"], f"Saved to:\n{save_path}")
    
    def _finish_merge_error(self, save_path, error_msg, progress_dialog):
        """Handle merge error"""
        t = self.texts[self.lang_code]
        
        # Close progress dialog
        progress_dialog.close_dialog()
        
        # Update UI
        self.btn_merge.configure(state="normal", text=t["merge"])
        self.status_label.configure(text=f"Error: {error_msg}")
        
        messagebox.showerror("Error", error_msg)
    
    def _finish_merge_cancelled(self, progress_dialog):
        """Handle merge cancellation"""
        t = self.texts[self.lang_code]
        
        # Close progress dialog
        progress_dialog.close_dialog()
        
        # Update UI
        self.btn_merge.configure(state="normal", text=t["merge"])
        self.status_label.configure(text="Operation cancelled")
        
        messagebox.showinfo("Cancelled", "Merge operation was cancelled")

    def finish_merge(self, save_path, success, error_msg):
        """Legacy method - kept for compatibility"""
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