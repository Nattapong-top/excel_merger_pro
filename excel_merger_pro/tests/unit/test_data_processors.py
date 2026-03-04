# File: tests/unit/test_data_processors.py
"""
Unit tests for data processors (GroupBy, DuplicateRemover, ColumnSelector)

Tests data transformation operations with various edge cases
and validates processor interface compliance.
"""

import pytest
import pandas as pd
from src.domain.processing_options import (
    GroupByConfig, 
    DuplicateRemovalConfig,
    ColumnSelectionConfig
)
from src.infrastructure.data_processors import (
    GroupByProcessor,
    DuplicateRemover,
    ColumnSelector
)


class TestGroupByProcessor:
    """Test GroupByProcessor implementation"""
    
    def test_group_by_with_sum_aggregation(self):
        """Test grouping with sum aggregation"""
        df = pd.DataFrame({
            'Category': ['A', 'A', 'B', 'B'],
            'Amount': [10, 20, 30, 40],
            'Count': [1, 2, 3, 4]
        })
        
        config = GroupByConfig(
            group_columns=('Category',),
            aggregations={'Amount': 'sum', 'Count': 'sum'}
        )
        processor = GroupByProcessor(config)
        
        result = processor.process(df)
        
        assert len(result) == 2
        assert result[result['Category'] == 'A']['Amount'].values[0] == 30
        assert result[result['Category'] == 'B']['Amount'].values[0] == 70
        assert result[result['Category'] == 'A']['Count'].values[0] == 3
    
    def test_group_by_with_multiple_columns(self):
        """Test grouping by multiple columns"""
        df = pd.DataFrame({
            'Region': ['North', 'North', 'South', 'South'],
            'Category': ['A', 'B', 'A', 'B'],
            'Sales': [100, 200, 300, 400]
        })
        
        config = GroupByConfig(
            group_columns=('Region', 'Category'),
            aggregations={'Sales': 'sum'}
        )
        processor = GroupByProcessor(config)
        
        result = processor.process(df)
        
        assert len(result) == 4
        assert 'Region' in result.columns
        assert 'Category' in result.columns
    
    def test_group_by_with_mean_aggregation(self):
        """Test grouping with mean aggregation"""
        df = pd.DataFrame({
            'Type': ['X', 'X', 'Y', 'Y'],
            'Value': [10, 20, 30, 40]
        })
        
        config = GroupByConfig(
            group_columns=('Type',),
            aggregations={'Value': 'mean'}
        )
        processor = GroupByProcessor(config)
        
        result = processor.process(df)
        
        assert result[result['Type'] == 'X']['Value'].values[0] == 15.0
        assert result[result['Type'] == 'Y']['Value'].values[0] == 35.0
    
    def test_group_by_with_count_aggregation(self):
        """Test grouping with count aggregation"""
        df = pd.DataFrame({
            'Status': ['Active', 'Active', 'Inactive', 'Active'],
            'ID': [1, 2, 3, 4]
        })
        
        config = GroupByConfig(
            group_columns=('Status',),
            aggregations={'ID': 'count'}
        )
        processor = GroupByProcessor(config)
        
        result = processor.process(df)
        
        assert result[result['Status'] == 'Active']['ID'].values[0] == 3
        assert result[result['Status'] == 'Inactive']['ID'].values[0] == 1
    
    def test_group_by_with_first_last_aggregation(self):
        """Test grouping with first and last aggregations"""
        df = pd.DataFrame({
            'Group': ['A', 'A', 'B', 'B'],
            'Value': [1, 2, 3, 4],
            'Name': ['First', 'Second', 'Third', 'Fourth']
        })
        
        config = GroupByConfig(
            group_columns=('Group',),
            aggregations={'Value': 'first', 'Name': 'last'}
        )
        processor = GroupByProcessor(config)
        
        result = processor.process(df)
        
        assert result[result['Group'] == 'A']['Value'].values[0] == 1
        assert result[result['Group'] == 'A']['Name'].values[0] == 'Second'
    
    def test_group_by_ignores_missing_columns(self):
        """Test that processor handles missing columns gracefully"""
        df = pd.DataFrame({
            'Category': ['A', 'A', 'B'],
            'Amount': [10, 20, 30]
        })
        
        config = GroupByConfig(
            group_columns=('Category',),
            aggregations={'Amount': 'sum', 'NonExistent': 'sum'}
        )
        processor = GroupByProcessor(config)
        
        result = processor.process(df)
        
        assert 'Amount' in result.columns
        assert 'NonExistent' not in result.columns
    
    def test_processor_has_name(self):
        """Test that processor returns its name"""
        config = GroupByConfig(
            group_columns=('A',),
            aggregations={'B': 'sum'}
        )
        processor = GroupByProcessor(config)
        
        assert processor.get_name() == "GroupByProcessor"


