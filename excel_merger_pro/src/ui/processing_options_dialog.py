# File: src/ui/processing_options_dialog.py
"""
Dialog for configuring processing options

Allows users to enable/configure:
- Chunked reading for large files
- Parallel processing
- Group by with aggregations
- Duplicate removal
- Column selection and reordering
"""

import customtkinter as ctk
from typing import Optional, List
from src.domain.processing_options import (
    ProcessingOptions,
    GroupByConfig,
    DuplicateRemovalConfig,
    ColumnSelectionConfig
)


class ProcessingOptionsDialog(ctk.CTkToplevel):
    """
    Dialog for configuring all processing options
    
    Features:
    - Checkboxes for enabling features
    - Expandable sections for configuration
    - Input validation
    - OK/Cancel buttons
    - Multi-language support
    """
    
    # Language texts
    TEXTS = {
        "en": {
            "title": "Processing Options",
            "configure": "Configure Processing Options",
            "performance": "Performance Optimization",
            "chunked": "Enable chunked reading for large files (>100MB)",
            "chunk_size": "Chunk size:",
            "rows": "rows",
            "parallel": "Enable parallel processing",
            "max_workers": "Max workers:",
            "threads": "threads",
            "data_processing": "Data Processing (Optional)",
            "note": "Note: These features will be available after initial merge",
            "groupby": "Group by columns",
            "duplicates": "Remove duplicates (Coming soon)",
            "columns": "Select/reorder columns (Coming soon)",
            "ok": "OK",
            "cancel": "Cancel",
            "error_title": "Invalid Input",
            "error_msg": "Invalid configuration:"
        },
        "th": {
            "title": "ตัวเลือกการประมวลผล",
            "configure": "กำหนดค่าตัวเลือกการประมวลผล",
            "performance": "การเพิ่มประสิทธิภาพ",
            "chunked": "เปิดใช้การอ่านแบบแบ่งส่วนสำหรับไฟล์ขนาดใหญ่ (>100MB)",
            "chunk_size": "ขนาดส่วน:",
            "rows": "แถว",
            "parallel": "เปิดใช้การประมวลผลแบบขนาน",
            "max_workers": "จำนวน workers สูงสุด:",
            "threads": "threads",
            "data_processing": "การประมวลผลข้อมูล (ตัวเลือก)",
            "note": "หมายเหตุ: ฟีเจอร์เหล่านี้จะพร้อมใช้งานหลังจากรวมไฟล์เบื้องต้น",
            "groupby": "จัดกลุ่มตามคอลัมน์",
            "duplicates": "ลบข้อมูลซ้ำ (เร็วๆ นี้)",
            "columns": "เลือก/จัดเรียงคอลัมน์ (เร็วๆ นี้)",
            "ok": "ตกลง",
            "cancel": "ยกเลิก",
            "error_title": "ข้อมูลไม่ถูกต้อง",
            "error_msg": "การตั้งค่าไม่ถูกต้อง:"
        },
        "cn": {
            "title": "处理选项",
            "configure": "配置处理选项",
            "performance": "性能优化",
            "chunked": "启用大文件分块读取 (>100MB)",
            "chunk_size": "块大小:",
            "rows": "行",
            "parallel": "启用并行处理",
            "max_workers": "最大工作线程:",
            "threads": "线程",
            "data_processing": "数据处理（可选）",
            "note": "注意：这些功能将在初始合并后可用",
            "groupby": "按列分组",
            "duplicates": "删除重复项（即将推出）",
            "columns": "选择/重新排序列（即将推出）",
            "ok": "确定",
            "cancel": "取消",
            "error_title": "输入无效",
            "error_msg": "配置无效:"
        }
    }
    
    def __init__(self, parent, available_columns: List[str] = None, lang_code: str = "en"):
        """
        Initialize processing options dialog
        
        Args:
            parent: Parent window
            available_columns: List of available column names (for processors)
            lang_code: Language code (en, th, cn)
        """
        super().__init__(parent)
        
        self.available_columns = available_columns or []
        self.result: Optional[ProcessingOptions] = None
        self.lang_code = lang_code
        self.texts = self.TEXTS.get(lang_code, self.TEXTS["en"])
        
        # Set default performance values (hidden from UI but used in processing)
        # Memory-optimized for 16GB RAM limit: Enable chunking with smaller chunks, single worker
        self.chunking_var = ctk.BooleanVar(value=True)  # Enable chunking to save RAM
        self.chunk_size_value = 20000  # Moderate chunk size (balance speed vs memory)
        self.parallel_var = ctk.BooleanVar(value=True)  # Keep parallel enabled
        self.max_workers_value = 1  # Single worker to minimize RAM usage
        
        # Window configuration
        self.title(self.texts["title"])
        self.geometry("600x500")  # Reduced height since performance section is hidden
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 500) // 2  # Adjusted for new height
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self, width=560, height=400)  # Reduced height
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=self.texts["configure"],
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Performance section - HIDDEN, but values still set as defaults
        # self._create_performance_section(main_frame)
        
        # Data processing section
        self._create_data_processing_section(main_frame)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.ok_button = ctk.CTkButton(
            button_frame,
            text=self.texts["ok"],
            command=self._on_ok,
            width=120
        )
        self.ok_button.pack(side="right", padx=5)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text=self.texts["cancel"],
            command=self._on_cancel,
            width=120,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_button.pack(side="right", padx=5)
    
    def _create_performance_section(self, parent):
        """Create performance optimization section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=10)
        
        # Section title
        ctk.CTkLabel(
            section_frame,
            text=self.texts["performance"],
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Chunked reading
        self.chunking_var = ctk.BooleanVar(value=False)
        chunking_check = ctk.CTkCheckBox(
            section_frame,
            text=self.texts["chunked"],
            variable=self.chunking_var
        )
        chunking_check.pack(anchor="w", padx=20, pady=5)
        
        # Chunk size
        chunk_frame = ctk.CTkFrame(section_frame)
        chunk_frame.pack(fill="x", padx=30, pady=5)
        
        ctk.CTkLabel(chunk_frame, text=self.texts["chunk_size"]).pack(side="left", padx=5)
        self.chunk_size_entry = ctk.CTkEntry(chunk_frame, width=100)
        self.chunk_size_entry.insert(0, "10000")
        self.chunk_size_entry.pack(side="left", padx=5)
        ctk.CTkLabel(chunk_frame, text=self.texts["rows"]).pack(side="left", padx=5)
        
        # Parallel processing
        self.parallel_var = ctk.BooleanVar(value=True)
        parallel_check = ctk.CTkCheckBox(
            section_frame,
            text=self.texts["parallel"],
            variable=self.parallel_var
        )
        parallel_check.pack(anchor="w", padx=20, pady=5)
        
        # Max workers
        worker_frame = ctk.CTkFrame(section_frame)
        worker_frame.pack(fill="x", padx=30, pady=(5, 10))
        
        ctk.CTkLabel(worker_frame, text=self.texts["max_workers"]).pack(side="left", padx=5)
        self.max_workers_entry = ctk.CTkEntry(worker_frame, width=100)
        self.max_workers_entry.insert(0, "4")
        self.max_workers_entry.pack(side="left", padx=5)
        ctk.CTkLabel(worker_frame, text=self.texts["threads"]).pack(side="left", padx=5)
    
    def _create_data_processing_section(self, parent):
        """Create data processing section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=10)
        
        # Section title
        ctk.CTkLabel(
            section_frame,
            text=self.texts["data_processing"],
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Group by (NOW ENABLED!)
        self.groupby_var = ctk.BooleanVar(value=False)
        self.groupby_config = None
        
        groupby_frame = ctk.CTkFrame(section_frame)
        groupby_frame.pack(fill="x", padx=20, pady=5)
        
        groupby_check = ctk.CTkCheckBox(
            groupby_frame,
            text=self.texts["groupby"].replace(" (Coming soon)", ""),
            variable=self.groupby_var,
            command=self._on_groupby_toggle
        )
        groupby_check.pack(side="left")
        
        self.groupby_config_btn = ctk.CTkButton(
            groupby_frame,
            text="⚙️ Configure" if self.lang_code == "en" else "⚙️ ตั้งค่า" if self.lang_code == "th" else "⚙️ 配置",
            command=self._configure_groupby,
            width=100,
            state="disabled"
        )
        self.groupby_config_btn.pack(side="left", padx=10)
        
        # Duplicate removal (disabled for now)
        self.duplicate_var = ctk.BooleanVar(value=False)
        duplicate_check = ctk.CTkCheckBox(
            section_frame,
            text=self.texts["duplicates"],
            variable=self.duplicate_var,
            state="disabled"
        )
        duplicate_check.pack(anchor="w", padx=20, pady=5)
        
        # Column selection (NOW ENABLED!)
        self.column_var = ctk.BooleanVar(value=False)
        self.column_config = None
        
        column_frame = ctk.CTkFrame(section_frame)
        column_frame.pack(fill="x", padx=20, pady=(5, 10))
        
        self.column_check = ctk.CTkCheckBox(
            column_frame,
            text=self.texts["columns"].replace(" (Coming soon)", "").replace(" (เร็วๆ นี้)", "").replace(" (即将推出)", ""),
            variable=self.column_var,
            command=self._on_column_toggle
        )
        self.column_check.pack(side="left")
        
        self.column_config_btn = ctk.CTkButton(
            column_frame,
            text="⚙️ Configure" if self.lang_code == "en" else "⚙️ ตั้งค่า" if self.lang_code == "th" else "⚙️ 配置",
            command=self._configure_columns,
            width=100,
            state="disabled"
        )
        self.column_config_btn.pack(side="left", padx=10)
    
    def _on_groupby_toggle(self):
        """Handle group by checkbox toggle"""
        if self.groupby_var.get():
            self.groupby_config_btn.configure(state="normal")
        else:
            self.groupby_config_btn.configure(state="disabled")
            self.groupby_config = None
    
    def _on_column_toggle(self):
        """Handle column selection checkbox toggle"""
        if self.column_var.get():
            self.column_config_btn.configure(state="normal")
        else:
            self.column_config_btn.configure(state="disabled")
            self.column_config = None
    
    def _update_column_checkbox_text(self):
        """Update column checkbox text to show selection count"""
        if self.column_config:
            count = len(self.column_config.selected_columns)
            if self.lang_code == "en":
                text = f"Select/reorder columns ({count} selected)"
            elif self.lang_code == "th":
                text = f"เลือก/จัดเรียงคอลัมน์ (เลือก {count} คอลัมน์)"
            else:  # cn
                text = f"选择/重新排序列 (已选择 {count} 列)"
            self.column_check.configure(text=text)
        else:
            # Reset to default text
            self.column_check.configure(
                text=self.texts["columns"].replace(" (Coming soon)", "").replace(" (เร็วๆ นี้)", "").replace(" (即将推出)", "")
            )
    
    def _configure_groupby(self):
        """Open group by configuration dialog"""
        if not self.available_columns:
            # Show error - no columns available
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Error" if self.lang_code == "en" else "ข้อผิดพลาด" if self.lang_code == "th" else "错误")
            error_dialog.geometry("350x120")
            
            msg = "Could not read columns from files.\nPlease check your Excel files." if self.lang_code == "en" else \
                  "ไม่สามารถอ่านคอลัมน์จากไฟล์ได้\nกรุณาตรวจสอบไฟล์ Excel" if self.lang_code == "th" else \
                  "无法从文件中读取列。\n请检查您的Excel文件。"
            
            ctk.CTkLabel(error_dialog, text=msg, wraplength=300).pack(pady=20)
            ctk.CTkButton(
                error_dialog, 
                text="OK" if self.lang_code == "en" else "ตกลง" if self.lang_code == "th" else "确定", 
                command=error_dialog.destroy
            ).pack()
            return
        
        from src.ui.groupby_dialog import GroupByConfigDialog
        
        dialog = GroupByConfigDialog(self, self.available_columns, self.lang_code)
        self.wait_window(dialog)
        
        config = dialog.get_result()
        if config:
            self.groupby_config = config
    
    def _configure_columns(self):
        """Open column selection configuration dialog"""
        if not self.available_columns:
            # Show error - no columns available
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Error" if self.lang_code == "en" else "ข้อผิดพลาด" if self.lang_code == "th" else "错误")
            error_dialog.geometry("350x120")
            
            msg = "Could not read columns from files.\nPlease check your Excel files." if self.lang_code == "en" else \
                  "ไม่สามารถอ่านคอลัมน์จากไฟล์ได้\nกรุณาตรวจสอบไฟล์ Excel" if self.lang_code == "th" else \
                  "无法从文件中读取列。\n请检查您的Excel文件。"
            
            ctk.CTkLabel(error_dialog, text=msg, wraplength=300).pack(pady=20)
            ctk.CTkButton(
                error_dialog, 
                text="OK" if self.lang_code == "en" else "ตกลง" if self.lang_code == "th" else "确定", 
                command=error_dialog.destroy
            ).pack()
            return
        
        from src.ui.column_selection_dialog import ColumnSelectionDialog
        from src.domain.column_metadata import ColumnMetadata
        
        # Convert available_columns (list of strings) to ColumnMetadata objects
        column_metadata_list = [
            ColumnMetadata(
                name=col,
                source_files=["merged"],  # Placeholder since we don't track individual files here
                is_from_header=True,
                data_type=None
            )
            for col in self.available_columns
        ]
        
        # Pass existing config to dialog so it can restore previous selection
        dialog = ColumnSelectionDialog(
            self, 
            column_metadata_list, 
            self.lang_code,
            existing_config=self.column_config  # Pass existing config
        )
        config = dialog.get_selection_config()
        
        if config:
            self.column_config = config
            # Update checkbox text to show selection count
            self._update_column_checkbox_text()
    
    def _on_ok(self):
        """Handle OK button click"""
        try:
            # Validate column selection if enabled
            if self.column_var.get() and not self.column_config:
                # Show error - column selection is enabled but not configured
                error_dialog = ctk.CTkToplevel(self)
                error_dialog.title(self.texts["error_title"])
                error_dialog.geometry("350x150")
                
                msg = "Please configure column selection or uncheck the option." if self.lang_code == "en" else \
                      "กรุณาตั้งค่าการเลือกคอลัมน์ หรือยกเลิกการเลือก" if self.lang_code == "th" else \
                      "请配置列选择或取消选中该选项。"
                
                ctk.CTkLabel(error_dialog, text=msg, wraplength=300).pack(pady=20)
                ctk.CTkButton(
                    error_dialog,
                    text=self.texts["ok"],
                    command=error_dialog.destroy
                ).pack(pady=10)
                return
            
            # Validate group by if enabled
            if self.groupby_var.get() and not self.groupby_config:
                # Show error - group by is enabled but not configured
                error_dialog = ctk.CTkToplevel(self)
                error_dialog.title(self.texts["error_title"])
                error_dialog.geometry("350x150")
                
                msg = "Please configure group by or uncheck the option." if self.lang_code == "en" else \
                      "กรุณาตั้งค่าการจัดกลุ่ม หรือยกเลิกการเลือก" if self.lang_code == "th" else \
                      "请配置分组或取消选中该选项。"
                
                ctk.CTkLabel(error_dialog, text=msg, wraplength=300).pack(pady=20)
                ctk.CTkButton(
                    error_dialog,
                    text=self.texts["ok"],
                    command=error_dialog.destroy
                ).pack(pady=10)
                return
            
            # Use default values for performance settings (hidden from UI)
            chunk_size = self.chunk_size_value
            max_workers = self.max_workers_value
            
            self.result = ProcessingOptions(
                enable_chunking=self.chunking_var.get(),
                chunk_size=chunk_size,
                enable_parallel=self.parallel_var.get(),
                max_workers=max_workers,
                group_by_config=self.groupby_config if self.groupby_var.get() else None,
                duplicate_removal_config=None,  # Not implemented yet
                column_selection_config=self.column_config if self.column_var.get() else None
            )
            
            self.grab_release()
            self.destroy()
            
        except ValueError as e:
            # Show error message
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title(self.texts["error_title"])
            error_dialog.geometry("300x150")
            
            ctk.CTkLabel(
                error_dialog,
                text=f"{self.texts['error_msg']}\n{str(e)}",
                wraplength=250
            ).pack(pady=20)
            
            ctk.CTkButton(
                error_dialog,
                text=self.texts["ok"],
                command=error_dialog.destroy
            ).pack(pady=10)
    
    def _on_cancel(self):
        """Handle Cancel button click"""
        self.result = None
        self.grab_release()
        self.destroy()
    
    def get_result(self) -> Optional[ProcessingOptions]:
        """
        Get the configured processing options
        
        Returns:
            ProcessingOptions if OK was clicked, None if cancelled
        """
        return self.result
