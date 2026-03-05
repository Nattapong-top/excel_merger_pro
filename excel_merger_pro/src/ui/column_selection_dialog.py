# File: src/ui/column_selection_dialog.py
"""
Column Selection Dialog for Excel Merger Pro

Allows users to:
- View all available columns from source files
- Select/deselect columns for merge
- Reorder columns via drag-and-drop (up/down buttons)
- Save and load column selection configurations
"""

import customtkinter as ctk
from typing import List, Optional
from src.domain.column_metadata import ColumnMetadata
from src.domain.processing_options import ColumnSelectionConfig
from src.application.services.column_selection_service import ColumnSelectionService
from src.infrastructure.repositories.configuration_repository import JsonConfigurationRepository
from pathlib import Path


class ColumnSelectionDialog(ctk.CTkToplevel):
    """
    Dialog for selecting and ordering columns for merge operation
    
    Features:
    - Display all available columns with checkboxes
    - Select All / Deselect All buttons
    - Reorder columns with Up/Down buttons
    - Save/Load configuration
    """
    
    # Language texts
    TEXTS = {
        "en": {
            "title": "Select Columns",
            "header": "Select Columns to Merge",
            "found": "Found {count} unique columns",
            "select_all": "Select All",
            "deselect_all": "Deselect All",
            "reorder": "Reorder",
            "up": "↑ Up",
            "down": "↓ Down",
            "reorder_hint": "Select a column and use Up/Down to change order",
            "confirm": "Confirm Selection",
            "error": "Error",
            "error_no_selection": "Please select at least one column",
            "file_count": "({count} file(s))"
        },
        "th": {
            "title": "เลือกคอลัมน์",
            "header": "เลือกคอลัมน์ที่ต้องการรวม",
            "found": "พบ {count} คอลัมน์",
            "select_all": "เลือกทั้งหมด",
            "deselect_all": "ยกเลิกทั้งหมด",
            "reorder": "เรียงลำดับ",
            "up": "↑ ขึ้น",
            "down": "↓ ลง",
            "reorder_hint": "เลือกคอลัมน์แล้วใช้ปุ่มขึ้น/ลงเพื่อเปลี่ยนลำดับ",
            "confirm": "ยืนยันการเลือก",
            "error": "ข้อผิดพลาด",
            "error_no_selection": "กรุณาเลือกอย่างน้อย 1 คอลัมน์",
            "file_count": "({count} ไฟล์)"
        },
        "cn": {
            "title": "选择列",
            "header": "选择要合并的列",
            "found": "找到 {count} 个唯一列",
            "select_all": "全选",
            "deselect_all": "取消全选",
            "reorder": "重新排序",
            "up": "↑ 上移",
            "down": "↓ 下移",
            "reorder_hint": "选择列并使用上/下按钮更改顺序",
            "confirm": "确认选择",
            "error": "错误",
            "error_no_selection": "请至少选择一列",
            "file_count": "({count} 个文件)"
        }
    }
    
    def __init__(
        self,
        parent,
        available_columns: List[ColumnMetadata],
        lang_code: str = "en",
        existing_config: Optional[ColumnSelectionConfig] = None
    ):
        """
        Initialize dialog with available columns
        
        Args:
            parent: Parent window
            available_columns: List of columns discovered from source files
            lang_code: Language code (en, th, cn)
            existing_config: Previously selected configuration to restore
        """
        super().__init__(parent)
        
        self.lang_code = lang_code
        self.texts = self.TEXTS.get(lang_code, self.TEXTS["en"])
        self.available_columns = available_columns
        self.existing_config = existing_config  # Store existing config
        self.selected_config: Optional[ColumnSelectionConfig] = None
        self.column_checkboxes = []  # List of (checkbox, column_name)
        
        # Initialize services (not used anymore but kept for compatibility)
        config_dir = Path.home() / ".excel_merger_pro" / "column_configs"
        self.config_repository = JsonConfigurationRepository(config_dir)
        self.selection_service = ColumnSelectionService(
            repository=self.config_repository,
            logger=None  # Will use print for now
        )
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface"""
        self.title(self.texts["title"])
        self.geometry("500x650")  # Reduced height since we removed config buttons
        self.grab_set()
        self.focus_force()
        
        # Header
        header_label = ctk.CTkLabel(
            self,
            text=self.texts["header"],
            font=("Arial", 16, "bold")
        )
        header_label.pack(pady=(15, 5))
        
        hint_label = ctk.CTkLabel(
            self,
            text=self.texts["found"].format(count=len(self.available_columns))
        )
        hint_label.pack(pady=5)
        
        # Action buttons frame
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=10, fill="x", padx=20)
        
        btn_select_all = ctk.CTkButton(
            action_frame,
            text=self.texts["select_all"],
            width=100,
            height=30,
            fg_color="#3B8ED0",
            command=self._select_all
        )
        btn_select_all.pack(side="left", padx=5, expand=True)
        
        btn_deselect_all = ctk.CTkButton(
            action_frame,
            text=self.texts["deselect_all"],
            width=100,
            height=30,
            fg_color="gray",
            command=self._deselect_all
        )
        btn_deselect_all.pack(side="right", padx=5, expand=True)
        
        # Main content frame with scrollable list and reorder buttons
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Scrollable column list
        self.scroll_frame = ctk.CTkScrollableFrame(
            content_frame,
            width=350,
            height=350
        )
        self.scroll_frame.pack(side="left", fill="both", expand=True)
        
        # Reorder buttons
        reorder_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=80)
        reorder_frame.pack(side="right", fill="y", padx=(10, 0))
        
        ctk.CTkLabel(
            reorder_frame, 
            text=self.texts["reorder"], 
            font=("Arial", 12, "bold")
        ).pack(pady=(0, 5))
        
        # Hint text
        ctk.CTkLabel(
            reorder_frame,
            text=self.texts["reorder_hint"],
            font=("Arial", 9),
            text_color="gray",
            wraplength=70
        ).pack(pady=(0, 10))
        
        btn_move_up = ctk.CTkButton(
            reorder_frame,
            text=self.texts["up"],
            width=70,
            height=35,
            command=self._move_up
        )
        btn_move_up.pack(pady=5)
        
        btn_move_down = ctk.CTkButton(
            reorder_frame,
            text=self.texts["down"],
            width=70,
            height=35,
            command=self._move_down
        )
        btn_move_down.pack(pady=5)
        
        # Create checkboxes for each column
        self._create_column_checkboxes()
        
        # Confirm button (removed Save/Load config buttons)
        btn_confirm = ctk.CTkButton(
            self,
            text=self.texts["confirm"],
            command=self._on_confirm,
            height=45,
            font=("Arial", 15, "bold"),
            fg_color="#2CC985"
        )
        btn_confirm.pack(pady=20, padx=20, fill="x")
    
    def _create_column_checkboxes(self):
        """Create checkboxes for all available columns"""
        self.column_checkboxes = []
        
        # If we have existing config, use it to determine order and selection
        if self.existing_config:
            # Create ordered list based on existing config
            ordered_columns = []
            
            # First, add columns from existing config in their order
            for col_name in self.existing_config.column_order:
                col_metadata = next(
                    (c for c in self.available_columns if c.name == col_name),
                    None
                )
                if col_metadata:
                    ordered_columns.append(col_metadata)
            
            # Then add any new columns that weren't in the config
            for col_metadata in self.available_columns:
                if col_metadata.name not in self.existing_config.column_order:
                    ordered_columns.append(col_metadata)
            
            columns_to_display = ordered_columns
        else:
            columns_to_display = self.available_columns
        
        for col_metadata in columns_to_display:
            # Create frame for each column
            col_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            col_frame.pack(fill="x", pady=3, padx=5)
            
            # Determine if this column should be selected by default
            if self.existing_config:
                is_selected = col_metadata.name in self.existing_config.selected_columns
            else:
                is_selected = True  # Select all by default if no existing config
            
            # Checkbox
            var = ctk.BooleanVar(value=is_selected)
            chk = ctk.CTkCheckBox(
                col_frame,
                text=col_metadata.name,
                variable=var,
                font=("Arial", 12)
            )
            chk.pack(side="left", fill="x", expand=True)
            
            # Source file info (small text)
            if col_metadata.source_files:
                source_info = self.texts["file_count"].format(count=len(col_metadata.source_files))
                info_label = ctk.CTkLabel(
                    col_frame,
                    text=source_info,
                    font=("Arial", 9),
                    text_color="gray"
                )
                info_label.pack(side="right", padx=5)
            
            self.column_checkboxes.append((chk, col_metadata.name, var))
    
    def _select_all(self):
        """Select all columns"""
        for chk, _, var in self.column_checkboxes:
            var.set(True)
    
    def _deselect_all(self):
        """Deselect all columns"""
        for chk, _, var in self.column_checkboxes:
            var.set(False)
    
    def _move_up(self):
        """Move selected column up in the list"""
        # Find first selected checkbox
        for i, (chk, col_name, var) in enumerate(self.column_checkboxes):
            if chk.cget("state") == "normal" and i > 0:
                # Check if this checkbox has focus or is being hovered
                # For simplicity, move the first checked item
                if var.get():
                    # Swap with previous
                    self.column_checkboxes[i], self.column_checkboxes[i-1] = \
                        self.column_checkboxes[i-1], self.column_checkboxes[i]
                    self._refresh_column_list()
                    break
    
    def _move_down(self):
        """Move selected column down in the list"""
        # Find first selected checkbox
        for i, (chk, col_name, var) in enumerate(self.column_checkboxes):
            if chk.cget("state") == "normal" and i < len(self.column_checkboxes) - 1:
                if var.get():
                    # Swap with next
                    self.column_checkboxes[i], self.column_checkboxes[i+1] = \
                        self.column_checkboxes[i+1], self.column_checkboxes[i]
                    self._refresh_column_list()
                    break
    
    def _refresh_column_list(self):
        """Refresh the column list display after reordering"""
        # Clear current display
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # Recreate checkboxes in new order
        new_checkboxes = []
        for chk, col_name, var in self.column_checkboxes:
            # Find original metadata
            col_metadata = next(
                (c for c in self.available_columns if c.name == col_name),
                None
            )
            
            if col_metadata:
                # Create frame for each column
                col_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
                col_frame.pack(fill="x", pady=3, padx=5)
                
                # Checkbox
                new_chk = ctk.CTkCheckBox(
                    col_frame,
                    text=col_metadata.name,
                    variable=var,
                    font=("Arial", 12)
                )
                new_chk.pack(side="left", fill="x", expand=True)
                
                # Source file info
                if col_metadata.source_files:
                    source_info = self.texts["file_count"].format(count=len(col_metadata.source_files))
                    info_label = ctk.CTkLabel(
                        col_frame,
                        text=source_info,
                        font=("Arial", 9),
                        text_color="gray"
                    )
                    info_label.pack(side="right", padx=5)
                
                new_checkboxes.append((new_chk, col_name, var))
        
        self.column_checkboxes = new_checkboxes
    
    def _on_confirm(self):
        """Confirm selection and close dialog"""
        selected_columns = []
        column_order = []
        
        for chk, col_name, var in self.column_checkboxes:
            column_order.append(col_name)
            if var.get():
                selected_columns.append(col_name)
        
        if not selected_columns:
            self._show_message(self.texts["error"], self.texts["error_no_selection"])
            return
        
        try:
            self.selected_config = ColumnSelectionConfig(
                selected_columns=tuple(selected_columns),
                column_order=tuple(selected_columns)  # Only include selected columns in order
            )
            self.destroy()
        except ValueError as e:
            self._show_message(self.texts["error"], str(e))
    
    def _show_message(self, title: str, message: str):
        """Show a message dialog"""
        msg_dialog = ctk.CTkToplevel(self)
        msg_dialog.title(title)
        msg_dialog.geometry("300x150")
        msg_dialog.grab_set()
        
        label = ctk.CTkLabel(msg_dialog, text=message, wraplength=250)
        label.pack(pady=20, padx=20)
        
        btn_ok = ctk.CTkButton(msg_dialog, text="OK", command=msg_dialog.destroy)
        btn_ok.pack(pady=10)
    
    def get_selection_config(self) -> Optional[ColumnSelectionConfig]:
        """
        Get the column selection configuration from user input
        
        Returns:
            ColumnSelectionConfig if user confirmed, None if cancelled
        """
        self.wait_window()
        return self.selected_config
