# File: tests/integration/test_chunked_reader.py
"""
Integration tests for ChunkedSheetReader

These tests use real Excel files to verify chunk reading functionality.
"""

import pytest
import pandas as pd
import os
from src.infrastructure.excel_reader import PandasSheetReader
from src.domain.value_objects import FilePath, SheetName


@pytest.fixture
def temp_excel_file(tmp_path):
    """Create a temporary Excel file for testing"""
    file_path = tmp_path / "test_data.xlsx"
    
    # สร้างข้อมูลทดสอบ 1,000 แถว
    data = {
        'ID': range(1, 1001),
        'Name': [f'Person_{i}' for i in range(1, 1001)],
        'Value': [i * 10 for i in range(1, 1001)]
    }
    df = pd.DataFrame(data)
    df.to_excel(file_path, sheet_name='TestSheet', index=False)
    
    return str(file_path)


@pytest.fixture
def large_excel_file(tmp_path):
    """Create a larger Excel file for chunk testing"""
    file_path = tmp_path / "large_data.xlsx"
    
    # สร้างข้อมูลทดสอบ 25,000 แถว
    data = {
        'ID': range(1, 25001),
        'Category': [f'Cat_{i % 10}' for i in range(1, 25001)],
        'Amount': [i * 1.5 for i in range(1, 25001)]
    }
    df = pd.DataFrame(data)
    df.to_excel(file_path, sheet_name='LargeSheet', index=False)
    
    return str(file_path)


class TestChunkedReading:
    """Test chunk-based reading functionality"""
    
    def test_read_sheet_chunked_basic(self, temp_excel_file):
        """Should read file in chunks"""
        reader = PandasSheetReader()
        path = FilePath(temp_excel_file)
        sheet = SheetName('TestSheet')
        
        chunks = list(reader.read_sheet_chunked(path, sheet, chunk_size=250))
        
        # 1,000 แถว / 250 = 4 chunks
        assert len(chunks) == 4
        
        # แต่ละ chunk ควรมี 250 แถว (ยกเว้น chunk สุดท้ายอาจน้อยกว่า)
        assert len(chunks[0]) == 250
        assert len(chunks[1]) == 250
        assert len(chunks[2]) == 250
        assert len(chunks[3]) == 250
    
    def test_chunked_equals_full_read(self, temp_excel_file):
        """Chunked reading should produce same result as full read"""
        reader = PandasSheetReader()
        path = FilePath(temp_excel_file)
        sheet = SheetName('TestSheet')
        
        # อ่านแบบปกติ
        df_full = reader.read_sheet(path, sheet)
        
        # อ่านแบบ chunk แล้วรวมกัน
        chunks = list(reader.read_sheet_chunked(path, sheet, chunk_size=250))
        df_chunked = pd.concat(chunks, ignore_index=True)
        
        # ผลลัพธ์ต้องเหมือนกัน
        pd.testing.assert_frame_equal(df_full, df_chunked)
    
    def test_chunk_size_affects_number_of_chunks(self, temp_excel_file):
        """Different chunk sizes should produce different number of chunks"""
        reader = PandasSheetReader()
        path = FilePath(temp_excel_file)
        sheet = SheetName('TestSheet')
        
        # Chunk size 100 → 10 chunks
        chunks_100 = list(reader.read_sheet_chunked(path, sheet, chunk_size=100))
        assert len(chunks_100) == 10
        
        # Chunk size 500 → 2 chunks
        chunks_500 = list(reader.read_sheet_chunked(path, sheet, chunk_size=500))
        assert len(chunks_500) == 2
        
        # Chunk size 1000 → 1 chunk
        chunks_1000 = list(reader.read_sheet_chunked(path, sheet, chunk_size=1000))
        assert len(chunks_1000) == 1
    
    def test_large_file_chunked_reading(self, large_excel_file):
        """Should handle large files efficiently"""
        reader = PandasSheetReader()
        path = FilePath(large_excel_file)
        sheet = SheetName('LargeSheet')
        
        # อ่านทีละ 5,000 แถว
        chunks = list(reader.read_sheet_chunked(path, sheet, chunk_size=5000))
        
        # 25,000 แถว / 5,000 = 5 chunks
        assert len(chunks) == 5
        
        # รวมข้อมูลทั้งหมด
        df_combined = pd.concat(chunks, ignore_index=True)
        
        # ตรวจสอบจำนวนแถวรวม
        assert len(df_combined) == 25000
        
        # ตรวจสอบว่าข้อมูลครบถ้วน (แปลง column เป็น int ก่อนหา min/max)
        id_values = df_combined['ID'].astype(int)
        assert id_values.min() == 1
        assert id_values.max() == 25000
    
    def test_chunk_preserves_data_types(self, temp_excel_file):
        """Chunked reading should preserve data types"""
        reader = PandasSheetReader()
        path = FilePath(temp_excel_file)
        sheet = SheetName('TestSheet')
        
        chunks = list(reader.read_sheet_chunked(path, sheet, chunk_size=250))
        
        # ทุก chunk ควรมี columns เหมือนกัน
        expected_columns = ['ID', 'Name', 'Value']
        for chunk in chunks:
            assert list(chunk.columns) == expected_columns
            
            # astype(str) ทำให้ทุก column เป็น string dtype
            # pandas อาจใช้ StringDtype หรือ object ขึ้นอยู่กับเวอร์ชัน
            assert chunk['ID'].dtype in ['object', 'string', pd.StringDtype()]
            assert chunk['Name'].dtype in ['object', 'string', pd.StringDtype()]
            assert chunk['Value'].dtype in ['object', 'string', pd.StringDtype()]


