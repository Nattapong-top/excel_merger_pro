"""
Property-based tests for ColumnSelector.

Feature: column-selection-for-merge
"""

import pytest
import pandas as pd
from hypothesis import given, strategies as st, assume

from src.infrastructure.data_processors import ColumnSelector
from src.domain.processing_options import ColumnSelectionConfig


# Strategies for generating test data
@st.composite
def column_names(draw):
    """Generate valid column names"""
    return draw(st.text(
        alphabet=st.characters(
            whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'),
            min_codepoint=32,
            max_codepoint=126
        ),
        min_size=1,
        max_size=30
    ).filter(lambda x: x.strip() and x != ''))


@st.composite
def dataframe_with_columns(draw, columns=None):
    """Generate a DataFrame with specified or random columns"""
    if columns is None:
        columns = draw(st.lists(column_names(), min_size=1, max_size=20, unique=True))
    
    num_rows = draw(st.integers(min_value=0, max_value=50))
    
    data = {}
    for col in columns:
        # Generate random data for each column
        data[col] = draw(st.lists(
            st.one_of(
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.text(max_size=20),
                st.none()
            ),
            min_size=num_rows,
            max_size=num_rows
        ))
    
    return pd.DataFrame(data)


@st.composite
def column_selection_config_strategy(draw, available_columns=None):
    """Generate a valid ColumnSelectionConfig"""
    if available_columns is None:
        available_columns = draw(st.lists(column_names(), min_size=1, max_size=20, unique=True))
    
    # Select a subset of available columns
    num_selected = draw(st.integers(min_value=1, max_value=len(available_columns)))
    selected = draw(st.lists(
        st.sampled_from(available_columns),
        min_size=num_selected,
        max_size=num_selected,
        unique=True
    ))
    
    # Create a random ordering of selected columns
    column_order = draw(st.permutations(selected))
    
    return ColumnSelectionConfig(
        selected_columns=tuple(selected),
        column_order=tuple(column_order)
    ), available_columns


