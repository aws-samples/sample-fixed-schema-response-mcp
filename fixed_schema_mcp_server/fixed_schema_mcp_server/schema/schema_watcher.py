"""
Schema file watcher for hot-reloading schemas when they change.
"""

import os
import time
import logging
import threading
from typing import Dict, Callable, Optional

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Create dummy classes for type hints
    class Observer:
        pass
    
    class FileSystemEvent:
        pass
    
    class FileSystemEventHandler:
        pass

logger = logging.getLogger(__name__)


class SchemaFileHandler(FileSystemEventHandler):
    """
    File system event handler for schema files.
    
    This handler watches for changes to schema files and triggers a callback
    when a schema file is created, modified, or deleted.
    """
    
    def __init__(self, callback: Callable[[], None], file_patterns: Optional[list] = None):
        """
        Initialize the schema file handler.
        
        Args:
            callback: Function to call when a schema file changes
            file_patterns: List of file patterns to watch (e.g., ['.json', '.yaml'])
        """
        self.callback = callback
        self.file_patterns = file_patterns or ['.json', '.yaml', '.yml']
        self._last_event_time = 0
        self._debounce_seconds = 1.0  # Debounce period in seconds
    
    def on_any_event(self, event: FileSystemEvent) -> None:
        """
        Handle any file system event.
        
        Args:
            event: The file system event
        """
        if event.is_directory:
            return
        
        # Check if the file has a schema file extension
        if not any(event.src_path.endswith(pattern) for pattern in self.file_patterns):
            return
        
        # Debounce events to prevent multiple rapid callbacks
        current_time = time.time()
        if current_time - self._last_event_time < self._debounce_seconds:
            return
        
        self._last_event_time = current_time
        
        logger.info(f"Schema file changed: {event.src_path}")
        self.callback()


class SchemaWatcher:
    """
    Watches for changes to schema files and triggers reloading.
    
    This class sets up a file system observer to watch for changes to schema
    files and triggers a callback when a schema file is created, modified, or deleted.
    """
    
    def __init__(self, schema_path: str, reload_callback: Callable[[], None]):
        """
        Initialize the schema watcher.
        
        Args:
            schema_path: Path to the schema directory
            reload_callback: Function to call when schemas need to be reloaded
        """
        self.schema_path = schema_path
        self.reload_callback = reload_callback
        self.observer = None
        self._running = False
    
    def start(self) -> None:
        """
        Start watching for schema file changes.
        
        Raises:
            FileNotFoundError: If the schema path does not exist
            ValueError: If the schema path is not a directory
            RuntimeError: If watchdog is not available
        """
        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog package is not available. Schema hot-reloading is disabled.")
            return
            
        if not os.path.exists(self.schema_path):
            raise FileNotFoundError(f"Schema path '{self.schema_path}' does not exist")
        
        if not os.path.isdir(self.schema_path):
            raise ValueError(f"Schema path '{self.schema_path}' is not a directory")
        
        if self._running:
            return
        
        self.observer = Observer()
        handler = SchemaFileHandler(self.reload_callback)
        self.observer.schedule(handler, self.schema_path, recursive=False)
        self.observer.start()
        self._running = True
        
        logger.info(f"Started watching schema directory: {self.schema_path}")
    
    def stop(self) -> None:
        """Stop watching for schema file changes."""
        if self.observer and self._running:
            self.observer.stop()
            self.observer.join()
            self._running = False
            logger.info("Stopped watching schema directory")
    
    def is_running(self) -> bool:
        """
        Check if the watcher is running.
        
        Returns:
            True if the watcher is running, False otherwise
        """
        return self._running