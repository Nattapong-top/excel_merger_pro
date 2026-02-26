# Design Document: Performance Optimization and Data Processing

## Overview

This design extends Excel Merger Pro with performance optimization and data processing capabilities while maintaining strict adherence to DDD/Clean Architecture principles. The system will handle GB-sized files through chunk-based reading, process multiple files in parallel, provide real-time progress tracking, and offer data transformation features (group by, remove duplicates, column selection).

### Key Design Goals

1. **Memory Efficiency**: Process large files without loading entire datasets into memory
2. **Performance**: Leverage parallel processing to reduce merge operation time
3. **User Experience**: Provide real-time progress feedback and responsive UI
4. **Data Transformation**: Enable users to process data during merge operations
5. **Architecture Compliance**: Maintain clean separation between Domain, Application, Infrastructure, and UI layers

### Technology Stack

- **Chunk Reading**: openpyxl engine with pandas read_excel (chunksize parameter)
- **Parallel Processing**: concurrent.futures.ThreadPoolExecutor (max_workers=4)
- **Progress Tracking**: Callback mechanism with thread-safe queue
- **Data Processing**: pandas groupby, drop_duplicates, column indexing
- **Property Testing**: Hypothesis library (100+ iterations per property)

## Architecture

### Layer Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│                        UI Layer                              │
│  - ProcessingOptionsDialog                                   │
│  - ProgressDialog                                            │
│  - MainWindow (updated)                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ (calls)
┌──────────────────────▼──────────────────────────────────────┐
│                   Application Layer                          │
│  - MergeService (enhanced)                                   │
│  - ISheetReader (enhanced interface)                         │
│  - IProgressCallback (new interface)                         │
│  - IDataProcessor (new interface)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ (uses)
┌──────────────────────▼──────────────────────────────────────┐
│                    Domain Layer                              │
│  - ProcessingOptions (Value Object)                          │
│  - GroupByConfig (Value Object)                              │
│  - DuplicateRemovalConfig (Value Object)                     │
│  - ColumnSelectionConfig (Value Object)                      │
│  - ProgressState (Value Object)                              │
│  - SourceFile (Entity - enhanced)                            │
└──────────────────────┬──────────────────────────────────────┘
                       │ (implemented by)
┌──────────────────────▼──────────────────────────────────────┐
│                 Infrastructure Layer                         │
│  - ChunkedSheetReader (implements ISheetReader)              │
│  - ParallelMergeExecutor                                     │
│  - GroupByProcessor (implements IDataProcessor)              │
│  - DuplicateRemover (implements IDataProcessor)              │
│  - ColumnSelector (implements IDataProcessor)                │
│  - ThreadSafeProgressTracker (implements IProgressCallback)  │
└─────────────────────────────────────────────────────────────┘
```

### Dependency Flow

- UI Layer depends on Application Layer interfaces
- Application Layer depends on Domain Layer entities and value objects
- Infrastructure Layer implements Application Layer interfaces
- Domain Layer has no dependencies on other layers

### Key Architectural Decisions

1. **Chunk Reading Strategy**: Use openpyxl engine instead of default xlrd for better memory management with large files
2. **Parallel Processing Model**: ThreadPoolExecutor over ProcessPoolExecutor because pandas DataFrames are not easily picklable and thread overhead is acceptable for I/O-bound operations
3. **Progress Callback Pattern**: Use callback interface instead of polling to avoid tight coupling and enable real-time updates
4. **Data Processor Chain**: Implement processors as separate classes following Single Responsibility Principle, allowing flexible composition
5. **Value Object Validation**: All processing configurations validate their invariants at construction time, preventing invalid states

## Components and Interfaces

### Domain Layer Components

#### Value Objects

**ProcessingOptions**
```python
@dataclass(frozen=True)
class ProcessingOptions:
    enable_chunking: bool
    chunk_size: int
    enable_parallel: bool
    max_workers: int
    group_by_config: Optional[GroupByConfig]
    duplicate_removal_config: Optional[DuplicateRemovalConfig]
    column_selection_config: Optional[ColumnSelectionConfig]
    
    def __post_init__(self):
        # Validation rules
        if self.chunk_size < 1000 or self.chunk_size > 100000:
            raise ValueError("chunk_size must be between 1000 and 100000")
        if self.max_workers < 1 or self.max_workers > 8:
            raise ValueError("max_workers must be between 1 and 8")
        if self.enable_chunking and self.chunk_size < 1000:
            raise ValueError("chunk_size too small for chunking")
