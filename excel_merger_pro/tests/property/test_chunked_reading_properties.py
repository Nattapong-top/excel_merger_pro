# File: tests/property/test_chunked_reading_properties.py
"""
Property-based tests for chunked reading equivalence

Feature: performance-optimization-data-processing
Property 1: Chunked Reading Equivalence
For any Excel file and sheet, reading the file in chunks and concatenating 
the results should produce a DataFrame equivalent to reading the entire file at once.
"""

import pytest
import pandas as pd
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck
from src.domain.value_objects import FilePath, SheetName
from src.infrastructure.excel_reader import PandasSheetReader


# Custom strategies for generating test data
@st.composite
def dataframe_strategy(draw):
    """Generate random DataFrames with various shapes and types"""
    num_rows = draw(st.integers(min_value=100, max_value=1000))
    num_cols = draw(st.integers(min_value=1, max_value=5))
    
    data = {}
    for i in range(num_cols):
        col_name = f"col_{i}"
        # Use only integers to avoid type conversion issues
        data[col_name] = [draw(st.integers(min_value=0, max_value=1000)) for _ in range(num_rows)]
    
    return pd.DataFrame(data)


class TestChunkedReadingEquivalence:
    """
    Property 1: Chunked Reading Equivalence
    
    For any Excel file and sheet, reading in chunks should equal full reading
    """
    
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(df=dataframe_strategy())
    def test_chunked_equals_full_read_property(self, df, tmp_path):
        """
        Feature: performance-optimization-data-processing, Property 1: Chunked Reading Equivalence
        
        For any DataFrame, chunked reading should produce identical results to full reading
        """
        # Create temporary Excel file
        file_path = tmp_path / "test_property.xlsx"
        df.to_excel(file_path, index=False, engine='openpyxl')
        
        reader = PandasSheetReader()
        file_path_obj = FilePath(str(file_path))
        sheet_name = SheetName("Sheet1")
        
        # Read normally
        df_full = reader.read_sheet(file_path_obj, sheet_name)
        
        # Read in chunks
        chunk_size = max(10, len(df) // 5)  # Use 5 chunks
        chunks = list(reader.read_sheet_chunked(file_path_obj, sheet_name, chunk_size))
        df_chunked = pd.concat(chunks, ignore_index=True)
        
        # Assert equivalence
        assert len(df_full) == len(df_chunked), "Row count must match"
        assert list(df_full.columns) == list(df_chunked.columns), "Columns must match"
        
        # Compare data (convert to string to handle type differences)
        for col in df_full.columns:
            assert df_full[col].astype(str).tolist() == df_chunked[col].astype(str).tolist(), \
                f"Column {col} data must match"
    
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_rows=st.integers(min_value=50, max_value=1000),
        chunk_size=st.integers(min_value=10, max_value=100)
    )
    def test_chunk_size_does_not_affect_result(self, num_rows, chunk_size, tmp_path):
        """
        Feature: performance-optimization-data-processing, Property 1: Chunked Reading Equivalence
        
        Different chunk sizes should produce identical results
        """
        # Create test data
        df = pd.DataFrame({
            'id': range(num_rows),
            'value': [f'data_{i}' for i in range(num_rows)]
        })
        
        file_path = tmp_path / "test_chunk_size.xlsx"
        df.to_excel(file_path, index=False, engine='openpyxl')
        
        reader = PandasSheetReader()
        file_path_obj = FilePath(str(file_path))
        sheet_name = SheetName("Sheet1")
        
        # Read with different chunk sizes
        chunks1 = list(reader.read_sheet_chunked(file_path_obj, sheet_name, chunk_size))
        df1 = pd.concat(chunks1, ignore_index=True)
        
        chunks2 = list(reader.read_sheet_chunked(file_path_obj, sheet_name, chunk_size * 2))
        df2 = pd.concat(chunks2, ignore_index=True)
        
        # Results should be identical
        assert len(df1) == len(df2)
        assert df1['id'].tolist() == df2['id'].tolist()
        assert df1['value'].tolist() == df2['value'].tolist()
    
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_rows=st.integers(min_value=100, max_value=2000),
        num_cols=st.integers(min_value=1, max_value=15)
    )
    def test_chunked_preserves_row_count(self, num_rows, num_cols, tmp_path):
        """
        Feature: performance-optimization-data-processing, Property 1: Chunked Reading Equivalence
        
        Chunked reading must preserve exact row count
        """
        # Create test data
        data = {f'col_{i}': range(num_rows) for i in range(num_cols)}
        df = pd.DataFrame(data)
        
        file_path = tmp_path / "test_row_count.xlsx"
        df.to_excel(file_path, index=False, engine='openpyxl')
        
        reader = PandasSheetReader()
        file_path_obj = FilePath(str(file_path))
        sheet_name = SheetName("Sheet1")
        
        # Read in chunks
        chunks = list(reader.read_sheet_chunked(file_path_obj, sheet_name, 100))
        df_chunked = pd.concat(chunks, ignore_index=True)
        
        # Row count must be preserved
        assert len(df_chunked) == num_rows
        
        # Column count must be preserved
        assert len(df_chunked.columns) == num_cols
