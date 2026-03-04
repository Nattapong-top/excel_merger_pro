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