```

**GroupByConfig**
```python
@dataclass(frozen=True)
class GroupByConfig:
    group_columns: Tuple[str, ...]  # Columns to group by
    aggregations: Dict[str, str]     # {column: function} e.g., {"Amount": "sum"}
    
    VALID_FUNCTIONS = {"sum", "count", "mean", "min", "max", "first", "last"}
    
    def __post_init__(self):
        if not self.group_columns:
            raise ValueError("group_columns cannot be empty")
        if not self.aggregations:
            raise ValueError("aggregations cannot be empty")
        for func in self.aggregations.values():
            if func not in self.VALID_FUNCTIONS:
                raise ValueError(f"Invalid aggregation function: {func}")
```

**DuplicateRemovalConfig**
```python
@dataclass(frozen=True)
class DuplicateRemovalConfig:
    comparison_columns: Tuple[str, ...]
    keep: str  # "first" or "last"
    
    def __post_init__(self):
        if not self.comparison_columns:
            raise ValueError("comparison_columns cannot be empty")
        if self.keep not in ("first", "last"):
            raise ValueError("keep must be 'first' or 'last'")
```

**ColumnSelectionConfig**
```python
@dataclass(frozen=True)
class ColumnSelectionConfig:
    selected_columns: Tuple[str, ...]
    column_order: Tuple[str, ...]
    
    def __post_init__(self):
        if not self.selected_columns:
            raise ValueError("selected_columns cannot be empty")
        if set(self.column_order) != set(self.selected_columns):
            raise ValueError("column_order must contain exactly the selected_columns")
```

**ProgressState**
```python
@dataclass(frozen=True)
class ProgressState:
    current_file: str
    files_completed: int
    total_files: int
    rows_processed: int
    total_rows: int
    percentage: float
    estimated_seconds_remaining: float
    
    def __post_init__(self):
        if self.percentage < 0 or self.percentage > 100:
            raise ValueError("percentage must be between 0 and 100")
        if self.files_completed > self.total_files:
            raise ValueError("files_completed cannot exceed total_files")
```

#### Enhanced Entity

**SourceFile** (enhanced)
```python
@dataclass
class SourceFile:
    path: FilePath
    available_sheets: List[SheetName]
    selected_sheets: List[SheetName] = field(default_factory=list)
    file_size_bytes: int = 0  # NEW: for determining chunk strategy
    estimated_rows: int = 0    # NEW: for progress calculation
    
    def requires_chunking(self, threshold_mb: int = 100) -> bool:
        """Determine if file should be read in chunks"""
        return self.file_size_bytes > (threshold_mb * 1024 * 1024)
    
    def select_sheet(self, sheet: SheetName):
        if sheet not in self.available_sheets:
            raise ValueError(f"Sheet '{sheet.value}' not found")
        if sheet not in self.selected_sheets:
            self.selected_sheets.append(sheet)
    
    def select_all_sheets(self):
        self.selected_sheets = self.available_sheets.copy()
```

### Application Layer Interfaces

**IProgressCallback**
```python
class IProgressCallback(ABC):
    @abstractmethod
    def on_progress(self, state: ProgressState) -> None:
        """Called when progress updates"""
        pass
    
    @abstractmethod
    def should_cancel(self) -> bool:
        """Check if operation should be cancelled"""
        pass
```

**IDataProcessor**
```python
class IDataProcessor(ABC):
    @abstractmethod
    def process(self, df: Any) -> Any:
        """Process a DataFrame and return transformed DataFrame"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return processor name for logging"""
        pass
