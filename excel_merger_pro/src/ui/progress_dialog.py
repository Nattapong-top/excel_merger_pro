# File: src/ui/progress_dialog.py
"""
Progress dialog for displaying real-time merge operation progress

Shows progress bar, current file, estimated time remaining,
and provides cancellation support.
"""

import customtkinter as ctk
from typing import Optional
from src.infrastructure.progress_tracker import ThreadSafeProgressTracker


class ProgressDialog(ctk.CTkToplevel):
    """
    Non-blocking progress dialog with real-time updates
    
    Features:
    - Progress bar with percentage
    - Current file name display
    - Estimated time remaining
    - Cancel button
    - Auto-updates every 500ms
    """
    
    def __init__(self, parent, tracker: ThreadSafeProgressTracker, title: str = "Processing"):
        """
        Initialize progress dialog
        
        Args:
            parent: Parent window
            tracker: ThreadSafeProgressTracker for progress updates
            title: Dialog title
        """
        super().__init__(parent)
        
        self.tracker = tracker
        self.cancelled = False
        
        # Window configuration
        self.title(title)
        self.geometry("500x200")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 200) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
        self._start_timer()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Current file label
        self.file_label = ctk.CTkLabel(
            main_frame,
            text="Initializing...",
            font=("Arial", 12)
        )
        self.file_label.pack(pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(main_frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        # Percentage label
        self.percentage_label = ctk.CTkLabel(
            main_frame,
            text="0%",
            font=("Arial", 14, "bold")
        )
        self.percentage_label.pack(pady=5)
        
        # ETA label
        self.eta_label = ctk.CTkLabel(
            main_frame,
            text="Calculating...",
            font=("Arial", 10)
        )
        self.eta_label.pack(pady=5)
        
        # Cancel button
        self.cancel_button = ctk.CTkButton(
            main_frame,
            text="Cancel",
            command=self._on_cancel_clicked,
            fg_color="red",
            hover_color="darkred"
        )
        self.cancel_button.pack(pady=(10, 0))
    
    def _start_timer(self):
        """Start periodic UI updates"""
        self._update_progress()
    
    def _update_progress(self):
        """Pull latest progress state and update UI"""
        if self.cancelled:
            return
        
        state = self.tracker.get_latest_state()
        if state:
            # Update progress bar
            progress_value = state.percentage / 100.0
            self.progress_bar.set(progress_value)
            
            # Update labels
            self.percentage_label.configure(text=f"{state.percentage:.1f}%")
            
            # Update current file
            file_name = state.current_file.split('/')[-1].split('\\')[-1]
            self.file_label.configure(
                text=f"Processing: {file_name} ({state.files_completed}/{state.total_files})"
            )
            
            # Update ETA
            if state.estimated_seconds_remaining > 0:
                minutes = int(state.estimated_seconds_remaining // 60)
                seconds = int(state.estimated_seconds_remaining % 60)
                if minutes > 0:
                    eta_text = f"ETA: {minutes}m {seconds}s"
                else:
                    eta_text = f"ETA: {seconds}s"
                self.eta_label.configure(text=eta_text)
            else:
                self.eta_label.configure(text="Almost done...")
        
        # Schedule next update (500ms)
        if not self.cancelled:
            self.after(500, self._update_progress)
    
    def _on_cancel_clicked(self):
        """Handle cancel button click"""
        self.cancelled = True
        self.tracker.request_cancel()
        self.cancel_button.configure(state="disabled", text="Cancelling...")
        self.file_label.configure(text="Cancelling operation...")
    
    def close_dialog(self):
        """Close the dialog"""
        self.cancelled = True
        self.grab_release()
        self.destroy()
