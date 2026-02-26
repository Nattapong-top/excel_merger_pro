# File: src/ui/processing_options_dialog.py
"""
Dialog for configuring processing options

Allows users to enable/configure:
- Chunked reading for large files
- Parallel processing
- Group by with aggregations
- Duplicate removal
- Column selection and reordering
"""

import customtkinter as ctk
from typing import Optional, List
from src.domain.processing_options import (
    ProcessingOptions,
    GroupByConfig,
    DuplicateRemovalConfig,
    ColumnSelectionConfig
)


class ProcessingOptionsDialog(ctk.CTkToplevel):
    """
    Dialog for configuring all processing options
    
    Features:
    - Checkboxes for enabling features
    - Expandable sections for configuration
    - Input validation
    - OK/Cancel buttons
    """
    
    def __init__(self, parent, available_columns: List[str] = None):
        """
        Initialize processing options dialog
        
        Args:
            parent: Parent window
            available_columns: List of available column names (for processors)
        """
        super().__init__(parent)
        
        self.available_columns = available_columns or []
        self.result: Optional[ProcessingOptions] = None
        
        # Window configuration
        self.title("Processing Options")
        self.geometry("600x700")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 700) // 2
        self.geometry(f"+{x}+{y}")
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create dialog widgets"""
        # Main scrollable frame
        main_frame = ctk.CTkScrollableFrame(self, width=560, height=600)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="Configure Processing Options",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))
        
        # Performance section
        self._create_performance_section(main_frame)
        
        # Data processing section
        self._create_data_processing_section(main_frame)
        
        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        self.ok_button = ctk.CTkButton(
            button_frame,
            text="OK",
            command=self._on_ok,
            width=120
        )
        self.ok_button.pack(side="right", padx=5)
        
        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=120,
            fg_color="gray",
            hover_color="darkgray"
        )
        cancel_button.pack(side="right", padx=5)
    
    def _create_performance_section(self, parent):
        """Create performance optimization section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=10)
        
        # Section title
        ctk.CTkLabel(
            section_frame,
            text="Performance Optimization",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Chunked reading
        self.chunking_var = ctk.BooleanVar(value=False)
        chunking_check = ctk.CTkCheckBox(
            section_frame,
            text="Enable chunked reading for large files (>100MB)",
            variable=self.chunking_var
        )
        chunking_check.pack(anchor="w", padx=20, pady=5)
        
        # Chunk size
        chunk_frame = ctk.CTkFrame(section_frame)
        chunk_frame.pack(fill="x", padx=30, pady=5)
        
        ctk.CTkLabel(chunk_frame, text="Chunk size:").pack(side="left", padx=5)
        self.chunk_size_entry = ctk.CTkEntry(chunk_frame, width=100)
        self.chunk_size_entry.insert(0, "10000")
        self.chunk_size_entry.pack(side="left", padx=5)
        ctk.CTkLabel(chunk_frame, text="rows").pack(side="left", padx=5)
        
        # Parallel processing
        self.parallel_var = ctk.BooleanVar(value=True)
        parallel_check = ctk.CTkCheckBox(
            section_frame,
            text="Enable parallel processing",
            variable=self.parallel_var
        )
        parallel_check.pack(anchor="w", padx=20, pady=5)
        
        # Max workers
        worker_frame = ctk.CTkFrame(section_frame)
        worker_frame.pack(fill="x", padx=30, pady=(5, 10))
        
        ctk.CTkLabel(worker_frame, text="Max workers:").pack(side="left", padx=5)
        self.max_workers_entry = ctk.CTkEntry(worker_frame, width=100)
        self.max_workers_entry.insert(0, "4")
        self.max_workers_entry.pack(side="left", padx=5)
        ctk.CTkLabel(worker_frame, text="threads").pack(side="left", padx=5)
    
    def _create_data_processing_section(self, parent):
        """Create data processing section"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.pack(fill="x", pady=10)
        
        # Section title
        ctk.CTkLabel(
            section_frame,
            text="Data Processing (Optional)",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Note
        ctk.CTkLabel(
            section_frame,
            text="Note: These features will be available after initial merge",
            font=("Arial", 10),
            text_color="gray"
        ).pack(anchor="w", padx=20, pady=5)
        
        # Group by (disabled for now)
        self.groupby_var = ctk.BooleanVar(value=False)
        groupby_check = ctk.CTkCheckBox(
            section_frame,
            text="Group by columns (Coming soon)",
            variable=self.groupby_var,
            state="disabled"
        )
        groupby_check.pack(anchor="w", padx=20, pady=5)
        
        # Duplicate removal (disabled for now)
        self.duplicate_var = ctk.BooleanVar(value=False)
        duplicate_check = ctk.CTkCheckBox(
            section_frame,
            text="Remove duplicates (Coming soon)",
            variable=self.duplicate_var,
            state="disabled"
        )
        duplicate_check.pack(anchor="w", padx=20, pady=5)
        
        # Column selection (disabled for now)
        self.column_var = ctk.BooleanVar(value=False)
        column_check = ctk.CTkCheckBox(
            section_frame,
            text="Select/reorder columns (Coming soon)",
            variable=self.column_var,
            state="disabled"
        )
        column_check.pack(anchor="w", padx=20, pady=(5, 10))
    
    def _on_ok(self):
        """Handle OK button click"""
        try:
            # Validate and build ProcessingOptions
            chunk_size = int(self.chunk_size_entry.get())
            max_workers = int(self.max_workers_entry.get())
            
            self.result = ProcessingOptions(
                enable_chunking=self.chunking_var.get(),
                chunk_size=chunk_size,
                enable_parallel=self.parallel_var.get(),
                max_workers=max_workers,
                group_by_config=None,  # Not implemented yet
                duplicate_removal_config=None,  # Not implemented yet
                column_selection_config=None  # Not implemented yet
            )
            
            self.grab_release()
            self.destroy()
            
        except ValueError as e:
            # Show error message
            error_dialog = ctk.CTkToplevel(self)
            error_dialog.title("Invalid Input")
            error_dialog.geometry("300x150")
            
            ctk.CTkLabel(
                error_dialog,
                text=f"Invalid configuration:\n{str(e)}",
                wraplength=250
            ).pack(pady=20)
            
            ctk.CTkButton(
                error_dialog,
                text="OK",
                command=error_dialog.destroy
            ).pack(pady=10)
    
    def _on_cancel(self):
        """Handle Cancel button click"""
        self.result = None
        self.grab_release()
        self.destroy()
    
    def get_result(self) -> Optional[ProcessingOptions]:
        """
        Get the configured processing options
        
        Returns:
            ProcessingOptions if OK was clicked, None if cancelled
        """
        return self.result