```

**ISheetReader** (enhanced)
```python
class ISheetReader(ABC):
    @abstractmethod
    def get_sheet_names(self, path: FilePath) -> List[SheetName]:
        pass
    
    @abstractmethod
    def read_sheet(self, path: FilePath, sheet_name: SheetName) -> Any:
        pass
    
    @abstractmethod
    def read_sheet_chunked(
        self, 
        path: FilePath, 
        sheet_name: SheetName, 
        chunk_size: int
    ) -> Iterator[Any]:
        """Read sheet in chunks, yielding DataFrames"""
        pass
    
    @abstractmethod
    def estimate_row_count(self, path: FilePath, sheet_name: SheetName) -> int:
        """Estimate total rows without loading entire file"""
        pass
```

### Application Layer Service

**MergeService** (enhanced)
```python
class MergeService:
    def __init__(
        self, 
        logger: ILogger, 
        reader: ISheetReader,
        progress_callback: Optional[IProgressCallback] = None
    ):
        self.logger = logger
        self.reader = reader
        self.progress_callback = progress_callback
    
    def merge(
        self, 
        files: List[SourceFile],
        options: ProcessingOptions
    ) -> Any:
        """
        Main merge orchestration with optional parallel processing
        """
        if options.enable_parallel:
            return self._merge_parallel(files, options)
        else:
            return self._merge_sequential(files, options)
    
    def _merge_parallel(
        self, 
        files: List[SourceFile],
        options: ProcessingOptions
    ) -> Any:
        """Use ThreadPoolExecutor for parallel file processing"""
        pass
    
    def _merge_sequential(
        self, 
        files: List[SourceFile],
        options: ProcessingOptions
    ) -> Any:
        """Process files one at a time"""
        pass
    
    def _process_file(
        self,
        file: SourceFile,
        options: ProcessingOptions
    ) -> Any:
        """Process a single file with all selected sheets"""
        pass
    
    def _apply_processors(
        self,
        df: Any,
        processors: List[IDataProcessor]
    ) -> Any:
        """Apply data processors in sequence"""
        for processor in processors:
            df = processor.process(df)
        return df
```

### Infrastructure Layer Components

**ChunkedSheetReader**
```python
class ChunkedSheetReader(ISheetReader):
    """
    Implements chunk-based reading using openpyxl engine
    """
    
    def read_sheet_chunked(
        self, 
        path: FilePath, 
        sheet_name: SheetName, 
        chunk_size: int
    ) -> Iterator[Any]:
        import pandas as pd
        
        # Use openpyxl engine for better memory management
        for chunk in pd.read_excel(
            path.value,
            sheet_name=sheet_name.value,
            engine='openpyxl',
            chunksize=chunk_size,
            dtype=str
        ):
            yield chunk
    
    def estimate_row_count(
        self, 
        path: FilePath, 
        sheet_name: SheetName
    ) -> int:
        """
        Use openpyxl to count rows without loading data
        """
        from openpyxl import load_workbook
        wb = load_workbook(path.value, read_only=True)
        ws = wb[sheet_name.value]
        return ws.max_row
