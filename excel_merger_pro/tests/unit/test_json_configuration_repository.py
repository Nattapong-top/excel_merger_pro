"""Unit tests for JsonConfigurationRepository."""

import json
import os
import pytest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from excel_merger_pro.src.domain.processing_options import ColumnSelectionConfig
from excel_merger_pro.src.infrastructure.repositories.configuration_repository import (
    JsonConfigurationRepository
)


class TestJsonConfigurationRepository:
    """Unit tests for JsonConfigurationRepository."""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary directory for configuration files."""
        with TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def repository(self, temp_config_dir):
        """Create a repository instance with temporary directory."""
        return JsonConfigurationRepository(temp_config_dir)
    
    @pytest.fixture
    def sample_config(self):
        """Create a sample ColumnSelectionConfig for testing."""
        return ColumnSelectionConfig(
            selected_columns=("Date", "Product", "Amount"),
            column_order=("Date", "Product", "Amount")
        )
    
    def test_save_config_with_specific_name(self, repository, sample_config, temp_config_dir):
        """
        Test saving a configuration with a specific name.
        Requirements: 6.2
        """
        config_name = "sales_report"
        
        repository.save(sample_config, config_name)
        
        # Verify file was created
        config_file = temp_config_dir / f"{config_name}.json"
        assert config_file.exists()
        
        # Verify file content
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["name"] == config_name
        assert data["version"] == "1.0"
        assert "created_at" in data
        assert data["config"]["selected_columns"] == ["Date", "Product", "Amount"]
        assert data["config"]["column_order"] == ["Date", "Product", "Amount"]
    
    def test_save_config_with_special_characters_in_name(self, repository, sample_config, temp_config_dir):
        """
        Test saving a configuration with special characters in name.
        Requirements: 6.2
        """
        config_name = "my_config-2024"
        
        repository.save(sample_config, config_name)
        
        config_file = temp_config_dir / f"{config_name}.json"
        assert config_file.exists()
    
    def test_save_config_overwrites_existing(self, repository, sample_config, temp_config_dir):
        """
        Test that saving a config with existing name overwrites it.
        Requirements: 6.2
        """
        config_name = "test_config"
        
        # Save first config
        repository.save(sample_config, config_name)
        
        # Save different config with same name
        new_config = ColumnSelectionConfig(
            selected_columns=("A", "B"),
            column_order=("A", "B")
        )
        repository.save(new_config, config_name)
        
        # Verify only one file exists with new content
        config_file = temp_config_dir / f"{config_name}.json"
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert data["config"]["selected_columns"] == ["A", "B"]
        assert data["config"]["column_order"] == ["A", "B"]
    
    def test_load_existing_config(self, repository, sample_config):
        """
        Test loading an existing configuration.
        Requirements: 6.3
        """
        config_name = "test_load"
        
        # Save config first
        repository.save(sample_config, config_name)
        
        # Load it back
        loaded_config = repository.load(config_name)
        
        assert loaded_config.selected_columns == sample_config.selected_columns
        assert loaded_config.column_order == sample_config.column_order
    
    def test_load_config_with_different_order(self, repository):
        """
        Test loading a configuration with different column order.
        Requirements: 6.3
        """
        config = ColumnSelectionConfig(
            selected_columns=("Date", "Product", "Amount"),
            column_order=("Amount", "Date", "Product")
        )
        config_name = "reordered"
        
        repository.save(config, config_name)
        loaded_config = repository.load(config_name)
        
        assert loaded_config.column_order == ("Amount", "Date", "Product")
    
    def test_load_nonexistent_config_raises_file_not_found(self, repository):
        """
        Test that loading a non-existent config raises FileNotFoundError.
        Requirements: 6.3
        """
        with pytest.raises(FileNotFoundError) as exc_info:
            repository.load("nonexistent_config")
        
        assert "nonexistent_config" in str(exc_info.value)
        assert "not found" in str(exc_info.value).lower()
    
    def test_load_invalid_json_raises_error(self, repository, temp_config_dir):
        """
        Test that loading invalid JSON raises an error.
        Requirements: 6.4
        """
        config_name = "invalid_json"
        config_file = temp_config_dir / f"{config_name}.json"
        
        # Write invalid JSON
        with open(config_file, 'w') as f:
            f.write("{ invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            repository.load(config_name)
    
    def test_load_missing_required_fields_raises_error(self, repository, temp_config_dir):
        """
        Test that loading JSON with missing required fields raises an error.
        Requirements: 6.4
        """
        config_name = "missing_fields"
        config_file = temp_config_dir / f"{config_name}.json"
        
        # Write JSON without required fields
        with open(config_file, 'w') as f:
            json.dump({"name": "test"}, f)
        
        with pytest.raises(KeyError):
            repository.load(config_name)
    
    def test_load_empty_selected_columns_raises_error(self, repository, temp_config_dir):
        """
        Test that loading config with empty selected_columns raises ValueError.
        Requirements: 6.4
        """
        config_name = "empty_columns"
        config_file = temp_config_dir / f"{config_name}.json"
        
        # Write config with empty selected_columns
        data = {
            "name": config_name,
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00",
            "config": {
                "selected_columns": [],
                "column_order": []
            }
        }
        with open(config_file, 'w') as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError) as exc_info:
            repository.load(config_name)
        
        assert "selected_columns cannot be empty" in str(exc_info.value)
    
    def test_load_mismatched_columns_raises_error(self, repository, temp_config_dir):
        """
        Test that loading config with mismatched columns raises ValueError.
        Requirements: 6.4
        """
        config_name = "mismatched"
        config_file = temp_config_dir / f"{config_name}.json"
        
        # Write config with mismatched columns
        data = {
            "name": config_name,
            "version": "1.0",
            "created_at": "2024-01-01T00:00:00",
            "config": {
                "selected_columns": ["A", "B", "C"],
                "column_order": ["A", "B"]  # Missing C
            }
        }
        with open(config_file, 'w') as f:
            json.dump(data, f)
        
        with pytest.raises(ValueError) as exc_info:
            repository.load(config_name)
        
        assert "column_order must contain exactly the selected_columns" in str(exc_info.value)
    
    def test_list_saved_configs_empty(self, repository):
        """
        Test listing configs when directory is empty.
        Requirements: 6.3
        """
        configs = repository.list_saved_configs()
        assert configs == []
    
    def test_list_saved_configs_multiple(self, repository, sample_config):
        """
        Test listing multiple saved configurations.
        Requirements: 6.3
        """
        # Save multiple configs
        repository.save(sample_config, "config1")
        repository.save(sample_config, "config2")
        repository.save(sample_config, "config3")
        
        configs = repository.list_saved_configs()
        
        assert len(configs) == 3
        assert "config1" in configs
        assert "config2" in configs
        assert "config3" in configs
    
    def test_list_saved_configs_ignores_non_json_files(self, repository, sample_config, temp_config_dir):
        """
        Test that list_saved_configs ignores non-JSON files.
        Requirements: 6.3
        """
        # Save a config
        repository.save(sample_config, "valid_config")
        
        # Create a non-JSON file
        (temp_config_dir / "readme.txt").write_text("This is not a config")
        
        configs = repository.list_saved_configs()
        
        assert len(configs) == 1
        assert "valid_config" in configs
        assert "readme" not in configs
    
    def test_delete_existing_config(self, repository, sample_config, temp_config_dir):
        """
        Test deleting an existing configuration.
        Requirements: 6.3
        """
        config_name = "to_delete"
        
        # Save and verify it exists
        repository.save(sample_config, config_name)
        assert (temp_config_dir / f"{config_name}.json").exists()
        
        # Delete it
        repository.delete(config_name)
        
        # Verify it's gone
        assert not (temp_config_dir / f"{config_name}.json").exists()
    
    def test_delete_nonexistent_config_does_not_raise(self, repository):
        """
        Test that deleting a non-existent config doesn't raise an error.
        Requirements: 6.3
        """
        # Should not raise any exception
        repository.delete("nonexistent")
    
    def test_repository_creates_directory_if_not_exists(self, temp_config_dir):
        """
        Test that repository creates config directory if it doesn't exist.
        Requirements: 6.2
        """
        nested_dir = temp_config_dir / "nested" / "config"
        
        # Directory doesn't exist yet
        assert not nested_dir.exists()
        
        # Create repository
        repository = JsonConfigurationRepository(nested_dir)
        
        # Directory should now exist
        assert nested_dir.exists()
        assert nested_dir.is_dir()
    
    def test_save_config_with_unicode_characters(self, repository, temp_config_dir):
        """
        Test saving configuration with Unicode characters in column names.
        Requirements: 6.2
        """
        config = ColumnSelectionConfig(
            selected_columns=("วันที่", "สินค้า", "จำนวน"),
            column_order=("วันที่", "สินค้า", "จำนวน")
        )
        config_name = "thai_columns"
        
        repository.save(config, config_name)
        
        # Verify file was created and can be read
        config_file = temp_config_dir / f"{config_name}.json"
        assert config_file.exists()
        
        # Load and verify
        loaded_config = repository.load(config_name)
        assert loaded_config.selected_columns == config.selected_columns
    
    def test_save_and_load_large_number_of_columns(self, repository):
        """
        Test saving and loading configuration with many columns.
        Requirements: 6.2, 6.3
        """
        # Create config with 100 columns
        columns = tuple(f"Column_{i}" for i in range(100))
        config = ColumnSelectionConfig(
            selected_columns=columns,
            column_order=columns
        )
        config_name = "large_config"
        
        repository.save(config, config_name)
        loaded_config = repository.load(config_name)
        
        assert len(loaded_config.selected_columns) == 100
        assert loaded_config.selected_columns == columns


class TestJsonConfigurationRepositoryPermissionErrors:
    """Tests for permission-related errors."""
    
    @pytest.mark.skipif(sys.platform == "win32", reason="Permission tests unreliable on Windows")
    def test_save_to_readonly_directory_raises_permission_error(self, tmp_path):
        """
        Test that saving to a read-only directory raises PermissionError.
        Requirements: 6.4
        
        Note: This test is skipped on Windows as file permissions work differently.
        """
        config_dir = tmp_path / "readonly"
        config_dir.mkdir()
        
        # Make directory read-only
        config_dir.chmod(0o444)
        
        try:
            repository = JsonConfigurationRepository(config_dir)
            config = ColumnSelectionConfig(
                selected_columns=("A", "B"),
                column_order=("A", "B")
            )
            
            with pytest.raises((PermissionError, OSError)):
                repository.save(config, "test")
        finally:
            # Restore permissions for cleanup
            config_dir.chmod(0o755)
    
    @pytest.mark.skipif(sys.platform == "win32", reason="Permission tests unreliable on Windows")
    def test_load_from_unreadable_file_raises_permission_error(self, tmp_path):
        """
        Test that loading from an unreadable file raises PermissionError.
        Requirements: 6.4
        
        Note: This test is skipped on Windows as file permissions work differently.
        """
        config_dir = tmp_path / "configs"
        config_dir.mkdir()
        
        repository = JsonConfigurationRepository(config_dir)
        config = ColumnSelectionConfig(
            selected_columns=("A", "B"),
            column_order=("A", "B")
        )
        
        # Save config first
        config_name = "unreadable"
        repository.save(config, config_name)
        
        # Make file unreadable
        config_file = config_dir / f"{config_name}.json"
        config_file.chmod(0o000)
        
        try:
            with pytest.raises((PermissionError, OSError)):
                repository.load(config_name)
        finally:
            # Restore permissions for cleanup
            config_file.chmod(0o644)
    
    def test_save_to_nonexistent_parent_directory(self, tmp_path):
        """
        Test that repository handles non-existent parent directories gracefully.
        Requirements: 6.4
        """
        # This should work because repository creates the directory
        config_dir = tmp_path / "nonexistent" / "nested" / "path"
        repository = JsonConfigurationRepository(config_dir)
        
        config = ColumnSelectionConfig(
            selected_columns=("A", "B"),
            column_order=("A", "B")
        )
        
        # Should not raise any error
        repository.save(config, "test")
        assert (config_dir / "test.json").exists()
