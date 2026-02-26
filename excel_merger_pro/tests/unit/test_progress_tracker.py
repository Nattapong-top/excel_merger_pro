# File: tests/unit/test_progress_tracker.py
"""
Unit tests for ThreadSafeProgressTracker

Tests thread-safe progress tracking with queue-based communication
and cancellation support.
"""

import pytest
import threading
import time
from src.domain.processing_options import ProgressState
from src.infrastructure.progress_tracker import ThreadSafeProgressTracker


class TestThreadSafeProgressTracker:
    """Test thread-safe progress tracking"""
    
    def test_initial_state_not_cancelled(self):
        """Test that tracker starts in non-cancelled state"""
        tracker = ThreadSafeProgressTracker()
        
        assert tracker.should_cancel() is False
    
    def test_request_cancel_sets_flag(self):
        """Test that request_cancel sets cancellation flag"""
        tracker = ThreadSafeProgressTracker()
        
        tracker.request_cancel()
        
        assert tracker.should_cancel() is True
    
    def test_on_progress_stores_state(self):
        """Test that on_progress stores progress state"""
        tracker = ThreadSafeProgressTracker()
        
        state = ProgressState(
            current_file="test.xlsx",
            files_completed=1,
            total_files=5,
            rows_processed=100,
            total_rows=500,
            percentage=20.0,
            estimated_seconds_remaining=40.0
        )
        
        tracker.on_progress(state)
        
        retrieved = tracker.get_latest_state()
        assert retrieved is not None
        assert retrieved.current_file == "test.xlsx"
        assert retrieved.percentage == 20.0
    
    def test_get_latest_state_returns_none_when_empty(self):
        """Test that get_latest_state returns None when queue is empty"""
        tracker = ThreadSafeProgressTracker()
        
        state = tracker.get_latest_state()
        
        assert state is None
    
    def test_multiple_progress_updates(self):
        """Test multiple progress updates"""
        tracker = ThreadSafeProgressTracker()
        
        for i in range(5):
            state = ProgressState(
                current_file=f"file_{i}.xlsx",
                files_completed=i,
                total_files=5,
                rows_processed=i * 100,
                total_rows=500,
                percentage=i * 20.0,
                estimated_seconds_remaining=50.0 - i * 10
            )
            tracker.on_progress(state)
        
        # Should be able to retrieve all states
        states = []
        while True:
            state = tracker.get_latest_state()
            if state is None:
                break
            states.append(state)
        
        assert len(states) == 5
        assert states[0].current_file == "file_0.xlsx"
        assert states[4].current_file == "file_4.xlsx"
    
    def test_thread_safe_progress_updates(self):
        """Test that progress updates are thread-safe"""
        tracker = ThreadSafeProgressTracker()
        
        def worker(thread_id):
            for i in range(10):
                state = ProgressState(
                    current_file=f"thread_{thread_id}_file_{i}.xlsx",
                    files_completed=i,
                    total_files=10,
                    rows_processed=i * 10,
                    total_rows=100,
                    percentage=i * 10.0,
                    estimated_seconds_remaining=10.0 - i
                )
                tracker.on_progress(state)
                time.sleep(0.001)  # Small delay
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        # Should have 30 states (3 threads × 10 updates)
        states = []
        while True:
            state = tracker.get_latest_state()
            if state is None:
                break
            states.append(state)
        
        assert len(states) == 30
    
    def test_thread_safe_cancellation(self):
        """Test that cancellation is thread-safe"""
        tracker = ThreadSafeProgressTracker()
        
        def worker():
            time.sleep(0.01)
            tracker.request_cancel()
        
        threads = [threading.Thread(target=worker) for _ in range(5)]
        
        for t in threads:
            t.start()
        
        for t in threads:
            t.join()
        
        assert tracker.should_cancel() is True
    
    def test_cancel_during_progress_updates(self):
        """Test cancellation while progress updates are happening"""
        tracker = ThreadSafeProgressTracker()
        cancel_detected = []
        
        def progress_worker():
            for i in range(20):
                if tracker.should_cancel():
                    cancel_detected.append(True)
                    break
                
                state = ProgressState(
                    current_file=f"file_{i}.xlsx",
                    files_completed=i,
                    total_files=20,
                    rows_processed=i * 50,
                    total_rows=1000,
                    percentage=i * 5.0,
                    estimated_seconds_remaining=100.0 - i * 5
                )
                tracker.on_progress(state)
                time.sleep(0.01)
        
        def cancel_worker():
            time.sleep(0.05)
            tracker.request_cancel()
        
        progress_thread = threading.Thread(target=progress_worker)
        cancel_thread = threading.Thread(target=cancel_worker)
        
        progress_thread.start()
        cancel_thread.start()
        
        progress_thread.join()
        cancel_thread.join()
        
        assert len(cancel_detected) > 0
        assert tracker.should_cancel() is True
    
    def test_get_latest_state_non_blocking(self):
        """Test that get_latest_state doesn't block"""
        tracker = ThreadSafeProgressTracker()
        
        start = time.time()
        state = tracker.get_latest_state()
        elapsed = time.time() - start
        
        assert state is None
        assert elapsed < 0.01  # Should be nearly instant
    
    def test_progress_state_fifo_order(self):
        """Test that states are retrieved in FIFO order"""
        tracker = ThreadSafeProgressTracker()
        
        states_sent = []
        for i in range(5):
            state = ProgressState(
                current_file=f"file_{i}.xlsx",
                files_completed=i,
                total_files=5,
                rows_processed=i * 100,
                total_rows=500,
                percentage=i * 20.0,
                estimated_seconds_remaining=50.0 - i * 10
            )
            states_sent.append(state)
            tracker.on_progress(state)
        
        states_received = []
        while True:
            state = tracker.get_latest_state()
            if state is None:
                break
            states_received.append(state)
        
        assert len(states_received) == 5
        for i in range(5):
            assert states_received[i].current_file == states_sent[i].current_file