```

**ParallelMergeExecutor**
```python
class ParallelMergeExecutor:
    """
    Manages parallel file processing using ThreadPoolExecutor
    """
    
    def __init__(self, max_workers: int):
        self.max_workers = max_workers
    
    def execute(
        self,
        files: List[SourceFile],
        process_func: Callable[[SourceFile], Any],
        progress_callback: Optional[IProgressCallback] = None
    ) -> List[Any]:
        """
        Process files in parallel and return list of DataFrames
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(process_func, file): file 
                for file in files
            }
            
            for future in as_completed(future_to_file):
                if progress_callback and progress_callback.should_cancel():
                    executor.shutdown(wait=False)
                    raise CancellationException("Operation cancelled by user")
                
                file = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    # Log error but continue processing other files
                    raise ProcessingException(f"Error processing {file.path.value}: {e}")
        
        return results
```

**GroupByProcessor**
```python
class GroupByProcessor(IDataProcessor):
    """
    Implements group by with aggregation using pandas groupby
    """
    
    def __init__(self, config: GroupByConfig):
        self.config = config
    
    def process(self, df: Any) -> Any:
        import pandas as pd
        
        # Group by specified columns
        grouped = df.groupby(list(self.config.group_columns))
        
        # Apply aggregations
        agg_dict = {}
        for col, func in self.config.aggregations.items():
            if col in df.columns:
                agg_dict[col] = func
        
        result = grouped.agg(agg_dict).reset_index()
        return result
    
    def get_name(self) -> str:
        return "GroupByProcessor"
```

**DuplicateRemover**
```python
class DuplicateRemover(IDataProcessor):
    """
    Removes duplicates using pandas drop_duplicates
    """
    
    def __init__(self, config: DuplicateRemovalConfig):
        self.config = config
    
    def process(self, df: Any) -> Any:
        import pandas as pd
        
        result = df.drop_duplicates(
            subset=list(self.config.comparison_columns),
            keep=self.config.keep
        )
        return result
    
    def get_name(self) -> str:
        return "DuplicateRemover"
```

**ColumnSelector**
```python
class ColumnSelector(IDataProcessor):
    """
    Selects and reorders columns using pandas column indexing
    """
    
    def __init__(self, config: ColumnSelectionConfig):
        self.config = config
    
    def process(self, df: Any) -> Any:
        import pandas as pd
        
        # Select only columns that exist in the DataFrame
        available_columns = [
            col for col in self.config.column_order 
            if col in df.columns
        ]
        
        result = df[available_columns]
        return result
    
    def get_name(self) -> str:
        return "ColumnSelector"
```

**ThreadSafeProgressTracker**
```python
class ThreadSafeProgressTracker(IProgressCallback):
    """
    Thread-safe progress tracking using queue
    """
    
    def __init__(self):
        from queue import Queue
        self._queue = Queue()
        self._cancel_flag = False
        self._lock = threading.Lock()
    
    def on_progress(self, state: ProgressState) -> None:
        self._queue.put(state)
    
    def should_cancel(self) -> bool:
        with self._lock:
            return self._cancel_flag
    
    def request_cancel(self) -> None:
        with self._lock:
            self._cancel_flag = True
    
    def get_latest_state(self) -> Optional[ProgressState]:
        """Non-blocking retrieval of latest progress state"""
        try:
            return self._queue.get_nowait()
        except:
            return None
```

### UI Layer Components

**ProcessingOptionsDialog**
```python
class ProcessingOptionsDialog(QDialog):
    """
    Dialog for configuring all processing options
    
    Features:
    - Checkboxes for enabling features
    - Expandable sections for feature configuration
    - Column selection with drag-and-drop reordering
    - Preset save/load functionality
    - Validation before proceeding
    """
    
    def __init__(self, available_columns: List[str], parent=None):
        super().__init__(parent)
        self.available_columns = available_columns
        self.setup_ui()
    
    def get_processing_options(self) -> ProcessingOptions:
        """Build ProcessingOptions from UI state"""
        pass
    
    def validate_options(self) -> bool:
        """Validate that configuration is valid"""
        pass
```

**ProgressDialog**
```python
class ProgressDialog(QDialog):
    """
    Non-blocking progress dialog with real-time updates
    
    Features:
    - Progress bar with percentage
    - Current file name display
    - Estimated time remaining
    - Cancel button
    - Updates every 500ms via QTimer
    """
    
    def __init__(self, tracker: ThreadSafeProgressTracker, parent=None):
        super().__init__(parent)
        self.tracker = tracker
        self.setup_ui()
        self.start_timer()
    
    def start_timer(self):
        """Start QTimer for periodic UI updates"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(500)  # Update every 500ms
    
    def update_progress(self):
        """Pull latest progress state and update UI"""
        state = self.tracker.get_latest_state()
        if state:
            self.progress_bar.setValue(int(state.percentage))
            self.file_label.setText(state.current_file)
            self.eta_label.setText(f"ETA: {state.estimated_seconds_remaining:.0f}s")
    
    def on_cancel_clicked(self):
        """Request cancellation"""
        self.tracker.request_cancel()
```

## Data Models

### Processing Configuration Flow

```
User Input (UI)
    ↓
ProcessingOptionsDialog
    ↓
