# File: src/ui/groupby_dialog.py
"""
Dialog for configuring Group By options

Allows users to:
- Select columns to group by
- Choose aggregation functions for each column
"""

import customtkinter as ctk
from typing import Optional, List, Dict
from src.domain.processing_options import GroupByConfig


class GroupByConfigDialog(ctk.CTkToplevel):
    """Dialog for configuring group by options"""
    
    TEXTS = {
        "en": {
            "title": "Group By Configuration",
            "select_group": "Select columns to group by:",
            "select_agg": "Select aggregation functions:",
            "column": "Column",
            "function": "Function",
            "ok": "OK",
            "cancel": "Cancel",
            "error": "Please select at least one group column and one aggregation"
        },
        "th": {
            "title": "ตั้งค่าการจัดกลุ่ม",
            "select_group": "เลือกคอลัมน์ที่จะจัดกลุ่ม:",
            "select_agg": "เลือกฟังก์ชันการรวมข้อมูล:",
            "column": "คอลัมน์",
            "function": "ฟังก์ชัน",
            "ok": "ตกลง",
            "cancel": "ยกเลิก",
            "error": "กรุณาเลือกคอลัมน์จัดกลุ่มและฟังก์ชันรวมข้อมูลอย่างน้อย 1 รายการ"
        },
        "cn": {
            "title": "分组配置",
            "select_group": "选择分组列:",
            "select_agg": "选择聚合函数:",
            "column": "列",
            "function": "函数",
            "ok": "确定",
            "cancel": "取消",
            "error": "请至少选择一个分组列和一个聚合函数"
        }
    }
    
    AGG_FUNCTIONS = ["sum", "count", "mean", "min", "max", "first", "last"]
    
    def __init__(self, parent, available_columns: List[str], lang_code: str = "en"):
        super().__init__(parent)
        
        self.available_columns = available_columns
        self.lang_code = lang_code
        self.texts = self.TEXTS.get(lang_code, self.TEXTS["en"])
        self.result: Optional[GroupByConfig] = None
        
        # Window configuration
        self.title(self.texts["title"])
        self.geometry("550x650")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 600) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Group columns section
        ctk.CTkLabel(
            main_frame,
            text=self.texts["select_group"],
            font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Scrollable frame for group columns
        group_frame = ctk.CTkScrollableFrame(main_frame, height=150)
        group_frame.pack(fill="x", pady=(0, 20))
        
        self.group_vars = {}
        for col in self.available_columns:
            var = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(
                group_frame,
                text=col,
                variable=var
            ).pack(anchor="w", padx=10, pady=2)
            self.group_vars[col] = var
        
        # Aggregation section
        ctk.CTkLabel(
            main_frame,
            text=self.texts["select_agg"],
            font=("Arial", 12, "bold")
        ).pack(anchor="w", pady=(0, 10))
        
        # Scrollable frame for aggregations
        agg_frame = ctk.CTkScrollableFrame(main_frame, height=250)
        agg_frame.pack(fill="x", pady=(0, 20))
        
        self.agg_menus = {}
        for col in self.available_columns:
            row_frame = ctk.CTkFrame(agg_frame)
            row_frame.pack(fill="x", padx=10, pady=5)
            
            ctk.CTkLabel(
                row_frame,
                text=f"{col}:",
                width=150
            ).pack(side="left", padx=5)
            
            menu = ctk.CTkOptionMenu(
                row_frame,
                values=["None"] + self.AGG_FUNCTIONS,
                width=120
            )
            menu.set("None")
            menu.pack(side="left", padx=5)
            self.agg_menus[col] = menu
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(
            button_frame,
            text=self.texts["cancel"],
            command=self._on_cancel,
            width=150,
            height=40,
            font=("Arial", 13),
            fg_color="gray",
            hover_color="darkgray"
        ).pack(side="right", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text=self.texts["ok"],
            command=self._on_ok,
            width=150,
            height=40,
            font=("Arial", 13, "bold"),
            fg_color="#2CC985",
            hover_color="#28B574"
        ).pack(side="right", padx=5)
    
    def _on_ok(self):
        """Handle OK button"""
        # Get selected group columns
        group_cols = [col for col, var in self.group_vars.items() if var.get()]
        
        # Get aggregations
        aggregations = {}
        for col, menu in self.agg_menus.items():
            func = menu.get()
            if func != "None":
                aggregations[col] = func
        
        # Validate
        if not group_cols or not aggregations:
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Error")
            error_dialog.geometry("300x100")
            
            ctk.CTkLabel(
                error_dialog,
                text=self.texts["error"],
                wraplength=250
            ).pack(pady=20)
            
            ctk.CTkButton(
                error_dialog,
                text=self.texts["ok"],
                command=error_dialog.destroy
            ).pack()
            return
        
        # Create config
        try:
            self.result = GroupByConfig(
                group_columns=tuple(group_cols),
                aggregations=aggregations
            )
            self.grab_release()
            self.destroy()
        except ValueError as e:
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Error")
            error_dialog.geometry("300x100")
            
            ctk.CTkLabel(
                error_dialog,
                text=str(e),
                wraplength=250
            ).pack(pady=20)
            
            ctk.CTkButton(
                error_dialog,
                text=self.texts["ok"],
                command=error_dialog.destroy
            ).pack()
    
    def _on_cancel(self):
        """Handle Cancel button"""
        self.result = None
        self.grab_release()
        self.destroy()
    
    def get_result(self) -> Optional[GroupByConfig]:
        """Get the configured group by config"""
        return self.result
