# File: tests/property/test_data_processor_properties.py
"""
Property-based tests for data processors

Feature: performance-optimization-data-processing
Property 5: Group By Uniqueness
Property 7: Duplicate Detection Accuracy
Property 10: Non-Duplicate Order Preservation
Property 12: Column Order Preservation
"""

import pytest
import pandas as pd
from hypothesis import given, strategies as st, settings, assume
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


class TestGroupByProperties:
    """
    Property 5: Group By Uniqueness
    
    For any DataFrame and set of grouping columns, after applying group by,
    each unique combination of values in the grouping columns should appear exactly once.
    """
    
    @settings(max_examples=30, deadline=None)
    @given(
        num_rows=st.integers(min_value=10, max_value=500),
        num_groups=st.integers(min_value=2, max_value=10)
    )
    def test_group_by_produces_unique_combinations(self, num_rows, num_groups):
        """
        Feature: performance-optimization-data-processing, Property 5: Group By Uniqueness
        
        After grouping, each unique combination should appear exactly once
        """
        # Create data with known groups
        df = pd.DataFrame({
            'group_col': [f'group_{i % num_groups}' for i in range(num_rows)],
            'value': range(num_rows)
        })
        
        config = GroupByConfig(
            group_columns=('group_col',),
            aggregations={'value': 'sum'}
        )
        processor = GroupByProcessor(config)
        
        result = processor.process(df)
        
        # Each group should appear exactly once
        assert len(result) == num_groups
        assert result['group_col'].nunique() == num_groups
        
        # No duplicates in group column
        assert not result['group_col'].duplicated().any()
    
    @settings(max_examples=20, deadline=None)
    @given(
        num_rows=st.integers(min_value=20, max_value=300).filter(lambda x: x % 2 == 0)
    )
    def test_aggregation_sum_correctness(self, num_rows):
        """
        Feature: performance-optimization-data-processing, Property 6: Aggregation Function Correctness
        
        Sum aggregation should produce mathematically correct results
        """
        # Create data with known sums (ensure even number of rows)
        df = pd.DataFrame({
            'category': ['A', 'B'] * (num_rows // 2),
            'amount': list(range(num_rows))
        })
        
        # Calculate expected sums
        expected_sum_a = sum(i for i in range(num_rows) if i % 2 == 0)
        expected_sum_b = sum(i for i in range(num_rows) if i % 2 == 1)
        
        config = GroupByConfig(
            group_columns=('category',),
            aggregations={'amount': 'sum'}
        )
        processor = GroupByProcessor(config)
        
        result = processor.process(df)
        
        # Verify sums are correct
        actual_sum_a = result[result['category'] == 'A']['amount'].values[0]
        actual_sum_b = result[result['category'] == 'B']['amount'].values[0]
        
        assert actual_sum_a == expected_sum_a
        assert actual_sum_b == expected_sum_b
        
        # Total sum should be preserved
        assert result['amount'].sum() == df['amount'].sum()


class TestDuplicateRemovalProperties:
    """
    Property 7: Duplicate Detection Accuracy
    Property 8: Duplicate Removal Keep Strategy
    Property 10: Non-Duplicate Order Preservation
    """
    
    @settings(max_examples=30, deadline=None)
    @given(
        num_unique=st.integers(min_value=5, max_value=50),
        duplicates_per_unique=st.integers(min_value=1, max_value=5)
    )
    def test_duplicate_detection_accuracy(self, num_unique, duplicates_per_unique):
        """
        Feature: performance-optimization-data-processing, Property 7: Duplicate Detection Accuracy
        
        Rows identified as duplicates should have identical values in comparison columns
        """
        # Create data with known duplicates
        data = []
        for i in range(num_unique):
            for j in range(duplicates_per_unique):
                data.append({
                    'id': i,
                    'name': f'name_{i}',
                    'sequence': j
                })
        
        df = pd.DataFrame(data)
        
        config = DuplicateRemovalConfig(
            comparison_columns=('id', 'name'),
            keep='first'
        )
        remover = DuplicateRemover(config)
        
        result = remover.process(df)
        
        # Should have exactly num_unique rows
        assert len(result) == num_unique
        
        # Each id should appear exactly once
        assert result['id'].nunique() == num_unique
        assert not result['id'].duplicated().any()
    
    @settings(max_examples=25, deadline=None)
    @given(
        num_rows=st.integers(min_value=10, max_value=200)
    )
    def test_keep_first_vs_keep_last(self, num_rows):
        """
        Feature: performance-optimization-data-processing, Property 8: Duplicate Removal Keep Strategy
        
        keep='first' should keep first occurrence, keep='last' should keep last occurrence
        """
        # Create data with duplicates
        df = pd.DataFrame({
            'key': [i % 10 for i in range(num_rows)],
            'order': range(num_rows)
        })
        
        # Keep first
        config_first = DuplicateRemovalConfig(
            comparison_columns=('key',),
            keep='first'
        )
        remover_first = DuplicateRemover(config_first)
        result_first = remover_first.process(df)
        
        # Keep last
        config_last = DuplicateRemovalConfig(
            comparison_columns=('key',),
            keep='last'
        )
        remover_last = DuplicateRemover(config_last)
        result_last = remover_last.process(df)
        
        # Both should have same number of rows
        assert len(result_first) == len(result_last)
        
        # But different 'order' values
        for key in range(10):
            if key < num_rows:
                first_order = result_first[result_first['key'] == key]['order'].values[0]
                last_order = result_last[result_last['key'] == key]['order'].values[0]
                
                # First should have smaller order than last
                assert first_order <= last_order
    
    @settings(max_examples=20, deadline=None)
    @given(
        num_unique=st.integers(min_value=5, max_value=30),
        num_duplicates=st.integers(min_value=5, max_value=30)
    )
    def test_non_duplicate_order_preservation(self, num_unique, num_duplicates):
        """
        Feature: performance-optimization-data-processing, Property 10: Non-Duplicate Order Preservation
        
        Relative order of non-duplicate rows should be preserved
        """
        # Create data with unique and duplicate rows
        data = []
        unique_orders = []
        
        # Add unique rows
        for i in range(num_unique):
            order = i * 2
            data.append({'id': 1000 + i, 'order': order})
            unique_orders.append(order)
        
        # Add duplicate rows
        for i in range(num_duplicates):
            data.append({'id': 0, 'order': i * 2 + 1})
        
        df = pd.DataFrame(data)
        
        config = DuplicateRemovalConfig(
            comparison_columns=('id',),
            keep='first'
        )
        remover = DuplicateRemover(config)
        
        result = remover.process(df)
        
        # Extract orders of unique rows
        unique_result_orders = result[result['id'] >= 1000]['order'].tolist()
        
        # Order should be preserved
        assert unique_result_orders == sorted(unique_result_orders)


class TestColumnSelectionProperties:
    """
    Property 12: Column Order Preservation
    Property 11: Column Selection Inclusion
    """
    
    @settings(max_examples=30, deadline=None)
    @given(
        num_cols=st.integers(min_value=3, max_value=15),
        num_selected=st.integers(min_value=1, max_value=10)
    )
    def test_column_order_preservation(self, num_cols, num_selected):
        """
        Feature: performance-optimization-data-processing, Property 12: Column Order Preservation
        
        Output DataFrame should have columns in exactly the specified order
        """
        assume(num_selected <= num_cols)
        
        # Create DataFrame with many columns
        data = {f'col_{i}': range(10) for i in range(num_cols)}
        df = pd.DataFrame(data)
        
        # Select subset in specific order
        all_cols = [f'col_{i}' for i in range(num_cols)]
        selected_cols = all_cols[:num_selected]
        reversed_order = list(reversed(selected_cols))
        
        config = ColumnSelectionConfig(
            selected_columns=tuple(reversed_order),
            column_order=tuple(reversed_order)
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        # Verify order
        assert list(result.columns) == reversed_order
        assert len(result.columns) == num_selected
    
    @settings(max_examples=25, deadline=None)
    @given(
        num_cols=st.integers(min_value=5, max_value=20),
        num_selected=st.integers(min_value=2, max_value=15)
    )
    def test_column_selection_inclusion(self, num_cols, num_selected):
        """
        Feature: performance-optimization-data-processing, Property 11: Column Selection Inclusion
        
        Output should contain exactly the selected columns that exist in input
        """
        assume(num_selected <= num_cols)
        
        # Create DataFrame
        data = {f'col_{i}': range(10) for i in range(num_cols)}
        df = pd.DataFrame(data)
        
        # Select subset
        selected_cols = [f'col_{i}' for i in range(num_selected)]
        
        config = ColumnSelectionConfig(
            selected_columns=tuple(selected_cols),
            column_order=tuple(selected_cols)
        )
        selector = ColumnSelector(config)
        
        result = selector.process(df)
        
        # Verify inclusion
        assert set(result.columns) == set(selected_cols)
        assert len(result.columns) == num_selected
        
        # Verify excluded columns are not present
        excluded_cols = [f'col_{i}' for i in range(num_selected, num_cols)]
        for col in excluded_cols:
            assert col not in result.columns
