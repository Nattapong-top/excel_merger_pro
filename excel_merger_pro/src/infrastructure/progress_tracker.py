# File: src/infrastructure/progress_tracker.py
"""
Thread-safe progress tracking for merge operations

Uses queue for thread-safe communication between worker threads
and UI thread, with cancellation support.
"""

import threading
from queue import Queue, Empty
from typing import Optional

from src.application.interfaces import IProgressCallback
from src.domain.processing_options import ProgressState


class ThreadSafeProgressTracker(IProgressCallback):
    """
    Thread-safe progress tracker using queue-based communication
    
    Features:
    - Non-blocking progress state retrieval
    - Thread-safe cancellation flag
    - FIFO queue for progress updates
    - No polling required
    """
    
    def __init__(self):
        """Initialize tracker with empty queue and no cancellation"""
        self._queue: Queue = Queue()
        self._cancel_flag: bool = False
        self._lock: threading.Lock = threading.Lock()
    
    def on_progress(self, state: ProgressState) -> None:
        """
        Store progress state in queue (called from worker thread)
        
        Args:
            state: Current progress state
        
        Note:
            This method is thread-safe and non-blocking
        """
        self._queue.put(state)
    
    def should_cancel(self) -> bool:
        """
        Check if cancellation has been requested (called from worker thread)
        
        Returns:
            True if cancellation requested, False otherwise
        
        Note:
            This method is thread-safe
        """
        with self._lock:
            return self._cancel_flag
    
    def request_cancel(self) -> None:
        """
        Request cancellation of operation (called from UI thread)
        
        Note:
            This method is thread-safe
        """
        with self._lock:
            self._cancel_flag = True
    
    def get_latest_state(self) -> Optional[ProgressState]:
        """
        Retrieve latest progress state from queue (called from UI thread)
        
        Returns:
            Latest ProgressState if available, None if queue is empty
        
        Note:
            This method is non-blocking and thread-safe
        """
        try:
            return self._queue.get_nowait()
        except Empty:
            return None
