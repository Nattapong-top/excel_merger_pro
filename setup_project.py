import os
import textwrap

def create_file(path, content):
    """ฟังก์ชันช่วยสร้างไฟล์และโฟลเดอร์"""
    # สร้างโฟลเดอร์ถ้ายังไม่มี
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    # เขียนไฟล์ (ลบ Indent ออกเพื่อให้โค้ดสวย)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(textwrap.dedent(content).strip())
    print(f"✅ Created: {path}")

# ==========================================
# 1. Domain Layer (ไข่แดง - Logic ล้วนๆ)
# ==========================================

# Value Objects
create_file("excel_merger_pro/src/domain/value_objects.py", """
from dataclasses import dataclass

@dataclass(frozen=True)
class FilePath:
    value: str

@dataclass(frozen=True)
class SheetName:
    value: str
""")

# Entities
create_file("excel_merger_pro/src/domain/entities.py", """
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
""")

# ==========================================
# 2. Application Layer (ตัวกลาง - กำหนด Interface)
# ==========================================

# Interfaces (สัญญาจ้างงาน)
create_file("excel_merger_pro/src/application/interfaces.py", """
from abc import ABC, abstractmethod

class ILogger(ABC):
    @abstractmethod
    def info(self, message: str):
        pass

    @abstractmethod
    def error(self, message: str):
        pass
""")

# Services (Logic การทำงาน)
# *เริ่มแบบว่างๆ ไว้ก่อน เพื่อให้ Test พัง (Red Phase)*
create_file("excel_merger_pro/src/application/services.py", """
from typing import List
from src.application.interfaces import ILogger
from src.domain.entities import SourceFile

class MergeService:
    def __init__(self, logger: ILogger):
        self.logger = logger
    
    def merge(self, files: List[SourceFile]):
        # TODO: Implement Logic here
        # self.logger.info("Starting merge process")
        pass
""")

# ==========================================
# 3. Infrastructure Layer (คนงาน)
# ==========================================

# ตัวอย่าง Logger ของจริง (พิมพ์ลงจอดำ)
create_file("excel_merger_pro/src/infrastructure/console_logger.py", """
from src.application.interfaces import ILogger

class ConsoleLogger(ILogger):
    def info(self, message: str):
        print(f"[INFO] {message}")

    def error(self, message: str):
        print(f"[ERROR] {message}")
""")

# ==========================================
# 4. Tests (ส่วนตรวจสอบ - TDD)
# ==========================================

# Spy Logger (สายลับสำหรับ Test)
create_file("excel_merger_pro/tests/doubles/spy_logger.py", """
from src.application.interfaces import ILogger

class SpyLogger(ILogger):
    def __init__(self):
        self.logs = []

    def info(self, message: str):
        self.logs.append(f"INFO: {message}")

    def error(self, message: str):
        self.logs.append(f"ERROR: {message}")
""")

# Test Case (ตัวที่เราคุยกัน)
create_file("excel_merger_pro/tests/unit/test_merge_service_logging.py", """
import unittest
import sys
import os

# Hack: เพิ่ม path ให้มองเห็น src (เผื่อรันจากใน subfolder)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from src.domain.entities import SourceFile
from src.domain.value_objects import FilePath, SheetName
from src.application.services import MergeService
from tests.doubles.spy_logger import SpyLogger

class TestMergeServiceLogging(unittest.TestCase):
    
    def test_merge_process_should_log_steps(self):
        # Arrange
        spy_logger = SpyLogger()
        service = MergeService(logger=spy_logger)
        
        # Mock Data
        path = FilePath("C:/test/data.xlsx")
        sheets = [SheetName("Sheet1")]
        files = [SourceFile(path, sheets)]
        
        # Act
        service.merge(files)
        
        # Assert
        # เช็คว่ามี Log เขียนว่า "Starting merge process" หรือไม่
        has_start_log = any("Starting merge process" in log for log in spy_logger.logs)
        self.assertTrue(has_start_log, "Service should log 'Starting merge process'")
        
        # เช็คว่ามี Log เขียนชื่อไฟล์หรือไม่
        has_file_log = any("Processing file: C:/test/data.xlsx" in log for log in spy_logger.logs)
        self.assertTrue(has_file_log, "Service should log the file being processed")

if __name__ == '__main__':
    unittest.main()
""")

# สร้างไฟล์ __init__.py เพื่อให้ Python มองเป็น Package
create_file("excel_merger_pro/src/__init__.py", "")
create_file("excel_merger_pro/src/domain/__init__.py", "")
create_file("excel_merger_pro/src/application/__init__.py", "")
create_file("excel_merger_pro/tests/__init__.py", "")

print("-" * 50)
print("🎉 สร้างโปรเจคเสร็จเรียบร้อยครับป๋า!")
print("วิธีรัน Test: ให้เปิด Terminal เข้าไปในโฟลเดอร์ excel_merger_pro แล้วพิมพ์:")
print("python -m unittest discover tests")