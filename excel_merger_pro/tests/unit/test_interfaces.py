# File: tests/unit/test_interfaces.py
"""
Unit tests for Application Layer Interfaces

Tests verify that interfaces can be implemented correctly
and that implementations follow the contract.
"""

import pytest
from src.application.interfaces import IProgressCallback, IDataProcessor, ISheetReader
from src.domain.processing_options import ProgressState
from src.domain.value_objects import FilePath, SheetName


class TestIProgressCallback:
    """Test IProgressCallback interface implementation"""
    
    def test_can_implement_interface(self):
        """Should be able to create a concrete implementation"""
        
        class MockProgressCallback(IProgressCallback):
            def __init__(self):
                self.states = []
                self.cancel_requested = False
            
            def on_progress(self, state: ProgressState) -> None:
                self.states.append(state)
            
            def should_cancel(self) -> bool:
                return self.cancel_requested
        
        callback = MockProgressCallback()
        assert callback is not None
        assert isinstance(callback, IProgressCallback)
    
    def test_on_progress_receives_state(self):
        """on_progress should receive and store ProgressState"""
        
        class MockProgressCallback(IProgressCallback):
            def __init__(self):
                self.states = []
            
            def on_progress(self, state: ProgressState) -> None:
                self.states.append(state)
            
            def should_cancel(self) -> bool:
                return False
        
        callback = MockProgressCallback()
        state = ProgressState(
            current_file="test.xlsx",
            files_completed=1,
            total_files=5,
            rows_processed=1000,
            total_rows=5000,
            percentage=20.0,
            estimated_seconds_remaining=40.0
        )
        
        callback.on_progress(state)
        
        assert len(callback.states) == 1
        assert callback.states[0].current_file == "test.xlsx"
        assert callback.states[0].percentage == 20.0
    
    def test_should_cancel_returns_boolean(self):
        """should_cancel should return True or False"""
        
        class MockProgressCallback(IProgressCallback):
            def __init__(self, cancel_flag: bool):
                self.cancel_flag = cancel_flag
            
            def on_progress(self, state: ProgressState) -> None:
                pass
            
            def should_cancel(self) -> bool:
                return self.cancel_flag
        
        callback_continue = MockProgressCallback(cancel_flag=False)
        callback_cancel = MockProgressCallback(cancel_flag=True)
        
        assert callback_continue.should_cancel() is False
        assert callback_cancel.should_cancel() is True
    
    def test_multiple_progress_updates(self):
        """Should handle multiple progress updates"""
        
        class MockProgressCallback(IProgressCallback):
            def __init__(self):
                self.states = []
            
            def on_progress(self, state: ProgressState) -> None:
                self.states.append(state)
            
            def should_cancel(self) -> bool:
                return False
        
        callback = MockProgressCallback()
        
        # Simulate multiple progress updates
        for i in range(5):
            state = ProgressState(
                current_file=f"file{i}.xlsx",
                files_completed=i,
                total_files=5,
                rows_processed=i * 1000,
                total_rows=5000,
                percentage=i * 20.0,
                estimated_seconds_remaining=(5 - i) * 10.0
            )
            callback.on_progress(state)
        
        assert len(callback.states) == 5
        assert callback.states[0].percentage == 0.0
        assert callback.states[4].percentage == 80.0


class TestIDataProcessor:
    """Test IDataProcessor interface implementation"""
    
    def test_can_implement_interface(self):
        """Should be able to create a concrete implementation"""
        
        class MockDataProcessor(IDataProcessor):
            def process(self, df):
                return df
            
            def get_name(self) -> str:
                return "MockProcessor"
        
        processor = MockDataProcessor()
        assert processor is not None
        assert isinstance(processor, IDataProcessor)
    
    def test_process_receives_and_returns_data(self):
        """process should receive data and return processed data"""
        
        class DoubleValueProcessor(IDataProcessor):
            """Processor that doubles all values"""
            
            def process(self, df):
                # Simple transformation for testing
                return [x * 2 for x in df]
            
            def get_name(self) -> str:
                return "DoubleValueProcessor"
        
        processor = DoubleValueProcessor()
        input_data = [1, 2, 3, 4, 5]
        result = processor.process(input_data)
        
        assert result == [2, 4, 6, 8, 10]
    
    def test_get_name_returns_string(self):
        """get_name should return processor name"""
        
        class TestProcessor(IDataProcessor):
            def process(self, df):
                return df
            
            def get_name(self) -> str:
                return "TestProcessor"
        
        processor = TestProcessor()
        assert processor.get_name() == "TestProcessor"
        assert isinstance(processor.get_name(), str)
    
    def test_processor_chain(self):
        """Multiple processors should be chainable"""
        
        class AddOneProcessor(IDataProcessor):
            def process(self, df):
                return [x + 1 for x in df]
            
            def get_name(self) -> str:
                return "AddOneProcessor"
        
        class MultiplyTwoProcessor(IDataProcessor):
            def process(self, df):
                return [x * 2 for x in df]
            
            def get_name(self) -> str:
                return "MultiplyTwoProcessor"
        
        # Chain processors
        processors = [AddOneProcessor(), MultiplyTwoProcessor()]
        
        input_data = [1, 2, 3]
        result = input_data
        
        for processor in processors:
            result = processor.process(result)
        
        # [1,2,3] -> AddOne -> [2,3,4] -> MultiplyTwo -> [4,6,8]
        assert result == [4, 6, 8]
    
    def test_identity_processor(self):
        """Processor that returns data unchanged"""
        
        class IdentityProcessor(IDataProcessor):
            def process(self, df):
                return df
            
            def get_name(self) -> str:
                return "IdentityProcessor"
        
        processor = IdentityProcessor()
        input_data = [1, 2, 3, 4, 5]
        result = processor.process(input_data)
        
        assert result == input_data
        assert result is input_data  # Same object


