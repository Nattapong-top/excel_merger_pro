"""Configuration repository for saving and loading column selection configurations."""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from datetime import datetime

from ...domain.processing_options import ColumnSelectionConfig


class IConfigurationRepository(ABC):
    """
    Repository interface for persisting column selection configurations.
    """
    
    @abstractmethod
    def save(self, config: ColumnSelectionConfig, name: str) -> None:
        """
        Save configuration with a name.
        
        Args:
            config: Configuration to save
            name: Name for the configuration
        """
        pass
    
    @abstractmethod
    def load(self, name: str) -> ColumnSelectionConfig:
        """
        Load configuration by name.
        
        Args:
            name: Name of the configuration
        
        Returns:
            Loaded configuration
        
        Raises:
            FileNotFoundError: If configuration not found
        """
        pass
    
    @abstractmethod
    def list_saved_configs(self) -> List[str]:
        """
        List all saved configuration names.
        
        Returns:
            List of configuration names
        """
        pass
    
    @abstractmethod
    def delete(self, name: str) -> None:
        """
        Delete saved configuration.
        
        Args:
            name: Name of the configuration to delete
        """
        pass


class JsonConfigurationRepository(IConfigurationRepository):
    """
    JSON file-based implementation of configuration repository.
    
    Saves configurations as JSON files in a designated directory.
    """
    
    def __init__(self, config_dir: Path):
        """
        Initialize repository with configuration directory.
        
        Args:
            config_dir: Directory for storing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def save(self, config: ColumnSelectionConfig, name: str) -> None:
        """Save configuration as JSON file."""
        config_data = {
            "name": name,
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "config": {
                "selected_columns": list(config.selected_columns),
                "column_order": list(config.column_order)
            }
        }
        
        file_path = self.config_dir / f"{name}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    def load(self, name: str) -> ColumnSelectionConfig:
        """Load configuration from JSON file."""
        file_path = self.config_dir / f"{name}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration '{name}' not found")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        config = config_data.get("config", {})
        return ColumnSelectionConfig(
            selected_columns=tuple(config["selected_columns"]),
            column_order=tuple(config["column_order"])
        )
    
    def list_saved_configs(self) -> List[str]:
        """List all saved configuration names."""
        return [
            f.stem for f in self.config_dir.glob("*.json")
        ]
    
    def delete(self, name: str) -> None:
        """Delete configuration file."""
        file_path = self.config_dir / f"{name}.json"
        if file_path.exists():
            file_path.unlink()