class TestOutputColumnFiltering:
    """
    Property 11: Output Column Filtering
    Validates: Requirements 4.2, 4.5
    
    For any column selection configuration and set of source files,
    the merged output should contain only the columns specified in the
    selection, and no other columns (except system-added columns).
    """
    
    @given(dataframe_with_columns())
    def test_output_contains_only_selected_columns(self, df):
        """
        Feature: column-selection-for-merge, Property 11: Output Column Filtering
        For any DataFrame and column selection, the output should contain
        only the selected columns.
        """
        assume(len(df.columns) > 0)
        
        # Select a subset of columns
        all_columns = list(df.columns)
        num_selected = max(1, len(all_columns) // 2)
        selected_columns = all_columns[:num_selected]
        
        config = ColumnSelectionConfig(
            selected_columns=tuple(selected_columns),
            column_order=tuple(selected_columns)
        )
        
        selector = ColumnSelector(config)
        result = selector.process(df)
        
        # Verify output contains only selected columns
        assert set(result.columns) == set(selected_columns)
        assert len(result.columns) == len(selected_columns)
    
    @given(
        df=dataframe_with_columns(),
        extra_columns=st.lists(column_names(), min_size=1, max_size=10, unique=True)
    )
    def test_unselected_columns_are_filtered_out(self, df, extra_columns):
        """
        Feature: column-selection-for-merge, Property 11: Output Column Filtering
        For any DataFrame with extra columns, unselected columns should not
        appear in the output.
        """
        assume(len(df.columns) > 0)
        
        # Ensure extra columns don't overlap with existing columns
        extra_columns = [col for col in extra_columns if col not in df.columns]
        assume(len(extra_columns) > 0)
        
        # Add extra columns to DataFrame
        for col in extra_columns:
            df[col] = 0
        
        # Select only original columns (not the extra ones)
        original_columns = [col for col in df.columns if col not in extra_columns]
        assume(len(original_columns) > 0)
        
        config = ColumnSelectionConfig(
            selected_columns=tuple(original_columns),
            column_order=tuple(original_columns)
        )
        
        selector = ColumnSelector(config)
        result = selector.process(df)
        
        # Verify extra columns are not in output
        for extra_col in extra_columns:
            assert extra_col not in result.columns
        
        # Verify only selected columns are present
        assert set(result.columns) == set(original_columns)


class TestOutputColumnOrdering:
    """
    Property 12: Output Column Ordering
    Validates: Requirements 4.3, 7.4
    
    For any column order specification in the configuration,
    the columns in the merged output should appear in exactly that order.
    """
    
    @given(dataframe_with_columns())
    def test_output_columns_match_specified_order(self, df):
        """
        Feature: column-selection-for-merge, Property 12: Output Column Ordering
        For any column order specification, the output columns should
        appear in exactly that order.
        """
        assume(len(df.columns) > 1)
        
        # Create a specific order (reverse of current order)
        columns = list(df.columns)
        reversed_order = list(reversed(columns))
        
        config = ColumnSelectionConfig(
            selected_columns=tuple(columns),
            column_order=tuple(reversed_order)
        )
        
        selector = ColumnSelector(config)
        result = selector.process(df)
        
        # Verify column order matches exactly
        assert list(result.columns) == reversed_order
    
    @given(dataframe_with_columns())
    def test_column_order_preserved_across_processing(self, df):
        """
        Feature: column-selection-for-merge, Property 12: Output Column Ordering
        For any arbitrary column ordering, the output should preserve
        that exact order.
        """
        assume(len(df.columns) >= 2)
        
        columns = list(df.columns)
        
        # Create multiple random orderings and test each
        import random
        random.seed(42)
        
        for _ in range(3):  # Test 3 different orderings
            shuffled = columns.copy()
            random.shuffle(shuffled)
            
            config = ColumnSelectionConfig(
                selected_columns=tuple(shuffled),
                column_order=tuple(shuffled)
            )
            
            selector = ColumnSelector(config)
            result = selector.process(df)
            
            # Verify exact order preservation
            assert list(result.columns) == shuffled
    
    @given(dataframe_with_columns())
    def test_partial_selection_maintains_order(self, df):
        """
        Feature: column-selection-for-merge, Property 12: Output Column Ordering
        When selecting a subset of columns, the specified order should
        be maintained in the output.
        """
        assume(len(df.columns) >= 3)
        
        columns = list(df.columns)
        
        # Select every other column in reverse order
        selected = columns[::2][::-1]
        assume(len(selected) >= 2)
        
        config = ColumnSelectionConfig(
            selected_columns=tuple(selected),
            column_order=tuple(selected)
        )
        
        selector = ColumnSelector(config)
        result = selector.process(df)
        
        # Verify order matches specification
        assert list(result.columns) == selected


class TestMissingColumnHandling:
    """
    Property 13: Missing Column Handling
    Validates: Requirements 4.4
    
    For any selected column that doesn't exist in a source file,
    the merged output should include that column with null/empty values.
    """
    
    @given(
        df=dataframe_with_columns(),
        missing_columns=st.lists(column_names(), min_size=1, max_size=5, unique=True)
    )
    def test_missing_columns_created_with_null_values(self, df, missing_columns):
        """
        Feature: column-selection-for-merge, Property 13: Missing Column Handling
        For any columns that don't exist in the DataFrame, they should be
        created with null values.
        """
        assume(len(df.columns) > 0)
        
        # Ensure missing columns don't overlap with existing columns
        missing_columns = [col for col in missing_columns if col not in df.columns]
        assume(len(missing_columns) > 0)
        
        # Select both existing and missing columns
        all_selected = list(df.columns) + missing_columns
        
        config = ColumnSelectionConfig(
            selected_columns=tuple(all_selected),
            column_order=tuple(all_selected)
        )
        
        selector = ColumnSelector(config)
        result = selector.process(df)
        
        # Verify missing columns exist in output
        for missing_col in missing_columns:
            assert missing_col in result.columns
            # Verify all values are null
            assert result[missing_col].isna().all() or (result[missing_col] == None).all()
    
    @given(
        df=dataframe_with_columns(),
        missing_columns=st.lists(column_names(), min_size=1, max_size=5, unique=True)
    )
    def test_missing_columns_preserve_row_count(self, df, missing_columns):
        """
        Feature: column-selection-for-merge, Property 13: Missing Column Handling
        When missing columns are added, the row count should remain unchanged.
        """
        assume(len(df.columns) > 0)
        
        # Ensure missing columns don't overlap with existing columns
        missing_columns = [col for col in missing_columns if col not in df.columns]
        assume(len(missing_columns) > 0)
        
        original_row_count = len(df)
        
        # Select both existing and missing columns
        all_selected = list(df.columns) + missing_columns
        
        config = ColumnSelectionConfig(
            selected_columns=tuple(all_selected),
            column_order=tuple(all_selected)
        )
        
        selector = ColumnSelector(config)
        result = selector.process(df)
        
        # Verify row count is preserved
        assert len(result) == original_row_count
    
    @given(
        df=dataframe_with_columns(),
        missing_columns=st.lists(column_names(), min_size=1, max_size=5, unique=True)
    )
    def test_existing_data_preserved_when_missing_columns_added(self, df, missing_columns):
        """
        Feature: column-selection-for-merge, Property 13: Missing Column Handling
        When missing columns are added, existing column data should be preserved.
        """
        assume(len(df.columns) > 0)
        assume(len(df) > 0)
        
        # Ensure missing columns don't overlap with existing columns
        missing_columns = [col for col in missing_columns if col not in df.columns]
        assume(len(missing_columns) > 0)
        
        # Store original data
        original_columns = list(df.columns)
        original_data = {col: df[col].copy() for col in original_columns}
        
        # Select both existing and missing columns
        all_selected = list(df.columns) + missing_columns
        
        config = ColumnSelectionConfig(
            selected_columns=tuple(all_selected),
            column_order=tuple(all_selected)
        )
        
        selector = ColumnSelector(config)
        result = selector.process(df)
        
        # Verify existing data is preserved
        for col in original_columns:
            pd.testing.assert_series_equal(
                result[col].reset_index(drop=True),
                original_data[col].reset_index(drop=True),
                check_names=False
            )
    
    @given(missing_columns=st.lists(column_names(), min_size=1, max_size=10, unique=True))
    def test_all_missing_columns_creates_empty_dataframe_structure(self, missing_columns):
        """
        Feature: column-selection-for-merge, Property 13: Missing Column Handling
        When all selected columns are missing from an empty DataFrame,
        the result should have the correct structure with null columns.
        """
        # Create empty DataFrame
        df = pd.DataFrame()
        
        config = ColumnSelectionConfig(
            selected_columns=tuple(missing_columns),
            column_order=tuple(missing_columns)
        )
        
        selector = ColumnSelector(config)
        result = selector.process(df)
        
        # Verify all columns exist
        assert set(result.columns) == set(missing_columns)
        # Verify order is correct
        assert list(result.columns) == missing_columns
        # Verify DataFrame is empty
        assert len(result) == 0
