# File: tests/property/test_value_object_properties.py
"""
Property-based tests for value object validation

Feature: performance-optimization-data-processing
Property 18: Value Object Invariant Validation
Property 14: Processing Options Validation
"""

import pytest
from hypothesis import given, strategies as st, settings
from src.domain.processing_options import (
    ProcessingOptions,
    GroupByConfig,
    DuplicateRemovalConfig,
    ColumnSelectionConfig,
    ProgressState
)


class TestProcessingOptionsValidation:
    """
    Property 18: Value Object Invariant Validation
    Property 14: Processing Options Validation
    
    For any invalid configuration, constructing the value object should raise ValueError
    """
    
    @settings(max_examples=50, deadline=None)
    @given(
        chunk_size=st.integers(min_value=-1000, max_value=999)
    )
    def test_chunk_size_below_minimum_raises_error(self, chunk_size):
        """
        Feature: performance-optimization-data-processing, Property 18: Value Object Invariant Validation
        
        chunk_size < 1000 should raise ValueError
        """
        with pytest.raises(ValueError, match="chunk_size must be between 1000 and 100000"):
            ProcessingOptions(
                enable_chunking=True,
                chunk_size=chunk_size,
                enable_parallel=False,
                max_workers=1
            )
    
    @settings(max_examples=50, deadline=None)
    @given(
        chunk_size=st.integers(min_value=100001, max_value=1000000)
    )
    def test_chunk_size_above_maximum_raises_error(self, chunk_size):
        """
        Feature: performance-optimization-data-processing, Property 18: Value Object Invariant Validation
        
        chunk_size > 100000 should raise ValueError
        """
        with pytest.raises(ValueError, match="chunk_size must be between 1000 and 100000"):
            ProcessingOptions(
                enable_chunking=True,
                chunk_size=chunk_size,
                enable_parallel=False,
                max_workers=1
            )
    
    @settings(max_examples=50, deadline=None)
    @given(
        max_workers=st.integers(min_value=-10, max_value=0)
    )
    def test_max_workers_below_minimum_raises_error(self, max_workers):
        """
        Feature: performance-optimization-data-processing, Property 18: Value Object Invariant Validation
        
        max_workers < 1 should raise ValueError
        """
        with pytest.raises(ValueError, match="max_workers must be between 1 and 8"):
            ProcessingOptions(
                enable_chunking=False,
                chunk_size=10000,
                enable_parallel=True,
                max_workers=max_workers
            )
    
    @settings(max_examples=50, deadline=None)
    @given(
        max_workers=st.integers(min_value=9, max_value=100)
    )
    def test_max_workers_above_maximum_raises_error(self, max_workers):
        """
        Feature: performance-optimization-data-processing, Property 18: Value Object Invariant Validation
        
        max_workers > 8 should raise ValueError
        """
        with pytest.raises(ValueError, match="max_workers must be between 1 and 8"):
            ProcessingOptions(
                enable_chunking=False,
                chunk_size=10000,
                enable_parallel=True,
                max_workers=max_workers
            )
    
    @settings(max_examples=100, deadline=None)
    @given(
        chunk_size=st.integers(min_value=1000, max_value=100000),
        max_workers=st.integers(min_value=1, max_value=8)
    )
    def test_valid_configuration_succeeds(self, chunk_size, max_workers):
        """
        Feature: performance-optimization-data-processing, Property 18: Value Object Invariant Validation
        
        Valid configurations should construct successfully
        """
        # Should not raise
        options = ProcessingOptions(
            enable_chunking=True,
            chunk_size=chunk_size,
            enable_parallel=True,
            max_workers=max_workers
        )
        
        assert options.chunk_size == chunk_size
        assert options.max_workers == max_workers


class TestGroupByConfigValidation:
    """
    Property 14: Processing Options Validation
    
    Group by with no columns should raise ValueError
    """
    
    @settings(max_examples=30, deadline=None)
    @given(
        agg_func=st.sampled_from(['sum', 'count', 'mean', 'min', 'max', 'first', 'last'])
    )
    def test_empty_group_columns_raises_error(self, agg_func):
        """
        Feature: performance-optimization-data-processing, Property 14: Processing Options Validation
        
        Empty group_columns should raise ValueError
        """
        with pytest.raises(ValueError, match="group_columns cannot be empty"):
            GroupByConfig(
                group_columns=(),
                aggregations={'col': agg_func}
            )
    
    @settings(max_examples=30, deadline=None)
    @given(
        num_cols=st.integers(min_value=1, max_value=10)
    )
    def test_empty_aggregations_raises_error(self, num_cols):
        """
        Feature: performance-optimization-data-processing, Property 14: Processing Options Validation
        
        Empty aggregations should raise ValueError
        """
        group_cols = tuple(f'col_{i}' for i in range(num_cols))
        
        with pytest.raises(ValueError, match="aggregations cannot be empty"):
            GroupByConfig(
                group_columns=group_cols,
                aggregations={}
            )
    
    @settings(max_examples=30, deadline=None)
    @given(
        invalid_func=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in {'sum', 'count', 'mean', 'min', 'max', 'first', 'last'}
        )
    )
    def test_invalid_aggregation_function_raises_error(self, invalid_func):
        """
        Feature: performance-optimization-data-processing, Property 18: Value Object Invariant Validation
        
        Invalid aggregation function should raise ValueError
        """
        with pytest.raises(ValueError, match="Invalid aggregation function"):
            GroupByConfig(
                group_columns=('col1',),
                aggregations={'col2': invalid_func}
            )


