import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading

# Import ของที่เราทำไว้
from src.domain.value_objects import FilePath
from src.domain.entities import SourceFile
from src.infrastructure.excel_reader import PandasSheetReader
from src.infrastructure.gui_logger import GuiLogger
from src.application.services import MergeService
from src.ui.dialogs import SheetSelectionDialog

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Excel Merger Pro (DDD Edition)")
        self.geometry("600x500")
        
        # เก็บรายการ SourceFile ที่เตรียมจะ Merge
        self.source_files = [] 

        # --- UI Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # ให้ช่อง Log ยืดได้

        # 1. ปุ่ม Add Files
        self.btn_add = ctk.CTkButton(self, text="Add Excel Files", command=self.add_files_action)
        self.btn_add.grid(row=0, column=0, pady=20, padx=20, sticky="ew")

        # 2. ปุ่ม Merge
        self.btn_merge = ctk.CTkButton(self, text="START MERGE", command=self.start_merge_thread, fg_color="green")
        self.btn_merge.grid(row=1, column=0, pady=10, padx=20, sticky="ew")

        # 3. Log Output (จอแสดงผล)
        self.txt_log = ctk.CTkTextbox(self)
        self.txt_log.grid(row=2, column=0, pady=20, padx=20, sticky="nsew")
        
        # --- เตรียมระบบหลังบ้าน ---
        # สร้าง Reader และ Logger รอไว้
        self.reader = PandasSheetReader()
        self.logger = GuiLogger(self.txt_log)
        self.service = MergeService(self.logger, self.reader)

    def add_files_action(self):
        """เมื่อกดปุ่ม Add Files"""
        file_paths = filedialog.askopenfilenames(filetypes=[("Excel Files", "*.xlsx *.xls")])
        
        if not file_paths:
            return

        for path_str in file_paths:
            try:
                path = FilePath(path_str)
                
                # 1. แอบอ่านชื่อ Sheet ก่อน
                sheets = self.reader.get_sheet_names(path)
                
                # 2. เด้ง Pop-up ให้เลือก Sheet
                dialog = SheetSelectionDialog(self, path_str, sheets)
                selected = dialog.get_selected()
                
                if not selected:
                    self.logger.info(f"Skipped file: {path_str} (No sheets selected)")
                    continue

                # 3. สร้าง SourceFile พร้อม Sheet ที่เลือก
                source_file = SourceFile(path, sheets)
                # เลือก Sheet ตามที่ user ติ๊กมา
                for s in selected:
                    source_file.select_sheet(s)
                
                self.source_files.append(source_file)
                self.logger.info(f"Added: {path_str} ({len(selected)} sheets)")
                
            except Exception as e:
                self.logger.error(f"Error adding file {path_str}: {e}")

    def start_merge_thread(self):
        """กดปุ่ม Merge (รันใน Thread แยก กันหน้าจอค้าง)"""
        if not self.source_files:
            messagebox.showwarning("Warning", "Please add files first!")
            return

        # ปิดปุ่มกันกดซ้ำ
        self.btn_merge.configure(state="disabled")
        
        def run():
            try:
                # เรียกใช้ Service พระเอกของเรา!
                result_df = self.service.merge(self.source_files)
                
                # (ตัวอย่าง) บันทึกไฟล์
                if not result_df.empty:
                    save_path = "merged_output.xlsx"
                    result_df.to_excel(save_path, index=False)
                    self.logger.info(f"Saved to: {save_path}")
                    messagebox.showinfo("Success", f"Done! Saved to {save_path}")
                else:
                    self.logger.info("Result is empty.")
                    
            except Exception as e:
                self.logger.error(f"Critical Error: {e}")
            finally:
                # เปิดปุ่มคืน
                self.btn_merge.configure(state="normal")

        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()