class TestRowCountEstimation:
    """Test row count estimation functionality"""
    
    def test_estimate_row_count_basic(self, temp_excel_file):
        """Should estimate row count correctly"""
        reader = PandasSheetReader()
        path = FilePath(temp_excel_file)
        sheet = SheetName('TestSheet')
        
        count = reader.estimate_row_count(path, sheet)
        
        # 1,000 แถวข้อมูล + 1 แถว header = 1,001
        assert count == 1001
    
    def test_estimate_row_count_large_file(self, large_excel_file):
        """Should estimate row count for large files"""
        reader = PandasSheetReader()
        path = FilePath(large_excel_file)
        sheet = SheetName('LargeSheet')
        
        count = reader.estimate_row_count(path, sheet)
        
        # 25,000 แถวข้อมูล + 1 แถว header = 25,001
        assert count == 25001
    
    def test_estimate_is_fast(self, large_excel_file):
        """Estimation should be much faster than full read"""
        import time
        
        reader = PandasSheetReader()
        path = FilePath(large_excel_file)
        sheet = SheetName('LargeSheet')
        
        # วัดเวลา estimate
        start = time.time()
        count = reader.estimate_row_count(path, sheet)
        estimate_time = time.time() - start
        
        # วัดเวลาอ่านทั้งหมด
        start = time.time()
        df = reader.read_sheet(path, sheet)
        full_read_time = time.time() - start
        
        # Estimate ควรเร็วกว่าอ่านทั้งหมดอย่างน้อย 5 เท่า
        assert estimate_time < full_read_time / 5
        
        # ตรวจสอบว่า estimate ถูกต้อง
        assert count == len(df) + 1  # +1 for header
    
    def test_estimate_invalid_sheet_returns_zero(self, temp_excel_file):
        """Should return 0 for invalid sheet instead of error"""
        reader = PandasSheetReader()
        path = FilePath(temp_excel_file)
        sheet = SheetName('NonExistentSheet')
        
        # ไม่ควร raise error แต่ return 0
        count = reader.estimate_row_count(path, sheet)
        assert count == 0


class TestChunkedReadingEdgeCases:
    """Test edge cases for chunked reading"""
    
    def test_chunk_size_larger_than_file(self, temp_excel_file):
        """Should handle chunk size larger than file"""
        reader = PandasSheetReader()
        path = FilePath(temp_excel_file)
        sheet = SheetName('TestSheet')
        
        # Chunk size 10,000 แต่ไฟล์มีแค่ 1,000 แถว
        chunks = list(reader.read_sheet_chunked(path, sheet, chunk_size=10000))
        
        # ควรได้ 1 chunk ที่มี 1,000 แถว
        assert len(chunks) == 1
        assert len(chunks[0]) == 1000
    
    def test_chunk_size_one(self, temp_excel_file):
        """Should handle chunk size of 1"""
        reader = PandasSheetReader()
        path = FilePath(temp_excel_file)
        sheet = SheetName('TestSheet')
        
        # อ่านทีละ 1 แถว
        chunks = list(reader.read_sheet_chunked(path, sheet, chunk_size=1))
        
        # ควรได้ 1,000 chunks
        assert len(chunks) == 1000
        
        # แต่ละ chunk มี 1 แถว
        for chunk in chunks:
            assert len(chunk) == 1
    
    def test_invalid_file_raises_error(self):
        """Should raise error for invalid file"""
        reader = PandasSheetReader()
        path = FilePath("nonexistent_file.xlsx")
        sheet = SheetName('Sheet1')
        
        with pytest.raises(ValueError, match="Error reading sheet"):
            list(reader.read_sheet_chunked(path, sheet, chunk_size=100))
    
    def test_empty_sheet_handling(self, tmp_path):
        """Should handle empty sheets"""
        file_path = tmp_path / "empty.xlsx"
        
        # สร้างไฟล์ที่มีแค่ header
        df = pd.DataFrame(columns=['A', 'B', 'C'])
        df.to_excel(file_path, sheet_name='EmptySheet', index=False)
        
        reader = PandasSheetReader()
        path = FilePath(str(file_path))
        sheet = SheetName('EmptySheet')
        
        chunks = list(reader.read_sheet_chunked(path, sheet, chunk_size=100))
        
        # ไม่มีข้อมูล จะไม่มี chunk เลย (เพราะมีแค่ header)
        assert len(chunks) == 0


class TestMemoryEfficiency:
    """Test memory efficiency of chunked reading"""
    
    def test_chunked_uses_less_memory(self, large_excel_file):
        """Chunked reading should use less memory than full read"""
        import sys
        
        reader = PandasSheetReader()
        path = FilePath(large_excel_file)
        sheet = SheetName('LargeSheet')
        
        # อ่านแบบ chunk และเก็บแค่ chunk แรก
        chunks_iter = reader.read_sheet_chunked(path, sheet, chunk_size=5000)
        first_chunk = next(chunks_iter)
        
        # Chunk แรกควรเล็กกว่าไฟล์ทั้งหมดมาก
        chunk_size = sys.getsizeof(first_chunk)
        
        # อ่านทั้งหมด
        df_full = reader.read_sheet(path, sheet)
        full_size = sys.getsizeof(df_full)
        
        # Chunk ควรเล็กกว่าอย่างน้อย 3 เท่า (เพราะเรามี 5 chunks)
        assert chunk_size < full_size / 3
