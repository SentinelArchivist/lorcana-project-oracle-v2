"""Optimization configuration utilities for controlling simulation performance tradeoffs."""

from typing import Dict, Any, Optional
import json
import os
from dataclasses import dataclass, asdict
from src.utils.logger import get_logger
from src.utils.error_handler import safe_operation, handle_file_operations

logger = get_logger()

@dataclass
class SimulationConfig:
    """Configuration options for simulation depth vs. speed tradeoffs.
    
    Attributes:
        max_turns_per_game: Maximum number of turns before a game simulation ends
        parallel_simulation: Whether to run simulations in parallel
        num_workers: Number of worker processes for parallel simulation (if enabled)
        game_sample_size: Number of games to simulate for each matchup
        cache_enabled: Whether to cache simulation results for similar matchups
        cache_size: Maximum number of entries in the simulation cache
        detailed_logging: Whether to enable detailed logging during simulations
        early_termination: Whether to terminate simulations early when outcome is clear
        early_termination_threshold: Score threshold to trigger early termination
    """
    max_turns_per_game: int = 50
    parallel_simulation: bool = True
    num_workers: int = 4
    game_sample_size: int = 10
    cache_enabled: bool = True
    cache_size: int = 1000
    detailed_logging: bool = False
    early_termination: bool = True
    early_termination_threshold: float = 0.8
    
    def __post_init__(self):
        """Validate configuration settings."""
        # Ensure max_turns_per_game is reasonable
        if self.max_turns_per_game < 10:
            logger.warning(f"max_turns_per_game set to {self.max_turns_per_game} is too low, setting to 10")
            self.max_turns_per_game = 10
        elif self.max_turns_per_game > 200:
            logger.warning(f"max_turns_per_game set to {self.max_turns_per_game} is too high, setting to 200")
            self.max_turns_per_game = 200
            
        # Ensure num_workers is reasonable
        import multiprocessing
        max_cpu = multiprocessing.cpu_count()
        if self.parallel_simulation:
            if self.num_workers < 1:
                logger.warning(f"num_workers set to {self.num_workers} is invalid, setting to 1")
                self.num_workers = 1
            elif self.num_workers > max_cpu:
                logger.warning(f"num_workers set to {self.num_workers} exceeds available CPUs ({max_cpu}), limiting to {max_cpu}")
                self.num_workers = max_cpu
        
        # Ensure game_sample_size is reasonable
        if self.game_sample_size < 5:
            logger.warning(f"game_sample_size set to {self.game_sample_size} is too low for reliable results, setting to 5")
            self.game_sample_size = 5

class OptimizationManager:
    """Manages optimization settings for simulations."""
    
    DEFAULT_CONFIG_PATH = "config/optimization.json"
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the optimization manager.
        
        Args:
            config_path: Path to the optimization configuration file. If None,
                        uses the default path.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
    
    @safe_operation(log_level='error')
    def _load_config(self) -> SimulationConfig:
        """Load optimization configuration from file."""
        # Create default config
        default_config = SimulationConfig()
        
        # If config file doesn't exist, create it with defaults
        if not os.path.exists(self.config_path):
            logger.info(f"Creating default optimization configuration at {self.config_path}")
            self._save_config(default_config)
            return default_config
        
        # Otherwise, try to load from file
        try:
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
                # Create a SimulationConfig with loaded values, falling back to defaults
                # for any missing values
                return SimulationConfig(
                    max_turns_per_game=config_data.get('max_turns_per_game', default_config.max_turns_per_game),
                    parallel_simulation=config_data.get('parallel_simulation', default_config.parallel_simulation),
                    num_workers=config_data.get('num_workers', default_config.num_workers),
                    game_sample_size=config_data.get('game_sample_size', default_config.game_sample_size),
                    cache_enabled=config_data.get('cache_enabled', default_config.cache_enabled),
                    cache_size=config_data.get('cache_size', default_config.cache_size),
                    detailed_logging=config_data.get('detailed_logging', default_config.detailed_logging),
                    early_termination=config_data.get('early_termination', default_config.early_termination),
                    early_termination_threshold=config_data.get('early_termination_threshold', default_config.early_termination_threshold)
                )
        except Exception as e:
            logger.error(f"Error loading optimization configuration: {e}. Using defaults.")
            return default_config
    
    @safe_operation(log_level='error')
    def _save_config(self, config: SimulationConfig) -> bool:
        """Save optimization configuration to file.
        
        Args:
            config: The configuration to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Save config to file
        with open(self.config_path, 'w') as f:
            json.dump(asdict(config), f, indent=4)
        
        logger.info(f"Saved optimization configuration to {self.config_path}")
        return True
    
    def update_config(self, **kwargs) -> bool:
        """Update optimization configuration with new values.
        
        Args:
            **kwargs: Keyword arguments with new configuration values
            
        Returns:
            True if updated successfully, False otherwise
        """
        # Create new config with updated values
        updated_config = SimulationConfig(
            **{**asdict(self.config), **kwargs}
        )
        
        # Save to file
        if self._save_config(updated_config):
            self.config = updated_config
            return True
        return False
    
    def get_config(self) -> SimulationConfig:
        """Get the current optimization configuration.
        
        Returns:
            The current SimulationConfig
        """
        return self.config