class TestISheetReader:
    """Test ISheetReader interface implementation"""
    
    def test_can_implement_interface(self):
        """Should be able to create a concrete implementation"""
        
        class MockSheetReader(ISheetReader):
            def get_sheet_names(self, path):
                return [SheetName("Sheet1")]
            
            def read_sheet(self, path, sheet_name):
                return {"data": "mock"}
            
            def read_sheet_chunked(self, path, sheet_name, chunk_size):
                yield {"chunk": 1}
                yield {"chunk": 2}
            
            def estimate_row_count(self, path, sheet_name):
                return 1000
        
        reader = MockSheetReader()
        assert reader is not None
        assert isinstance(reader, ISheetReader)
    
    def test_read_sheet_chunked_yields_chunks(self):
        """read_sheet_chunked should yield multiple chunks"""
        
        class MockSheetReader(ISheetReader):
            def get_sheet_names(self, path):
                return []
            
            def read_sheet(self, path, sheet_name):
                return None
            
            def read_sheet_chunked(self, path, sheet_name, chunk_size):
                # Simulate 3 chunks
                for i in range(3):
                    yield {"chunk_id": i, "rows": list(range(i * chunk_size, (i + 1) * chunk_size))}
            
            def estimate_row_count(self, path, sheet_name):
                return 0
        
        reader = MockSheetReader()
        path = FilePath("test.xlsx")
        sheet = SheetName("Sheet1")
        
        chunks = list(reader.read_sheet_chunked(path, sheet, chunk_size=10))
        
        assert len(chunks) == 3
        assert chunks[0]["chunk_id"] == 0
        assert chunks[1]["chunk_id"] == 1
        assert chunks[2]["chunk_id"] == 2
    
    def test_estimate_row_count_returns_int(self):
        """estimate_row_count should return integer"""
        
        class MockSheetReader(ISheetReader):
            def get_sheet_names(self, path):
                return []
            
            def read_sheet(self, path, sheet_name):
                return None
            
            def read_sheet_chunked(self, path, sheet_name, chunk_size):
                yield {}
            
            def estimate_row_count(self, path, sheet_name):
                return 5000
        
        reader = MockSheetReader()
        path = FilePath("test.xlsx")
        sheet = SheetName("Sheet1")
        
        count = reader.estimate_row_count(path, sheet)
        
        assert count == 5000
        assert isinstance(count, int)


class TestInterfaceContracts:
    """Test that interfaces enforce their contracts"""
    
    def test_cannot_instantiate_abstract_class(self):
        """Cannot create instance of abstract interface"""
        
        with pytest.raises(TypeError):
            IProgressCallback()  # Should raise TypeError
        
        with pytest.raises(TypeError):
            IDataProcessor()  # Should raise TypeError
        
        with pytest.raises(TypeError):
            ISheetReader()  # Should raise TypeError
    
    def test_incomplete_implementation_fails(self):
        """Implementation missing required methods should fail"""
        
        with pytest.raises(TypeError):
            # Missing should_cancel method
            class IncompleteCallback(IProgressCallback):
                def on_progress(self, state: ProgressState) -> None:
                    pass
            
            IncompleteCallback()
    
    def test_complete_implementation_succeeds(self):
        """Complete implementation should succeed"""
        
        class CompleteCallback(IProgressCallback):
            def on_progress(self, state: ProgressState) -> None:
                pass
            
            def should_cancel(self) -> bool:
                return False
        
        callback = CompleteCallback()
        assert callback is not None
