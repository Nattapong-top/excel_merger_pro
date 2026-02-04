# File: src/domain/entities.py
from typing import List
from dataclasses import dataclass, field
from src.domain.value_objects import FilePath, SheetName

@dataclass
class SourceFile:
    path: FilePath
    available_sheets: List[SheetName]
    # ใช้ field(default_factory=list) เพื่อให้ค่าเริ่มต้นเป็น list ว่าง
    selected_sheets: List[SheetName] = field(default_factory=list)

    def select_sheet(self, sheet: SheetName):
        """เลือก Sheet ที่ต้องการ (ต้องมีอยู่ใน available_sheets เท่านั้น)"""
        if sheet not in self.available_sheets:
            raise ValueError(f"Sheet '{sheet.value}' not found in file '{self.path.value}'")
        
        # ป้องกันการเลือกซ้ำ
        if sheet not in self.selected_sheets:
            self.selected_sheets.append(sheet)

    def select_all_sheets(self):
        """เลือกทุก Sheet"""
        self.selected_sheets = self.available_sheets.copy()