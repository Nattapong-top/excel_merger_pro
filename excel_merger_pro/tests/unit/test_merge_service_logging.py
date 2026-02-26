import unittest
from unittest.mock import MagicMock
from src.domain.entities import SourceFile
from src.domain.value_objects import FilePath, SheetName
from src.application.services import MergeService
from tests.doubles.spy_logger import SpyLogger

class TestMergeServiceLogging(unittest.TestCase):
    
    def test_merge_process_should_log_steps(self):
        # Arrange
        spy_logger = SpyLogger()
        mock_reader = MagicMock() # สร้างตัวปลอม
        service = MergeService(logger=spy_logger, reader=mock_reader)
        
        path = FilePath("test.xlsx")
        sheets = [SheetName("Sheet1")]
        files = [SourceFile(path, sheets)]
        
        # Act
        from src.domain.processing_options import ProcessingOptions
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=False,
            max_workers=1
        )
        service.merge(files, options)
        
        # Assert
        has_start_log = any("Starting merge process" in log for log in spy_logger.logs)
        self.assertTrue(has_start_log)
        
        has_file_log = any("Processing file: test.xlsx" in log for log in spy_logger.logs)
        self.assertTrue(has_file_log)

if __name__ == '__main__':
    unittest.main()