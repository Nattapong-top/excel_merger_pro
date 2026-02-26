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
        import pandas as pd
        import numpy as np
        
        # Group by specified columns
        group_cols = list(self.config.group_columns)
        
        # Separate aggregations for group columns and other columns
        agg_dict = {}
        count_column = None
        
        for col, func in self.config.aggregations.items():
            if col in df.columns:
                if col in group_cols:
                    # If aggregating a group column, we'll use size() to count rows
                    count_column = col
                else:
                    # Try to convert to numeric if using numeric aggregation
                    if func in ['sum', 'mean', 'min', 'max']:
                        # Try to convert to numeric, coerce errors to NaN
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    agg_dict[col] = func
        
        # Perform grouping
        grouped = df.groupby(group_cols, as_index=False)
        
        if agg_dict:
            # Apply aggregations to non-group columns
            result = grouped.agg(agg_dict)
        else:
            # No aggregations, just get first row of each group
            result = grouped.first()
        
        # If user wanted to count rows in each group
        if count_column:
            # Add count column
            count_result = df.groupby(group_cols).size().reset_index(name=f'{count_column}_count')
            if not result.empty:
                result = result.merge(count_result, on=group_cols, how='left')
            else:
                result = count_result
        
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
