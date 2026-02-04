from typing import List
from dataclasses import dataclass
from src.domain.value_objects import FilePath, SheetName

class SourceFile:
    def __init__(self, path: FilePath, available_sheets: List[SheetName]):
        self.path = path
        self.available_sheets = available_sheets
        self.selected_sheets = [] # Default คือยังไม่เลือก

    def select_sheet(self, sheet: SheetName):
        self.selected_sheets.append(sheet)