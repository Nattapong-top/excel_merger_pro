# File: tests/integration/test_pandas_excel_reader.py
import unittest
import pandas as pd
import os
from src.domain.value_objects import FilePath
# เราจะสร้าง Class นี้ในขั้นตอนถัดไป (ตอนนี้ยังไม่มี -> ต้อง Error)
from src.infrastructure.excel_reader import PandasSheetReader

class TestPandasSheetReader(unittest.TestCase):
    
    def setUp(self):
        """เตรียมไฟล์ Excel ของจริงขึ้นมาก่อนเทส"""
        self.test_file = "temp_test_sheets.xlsx"
        # สร้างไฟล์หลอกๆ ที่มี 2 Sheets
        df = pd.DataFrame({'A': [1, 2, 3]})
        with pd.ExcelWriter(self.test_file) as writer:
            df.to_excel(writer, sheet_name='Sales')
            df.to_excel(writer, sheet_name='HR')

    def tearDown(self):
        """ลบไฟล์ทิ้งเมื่อเทสเสร็จ"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_should_read_sheet_names_correctly(self):
        # Arrange
        reader = PandasSheetReader()
        path = FilePath(self.test_file)
        
        # Act (สั่งให้อ่าน)
        sheet_names = reader.get_sheet_names(path)
        
        # Assert (ตรวจสอบผลลัพธ์)
        # ต้องได้ List ของ SheetName กลับมา 2 อัน
        self.assertEqual(len(sheet_names), 2)
        # ค่าข้างในต้องถูกต้อง
        names = [s.value for s in sheet_names]
        self.assertIn("Sales", names)
        self.assertIn("HR", names)

if __name__ == '__main__':
    unittest.main()