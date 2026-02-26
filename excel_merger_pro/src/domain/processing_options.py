# File: src/domain/processing_options.py
"""
Domain Layer - Processing Options Value Objects

These value objects encapsulate all configuration for data processing operations.
They validate their own invariants at construction time, preventing invalid states.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Dict


@dataclass(frozen=True)
class ProcessingOptions:
    """
    Main configuration for merge processing operations.
    
    Validates:
    - chunk_size must be between 1000 and 100000
    - max_workers must be between 1 and 8
    - If chunking enabled, chunk_size must be >= 1000
    """
    enable_chunking: bool
    chunk_size: int
    enable_parallel: bool
    max_workers: int
    group_by_config: Optional['GroupByConfig'] = None
    duplicate_removal_config: Optional['DuplicateRemovalConfig'] = None
    column_selection_config: Optional['ColumnSelectionConfig'] = None
    
    def __post_init__(self):
        """Validate invariants"""
        if self.chunk_size < 1000 or self.chunk_size > 100000:
            raise ValueError(f"chunk_size must be between 1000 and 100000, got {self.chunk_size}")
        
        if self.max_workers < 1 or self.max_workers > 8:
            raise ValueError(f"max_workers must be between 1 and 8, got {self.max_workers}")
        
        if self.enable_chunking and self.chunk_size < 1000:
            raise ValueError("chunk_size too small for chunking (minimum 1000)")


@dataclass(frozen=True)
class GroupByConfig:
    """
    Configuration for Group By operation.
    
    Validates:
    - group_columns cannot be empty
    - aggregations cannot be empty
    - All aggregation functions must be valid
    """
    group_columns: Tuple[str, ...]
    aggregations: Dict[str, str]  # {column: function} e.g., {"Amount": "sum"}
    
    VALID_FUNCTIONS = {"sum", "count", "mean", "min", "max", "first", "last"}
    
    def __post_init__(self):
        """Validate invariants"""
        if not self.group_columns:
            raise ValueError("group_columns cannot be empty")
        
        if not self.aggregations:
            raise ValueError("aggregations cannot be empty")
        
        for col, func in self.aggregations.items():
            if func not in self.VALID_FUNCTIONS:
                raise ValueError(
                    f"Invalid aggregation function '{func}' for column '{col}'. "
                    f"Valid functions: {self.VALID_FUNCTIONS}"
                )


@dataclass(frozen=True)
class DuplicateRemovalConfig:
    """
    Configuration for duplicate removal operation.
    
    Validates:
    - comparison_columns cannot be empty
    - keep must be 'first' or 'last'
    """
    comparison_columns: Tuple[str, ...]
    keep: str  # "first" or "last"
    
    def __post_init__(self):
        """Validate invariants"""
        if not self.comparison_columns:
            raise ValueError("comparison_columns cannot be empty")
        
        if self.keep not in ("first", "last"):
            raise ValueError(f"keep must be 'first' or 'last', got '{self.keep}'")


@dataclass(frozen=True)
class ColumnSelectionConfig:
    """
    Configuration for column selection and reordering.
    
    Validates:
    - selected_columns cannot be empty
    - column_order must contain exactly the selected_columns
    """
    selected_columns: Tuple[str, ...]
    column_order: Tuple[str, ...]
    
    def __post_init__(self):
        """Validate invariants"""
        if not self.selected_columns:
            raise ValueError("selected_columns cannot be empty")
        
        if set(self.column_order) != set(self.selected_columns):
            raise ValueError(
                "column_order must contain exactly the selected_columns. "
                f"Missing: {set(self.selected_columns) - set(self.column_order)}, "
                f"Extra: {set(self.column_order) - set(self.selected_columns)}"
            )


@dataclass(frozen=True)
class ProgressState:
    """
    Immutable snapshot of merge operation progress.
    
    Validates:
    - percentage must be between 0 and 100
    - files_completed cannot exceed total_files
    - estimated_seconds_remaining must be non-negative
    """
    current_file: str
    files_completed: int
    total_files: int
    rows_processed: int
    total_rows: int
    percentage: float
    estimated_seconds_remaining: float
    
    def __post_init__(self):
        """Validate invariants"""
        if self.percentage < 0 or self.percentage > 100:
            raise ValueError(f"percentage must be between 0 and 100, got {self.percentage}")
        
        if self.files_completed > self.total_files:
            raise ValueError(
                f"files_completed ({self.files_completed}) cannot exceed "
                f"total_files ({self.total_files})"
            )
        
        if self.estimated_seconds_remaining < 0:
            raise ValueError(
                f"estimated_seconds_remaining must be non-negative, "
                f"got {self.estimated_seconds_remaining}"
            )
