"""Column selection service for managing column selection configurations."""

from typing import List, Optional

from ...domain.processing_options import ColumnSelectionConfig
from ...infrastructure.repositories.configuration_repository import IConfigurationRepository
from ..interfaces import ILogger


class ColumnSelectionService:
    """
    Service for managing column selection configurations.
    
    Responsibilities:
    - Validate column selections
    - Save/load configurations
    - Apply default selections
    """
    
    def __init__(self, repository: IConfigurationRepository, logger: ILogger):
        """
        Initialize service with dependencies.
        
        Args:
            repository: Repository for persisting configurations
            logger: Logger for operation tracking
        """
        self.repository = repository
        self.logger = logger
    
    def create_config(
        self,
        selected_columns: List[str],
        column_order: List[str]
    ) -> ColumnSelectionConfig:
        """
        Create and validate column selection configuration.
        
        Args:
            selected_columns: List of selected column names
            column_order: Ordered list of column names
        
        Returns:
            Validated ColumnSelectionConfig
        
        Raises:
            ValueError: If configuration is invalid
        """
        self.logger.log(f"Creating config with {len(selected_columns)} columns")
        
        # ColumnSelectionConfig will validate itself
        config = ColumnSelectionConfig(
            selected_columns=tuple(selected_columns),
            column_order=tuple(column_order)
        )
        
        return config
    
    def save_config(self, config: ColumnSelectionConfig, name: str) -> None:
        """
        Save configuration with a name.
        
        Args:
            config: Configuration to save
            name: Name for the configuration
        """
        self.logger.log(f"Saving configuration '{name}'")
        self.repository.save(config, name)
        self.logger.log(f"Configuration '{name}' saved successfully")
    
    def load_config(self, name: str) -> ColumnSelectionConfig:
        """
        Load saved configuration by name.
        
        Args:
            name: Name of the configuration
        
        Returns:
            Loaded configuration
        
        Raises:
            FileNotFoundError: If configuration not found
        """
        self.logger.log(f"Loading configuration '{name}'")
        config = self.repository.load(name)
        self.logger.log(f"Configuration '{name}' loaded successfully")
        return config
    
    def get_default_config(self, available_columns: List[str]) -> ColumnSelectionConfig:
        """
        Create default configuration (all columns selected).
        
        Args:
            available_columns: List of available column names
        
        Returns:
            Default configuration with all columns selected
        """
        self.logger.log(f"Creating default config with {len(available_columns)} columns")
        
        return ColumnSelectionConfig(
            selected_columns=tuple(available_columns),
            column_order=tuple(available_columns)
        )
    
    def filter_config_by_available_columns(
        self,
        config: ColumnSelectionConfig,
        available_columns: List[str]
    ) -> Optional[ColumnSelectionConfig]:
        """
        Filter configuration to only include available columns.
        
        Args:
            config: Configuration to filter
            available_columns: List of currently available columns
        
        Returns:
            Filtered configuration, or None if no columns match
        """
        available_set = set(available_columns)
        
        # Filter selected columns
        filtered_columns = [
            col for col in config.column_order
            if col in available_set
        ]
        
        if not filtered_columns:
            self.logger.log("Warning: No columns from config are available")
            return None
        
        self.logger.log(
            f"Filtered config: {len(filtered_columns)}/{len(config.selected_columns)} columns available"
        )
        
        return ColumnSelectionConfig(
            selected_columns=tuple(filtered_columns),
            column_order=tuple(filtered_columns)
        )
