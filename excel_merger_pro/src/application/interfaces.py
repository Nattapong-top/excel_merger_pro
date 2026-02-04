# File: src/application/interfaces.py
from abc import ABC, abstractmethod
from typing import List
# อย่าลืม import value objects ที่เราทำไว้
from src.domain.value_objects import FilePath, SheetName

class ILogger(ABC):
    @abstractmethod
    def info(self, message: str):
        pass

    @abstractmethod
    def error(self, message: str):
        pass

# --- เพิ่มตัวนี้ครับป๋า ---
class ISheetReader(ABC):
    @abstractmethod
    def get_sheet_names(self, path: FilePath) -> List[SheetName]:
        """อ่านรายชื่อ Sheet จากไฟล์"""
        pass