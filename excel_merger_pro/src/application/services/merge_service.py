# File: src/application/services.py
from typing import List, Any, Optional
from src.application.interfaces import ILogger, ISheetReader, IProgressCallback
from src.domain.entities import SourceFile
from src.domain.processing_options import ProcessingOptions, ProgressState
import time


class MergeService:
    """
    Enhanced merge service with performance optimization features
    
    Supports:
    - Chunked reading for large files
    - Parallel processing with ThreadPoolExecutor
    - Data transformation (group by, duplicate removal, column selection)
    - Real-time progress tracking
    - Cancellation support
    """
    
    def __init__(
        self, 
        logger: ILogger, 
        reader: ISheetReader,
        progress_callback: Optional[IProgressCallback] = None
    ):
        self.logger = logger
        self.reader = reader
        self.progress_callback = progress_callback
    
    def merge(self, files: List[SourceFile], options: ProcessingOptions) -> Any:
        """
        Merge files with optional performance optimizations and data processing
        
        Args:
            files: List of source files to merge
            options: Processing options (chunking, parallel, processors)
        
        Returns:
            Merged DataFrame
        
        Raises:
            Exception: If cancellation requested or processing fails
        """
        import pandas as pd
        
        self.logger.info("Starting merge process")
        
        # Check for early cancellation
        if self.progress_callback and self.progress_callback.should_cancel():
            raise Exception("Operation cancelled by user")
        
        if not files:
            self.logger.info("No files to merge")
            return pd.DataFrame()
        
        # Choose processing strategy
        if options.enable_parallel:
            self.logger.info(f"Using parallel processing with {options.max_workers} workers")
            all_data_frames = self._merge_parallel(files, options)
        else:
            self.logger.info("Using sequential processing")
            all_data_frames = self._merge_sequential(files, options)
        
        # Concatenate all DataFrames
        if not all_data_frames:
            self.logger.info("No data found to merge")
            return pd.DataFrame()
        
        result = pd.concat(all_data_frames, ignore_index=True)
        self.logger.info(f"Concatenated {len(all_data_frames)} DataFrames")
        
        # Apply data processors
        result = self._apply_processors(result, options)
        
        self.logger.info(f"Merge complete. Total rows: {len(result)}")
        return result
    
    def _merge_parallel(
        self, 
        files: List[SourceFile],
        options: ProcessingOptions
    ) -> List[Any]:
        """Process files in parallel using ThreadPoolExecutor"""
        from src.infrastructure.parallel_executor import ParallelMergeExecutor
        
        executor = ParallelMergeExecutor(max_workers=options.max_workers)
        
        def process_file(file: SourceFile) -> Any:
            return self._process_file(file, options)
        
        return executor.execute(files, process_file)
    
    def _merge_sequential(
        self, 
        files: List[SourceFile],
        options: ProcessingOptions
    ) -> List[Any]:
        """Process files one at a time"""
        all_data_frames = []
        
        for i, file in enumerate(files):
            # Check cancellation
            if self.progress_callback and self.progress_callback.should_cancel():
                raise Exception("Operation cancelled by user")
            
            # Report progress
            if self.progress_callback:
                state = ProgressState(
                    current_file=file.path.value,
                    files_completed=i,
                    total_files=len(files),
                    rows_processed=sum(len(df) for df in all_data_frames),
                    total_rows=0,  # Unknown until all files processed
                    percentage=(i / len(files)) * 100,
                    estimated_seconds_remaining=0.0
                )
                self.progress_callback.on_progress(state)
            
            df = self._process_file(file, options)
            all_data_frames.append(df)
        
        return all_data_frames
    
    def _process_file(
        self,
        file: SourceFile,
        options: ProcessingOptions
    ) -> Any:
        """Process a single file with all selected sheets"""
        import pandas as pd
        
        self.logger.info(f"Processing file: {file.path.value}")
        
        file_data_frames = []
        
        for sheet in file.selected_sheets:
            try:
                self.logger.info(f"  - Reading sheet: {sheet.value}")
                
                # Choose reading strategy
                if options.enable_chunking and file.requires_chunking():
                    self.logger.info(f"    Using chunked reading (chunk_size={options.chunk_size})")
                    df = self._read_sheet_chunked(file, sheet, options.chunk_size)
                else:
                    df = self.reader.read_sheet(file.path, sheet)
                
                # Add origin tracking
                df['Origin_File'] = file.path.value
                df['Origin_Sheet'] = sheet.value
                
                file_data_frames.append(df)
                
            except Exception as e:
                self.logger.error(f"Failed to read sheet {sheet.value}: {e}")
                raise
        
        # Concatenate sheets from this file
        if not file_data_frames:
            return pd.DataFrame()
        
        return pd.concat(file_data_frames, ignore_index=True)
    
    def _read_sheet_chunked(
        self,
        file: SourceFile,
        sheet,
        chunk_size: int
    ) -> Any:
        """Read sheet in chunks and concatenate"""
        import pandas as pd
        
        chunks = []
        for chunk in self.reader.read_sheet_chunked(file.path, sheet, chunk_size):
            chunks.append(chunk)
            
            # Check cancellation between chunks
            if self.progress_callback and self.progress_callback.should_cancel():
                raise Exception("Operation cancelled by user")
        
        return pd.concat(chunks, ignore_index=True)
    
    def _apply_processors(
        self,
        df: Any,
        options: ProcessingOptions
    ) -> Any:
        """Apply data processors in sequence"""
        from src.infrastructure.data_processors import (
            GroupByProcessor,
            DuplicateRemover,
            ColumnSelector
        )
        
        # Apply group by
        if options.group_by_config:
            self.logger.info("Applying group by processor")
            processor = GroupByProcessor(options.group_by_config)
            df = processor.process(df)
        
        # Apply duplicate removal
        if options.duplicate_removal_config:
            self.logger.info("Applying duplicate removal")
            processor = DuplicateRemover(options.duplicate_removal_config)
            df = processor.process(df)
        
        # Apply column selection
        if options.column_selection_config:
            # Validate that column selection is not empty
            if not options.column_selection_config.selected_columns:
                error_msg = "Column selection cannot be empty. Please select at least one column."
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
            self.logger.info("Applying column selection")
            processor = ColumnSelector(options.column_selection_config)
            df = processor.process(df)
        
        return df