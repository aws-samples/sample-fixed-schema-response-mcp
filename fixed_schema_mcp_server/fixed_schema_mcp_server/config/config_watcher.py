"""
Configuration file watcher for the Fixed Schema Response MCP Server.

This module provides functionality for watching configuration files for changes
and automatically reloading them.
"""

import os
import time
import logging
import threading
from pathlib import Path
from typing import Callable, Optional

from .config_manager import ConfigManager


class ConfigWatcher:
    """
    Configuration file watcher.
    
    This class watches a configuration file for changes and triggers
    a reload when the file is modified.
    """
    
    def __init__(self, config_manager: ConfigManager, config_path: str, poll_interval: float = 1.0):
        """
        Initialize the configuration watcher.
        
        Args:
            config_manager: The configuration manager to notify of changes
            config_path: Path to the configuration file to watch
            poll_interval: How often to check for changes (in seconds)
        """
        self._config_manager = config_manager
        self._config_path = config_path
        self._poll_interval = poll_interval
        self._last_modified = self._get_last_modified()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._logger = logging.getLogger(__name__)
    
    def start(self) -> None:
        """Start watching the configuration file."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        self._logger.info(f"Started watching configuration file: {self._config_path}")
    
    def stop(self) -> None:
        """Stop watching the configuration file."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._logger.info(f"Stopped watching configuration file: {self._config_path}")
    
    def _watch_loop(self) -> None:
        """Main watch loop that checks for file changes."""
        while self._running:
            try:
                current_modified = self._get_last_modified()
                if current_modified > self._last_modified:
                    self._logger.info(f"Configuration file changed: {self._config_path}")
                    self._config_manager.reload_config()
                    self._last_modified = current_modified
            except Exception as e:
                self._logger.error(f"Error watching configuration file: {str(e)}")
            
            # Sleep for the poll interval
            time.sleep(self._poll_interval)
    
    def _get_last_modified(self) -> float:
        """
        Get the last modified timestamp of the configuration file.
        
        Returns:
            The last modified timestamp as a float
        """
        try:
            return os.path.getmtime(self._config_path)
        except OSError:
            return 0.0