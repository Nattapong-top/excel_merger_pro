# File: src/application/interfaces.py
from abc import ABC, abstractmethod
from typing import List, Any 
# ใช้ Any ไปก่อนเพื่อเลี่ยงการ import pandas ใน Application Layer (รักษาความสะอาด)
# หรือถ้าป๋ายอมให้ App รู้จัก Pandas ได้ (เพื่อความง่าย) ก็ import pandas มาใส่ type hint ได้ครับ

from src.domain.value_objects import FilePath, SheetName

class ILogger(ABC):
    @abstractmethod
    def info(self, message: str): pass
    @abstractmethod
    def error(self, message: str): pass

class ISheetReader(ABC):
    @abstractmethod
    def get_sheet_names(self, path: FilePath) -> List[SheetName]:
        pass

    # --- เพิ่มตัวนี้ครับป๋า ---
    @abstractmethod
    def read_sheet(self, path: FilePath, sheet_name: SheetName) -> Any:
        """อ่านข้อมูลจาก Sheet ที่ระบุ ส่งกลับมาเป็น DataFrame"""
        pass