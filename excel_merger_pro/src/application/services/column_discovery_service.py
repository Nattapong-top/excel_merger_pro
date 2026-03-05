"""Column discovery service for identifying columns in source files."""

from typing import List, Optional
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
    
    def __init__(self, reader: ISheetReader, logger: Optional[ILogger] = None):
        """
        Initialize service with dependencies.
        
        Args:
            reader: Sheet reader for accessing Excel files
            logger: Logger for operation tracking (optional)
        """
        self.reader = reader
        self.logger = logger
    
    def _log(self, message: str):
        """Log message if logger is available"""
        if self.logger:
            if hasattr(self.logger, 'log'):
                self.logger.log(message)
            elif hasattr(self.logger, 'info'):
                self.logger.info(message)
    
    def discover_columns(self, files: List[SourceFile]) -> List[ColumnMetadata]:
        """
        Discover all unique columns from source files.
        
        Args:
            files: List of source files to analyze
        
        Returns:
            List of unique columns with metadata
        """
        self._log("Starting column discovery...")
        
        column_map = {}  # {column_name: ColumnMetadata}
        
        for source_file in files:
            try:
                # Read columns from each selected sheet
                for sheet in source_file.selected_sheets:
                    try:
                        # Read just the header (first row)
                        df = pd.read_excel(
                            source_file.path.value,
                            sheet_name=sheet.value,
                            nrows=1,  # Read only first row
                            engine='openpyxl'
                        )
                        
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
                            col_name_str = str(col_name)  # Convert to string
                            if col_name_str in column_map:
                                # Add this file to existing column metadata
                                file_path_str = str(source_file.path.value)
                                if file_path_str not in column_map[col_name_str].source_files:
                                    column_map[col_name_str].source_files.append(file_path_str)
                            else:
                                # Create new column metadata
                                column_map[col_name_str] = ColumnMetadata(
                                    name=col_name_str,
                                    source_files=[str(source_file.path.value)],
                                    is_from_header=is_from_header,
                                    data_type=None  # We don't have enough data to detect type
                                )
                    except Exception as e:
                        self._log(f"Error reading sheet {sheet.value}: {e}")
                        continue
                
            except Exception as e:
                self._log(f"Error reading {source_file.path.value}: {e}")
                continue
        
        result = list(column_map.values())
        self._log(f"Discovered {len(result)} unique columns")
        
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