ProcessingOptions (Value Object)
    ├─ GroupByConfig
    ├─ DuplicateRemovalConfig
    └─ ColumnSelectionConfig
    ↓
MergeService
    ↓
Infrastructure Processors
    ├─ GroupByProcessor
    ├─ DuplicateRemover
    └─ ColumnSelector
    ↓
Transformed DataFrame
```

### Progress Tracking Flow

```
MergeService (Worker Thread)
    ↓
ProgressState (Value Object)
    ↓
ThreadSafeProgressTracker.on_progress()
    ↓
Thread-Safe Queue
    ↓
ProgressDialog.update_progress() (UI Thread via QTimer)
    ↓
UI Update
```

### Chunk Processing Flow

```
ChunkedSheetReader.read_sheet_chunked()
    ↓
Iterator[DataFrame] (chunks)
    ↓
For each chunk:
    ├─ Apply processors
    ├─ Update progress
    └─ Accumulate results
    ↓
pd.concat(all_chunks)
    ↓
Final DataFrame
```

### Data Transformation Pipeline

```
Raw DataFrame
    ↓
[Optional] GroupByProcessor
    ↓ (grouped and aggregated)
[Optional] DuplicateRemover
    ↓ (duplicates removed)
[Optional] ColumnSelector
    ↓ (columns filtered and reordered)
Final DataFrame
    ↓
