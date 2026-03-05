import unittest
from unittest.mock import MagicMock
import pandas as pd
from src.domain.entities import SourceFile
from src.domain.value_objects import FilePath, SheetName
from src.application.services import MergeService

class TestMergeLogic(unittest.TestCase):
    
    def test_merge_only_selected_sheets(self):
        """
        Scenario: มีไฟล์ที่มี 2 Sheet (A, B) แต่เลือกแค่ A
        Expectation: ผลลัพธ์ต้องมีแค่ข้อมูลจาก A เท่านั้น
        """
        # 1. Prepare Mock (ตัวแสดงแทน)
        mock_logger = MagicMock()
        mock_reader = MagicMock()
        
        # สมมติข้อมูลใน Excel: Sheet A มี data=10, Sheet B มี data=99
        df_a = pd.DataFrame({'val': [10]})
        df_b = pd.DataFrame({'val': [99]})
        
        # สอน Mock: ถ้าขออ่าน A ให้เอา df_a ไป, ถ้าขอ B ให้เอา df_b ไป
        def side_effect(path, sheet, usecols=None):
            if sheet.value == "SheetA": return df_a
            if sheet.value == "SheetB": return df_b
            return pd.DataFrame()
        
        mock_reader.read_sheet.side_effect = side_effect
        
        # 2. Setup Data
        path = FilePath("dummy.xlsx")
        file = SourceFile(path, [SheetName("SheetA"), SheetName("SheetB")])
        
        # *** Key Point: เลือกแค่ Sheet A ***
        file.select_sheet(SheetName("SheetA"))
        
        # 3. Execute
        service = MergeService(logger=mock_logger, reader=mock_reader)
        
        # Create default options
        from src.domain.processing_options import ProcessingOptions
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=False,
            max_workers=1
        )
        
        result_df = service.merge([file], options)
        
        # 4. Assert
        self.assertEqual(len(result_df), 1, "ต้องมีข้อมูล 1 แถว")
        self.assertEqual(result_df.iloc[0]['val'], 10, "ข้อมูลต้องมาจาก Sheet A (ค่า 10)")
        # ต้องไม่เผลอไปเรียกอ่าน Sheet B
        # (ตรวจสอบว่า mock_reader ถูกเรียกอ่าน SheetA เท่านั้น)
        calls = mock_reader.read_sheet.call_args_list
        sheet_names_called = [args[1].value for args, _ in calls]
        
        self.assertIn("SheetA", sheet_names_called)
        self.assertNotIn("SheetB", sheet_names_called)

if __name__ == '__main__':
    unittest.main()