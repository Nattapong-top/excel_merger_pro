"""
Property-based tests for configuration serialization round trip.

Feature: column-selection-for-merge
"""

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from src.domain.processing_options import ColumnSelectionConfig
from src.infrastructure.repositories.configuration_repository import JsonConfigurationRepository


# Strategy for generating valid column names
column_names = st.text(
    alphabet=st.characters(
        whitelist_categories=('Lu', 'Ll', 'Nd', 'Pd'),
        min_codepoint=32,
        max_codepoint=126
    ),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip() and not x.startswith('.'))


# Strategy for generating valid ColumnSelectionConfig
@st.composite
def column_selection_config_strategy(draw):
    """Generate valid ColumnSelectionConfig instances."""
    # Generate a list of unique column names
    columns = draw(
        st.lists(
            column_names,
            min_size=1,
            max_size=20,
            unique=True
        )
    )
    
    # Create a permutation for column_order
    column_order = draw(st.permutations(columns))
    
    return ColumnSelectionConfig(
        selected_columns=tuple(columns),
        column_order=tuple(column_order)
    )


class TestConfigurationSerializationRoundTrip:
    """
    Property 14: Configuration Serialization Round Trip
    Validates: Requirements 6.2, 6.4
    
    Tests that saving a configuration to a file and then loading it back
    produces an equivalent configuration.
    """
    
    @given(
        config=column_selection_config_strategy(),
        config_name=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                min_codepoint=65,
                max_codepoint=122
            ),
            min_size=1,
            max_size=30
        ).filter(lambda x: x.strip())
    )
    def test_save_load_round_trip(self, config, config_name):
        """
        Feature: column-selection-for-merge, Property 14: Configuration Serialization Round Trip
        
        For any valid column selection configuration, saving it to a file and then
        loading it back should produce an equivalent configuration.
        
        **Validates: Requirements 6.2, 6.4**
        """
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = JsonConfigurationRepository(Path(temp_dir))
            
            # Save the configuration
            repository.save(config, config_name)
            
            # Load the configuration back
            loaded_config = repository.load(config_name)
            
            # Verify the loaded configuration is equivalent to the original
            assert loaded_config.selected_columns == config.selected_columns
            assert loaded_config.column_order == config.column_order
            assert loaded_config == config
    
    @given(
        config=column_selection_config_strategy(),
        config_name=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                min_codepoint=65,
                max_codepoint=122
            ),
            min_size=1,
            max_size=30
        ).filter(lambda x: x.strip())
    )
    def test_multiple_save_load_cycles(self, config, config_name):
        """
        Feature: column-selection-for-merge, Property 14: Configuration Serialization Round Trip
        
        For any valid configuration, multiple save-load cycles should preserve
        the configuration without degradation.
        
        **Validates: Requirements 6.2, 6.4**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = JsonConfigurationRepository(Path(temp_dir))
            
            current_config = config
            
            # Perform 3 save-load cycles
            for _ in range(3):
                repository.save(current_config, config_name)
                current_config = repository.load(config_name)
            
            # After multiple cycles, configuration should still be equivalent
            assert current_config == config
            assert current_config.selected_columns == config.selected_columns
            assert current_config.column_order == config.column_order
    
    @given(
        config=column_selection_config_strategy(),
        config_name=st.text(
            alphabet=st.characters(
                whitelist_categories=('Lu', 'Ll', 'Nd'),
                min_codepoint=65,
                max_codepoint=122
            ),
            min_size=1,
            max_size=30
        ).filter(lambda x: x.strip())
    )
    def test_saved_config_appears_in_list(self, config, config_name):
        """
        Feature: column-selection-for-merge, Property 14: Configuration Serialization Round Trip
        
        For any saved configuration, it should appear in the list of saved configurations.
        
        **Validates: Requirements 6.2**
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = JsonConfigurationRepository(Path(temp_dir))
            
            # Save the configuration
            repository.save(config, config_name)
            
            # Verify it appears in the list
            saved_configs = repository.list_saved_configs()
            assert config_name in saved_configs
