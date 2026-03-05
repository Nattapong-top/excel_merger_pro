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
    
    def __init__(self, config: GroupByConfig, logger=None):
        """
        Initialize with group by configuration
        
        Args:
            config: GroupByConfig with group columns and aggregations
            logger: Optional logger for progress reporting
        """
        self.config = config
        self.logger = logger
    
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
        
        if self.logger:
            self.logger.info(f"Starting group by operation on {len(df)} rows...")
            self.logger.info(f"Group by columns: {', '.join(self.config.group_columns)}")
        
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
                    if self.logger:
                        self.logger.info(f"  - Aggregating column '{col}' with function '{func}'")
        
        if self.logger:
            self.logger.info("Performing grouping operation...")
        
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
            if self.logger:
                self.logger.info(f"Adding row count for each group...")
            count_result = df.groupby(group_cols).size().reset_index(name=f'{count_column}_count')
            if not result.empty:
                result = result.merge(count_result, on=group_cols, how='left')
            else:
                result = count_result
        
        if self.logger:
            self.logger.info(f"Group by complete. Reduced from {len(df)} to {len(result)} rows")
        
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

    def __init__(self, config: ColumnSelectionConfig, logger=None):
        """
        Initialize with column selection configuration

        Args:
            config: ColumnSelectionConfig with selected columns and order
            logger: Optional logger for progress reporting
        """
        self.config = config
        self.logger = logger

    def process(self, df: Any) -> Any:
        """
        Select and reorder columns in DataFrame

        Args:
            df: Input pandas DataFrame

        Returns:
            DataFrame with selected columns in specified order
        """
        if self.logger:
            self.logger.info(f"Selecting {len(self.config.selected_columns)} columns from {len(df.columns)} available columns")
        
        result = self.apply_selection(df, self.config, self.logger)
        
        if self.logger:
            self.logger.info(f"Column selection complete. Final columns: {len(result.columns)}")
        
        return result

    @staticmethod
    def apply_selection(df: pd.DataFrame, config: ColumnSelectionConfig, logger=None) -> pd.DataFrame:
        """
        Apply column selection and reordering to DataFrame.

        Creates empty columns for selected columns that don't exist in the DataFrame.
        Automatically preserves Origin_File and Origin_Sheet columns if they exist.

        Args:
            df: Input pandas DataFrame
            config: ColumnSelectionConfig with selected columns and order
            logger: Optional logger for progress reporting

        Returns:
            DataFrame with selected columns in specified order, plus origin tracking columns
        """
        result = df.copy()

        # Create empty columns for missing columns
        missing_cols = []
        for col in config.column_order:
            if col not in result.columns:
                result[col] = None
                missing_cols.append(col)
        
        if logger and missing_cols:
            logger.info(f"Created {len(missing_cols)} empty columns for missing data: {', '.join(missing_cols[:5])}{'...' if len(missing_cols) > 5 else ''}")

        # Select and reorder columns
        selected_columns = list(config.column_order)
        
        # Automatically add Origin_File and Origin_Sheet at the end if they exist
        # These are metadata columns that should always be preserved
        if 'Origin_File' in result.columns and 'Origin_File' not in selected_columns:
            selected_columns.append('Origin_File')
        if 'Origin_Sheet' in result.columns and 'Origin_Sheet' not in selected_columns:
            selected_columns.append('Origin_Sheet')
        
        result = result[selected_columns]

        return result

    def get_name(self) -> str:
        """Return processor name for logging"""
        return "ColumnSelector"


