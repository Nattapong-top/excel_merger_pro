"""Column metadata entity for column selection feature."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ColumnMetadata:
    """
    Metadata about a column discovered from source files.
    
    Attributes:
        name: Column name (from header or letter like 'A', 'B')
        source_files: List of files containing this column
        is_from_header: Whether name comes from header row
        data_type: Detected data type (optional)
    """
    name: str
    source_files: List[str]
    is_from_header: bool
    data_type: Optional[str] = None
    
    def __post_init__(self):
        """Validate column metadata."""
        if not self.name:
            raise ValueError("Column name cannot be empty")
        if not self.source_files:
            raise ValueError("Column must have at least one source file")
