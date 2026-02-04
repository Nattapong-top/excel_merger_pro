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