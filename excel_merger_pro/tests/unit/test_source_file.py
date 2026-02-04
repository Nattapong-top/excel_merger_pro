# File: tests/unit/test_source_file.py
import unittest
from src.domain.entities import SourceFile
from src.domain.value_objects import FilePath, SheetName

class TestSourceFile(unittest.TestCase):
    
    def test_create_valid_source_file(self):
        """ทดสอบว่าสร้าง Object ได้ถูกต้อง"""
        path = FilePath("data.xlsx")
        sheets = [SheetName("Sheet1"), SheetName("Sheet2")]
        
        file = SourceFile(path, sheets)
        
        self.assertEqual(file.path.value, "data.xlsx")
        self.assertEqual(len(file.available_sheets), 2)
        # เริ่มต้นต้องยังไม่มี Sheet ถูกเลือก
        self.assertEqual(len(file.selected_sheets), 0)

    def test_select_specific_sheet(self):
        """ทดสอบการเลือก Sheet"""
        path = FilePath("data.xlsx")
        sheets = [SheetName("A"), SheetName("B"), SheetName("C")]
        file = SourceFile(path, sheets)
        
        # Act: เลือก Sheet A และ C
        file.select_sheet(SheetName("A"))
        file.select_sheet(SheetName("C"))
        
        # Assert: ต้องมี 2 sheet ที่ถูกเลือก
        self.assertEqual(len(file.selected_sheets), 2)
        self.assertIn(SheetName("A"), file.selected_sheets)
        self.assertNotIn(SheetName("B"), file.selected_sheets)

    def test_cannot_select_invalid_sheet(self):
        """ทดสอบว่าถ้าเลือก Sheet ที่ไม่มีจริง ต้อง Error"""
        path = FilePath("data.xlsx")
        sheets = [SheetName("Main")]
        file = SourceFile(path, sheets)
        
        # Act & Assert: เลือก 'Ghost' ที่ไม่มีจริง ต้อง Raise Error
        with self.assertRaises(ValueError):
            file.select_sheet(SheetName("Ghost"))

if __name__ == '__main__':
    unittest.main()