Save to Excel
```

### Memory Management Strategy

For files requiring chunking:
1. Read chunk (10,000 rows)
2. Apply all processors to chunk
3. Append to temporary list
4. Release chunk memory
5. Repeat until file complete
6. Concatenate all processed chunks
7. Maximum memory per file: ~500MB

For parallel processing:
- Each worker thread processes one file
- Maximum concurrent files: 4
- Total memory cap: ~2GB (4 files × 500MB)


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Chunked Reading Equivalence

*For any* Excel file and sheet, reading the file in chunks and concatenating the results should produce a DataFrame equivalent to reading the entire file at once.

**Validates: Requirements 1.3, 1.4**

### Property 2: Parallel Processing Equivalence

*For any* set of source files and processing options, merging files in parallel should produce the same result as merging them sequentially.

**Validates: Requirements 2.4**

### Property 3: Progress State Validity

*For any* progress state during a merge operation, the current file name should be non-empty, percentage should be between 0 and 100, and files_completed should not exceed total_files.

**Validates: Requirements 3.3**

### Property 4: Progress ETA Calculation

*For any* progress state with known rows processed and processing rate, the estimated time remaining should equal (total_rows - rows_processed) / processing_rate.

**Validates: Requirements 3.4**

### Property 5: Group By Uniqueness

*For any* DataFrame and set of grouping columns, after applying group by, each unique combination of values in the grouping columns should appear exactly once.

**Validates: Requirements 4.2**

### Property 6: Aggregation Function Correctness

*For any* DataFrame, grouping columns, and valid aggregation function, the aggregation should be applied to all non-grouping numeric columns and produce mathematically correct results (e.g., sum of grouped values equals sum of original values).

**Validates: Requirements 4.3, 4.4**

### Property 7: Duplicate Detection Accuracy

*For any* DataFrame and set of comparison columns, rows identified as duplicates should have identical values in all comparison columns.

**Validates: Requirements 5.2**

### Property 8: Duplicate Removal Keep Strategy

*For any* DataFrame with duplicates, when keep="first" is specified, the first occurrence of each duplicate set should be retained, and when keep="last", the last occurrence should be retained.

**Validates: Requirements 5.3**

### Property 9: Duplicate Count Consistency

*For any* DataFrame and duplicate removal operation, the count of rows removed should equal the original row count minus the final row count.

**Validates: Requirements 5.4, 5.5**

### Property 10: Non-Duplicate Order Preservation

*For any* DataFrame and duplicate removal operation, the relative order of rows that are not duplicates should be preserved in the output.

**Validates: Requirements 5.6**

### Property 11: Column Selection Inclusion

*For any* DataFrame and set of selected columns, the output DataFrame should contain exactly the selected columns that exist in the input DataFrame.

**Validates: Requirements 6.2**

### Property 12: Column Order Preservation

*For any* DataFrame and specified column order, the output DataFrame should have columns in exactly the specified order.

**Validates: Requirements 6.3, 6.5**

### Property 13: Column Union Completeness

*For any* set of DataFrames with different column sets, the union of all columns should contain every unique column that appears in at least one DataFrame.

**Validates: Requirements 6.6**

### Property 14: Processing Options Validation

*For any* ProcessingOptions configuration where group by or duplicate removal is enabled, if no columns are specified, the value object construction should raise a ValueError.

**Validates: Requirements 7.4**

### Property 15: Configuration Preset Round Trip

*For any* valid ProcessingOptions configuration, saving it as a preset and then loading it should produce an equivalent configuration.

**Validates: Requirements 7.5**

### Property 16: Cancellation Stops Processing

*For any* merge operation in progress, when cancellation is requested, the operation should stop and no further files should be processed.

**Validates: Requirements 8.3**

### Property 17: Cancellation Cleanup

*For any* merge operation that is cancelled, no partial output files should exist after cancellation completes.

**Validates: Requirements 8.4**

### Property 18: Value Object Invariant Validation

*For any* invalid configuration (e.g., chunk_size < 1000, max_workers > 8, empty group_columns), constructing the corresponding value object should raise a ValueError.

**Validates: Requirements 10.4**

### Property 19: File Read Error Handling

*For any* file that cannot be read, the system should raise an exception with a message identifying the problematic file.

**Validates: Requirements 12.1**

### Property 20: Aggregation Type Error Handling

*For any* aggregation function applied to an incompatible column type (e.g., sum on text column), the system should raise an exception identifying the column and type mismatch.

**Validates: Requirements 12.2**

### Property 21: Parallel Processing Error Isolation

*For any* set of files where one file fails to process, the remaining files should continue processing and produce valid results.

**Validates: Requirements 12.4**

### Property 22: Source File Preservation

*For any* processing error that occurs, all source files should remain unmodified (same content and modification timestamp).

**Validates: Requirements 12.5**

## Error Handling

### Error Categories

**File Reading Errors**
- Invalid file format
- Corrupted file
- File not found
- Permission denied
- Sheet not found

**Processing Errors**
- Type mismatch in aggregation
- Invalid column names
- Memory exhaustion
- Cancellation by user

**Configuration Errors**
- Invalid chunk size
- Invalid max workers
- Empty column selection
- Invalid aggregation function

### Error Handling Strategy

1. **Value Object Validation**: All configuration errors are caught at construction time through value object validation, preventing invalid states from propagating through the system.

2. **File-Level Error Isolation**: In parallel processing mode, errors in one file do not affect processing of other files. Failed files are logged and skipped.

3. **Graceful Degradation**: If chunked reading fails, the system falls back to standard reading. If parallel processing fails, the system falls back to sequential processing.

4. **User-Friendly Messages**: All errors are translated to user-friendly messages in the selected language, with specific details about what went wrong and suggested remediation.

5. **Resource Cleanup**: All errors trigger proper resource cleanup (closing file handles, releasing memory, cancelling pending tasks).

### Error Propagation

```
Infrastructure Layer (raises specific exceptions)
    ↓
Application Layer (catches, logs, wraps in domain exceptions)
    ↓
UI Layer (catches, displays user-friendly message)
```

### Exception Hierarchy

```python
class MergeException(Exception):
    """Base exception for merge operations"""
    pass

class FileReadException(MergeException):
    """Error reading source file"""
    def __init__(self, file_path: str, reason: str):
        self.file_path = file_path
        self.reason = reason
        super().__init__(f"Cannot read {file_path}: {reason}")

class ProcessingException(MergeException):
    """Error during data processing"""
    def __init__(self, processor_name: str, reason: str):
        self.processor_name = processor_name
        self.reason = reason
        super().__init__(f"{processor_name} failed: {reason}")

class CancellationException(MergeException):
    """Operation cancelled by user"""
    pass

class ConfigurationException(MergeException):
    """Invalid configuration"""
    pass
