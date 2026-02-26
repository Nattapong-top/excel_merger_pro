# File: tests/unit/test_enhanced_merge_service.py
"""
Unit tests for enhanced MergeService with performance features

Tests chunked reading, parallel processing, data processors,
and progress tracking integration.
"""

import pytest
import pandas as pd
from pathlib import Path
from typing import List

from src.application.services import MergeService
from src.domain.entities import SourceFile
from src.domain.value_objects import FilePath, SheetName
from src.domain.processing_options import (
    ProcessingOptions,
    GroupByConfig,
    DuplicateRemovalConfig,
    ColumnSelectionConfig,
    ProgressState
)
from src.infrastructure.excel_reader import PandasSheetReader
from tests.doubles.spy_logger import SpyLogger


class TestEnhancedMergeService:
    """Test enhanced MergeService with performance features"""
    
    @pytest.fixture
    def temp_excel_files(self, tmp_path) -> List[Path]:
        """Create test Excel files"""
        files = []
        for i in range(3):
            file_path = tmp_path / f"test_{i}.xlsx"
            df = pd.DataFrame({
                'Category': ['A', 'B', 'A', 'B'] * 5,
                'Amount': list(range(i * 20, (i + 1) * 20)),
                'Name': [f'Item_{j}' for j in range(20)]
            })
            df.to_excel(file_path, index=False, engine='openpyxl')
            files.append(file_path)
        return files
    
    @pytest.fixture
    def source_files(self, temp_excel_files) -> List[SourceFile]:
        """Create SourceFile entities"""
        files = []
        for path in temp_excel_files:
            file = SourceFile(
                path=FilePath(str(path)),
                available_sheets=[SheetName("Sheet1")],
                selected_sheets=[SheetName("Sheet1")]
            )
            files.append(file)
        return files
    
    @pytest.fixture
    def logger(self):
        """Create spy logger"""
        return SpyLogger()
    
    @pytest.fixture
    def reader(self):
        """Create Excel reader"""
        return PandasSheetReader()
    
    def test_merge_with_default_options(self, source_files, logger, reader):
        """Test merge with default processing options"""
        service = MergeService(logger, reader)
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=False,
            max_workers=1
        )
        
        result = service.merge(source_files, options)
        
        assert len(result) == 60  # 3 files × 20 rows
        assert 'Category' in result.columns
        assert 'Amount' in result.columns
    
    def test_merge_with_parallel_processing(self, source_files, logger, reader):
        """Test merge with parallel processing enabled"""
        service = MergeService(logger, reader)
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=True,
            max_workers=3
        )
        
        result = service.merge(source_files, options)
        
        assert len(result) == 60
        assert any('parallel' in msg.lower() for msg in logger.logs)
    
    def test_merge_with_group_by(self, source_files, logger, reader):
        """Test merge with group by processing"""
        service = MergeService(logger, reader)
        
        group_config = GroupByConfig(
            group_columns=('Category',),
            aggregations={'Amount': 'sum'}
        )
        
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=False,
            max_workers=1,
            group_by_config=group_config
        )
        
        result = service.merge(source_files, options)
        
        # Should have 2 rows (Category A and B)
        assert len(result) == 2
        assert 'Category' in result.columns
        assert 'Amount' in result.columns
    
    def test_merge_with_duplicate_removal(self, source_files, logger, reader):
        """Test merge with duplicate removal"""
        service = MergeService(logger, reader)
        
        dup_config = DuplicateRemovalConfig(
            comparison_columns=('Category',),
            keep='first'
        )
        
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=False,
            max_workers=1,
            duplicate_removal_config=dup_config
        )
        
        result = service.merge(source_files, options)
        
        # Should have 2 rows (first occurrence of A and B)
        assert len(result) == 2
    
    def test_merge_with_column_selection(self, source_files, logger, reader):
        """Test merge with column selection"""
        service = MergeService(logger, reader)
        
        col_config = ColumnSelectionConfig(
            selected_columns=('Category', 'Amount'),
            column_order=('Amount', 'Category')
        )
        
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=False,
            max_workers=1,
            column_selection_config=col_config
        )
        
        result = service.merge(source_files, options)
        
        assert list(result.columns)[:2] == ['Amount', 'Category']
        assert 'Name' not in result.columns
    
    def test_merge_with_all_processors(self, source_files, logger, reader):
        """Test merge with all processors enabled"""
        service = MergeService(logger, reader)
        
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=False,
            max_workers=1,
            group_by_config=GroupByConfig(
                group_columns=('Category',),
                aggregations={'Amount': 'sum'}
            ),
            duplicate_removal_config=None,  # Skip duplicate removal after grouping
            column_selection_config=ColumnSelectionConfig(
                selected_columns=('Category', 'Amount'),
                column_order=('Category', 'Amount')
            )
        )
        
        result = service.merge(source_files, options)
        
        assert len(result) == 2  # Grouped by Category
        assert list(result.columns) == ['Category', 'Amount']
    
    def test_merge_with_progress_callback(self, source_files, logger, reader):
        """Test merge with progress callback"""
        from src.infrastructure.progress_tracker import ThreadSafeProgressTracker
        
        tracker = ThreadSafeProgressTracker()
        service = MergeService(logger, reader, progress_callback=tracker)
        
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=False,
            max_workers=1
        )
        
        result = service.merge(source_files, options)
        
        # Should have received progress updates
        states = []
        while True:
            state = tracker.get_latest_state()
            if state is None:
                break
            states.append(state)
        
        assert len(states) > 0
        assert len(result) == 60
    
    def test_merge_respects_cancellation(self, source_files, logger, reader):
        """Test that merge respects cancellation request"""
        from src.infrastructure.progress_tracker import ThreadSafeProgressTracker
        
        tracker = ThreadSafeProgressTracker()
        tracker.request_cancel()  # Cancel before starting
        
        service = MergeService(logger, reader, progress_callback=tracker)
        
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=False,
            max_workers=1
        )
        
        with pytest.raises(Exception) as exc_info:
            service.merge(source_files, options)
        
        assert 'cancel' in str(exc_info.value).lower()
    
    def test_merge_with_chunked_reading(self, tmp_path, logger, reader):
        """Test merge with chunked reading for large file"""
        # Create a larger file
        large_file = tmp_path / "large.xlsx"
        df = pd.DataFrame({
            'ID': range(15000),
            'Value': [f'data_{i}' for i in range(15000)]
        })
        df.to_excel(large_file, index=False, engine='openpyxl')
        
        file = SourceFile(
            path=FilePath(str(large_file)),
            available_sheets=[SheetName("Sheet1")],
            selected_sheets=[SheetName("Sheet1")],
            file_size_bytes=200 * 1024 * 1024  # Simulate 200MB
        )
        
        service = MergeService(logger, reader)
        options = ProcessingOptions(
            enable_chunking=True,
            chunk_size=5000,
            enable_parallel=False,
            max_workers=1
        )
        
        result = service.merge([file], options)
        
        assert len(result) == 15000
        assert any('chunk' in msg.lower() for msg in logger.logs)
    
    def test_merge_empty_file_list(self, logger, reader):
        """Test merge with empty file list"""
        service = MergeService(logger, reader)
        options = ProcessingOptions(
            enable_chunking=False,
            chunk_size=10000,
            enable_parallel=False,
            max_workers=1
        )
        
        result = service.merge([], options)
        
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)
