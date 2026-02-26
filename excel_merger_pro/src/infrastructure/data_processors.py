# File: src/infrastructure/data_processors.py
"""
Data processors for transforming DataFrames during merge operations

Implements IDataProcessor interface for group by, duplicate removal,
and column selection operations.
"""

from typing import Any
import pandas as pd

from src.application.interfaces import IDataProcessor
from src.domain.processing_options import (
    GroupByConfig,
    DuplicateRemovalConfig,
    ColumnSelectionConfig
)


class GroupByProcessor(IDataProcessor):
    """
    Groups rows by specified columns and applies aggregation functions
    
    Supports: sum, count, mean, min, max, first, last
    """
    
    def __init__(self, config: GroupByConfig):
        """
        Initialize with group by configuration
        
        Args:
            config: GroupByConfig with group columns and aggregations
        """
        self.config = config
    
    def process(self, df: Any) -> Any:
        """
        Apply group by with aggregations to DataFrame
        
        Args:
            df: Input pandas DataFrame
        
        Returns:
            Grouped and aggregated DataFrame
        """
        # Group by specified columns
        grouped = df.groupby(list(self.config.group_columns))
        
        # Build aggregation dict for columns that exist
        agg_dict = {}
        for col, func in self.config.aggregations.items():
            if col in df.columns:
                agg_dict[col] = func
        
        # Apply aggregations and reset index
        result = grouped.agg(agg_dict).reset_index()
        
        return result
    
    def get_name(self) -> str:
        """Return processor name for logging"""
        return "GroupByProcessor"


class DuplicateRemover(IDataProcessor):
    """
    Removes duplicate rows based on comparison columns
    
    Supports keeping first or last occurrence of duplicates
    """
    
    def __init__(self, config: DuplicateRemovalConfig):
        """
        Initialize with duplicate removal configuration
        
        Args:
            config: DuplicateRemovalConfig with comparison columns and keep strategy
        """
        self.config = config
    
    def process(self, df: Any) -> Any:
        """
        Remove duplicates from DataFrame
        
        Args:
            df: Input pandas DataFrame
        
        Returns:
            DataFrame with duplicates removed
        """
        result = df.drop_duplicates(
            subset=list(self.config.comparison_columns),
            keep=self.config.keep
        )
        
        return result
    
    def get_name(self) -> str:
        """Return processor name for logging"""
        return "DuplicateRemover"


class ColumnSelector(IDataProcessor):
    """
    Selects and reorders columns in DataFrame
    
    Filters to selected columns and applies specified order
    """
    
    def __init__(self, config: ColumnSelectionConfig):
        """
        Initialize with column selection configuration
        
        Args:
            config: ColumnSelectionConfig with selected columns and order
        """
        self.config = config
    
    def process(self, df: Any) -> Any:
        """
        Select and reorder columns in DataFrame
        
        Args:
            df: Input pandas DataFrame
        
        Returns:
            DataFrame with selected columns in specified order
        """
        # Select only columns that exist in the DataFrame
        available_columns = [
            col for col in self.config.column_order
            if col in df.columns
        ]
        
        result = df[available_columns]
        
        return result
    
    def get_name(self) -> str:
        """Return processor name for logging"""
        return "ColumnSelector"