class TestDuplicateRemovalConfigValidation:
    """Property validation for duplicate removal configuration"""
    
    @settings(max_examples=20, deadline=None)
    @given(
        keep_value=st.text(min_size=1, max_size=20).filter(
            lambda x: x not in {'first', 'last'}
        )
    )
    def test_invalid_keep_value_raises_error(self, keep_value):
        """
        Feature: performance-optimization-data-processing, Property 18: Value Object Invariant Validation
        
        Invalid keep value should raise ValueError
        """
        with pytest.raises(ValueError, match="keep must be 'first' or 'last'"):
            DuplicateRemovalConfig(
                comparison_columns=('col1',),
                keep=keep_value
            )


class TestProgressStateValidation:
    """
    Property 3: Progress State Validity
    
    For any progress state, percentage should be 0-100 and files_completed <= total_files
    """
    
    @settings(max_examples=50, deadline=None)
    @given(
        percentage=st.floats(min_value=-100.0, max_value=-0.01)
    )
    def test_negative_percentage_raises_error(self, percentage):
        """
        Feature: performance-optimization-data-processing, Property 3: Progress State Validity
        
        Negative percentage should raise ValueError
        """
        with pytest.raises(ValueError, match="percentage must be between 0 and 100"):
            ProgressState(
                current_file="test.xlsx",
                files_completed=1,
                total_files=5,
                rows_processed=100,
                total_rows=500,
                percentage=percentage,
                estimated_seconds_remaining=10.0
            )
    
    @settings(max_examples=50, deadline=None)
    @given(
        percentage=st.floats(min_value=100.01, max_value=1000.0)
    )
    def test_percentage_above_100_raises_error(self, percentage):
        """
        Feature: performance-optimization-data-processing, Property 3: Progress State Validity
        
        Percentage > 100 should raise ValueError
        """
        with pytest.raises(ValueError, match="percentage must be between 0 and 100"):
            ProgressState(
                current_file="test.xlsx",
                files_completed=1,
                total_files=5,
                rows_processed=100,
                total_rows=500,
                percentage=percentage,
                estimated_seconds_remaining=10.0
            )
    
    @settings(max_examples=50, deadline=None)
    @given(
        total_files=st.integers(min_value=1, max_value=100),
        extra_completed=st.integers(min_value=1, max_value=50)
    )
    def test_files_completed_exceeds_total_raises_error(self, total_files, extra_completed):
        """
        Feature: performance-optimization-data-processing, Property 3: Progress State Validity
        
        files_completed > total_files should raise ValueError
        """
        files_completed = total_files + extra_completed
        
        with pytest.raises(ValueError, match="files_completed .* cannot exceed total_files"):
            ProgressState(
                current_file="test.xlsx",
                files_completed=files_completed,
                total_files=total_files,
                rows_processed=100,
                total_rows=500,
                percentage=50.0,
                estimated_seconds_remaining=10.0
            )
    
    @settings(max_examples=100, deadline=None)
    @given(
        files_completed=st.integers(min_value=0, max_value=100),
        total_files=st.integers(min_value=1, max_value=100),
        percentage=st.floats(min_value=0.0, max_value=100.0)
    )
    def test_valid_progress_state_succeeds(self, files_completed, total_files, percentage):
        """
        Feature: performance-optimization-data-processing, Property 3: Progress State Validity
        
        Valid progress state should construct successfully
        """
        # Ensure files_completed <= total_files
        if files_completed > total_files:
            files_completed = total_files
        
        # Should not raise
        state = ProgressState(
            current_file="test.xlsx",
            files_completed=files_completed,
            total_files=total_files,
            rows_processed=100,
            total_rows=500,
            percentage=percentage,
            estimated_seconds_remaining=10.0
        )
        
        assert state.files_completed == files_completed
        assert state.total_files == total_files
        assert 0 <= state.percentage <= 100
