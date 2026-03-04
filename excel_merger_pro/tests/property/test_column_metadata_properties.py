"""
Property-based tests for ColumnMetadata validation.

Feature: column-selection-for-merge
"""

import pytest
from hypothesis import given, strategies as st

from src.domain.column_metadata import ColumnMetadata


class TestColumnMetadataValidation:
    """
    Property: ColumnMetadata Validation Invariants
    Validates: Requirements 1.1
    
    Tests that ColumnMetadata enforces its validation rules consistently
    across all possible inputs.
    """
    
    @given(
        source_files=st.lists(
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=10
        ),
        is_from_header=st.booleans(),
        data_type=st.one_of(
            st.none(),
            st.sampled_from(['string', 'integer', 'float', 'boolean', 'datetime'])
        )
    )
    def test_empty_name_raises_error(self, source_files, is_from_header, data_type):
        """
        Feature: column-selection-for-merge, Property: ColumnMetadata Validation Invariants
        For any valid source_files list, creating ColumnMetadata with empty name
        should raise ValueError.
        """
        with pytest.raises(ValueError, match="Column name cannot be empty"):
            ColumnMetadata(
                name="",
                source_files=source_files,
                is_from_header=is_from_header,
                data_type=data_type
            )
    
    @given(
        name=st.text(min_size=1, max_size=100),
        is_from_header=st.booleans(),
        data_type=st.one_of(
            st.none(),
            st.sampled_from(['string', 'integer', 'float', 'boolean', 'datetime'])
        )
    )
    def test_empty_source_files_raises_error(self, name, is_from_header, data_type):
        """
        Feature: column-selection-for-merge, Property: ColumnMetadata Validation Invariants
        For any valid name, creating ColumnMetadata with empty source_files
        should raise ValueError.
        """
        with pytest.raises(ValueError, match="Column must have at least one source file"):
            ColumnMetadata(
                name=name,
                source_files=[],
                is_from_header=is_from_header,
                data_type=data_type
            )
    
    @given(
        name=st.text(min_size=1, max_size=100),
        source_files=st.lists(
            st.text(min_size=1, max_size=100),
            min_size=1,
            max_size=10
        ),
        is_from_header=st.booleans(),
        data_type=st.one_of(
            st.none(),
            st.sampled_from(['string', 'integer', 'float', 'boolean', 'datetime'])
        )
    )
    def test_valid_column_metadata_succeeds(self, name, source_files, is_from_header, data_type):
        """
        Feature: column-selection-for-merge, Property: ColumnMetadata Validation Invariants
        For any valid inputs, creating ColumnMetadata should succeed and
        preserve all attributes correctly.
        """
        metadata = ColumnMetadata(
            name=name,
            source_files=source_files,
            is_from_header=is_from_header,
            data_type=data_type
        )
        
        assert metadata.name == name
        assert metadata.source_files == source_files
        assert metadata.is_from_header == is_from_header
        assert metadata.data_type == data_type
