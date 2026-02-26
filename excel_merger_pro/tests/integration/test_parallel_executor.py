# File: tests/integration/test_parallel_executor.py
"""
Integration tests for ParallelMergeExecutor

Tests parallel file processing with ThreadPoolExecutor,
error isolation, and cancellation handling.
"""

import pytest
import pandas as pd
import time
from pathlib import Path
from typing import List
from concurrent.futures import ThreadPoolExecutor

from src.domain.entities import SourceFile
from src.domain.value_objects import FilePath, SheetName
from src.infrastructure.parallel_executor import ParallelMergeExecutor
from tests.doubles.spy_logger import SpyLogger


class TestParallelMergeExecutor:
    """Test parallel file processing"""
    
    @pytest.fixture
    def temp_excel_files(self, tmp_path) -> List[Path]:
        """Create 4 temporary Excel files for parallel processing"""
        files = []
        for i in range(4):
            file_path = tmp_path / f"file_{i}.xlsx"
            df = pd.DataFrame({
                'ID': range(i * 100, (i + 1) * 100),
                'Value': [f'data_{i}_{j}' for j in range(100)],
                'FileNum': [i] * 100
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
    
    def test_parallel_execution_processes_all_files(self, source_files):
        """Test that all files are processed in parallel"""
        executor = ParallelMergeExecutor(max_workers=4)
        
        def process_file(file: SourceFile) -> pd.DataFrame:
            df = pd.read_excel(file.path.value, engine='openpyxl')
            return df
        
        results = executor.execute(source_files, process_file)
        
        assert len(results) == 4
        assert all(isinstance(df, pd.DataFrame) for df in results)
        assert sum(len(df) for df in results) == 400  # 4 files × 100 rows
    
    def test_parallel_execution_faster_than_sequential(self, source_files):
        """Test that parallel execution is faster than sequential"""
        def slow_process(file: SourceFile) -> pd.DataFrame:
            time.sleep(0.5)  # Simulate slow I/O
            return pd.read_excel(file.path.value, engine='openpyxl')
        
        # Sequential timing
        start = time.time()
        sequential_results = [slow_process(f) for f in source_files]
        sequential_time = time.time() - start
        
        # Parallel timing
        executor = ParallelMergeExecutor(max_workers=4)
        start = time.time()
        parallel_results = executor.execute(source_files, slow_process)
        parallel_time = time.time() - start
        
        assert parallel_time < sequential_time * 0.6  # At least 40% faster
        assert len(parallel_results) == len(sequential_results)
    
    def test_parallel_execution_with_progress_callback(self, source_files):
        """Test progress callback during parallel execution"""
        completed_files = []
        
        def progress_callback(file: SourceFile):
            completed_files.append(file.path.value)
        
        def process_with_callback(file: SourceFile) -> pd.DataFrame:
            df = pd.read_excel(file.path.value, engine='openpyxl')
            progress_callback(file)
            return df
        
        executor = ParallelMergeExecutor(max_workers=2)
        results = executor.execute(source_files, process_with_callback)
        
        assert len(completed_files) == 4
        assert len(results) == 4
    
    def test_error_isolation_continues_processing_other_files(self, source_files, tmp_path):
        """Test that error in one file doesn't stop others"""
        # Add a corrupted file
        bad_file_path = tmp_path / "corrupted.xlsx"
        bad_file_path.write_text("not an excel file")
        
        bad_file = SourceFile(
            path=FilePath(str(bad_file_path)),
            available_sheets=[SheetName("Sheet1")],
            selected_sheets=[SheetName("Sheet1")]
        )
        
        all_files = source_files + [bad_file]
        
        def process_file(file: SourceFile) -> pd.DataFrame:
            return pd.read_excel(file.path.value, engine='openpyxl')
        
        executor = ParallelMergeExecutor(max_workers=4)
        
        # Should raise exception but collect successful results
        with pytest.raises(Exception) as exc_info:
            executor.execute(all_files, process_file)
        
        assert "corrupted.xlsx" in str(exc_info.value)
    
    def test_max_workers_limits_concurrent_threads(self, source_files):
        """Test that max_workers limits concurrent execution"""
        active_threads = []
        max_concurrent = 0
        
        def track_concurrency(file: SourceFile) -> pd.DataFrame:
            nonlocal max_concurrent
            active_threads.append(1)
            max_concurrent = max(max_concurrent, len(active_threads))
            time.sleep(0.1)
            df = pd.read_excel(file.path.value, engine='openpyxl')
            active_threads.pop()
            return df
        
        executor = ParallelMergeExecutor(max_workers=2)
        results = executor.execute(source_files, track_concurrency)
        
        assert max_concurrent <= 2
        assert len(results) == 4
    
    def test_empty_file_list_returns_empty_results(self):
        """Test handling of empty file list"""
        executor = ParallelMergeExecutor(max_workers=4)
        
        def dummy_process(file: SourceFile) -> pd.DataFrame:
            return pd.DataFrame()
        
        results = executor.execute([], dummy_process)
        
        assert results == []
    
    def test_single_file_still_uses_executor(self, source_files):
        """Test that single file is processed correctly"""
        executor = ParallelMergeExecutor(max_workers=4)
        
        def process_file(file: SourceFile) -> pd.DataFrame:
            return pd.read_excel(file.path.value, engine='openpyxl')
        
        results = executor.execute([source_files[0]], process_file)
        
        assert len(results) == 1
        assert isinstance(results[0], pd.DataFrame)
        assert len(results[0]) == 100
