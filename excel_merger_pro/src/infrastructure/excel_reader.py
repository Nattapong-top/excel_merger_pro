# File: src/infrastructure/excel_reader.py
import pandas as pd
from typing import List
from src.application.interfaces import ISheetReader
from src.domain.value_objects import FilePath, SheetName

class PandasSheetReader(ISheetReader):
    def get_sheet_names(self, path: FilePath) -> List[SheetName]:
        try:
            # แก้ตรงนี้: ใส่ with เพื่อให้มัน Auto-Close ไฟล์ทันทีที่อ่านจบ
            with pd.ExcelFile(path.value) as excel_file:
                raw_names = excel_file.sheet_names
                
                # จังหวะนี้ไฟล์ยังเปิดอยู่ อ่านค่าออกมา
                return [SheetName(name) for name in raw_names]
            # พอหลุดบรรทัดนี้ ไฟล์จะถูกปิดทันที! (Windows จะไม่ด่าแล้ว)
            
        except Exception as e:
            raise ValueError(f"Cannot read file '{path.value}': {e}")