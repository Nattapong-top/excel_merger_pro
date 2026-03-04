# File: tests/unit/test_processing_options.py
"""
Unit tests for Processing Options Value Objects
"""

import pytest
from src.domain.processing_options import (
    ProcessingOptions,
    GroupByConfig,
    DuplicateRemovalConfig,
    ColumnSelectionConfig,
    ProgressState
)


class TestProcessingOptions:
    """Test ProcessingOptions value object validation"""
    
    def test_valid_configuration(self):
        """Valid configuration should be created successfully"""
        options = ProcessingOptions(
            enable_chunking=True,
            chunk_size=10000,
            enable_parallel=True,
            max_workers=4
        )
        assert options.chunk_size == 10000
        assert options.max_workers == 4
    
    def test_chunk_size_too_small(self):
        """chunk_size < 1000 should raise ValueError"""
        with pytest.raises(ValueError, match="chunk_size must be between 1000 and 100000"):
            ProcessingOptions(
                enable_chunking=True,
                chunk_size=500,
                enable_parallel=False,
                max_workers=1
            )
    
    def test_chunk_size_too_large(self):
        """chunk_size > 100000 should raise ValueError"""
        with pytest.raises(ValueError, match="chunk_size must be between 1000 and 100000"):
            ProcessingOptions(
                enable_chunking=True,
                chunk_size=200000,
                enable_parallel=False,
                max_workers=1
            )
    
    def test_max_workers_too_small(self):
        """max_workers < 1 should raise ValueError"""
        with pytest.raises(ValueError, match="max_workers must be between 1 and 8"):
            ProcessingOptions(
                enable_chunking=False,
                chunk_size=10000,
                enable_parallel=True,
                max_workers=0
            )
    
    def test_max_workers_too_large(self):
        """max_workers > 8 should raise ValueError"""
        with pytest.raises(ValueError, match="max_workers must be between 1 and 8"):
            ProcessingOptions(
                enable_chunking=False,
                chunk_size=10000,
                enable_parallel=True,
                max_workers=16
            )
    
    def test_with_column_selection_config(self):
        """ProcessingOptions should accept ColumnSelectionConfig"""
        column_config = ColumnSelectionConfig(
            selected_columns=("Name", "Age", "City"),
            column_order=("Age", "Name", "City")
        )
        options = ProcessingOptions(
            enable_chunking=True,
            chunk_size=10000,
            enable_parallel=True,
            max_workers=4,
            column_selection_config=column_config
        )
        assert options.column_selection_config is not None
        assert options.column_selection_config.selected_columns == ("Name", "Age", "City")
        assert options.column_selection_config.column_order == ("Age", "Name", "City")
    
    def test_column_selection_config_default_none(self):
        """column_selection_config should default to None"""
        options = ProcessingOptions(
            enable_chunking=True,
            chunk_size=10000,
            enable_parallel=True,
            max_workers=4
        )
        assert options.column_selection_config is None
    
    def test_with_all_optional_configs(self):
        """ProcessingOptions should accept all optional configs including column_selection_config"""
        group_config = GroupByConfig(
            group_columns=("Category",),
            aggregations={"Amount": "sum"}
        )
        duplicate_config = DuplicateRemovalConfig(
            comparison_columns=("ID",),
            keep="first"
        )
        column_config = ColumnSelectionConfig(
            selected_columns=("ID", "Name", "Amount"),
            column_order=("ID", "Name", "Amount")
        )
        
        options = ProcessingOptions(
            enable_chunking=True,
            chunk_size=10000,
            enable_parallel=True,
            max_workers=4,
            group_by_config=group_config,
            duplicate_removal_config=duplicate_config,
            column_selection_config=column_config
        )
        
        assert options.group_by_config is not None
        assert options.duplicate_removal_config is not None
        assert options.column_selection_config is not None
        assert options.column_selection_config.selected_columns == ("ID", "Name", "Amount")


class TestGroupByConfig:
    """Test GroupByConfig value object validation"""
    
    def test_valid_configuration(self):
        """Valid group by configuration should be created successfully"""
        config = GroupByConfig(
            group_columns=("Category", "Region"),
            aggregations={"Amount": "sum", "Count": "count"}
        )
        assert config.group_columns == ("Category", "Region")
        assert config.aggregations["Amount"] == "sum"
    
    def test_empty_group_columns(self):
        """Empty group_columns should raise ValueError"""
        with pytest.raises(ValueError, match="group_columns cannot be empty"):
            GroupByConfig(
                group_columns=(),
                aggregations={"Amount": "sum"}
            )
    
    def test_empty_aggregations(self):
        """Empty aggregations should raise ValueError"""
        with pytest.raises(ValueError, match="aggregations cannot be empty"):
            GroupByConfig(
                group_columns=("Category",),
                aggregations={}
            )
    
    def test_invalid_aggregation_function(self):
        """Invalid aggregation function should raise ValueError"""
        with pytest.raises(ValueError, match="Invalid aggregation function"):
            GroupByConfig(
                group_columns=("Category",),
                aggregations={"Amount": "invalid_func"}
            )
    
    def test_all_valid_functions(self):
        """All valid aggregation functions should work"""
        for func in GroupByConfig.VALID_FUNCTIONS:
            config = GroupByConfig(
                group_columns=("Category",),
                aggregations={"Amount": func}
            )
            assert config.aggregations["Amount"] == func


