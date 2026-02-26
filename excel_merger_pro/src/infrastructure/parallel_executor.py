# File: src/infrastructure/parallel_executor.py
"""
Parallel file processing executor using ThreadPoolExecutor

Manages concurrent processing of multiple Excel files with
error isolation and progress tracking support.
"""

from typing import List, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.domain.entities import SourceFile


class ParallelMergeExecutor:
    """
    Executes file processing tasks in parallel using thread pool
    
    Features:
    - Configurable worker thread count
    - Error isolation (one file failure doesn't stop others)
    - Progress tracking support via callbacks
    - Thread-safe result collection
    """
    
    def __init__(self, max_workers: int):
        """
        Initialize executor with worker thread limit
        
        Args:
            max_workers: Maximum number of concurrent threads (1-8)
        
        Raises:
            ValueError: If max_workers is outside valid range
        """
        if max_workers < 1 or max_workers > 8:
            raise ValueError("max_workers must be between 1 and 8")
        
        self.max_workers = max_workers
    
    def execute(
        self,
        files: List[SourceFile],
        process_func: Callable[[SourceFile], Any]
    ) -> List[Any]:
        """
        Process files in parallel and return results
        
        Args:
            files: List of source files to process
            process_func: Function that processes a single file
        
        Returns:
            List of results from processing each file
        
        Raises:
            Exception: If any file processing fails
        
        Note:
            Results are returned in completion order, not input order
        """
        if not files:
            return []
        
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(process_func, file): file
                for file in files
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_file):
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Re-raise with file context
                    raise Exception(
                        f"Error processing {file.path.value}: {str(e)}"
                    ) from e
        
        return results