```

## Testing Strategy

### Dual Testing Approach

This feature requires both unit tests and property-based tests to ensure comprehensive coverage:

**Unit Tests** focus on:
- Specific examples of chunk reading with known data
- UI dialog initialization and interaction
- Progress callback mechanism
- Error message formatting
- Language switching behavior
- Specific edge cases (empty files, single row, single column)

**Property-Based Tests** focus on:
- Universal properties that hold for all inputs
- Equivalence properties (chunked vs non-chunked, parallel vs sequential)
- Invariant preservation (order, data integrity)
- Validation rules for value objects
- Error handling across random inputs

Together, these approaches provide comprehensive coverage: unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across a wide range of inputs.

### Property-Based Testing Configuration

**Library**: Hypothesis for Python

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with comment referencing design property
- Tag format: `# Feature: performance-optimization-data-processing, Property {number}: {property_text}`

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st
import pandas as pd

# Feature: performance-optimization-data-processing, Property 1: Chunked Reading Equivalence
@given(
    data=st.lists(
        st.dictionaries(
            keys=st.text(min_size=1, max_size=10),
            values=st.text(min_size=0, max_size=100)
        ),
        min_size=1000,
        max_size=50000
    )
)
def test_chunked_reading_equivalence(data):
    """For any Excel file, chunked reading should equal full reading"""
    # Create temporary Excel file
    df_original = pd.DataFrame(data)
    
    # Read normally
    df_full = reader.read_sheet(file_path, sheet_name)
    
    # Read in chunks
    chunks = list(reader.read_sheet_chunked(file_path, sheet_name, chunk_size=10000))
    df_chunked = pd.concat(chunks, ignore_index=True)
    
    # Assert equivalence
    pd.testing.assert_frame_equal(df_full, df_chunked)
```

### Test Coverage Requirements

**Domain Layer** (100% coverage target):
- All value object validation rules
- Entity business logic
- Invariant preservation

**Application Layer** (90% coverage target):
- Service orchestration logic
- Interface contracts
- Error handling paths

**Infrastructure Layer** (80% coverage target):
- Chunk reading implementation
- Parallel execution
- Data processor implementations
- Progress tracking

**UI Layer** (60% coverage target):
- Dialog initialization
- User input validation
- Event handlers
- Focus on logic, not Qt framework code

### Integration Tests

**End-to-End Scenarios**:
1. Merge 3 large files (>100MB each) with chunking and parallel processing
2. Merge with group by and duplicate removal
3. Merge with column selection and reordering
4. Merge with all processing options enabled
5. Cancel operation mid-processing
6. Handle file read errors gracefully
7. Switch language during operation

**Performance Benchmarks**:
- Baseline: Merge 5 files (500MB total) without optimization
- With chunking: Same files with chunk reading enabled
- With parallel: Same files with 4 worker threads
- Combined: Chunking + parallel processing
- Target: 50% reduction in processing time

### Mock Strategy

**Mock External Dependencies**:
- File system operations (for testing error handling)
- Excel file reading (for testing chunk boundaries)
- Thread pool executor (for testing parallel coordination)

**Do Not Mock**:
- pandas operations (test against real pandas)
- Value object validation (test real validation logic)
- Data processors (test real implementations)

### Test Data Strategy

**Property Test Generators**:
- Random DataFrames with various shapes (1-10000 rows, 1-100 columns)
- Random column names (ASCII, Unicode, special characters)
- Random data types (strings, numbers, dates, mixed)
- Random configurations (all valid combinations of options)

**Fixed Test Data**:
- Small example files (10 rows) for unit tests
- Edge cases (empty, single row, single column)
- Known problematic data (duplicates, nulls, special characters)

### Continuous Integration

**Pre-commit Hooks**:
- Run unit tests (fast feedback)
- Run linting and type checking

**CI Pipeline**:
- Run all unit tests
- Run property tests (100 iterations)
- Run integration tests
- Generate coverage report
- Run performance benchmarks (on main branch only)

**Performance Regression Detection**:
- Track merge time for standard dataset
- Alert if performance degrades by >10%
- Store benchmark results for trend analysis
