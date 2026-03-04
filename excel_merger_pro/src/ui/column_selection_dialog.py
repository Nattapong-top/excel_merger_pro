# File: src/ui/column_selection_dialog.py
"""
Column Selection Dialog for Excel Merger Pro

Allows users to:
- View all available columns from source files
- Select/deselect columns for merge
- Reorder columns via drag-and-drop (up/down buttons)
- Save and load column selection configurations
"""

import customtkinter as ctk
from typing import List, Optional
from src.domain.column_metadata import ColumnMetadata
from src.domain.processing_options import ColumnSelectionConfig
from src.application.services.column_selection_service import ColumnSelectionService
from src.infrastructure.repositories.configuration_repository import JsonConfigurationRepository
from pathlib import Path


class ColumnSelectionDialog(ctk.CTkToplevel):
    """
    Dialog for selecting and ordering columns for merge operation
    
    Features:
    - Display all available columns with checkboxes
    - Select All / Deselect All buttons
    - Reorder columns with Up/Down buttons
    - Save/Load configuration
    """
    
    def __init__(
        self,
        parent,
        available_columns: List[ColumnMetadata],
        lang_code: str = "en"
    ):
        """
        Initialize dialog with available columns
        
        Args:
            parent: Parent window
            available_columns: List of columns discovered from source files
            lang_code: Language code (en, th, cn)
        """
        super().__init__(parent)
        
        self.lang_code = lang_code
        self.available_columns = available_columns
        self.selected_config: Optional[ColumnSelectionConfig] = None
        self.column_checkboxes = []  # List of (checkbox, column_name)
        
        # Initialize services
        config_dir = Path.home() / ".excel_merger_pro" / "column_configs"
        self.config_repository = JsonConfigurationRepository(config_dir)
        self.selection_service = ColumnSelectionService(
            repository=self.config_repository,
            logger=None  # Will use print for now
        )
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface"""
        self.title("Select Columns")
        self.geometry("500x700")
        self.grab_set()
        self.focus_force()
        
        # Header
        header_label = ctk.CTkLabel(
            self,
            text="Select Columns to Merge",
            font=("Arial", 16, "bold")
        )
        header_label.pack(pady=(15, 5))
        
        hint_label = ctk.CTkLabel(
            self,
            text=f"Found {len(self.available_columns)} unique columns"
        )
        hint_label.pack(pady=5)
        
        # Action buttons frame
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(pady=10, fill="x", padx=20)
        
        btn_select_all = ctk.CTkButton(
            action_frame,
            text="Select All",
            width=100,
            height=30,
            fg_color="#3B8ED0",
            command=self._select_all
        )
        btn_select_all.pack(side="left", padx=5, expand=True)
        
        btn_deselect_all = ctk.CTkButton(
            action_frame,
            text="Deselect All",
            width=100,
            height=30,
            fg_color="gray",
            command=self._deselect_all
        )
        btn_deselect_all.pack(side="right", padx=5, expand=True)
        
        # Main content frame with scrollable list and reorder buttons
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Scrollable column list
        self.scroll_frame = ctk.CTkScrollableFrame(
            content_frame,
            width=350,
            height=350
        )
        self.scroll_frame.pack(side="left", fill="both", expand=True)
        
        # Reorder buttons
        reorder_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=80)
        reorder_frame.pack(side="right", fill="y", padx=(10, 0))
        
        ctk.CTkLabel(reorder_frame, text="Reorder", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        btn_move_up = ctk.CTkButton(
            reorder_frame,
            text="↑ Up",
            width=70,
            height=35,
            command=self._move_up
        )
        btn_move_up.pack(pady=5)
        
        btn_move_down = ctk.CTkButton(
            reorder_frame,
            text="↓ Down",
            width=70,
            height=35,
            command=self._move_down
        )
        btn_move_down.pack(pady=5)
        
        # Create checkboxes for each column
        self._create_column_checkboxes()
        
        # Config management frame
        config_frame = ctk.CTkFrame(self, fg_color="transparent")
        config_frame.pack(pady=10, fill="x", padx=20)
        
        btn_save = ctk.CTkButton(
            config_frame,
            text="💾 Save Config",
            width=120,
            height=35,
            fg_color="#2CC985",
            command=self._save_configuration
        )
        btn_save.pack(side="left", padx=5, expand=True)
        
        btn_load = ctk.CTkButton(
            config_frame,
            text="📂 Load Config",
            width=120,
            height=35,
            fg_color="#FFA500",
            command=self._load_configuration
        )
        btn_load.pack(side="right", padx=5, expand=True)
        
        # Confirm button
        btn_confirm = ctk.CTkButton(
            self,
            text="Confirm Selection",
            command=self._on_confirm,
            height=45,
            font=("Arial", 15, "bold"),
            fg_color="#2CC985"
        )
        btn_confirm.pack(pady=20, padx=20, fill="x")
    
    def _create_column_checkboxes(self):
        """Create checkboxes for all available columns"""
        self.column_checkboxes = []
        
        for col_metadata in self.available_columns:
            # Create frame for each column
            col_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
            col_frame.pack(fill="x", pady=3, padx=5)
            
            # Checkbox
            var = ctk.BooleanVar(value=True)  # Selected by default
            chk = ctk.CTkCheckBox(
                col_frame,
                text=col_metadata.name,
                variable=var,
                font=("Arial", 12)
            )
            chk.pack(side="left", fill="x", expand=True)
            
            # Source file info (small text)
            if col_metadata.source_files:
                source_info = f"({len(col_metadata.source_files)} file(s))"
                info_label = ctk.CTkLabel(
                    col_frame,
                    text=source_info,
                    font=("Arial", 9),
                    text_color="gray"
                )
                info_label.pack(side="right", padx=5)
            
            self.column_checkboxes.append((chk, col_metadata.name, var))
    
    def _select_all(self):
        """Select all columns"""
        for chk, _, var in self.column_checkboxes:
            var.set(True)
    
    def _deselect_all(self):
        """Deselect all columns"""
        for chk, _, var in self.column_checkboxes:
            var.set(False)
    
    def _move_up(self):
        """Move selected column up in the list"""
        # Find first selected checkbox
        for i, (chk, col_name, var) in enumerate(self.column_checkboxes):
            if chk.cget("state") == "normal" and i > 0:
                # Check if this checkbox has focus or is being hovered
                # For simplicity, move the first checked item
                if var.get():
                    # Swap with previous
                    self.column_checkboxes[i], self.column_checkboxes[i-1] = \
                        self.column_checkboxes[i-1], self.column_checkboxes[i]
                    self._refresh_column_list()
                    break
    
    def _move_down(self):
        """Move selected column down in the list"""
        # Find first selected checkbox
        for i, (chk, col_name, var) in enumerate(self.column_checkboxes):
            if chk.cget("state") == "normal" and i < len(self.column_checkboxes) - 1:
                if var.get():
                    # Swap with next
                    self.column_checkboxes[i], self.column_checkboxes[i+1] = \
                        self.column_checkboxes[i+1], self.column_checkboxes[i]
                    self._refresh_column_list()
                    break
    
    def _refresh_column_list(self):
        """Refresh the column list display after reordering"""
        # Clear current display
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
        
        # Recreate checkboxes in new order
        new_checkboxes = []
        for chk, col_name, var in self.column_checkboxes:
            # Find original metadata
            col_metadata = next(
                (c for c in self.available_columns if c.name == col_name),
                None
            )
            
            if col_metadata:
                # Create frame for each column
                col_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
                col_frame.pack(fill="x", pady=3, padx=5)
                
                # Checkbox
                new_chk = ctk.CTkCheckBox(
                    col_frame,
                    text=col_metadata.name,
                    variable=var,
                    font=("Arial", 12)
                )
                new_chk.pack(side="left", fill="x", expand=True)
                
                # Source file info
                if col_metadata.source_files:
                    source_info = f"({len(col_metadata.source_files)} file(s))"
                    info_label = ctk.CTkLabel(
                        col_frame,
                        text=source_info,
                        font=("Arial", 9),
                        text_color="gray"
                    )
                    info_label.pack(side="right", padx=5)
                
                new_checkboxes.append((new_chk, col_name, var))
        
        self.column_checkboxes = new_checkboxes
    
    def _save_configuration(self):
        """Save current selection as a configuration"""
        # Get current selection
        selected_columns = []
        column_order = []
        
        for chk, col_name, var in self.column_checkboxes:
            if var.get():
                selected_columns.append(col_name)
            column_order.append(col_name)
        
        if not selected_columns:
            self._show_message("Error", "Please select at least one column")
            return
        
        # Ask for configuration name
        name_dialog = ctk.CTkInputDialog(
            text="Enter configuration name:",
            title="Save Configuration"
        )
        config_name = name_dialog.get_input()
        
        if config_name:
            try:
                config = ColumnSelectionConfig(
                    selected_columns=tuple(selected_columns),
                    column_order=tuple(column_order)
                )
                self.selection_service.save_config(config, config_name)
                self._show_message("Success", f"Configuration '{config_name}' saved!")
            except Exception as e:
                self._show_message("Error", f"Failed to save: {str(e)}")
    
    def _load_configuration(self):
        """Load a saved configuration"""
        # Get list of saved configs
        try:
            saved_configs = self.config_repository.list_saved_configs()
            
            if not saved_configs:
                self._show_message("Info", "No saved configurations found")
                return
            
            # Show selection dialog
            config_dialog = ConfigSelectionDialog(self, saved_configs)
            selected_name = config_dialog.get_selected()
            
            if selected_name:
                config = self.selection_service.load_config(selected_name)
                self.load_configuration(config)
                self._show_message("Success", f"Configuration '{selected_name}' loaded!")
        except Exception as e:
            self._show_message("Error", f"Failed to load: {str(e)}")
    
    def load_configuration(self, config: ColumnSelectionConfig):
        """
        Load saved configuration into dialog
        
        Args:
            config: Previously saved column selection configuration
        """
        # Update checkboxes based on config
        for chk, col_name, var in self.column_checkboxes:
            var.set(col_name in config.selected_columns)
        
        # Reorder based on config.column_order
        # Create new order matching config
        ordered_checkboxes = []
        for col_name in config.column_order:
            for chk, name, var in self.column_checkboxes:
                if name == col_name:
                    ordered_checkboxes.append((chk, name, var))
                    break
        
        # Add any columns not in config (at the end)
        for chk, name, var in self.column_checkboxes:
            if name not in config.column_order:
                ordered_checkboxes.append((chk, name, var))
        
        self.column_checkboxes = ordered_checkboxes
        self._refresh_column_list()
    
    def _on_confirm(self):
        """Confirm selection and close dialog"""
        selected_columns = []
        column_order = []
        
        for chk, col_name, var in self.column_checkboxes:
            column_order.append(col_name)
            if var.get():
                selected_columns.append(col_name)
        
        if not selected_columns:
            self._show_message("Error", "Please select at least one column")
            return
        
        try:
            self.selected_config = ColumnSelectionConfig(
                selected_columns=tuple(selected_columns),
                column_order=tuple(selected_columns)  # Only include selected columns in order
            )
            self.destroy()
        except ValueError as e:
            self._show_message("Error", str(e))
    
    def _show_message(self, title: str, message: str):
        """Show a message dialog"""
        msg_dialog = ctk.CTkToplevel(self)
        msg_dialog.title(title)
        msg_dialog.geometry("300x150")
        msg_dialog.grab_set()
        
        label = ctk.CTkLabel(msg_dialog, text=message, wraplength=250)
        label.pack(pady=20, padx=20)
        
        btn_ok = ctk.CTkButton(msg_dialog, text="OK", command=msg_dialog.destroy)
        btn_ok.pack(pady=10)
    
    def get_selection_config(self) -> Optional[ColumnSelectionConfig]:
        """
        Get the column selection configuration from user input
        
        Returns:
            ColumnSelectionConfig if user confirmed, None if cancelled
        """
        self.wait_window()
        return self.selected_config


class ConfigSelectionDialog(ctk.CTkToplevel):
    """Dialog for selecting a saved configuration"""
    
    def __init__(self, parent, config_names: List[str]):
        super().__init__(parent)
        
        self.title("Load Configuration")
        self.geometry("350x400")
        self.grab_set()
        self.focus_force()
        
        self.selected_name: Optional[str] = None
        
        # Header
        label = ctk.CTkLabel(
            self,
            text="Select a configuration to load:",
            font=("Arial", 14, "bold")
        )
        label.pack(pady=15)
        
        # Scrollable list
        scroll_frame = ctk.CTkScrollableFrame(self, width=300, height=250)
        scroll_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Create buttons for each config
        for name in config_names:
            btn = ctk.CTkButton(
                scroll_frame,
                text=name,
                command=lambda n=name: self._select_config(n),
                height=35
            )
            btn.pack(pady=5, padx=10, fill="x")
        
        # Cancel button
        btn_cancel = ctk.CTkButton(
            self,
            text="Cancel",
            command=self.destroy,
            fg_color="gray",
            height=35
        )
        btn_cancel.pack(pady=15, padx=20, fill="x")
    
    def _select_config(self, name: str):
        """Select a configuration"""
        self.selected_name = name
        self.destroy()
    
    def get_selected(self) -> Optional[str]:
        """Get the selected configuration name"""
        self.wait_window()
        return self.selected_name
