"""Column discovery service for identifying columns in source files."""

from typing import List
import pandas as pd

from ...domain.entities import SourceFile
from ...domain.column_metadata import ColumnMetadata
from ..interfaces import ISheetReader, ILogger


class ColumnDiscoveryService:
    """
    Service for discovering available columns from source files.
    
    Responsibilities:
    - Read column names from all source files
    - Merge column lists from multiple files
    - Handle duplicate column names
    - Detect header rows
    """
    
    def __init__(self, reader: ISheetReader, logger: ILogger):
        """
        Initialize service with dependencies.
        
        Args:
            reader: Sheet reader for accessing Excel files
            logger: Logger for operation tracking
        """
        self.reader = reader
        self.logger = logger
    
    def discover_columns(self, files: List[SourceFile]) -> List[ColumnMetadata]:
        """
        Discover all unique columns from source files.
        
        Args:
            files: List of source files to analyze
        
        Returns:
            List of unique columns with metadata
        """
        self.logger.log("Starting column discovery...")
        
        column_map = {}  # {column_name: ColumnMetadata}
        
        for source_file in files:
            try:
                # Read first few rows to detect columns
                df_chunks = list(self.reader.read_sheet_chunked(
                    source_file.path,
                    source_file.selected_sheet,
                    chunk_size=10
                ))
                
                if not df_chunks:
                    self.logger.log(f"Warning: No data in {source_file.path}")
                    continue
                
                df = df_chunks[0]
                
                # Check if first row looks like a header
                is_from_header = self._has_header_row(df)
                
                if is_from_header:
                    # Use column names from DataFrame
                    columns = list(df.columns)
                else:
                    # Generate letter-based column names
                    columns = self._generate_letter_names(len(df.columns))
                
                # Add to column map
                for col_name in columns:
                    if col_name in column_map:
                        # Add this file to existing column metadata
                        if source_file.path not in column_map[col_name].source_files:
                            column_map[col_name].source_files.append(source_file.path)
                    else:
                        # Create new column metadata
                        column_map[col_name] = ColumnMetadata(
                            name=col_name,
                            source_files=[source_file.path],
                            is_from_header=is_from_header,
                            data_type=self._detect_data_type(df[col_name]) if is_from_header else None
                        )
                
            except Exception as e:
                self.logger.log(f"Error reading {source_file.path}: {e}")
                continue
        
        result = list(column_map.values())
        self.logger.log(f"Discovered {len(result)} unique columns")
        
        return result
    
    def _has_header_row(self, df: pd.DataFrame) -> bool:
        """
        Detect if DataFrame has a header row.
        
        Simple heuristic: if column names are not default (Unnamed, integers),
        assume they are from a header row.
        
        Args:
            df: DataFrame to check
        
        Returns:
            True if header row detected
        """
        # Check if any column name starts with "Unnamed"
        for col in df.columns:
            if isinstance(col, str) and col.startswith("Unnamed"):
                return False
            if isinstance(col, int):
                return False
        
        return True
    
    def _generate_letter_names(self, count: int) -> List[str]:
        """
        Generate Excel-style letter column names (A, B, C, ..., Z, AA, AB, ...).
        
        Args:
            count: Number of column names to generate
        
        Returns:
            List of letter-based column names
        """
        names = []
        for i in range(count):
            name = ""
            num = i
            while True:
                name = chr(65 + (num % 26)) + name
                num = num // 26
                if num == 0:
                    break
                num -= 1
            names.append(name)
        
        return names
    
    def _detect_data_type(self, series: pd.Series) -> str:
        """
        Detect data type of a pandas Series.
        
        Args:
            series: Pandas Series to analyze
        
        Returns:
            String representation of data type
        """
        dtype = series.dtype
        
        if pd.api.types.is_integer_dtype(dtype):
            return "integer"
        elif pd.api.types.is_float_dtype(dtype):
            return "float"
        elif pd.api.types.is_bool_dtype(dtype):
            return "boolean"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            return "datetime"
        else:
            return "string"