class TestDuplicateRemovalConfig:
    """Test DuplicateRemovalConfig value object validation"""
    
    def test_valid_configuration_keep_first(self):
        """Valid configuration with keep='first' should work"""
        config = DuplicateRemovalConfig(
            comparison_columns=("ID", "Name"),
            keep="first"
        )
        assert config.keep == "first"
    
    def test_valid_configuration_keep_last(self):
        """Valid configuration with keep='last' should work"""
        config = DuplicateRemovalConfig(
            comparison_columns=("ID",),
            keep="last"
        )
        assert config.keep == "last"
    
    def test_empty_comparison_columns(self):
        """Empty comparison_columns should raise ValueError"""
        with pytest.raises(ValueError, match="comparison_columns cannot be empty"):
            DuplicateRemovalConfig(
                comparison_columns=(),
                keep="first"
            )
    
    def test_invalid_keep_value(self):
        """Invalid keep value should raise ValueError"""
        with pytest.raises(ValueError, match="keep must be 'first' or 'last'"):
            DuplicateRemovalConfig(
                comparison_columns=("ID",),
                keep="middle"
            )


class TestColumnSelectionConfig:
    """Test ColumnSelectionConfig value object validation"""
    
    def test_valid_configuration(self):
        """Valid configuration should work"""
        config = ColumnSelectionConfig(
            selected_columns=("Name", "Age", "City"),
            column_order=("Age", "Name", "City")
        )
        assert len(config.selected_columns) == 3
    
    def test_empty_selected_columns(self):
        """Empty selected_columns should raise ValueError"""
        with pytest.raises(ValueError, match="selected_columns cannot be empty"):
            ColumnSelectionConfig(
                selected_columns=(),
                column_order=()
            )
    
    def test_column_order_mismatch(self):
        """column_order not matching selected_columns should raise ValueError"""
        with pytest.raises(ValueError, match="column_order must contain exactly"):
            ColumnSelectionConfig(
                selected_columns=("Name", "Age"),
                column_order=("Name", "City")  # City not in selected_columns
            )
    
    def test_column_order_missing_column(self):
        """column_order missing a selected column should raise ValueError"""
        with pytest.raises(ValueError, match="column_order must contain exactly"):
            ColumnSelectionConfig(
                selected_columns=("Name", "Age", "City"),
                column_order=("Name", "Age")  # Missing City
            )


class TestProgressState:
    """Test ProgressState value object validation"""
    
    def test_valid_state(self):
        """Valid progress state should be created successfully"""
        state = ProgressState(
            current_file="file1.xlsx",
            files_completed=2,
            total_files=5,
            rows_processed=10000,
            total_rows=50000,
            percentage=20.0,
            estimated_seconds_remaining=120.5
        )
        assert state.percentage == 20.0
        assert state.files_completed == 2
    
    def test_percentage_too_low(self):
        """percentage < 0 should raise ValueError"""
        with pytest.raises(ValueError, match="percentage must be between 0 and 100"):
            ProgressState(
                current_file="file1.xlsx",
                files_completed=0,
                total_files=5,
                rows_processed=0,
                total_rows=50000,
                percentage=-5.0,
                estimated_seconds_remaining=120.0
            )
    
    def test_percentage_too_high(self):
        """percentage > 100 should raise ValueError"""
        with pytest.raises(ValueError, match="percentage must be between 0 and 100"):
            ProgressState(
                current_file="file1.xlsx",
                files_completed=5,
                total_files=5,
                rows_processed=50000,
                total_rows=50000,
                percentage=105.0,
                estimated_seconds_remaining=0.0
            )
    
    def test_files_completed_exceeds_total(self):
        """files_completed > total_files should raise ValueError"""
        with pytest.raises(ValueError, match="files_completed .* cannot exceed total_files"):
            ProgressState(
                current_file="file1.xlsx",
                files_completed=6,
                total_files=5,
                rows_processed=50000,
                total_rows=50000,
                percentage=100.0,
                estimated_seconds_remaining=0.0
            )
    
    def test_negative_estimated_time(self):
        """Negative estimated_seconds_remaining should raise ValueError"""
        with pytest.raises(ValueError, match="estimated_seconds_remaining must be non-negative"):
            ProgressState(
                current_file="file1.xlsx",
                files_completed=2,
                total_files=5,
                rows_processed=10000,
                total_rows=50000,
                percentage=20.0,
                estimated_seconds_remaining=-10.0
            )