class TestDuplicateRemover:
    """Test DuplicateRemover implementation"""
    
    def test_remove_duplicates_keep_first(self):
        """Test removing duplicates keeping first occurrence"""
        df = pd.DataFrame({
            'ID': [1, 2, 1, 3],
            'Name': ['Alice', 'Bob', 'Alice2', 'Charlie'],
            'Value': [100, 200, 150, 300]
        })
        
        config = DuplicateRemovalConfig(
            comparison_columns=('ID',),
            keep='first'
        )
        remover = DuplicateRemover(config)
        
        result = remover.process(df)
        
        assert len(result) == 3
        assert result[result['ID'] == 1]['Name'].values[0] == 'Alice'
    
    def test_remove_duplicates_keep_last(self):
        """Test removing duplicates keeping last occurrence"""
        df = pd.DataFrame({
            'ID': [1, 2, 1, 3],
            'Name': ['Alice', 'Bob', 'Alice2', 'Charlie'],
            'Value': [100, 200, 150, 300]
        })
        
        config = DuplicateRemovalConfig(
            comparison_columns=('ID',),
            keep='last'
        )
        remover = DuplicateRemover(config)
        
        result = remover.process(df)
        
        assert len(result) == 3
        assert result[result['ID'] == 1]['Name'].values[0] == 'Alice2'
    
    def test_remove_duplicates_multiple_columns(self):
        """Test removing duplicates based on multiple columns"""
        df = pd.DataFrame({
            'FirstName': ['John', 'Jane', 'John', 'Jane'],
            'LastName': ['Doe', 'Doe', 'Doe', 'Smith'],
            'Age': [30, 25, 30, 28]
        })
        
        config = DuplicateRemovalConfig(
            comparison_columns=('FirstName', 'LastName'),
            keep='first'
        )
        remover = DuplicateRemover(config)
        
        result = remover.process(df)
        
        assert len(result) == 3
    
    def test_no_duplicates_returns_same_dataframe(self):
        """Test that no duplicates returns all rows"""
        df = pd.DataFrame({
            'ID': [1, 2, 3, 4],
            'Value': [10, 20, 30, 40]
        })
        
        config = DuplicateRemovalConfig(
            comparison_columns=('ID',),
            keep='first'
        )
        remover = DuplicateRemover(config)
        
        result = remover.process(df)
        
        assert len(result) == 4
    
    def test_all_duplicates_keeps_one(self):
        """Test that all duplicates keeps only one row"""
        df = pd.DataFrame({
            'Value': [1, 1, 1, 1],
            'Name': ['A', 'B', 'C', 'D']
        })
        
        config = DuplicateRemovalConfig(
            comparison_columns=('Value',),
            keep='first'
        )
        remover = DuplicateRemover(config)
        
        result = remover.process(df)
        
        assert len(result) == 1
        assert result['Name'].values[0] == 'A'
    
    def test_preserve_order_of_non_duplicates(self):
        """Test that relative order is preserved"""
        df = pd.DataFrame({
            'ID': [1, 2, 3, 2, 4],
            'Order': [0, 1, 2, 3, 4]
        })
        
        config = DuplicateRemovalConfig(
            comparison_columns=('ID',),
            keep='first'
        )
        remover = DuplicateRemover(config)
        
        result = remover.process(df)
        
        assert len(result) == 4
        assert list(result['Order']) == [0, 1, 2, 4]
    
    def test_processor_has_name(self):
        """Test that processor returns its name"""
        config = DuplicateRemovalConfig(
            comparison_columns=('A',),
            keep='first'
        )
        remover = DuplicateRemover(config)
        
        assert remover.get_name() == "DuplicateRemover"


