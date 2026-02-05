# File: src/infrastructure/excel_reader.py
from typing import List, Any
from src.application.interfaces import ISheetReader
from src.domain.value_objects import FilePath, SheetName

class PandasSheetReader(ISheetReader):
    def get_sheet_names(self, path: FilePath) -> List[SheetName]:
        import pandas as pd
        try:
            with pd.ExcelFile(path.value) as excel_file:
                return [SheetName(name) for name in excel_file.sheet_names]
        except Exception as e:
            raise ValueError(f"Cannot read file '{path.value}': {e}")

    # --- เพิ่มส่วนนี้ครับป๋า ---
    def read_sheet(self, path: FilePath, sheet_name: SheetName) -> Any:
        import pandas as pd
        try:
            # อ่านข้อมูลจาก Sheet ที่ระบุ
            # dtype=str เพื่อป้องกัน Excel เปลี่ยนเบอร์โทร 081 เป็นตัวเลข 81
            df = pd.read_excel(path.value, sheet_name=sheet_name.value, dtype=str)
            return df
        except Exception as e:
            raise ValueError(f"Error reading sheet '{sheet_name.value}': {e}")