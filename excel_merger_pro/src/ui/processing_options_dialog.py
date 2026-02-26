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
            "groupby": "Group by columns (Coming soon)",
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
            "groupby": "จัดกลุ่มตามคอลัมน์ (เร็วๆ นี้)",
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
            "groupby": "按列分组（即将推出）",
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
        
        # Window configuration
        self.title(self.texts["title"])
        self.geometry("600x700")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 700) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self, width=560, height=600)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text=self.texts["configure"],
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Performance section
        self._create_performance_section(main_frame)
        
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
        
        # Note
        ctk.CTkLabel(
            section_frame,
            text=self.texts["note"],
            font=("Arial", 10),
            text_color="gray"
        ).pack(anchor="w", padx=20, pady=5)
        
        # Group by (disabled for now)
        self.groupby_var = ctk.BooleanVar(value=False)
        groupby_check = ctk.CTkCheckBox(
            section_frame,
            text=self.texts["groupby"],
            variable=self.groupby_var,
            state="disabled"
        )
        groupby_check.pack(anchor="w", padx=20, pady=5)
        
        # Duplicate removal (disabled for now)
        self.duplicate_var = ctk.BooleanVar(value=False)
        duplicate_check = ctk.CTkCheckBox(
            section_frame,
            text=self.texts["duplicates"],
            variable=self.duplicate_var,
            state="disabled"
        )
        duplicate_check.pack(anchor="w", padx=20, pady=5)
        
        # Column selection (disabled for now)
        self.column_var = ctk.BooleanVar(value=False)
        column_check = ctk.CTkCheckBox(
            section_frame,
            text=self.texts["columns"],
            variable=self.column_var,
            state="disabled"
        )
        column_check.pack(anchor="w", padx=20, pady=(5, 10))
    
    def _on_ok(self):
        """Handle OK button click"""
        try:
            # Validate and build ProcessingOptions
            chunk_size = int(self.chunk_size_entry.get())
            max_workers = int(self.max_workers_entry.get())
            
            self.result = ProcessingOptions(
                enable_chunking=self.chunking_var.get(),
                chunk_size=chunk_size,
                enable_parallel=self.parallel_var.get(),
                max_workers=max_workers,
                group_by_config=None,  # Not implemented yet
                duplicate_removal_config=None,  # Not implemented yet
                column_selection_config=None  # Not implemented yet
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