class TestColumnSelector:
    """Test ColumnSelector implementation"""
    
    def test_select_subset_of_columns(self):
        """Test selecting specific columns"""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': [7, 8, 9],
            'D': [10, 11, 12]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('A', 'C'),
            column_order=('A', 'C')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        assert list(result.columns) == ['A', 'C']
        assert len(result) == 3
    
    def test_reorder_columns(self):
        """Test reordering columns"""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': [7, 8, 9]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('C', 'A', 'B'),
            column_order=('C', 'A', 'B')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        assert list(result.columns) == ['C', 'A', 'B']
    
    def test_select_single_column(self):
        """Test selecting single column"""
        df = pd.DataFrame({
            'ID': [1, 2, 3],
            'Name': ['A', 'B', 'C'],
            'Value': [10, 20, 30]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('Name',),
            column_order=('Name',)
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        assert list(result.columns) == ['Name']
        assert len(result) == 3
    
    def test_ignore_non_existent_columns(self):
        """Test that non-existent columns are created as empty columns"""
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('A', 'C', 'B'),
            column_order=('A', 'C', 'B')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        # Should include all selected columns, creating empty ones for missing
        assert list(result.columns) == ['A', 'C', 'B']
        # Column C should be None/NaN since it didn't exist
        assert result['C'].isna().all()
    
    def test_select_all_columns_in_order(self):
        """Test selecting all columns with custom order"""
        df = pd.DataFrame({
            'Z': [1, 2],
            'Y': [3, 4],
            'X': [5, 6]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('X', 'Y', 'Z'),
            column_order=('X', 'Y', 'Z')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        assert list(result.columns) == ['X', 'Y', 'Z']
    
    def test_processor_has_name(self):
        """Test that processor returns its name"""
        config = ColumnSelectionConfig(
            selected_columns=('A',),
            column_order=('A',)
        )
        selector = ColumnSelector(config)
        
        assert selector.get_name() == "ColumnSelector"
    
    # Edge case tests for task 2.7
    
    def test_all_selected_columns_missing_from_file(self):
        """
        Edge case: All selected columns don't exist in the file
        Requirements: 4.4 - Missing columns should be created with empty values
        """
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('X', 'Y', 'Z'),
            column_order=('X', 'Y', 'Z')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        # Should create all missing columns
        assert list(result.columns) == ['X', 'Y', 'Z']
        assert len(result) == 3
        # All columns should be None/NaN
        assert result['X'].isna().all()
        assert result['Y'].isna().all()
        assert result['Z'].isna().all()
    
    def test_mixed_existing_and_missing_columns(self):
        """
        Edge case: Some selected columns exist, others don't
        Requirements: 4.2, 4.4 - Filter existing columns and create missing ones
        """
        df = pd.DataFrame({
            'Name': ['Alice', 'Bob', 'Charlie'],
            'Age': [25, 30, 35],
            'City': ['NYC', 'LA', 'SF']
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('Name', 'Email', 'Age', 'Phone'),
            column_order=('Name', 'Email', 'Age', 'Phone')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        # Should have all selected columns in order
        assert list(result.columns) == ['Name', 'Email', 'Age', 'Phone']
        # Existing columns should have data
        assert list(result['Name']) == ['Alice', 'Bob', 'Charlie']
        assert list(result['Age']) == [25, 30, 35]
        # Missing columns should be None/NaN
        assert result['Email'].isna().all()
        assert result['Phone'].isna().all()
    
    def test_column_ordering_with_reverse_order(self):
        """
        Edge case: Reverse the order of columns
        Requirements: 4.3 - Maintain specified column order
        """
        df = pd.DataFrame({
            'First': [1, 2, 3],
            'Second': [4, 5, 6],
            'Third': [7, 8, 9],
            'Fourth': [10, 11, 12]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('Fourth', 'Third', 'Second', 'First'),
            column_order=('Fourth', 'Third', 'Second', 'First')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        # Should be in reverse order
        assert list(result.columns) == ['Fourth', 'Third', 'Second', 'First']
        # Data should be preserved
        assert list(result['First']) == [1, 2, 3]
        assert list(result['Fourth']) == [10, 11, 12]
    
    def test_column_ordering_with_interleaved_order(self):
        """
        Edge case: Interleave columns in non-sequential order
        Requirements: 4.3 - Maintain specified column order
        """
        df = pd.DataFrame({
            'A': [1, 2],
            'B': [3, 4],
            'C': [5, 6],
            'D': [7, 8],
            'E': [9, 10]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('B', 'D', 'A', 'E', 'C'),
            column_order=('B', 'D', 'A', 'E', 'C')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        # Should be in specified interleaved order
        assert list(result.columns) == ['B', 'D', 'A', 'E', 'C']
        assert list(result['A']) == [1, 2]
        assert list(result['B']) == [3, 4]
    
    def test_empty_dataframe_with_column_selection(self):
        """
        Edge case: Apply column selection to empty DataFrame
        Requirements: 4.2, 4.4 - Handle empty data gracefully
        """
        df = pd.DataFrame({
            'A': [],
            'B': [],
            'C': []
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('A', 'D'),
            column_order=('A', 'D')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        # Should have selected columns even with no rows
        assert list(result.columns) == ['A', 'D']
        assert len(result) == 0
    
    def test_single_row_dataframe_with_missing_columns(self):
        """
        Edge case: Single row DataFrame with missing columns
        Requirements: 4.4 - Create missing columns with empty values
        """
        df = pd.DataFrame({
            'ID': [1],
            'Value': [100]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('ID', 'Name', 'Value', 'Status'),
            column_order=('ID', 'Name', 'Value', 'Status')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        assert list(result.columns) == ['ID', 'Name', 'Value', 'Status']
        assert result['ID'].values[0] == 1
        assert result['Value'].values[0] == 100
        assert pd.isna(result['Name'].values[0])
        assert pd.isna(result['Status'].values[0])
    
    def test_column_selection_preserves_data_types(self):
        """
        Edge case: Ensure data types are preserved after selection
        Requirements: 4.2 - Filter columns without altering data
        """
        df = pd.DataFrame({
            'IntCol': [1, 2, 3],
            'FloatCol': [1.5, 2.5, 3.5],
            'StrCol': ['a', 'b', 'c'],
            'BoolCol': [True, False, True]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('StrCol', 'IntCol', 'BoolCol'),
            column_order=('StrCol', 'IntCol', 'BoolCol')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        # Data types should be preserved
        assert result['IntCol'].dtype == df['IntCol'].dtype
        assert result['StrCol'].dtype == df['StrCol'].dtype
        assert result['BoolCol'].dtype == df['BoolCol'].dtype
    
    def test_column_selection_with_special_characters_in_names(self):
        """
        Edge case: Column names with special characters
        Requirements: 4.2, 4.3 - Handle special column names
        """
        df = pd.DataFrame({
            'Column A': [1, 2, 3],
            'Column-B': [4, 5, 6],
            'Column_C': [7, 8, 9],
            'Column.D': [10, 11, 12]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('Column.D', 'Column A', 'Column_C'),
            column_order=('Column.D', 'Column A', 'Column_C')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        assert list(result.columns) == ['Column.D', 'Column A', 'Column_C']
        assert list(result['Column A']) == [1, 2, 3]
        assert list(result['Column.D']) == [10, 11, 12]
    
    def test_column_selection_with_numeric_column_names(self):
        """
        Edge case: Numeric column names (common in Excel without headers)
        Requirements: 4.2, 4.3 - Handle numeric column names
        """
        df = pd.DataFrame({
            0: [1, 2, 3],
            1: [4, 5, 6],
            2: [7, 8, 9]
        })
        
        # Convert to string column names as ColumnSelectionConfig expects strings
        df.columns = ['0', '1', '2']
        
        config = ColumnSelectionConfig(
            selected_columns=('2', '0'),
            column_order=('2', '0')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        assert list(result.columns) == ['2', '0']
        assert list(result['0']) == [1, 2, 3]
        assert list(result['2']) == [7, 8, 9]
    
    def test_apply_selection_static_method(self):
        """
        Edge case: Test static method apply_selection directly
        Requirements: 4.2, 4.3, 4.4 - Verify static method works independently
        """
        df = pd.DataFrame({
            'A': [1, 2],
            'B': [3, 4]
        })
        
        config = ColumnSelectionConfig(
            selected_columns=('B', 'C', 'A'),
            column_order=('B', 'C', 'A')
        )
        
        result = ColumnSelector.apply_selection(df, config)
        
        assert list(result.columns) == ['B', 'C', 'A']
        assert list(result['A']) == [1, 2]
        assert list(result['B']) == [3, 4]
        assert result['C'].isna().all()
    
    def test_column_selection_does_not_modify_original_dataframe(self):
        """
        Edge case: Ensure original DataFrame is not modified
        Requirements: 4.2 - Process should not have side effects
        """
        df = pd.DataFrame({
            'A': [1, 2, 3],
            'B': [4, 5, 6],
            'C': [7, 8, 9]
        })
        original_columns = list(df.columns)
        
        config = ColumnSelectionConfig(
            selected_columns=('A', 'C'),
            column_order=('A', 'C')
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        # Original DataFrame should be unchanged
        assert list(df.columns) == original_columns
        assert 'B' in df.columns
        # Result should have only selected columns
        assert list(result.columns) == ['A', 'C']
        assert 'B' not in result.columns
