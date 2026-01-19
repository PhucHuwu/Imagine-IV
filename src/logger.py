"""
Logger - Thread-safe logging with GUI and file output
"""
import logging
import os
import queue
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional


class ThreadLogger:
    """Thread-safe logger with per-thread prefix and GUI callback."""

    def __init__(self,
                 log_dir: str = None,
                 gui_callback: Optional[Callable[[str], None]] = None,
                 verbose: bool = True):
        """
        Initialize logger.

        Args:
            log_dir: Directory to save log files (auto-detected if None)
            gui_callback: Callback function to send logs to GUI
            verbose: Enable verbose logging
        """
        import sys

        if log_dir is None:
            # Auto-detect log directory
            if getattr(sys, 'frozen', False):
                # Frozen app - use directory next to the app
                base_dir = Path(sys.executable).parent
                # For macOS .app bundle, go up from MacOS folder
                if base_dir.name == 'MacOS':
                    base_dir = base_dir.parent.parent.parent
                self.log_dir = base_dir / "logs"
            else:
                # Development mode - use local logs folder
                self.log_dir = Path(__file__).parent.parent / "logs"
        else:
            self.log_dir = Path(log_dir)

        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.gui_callback = gui_callback
        self.verbose = verbose
        self._lock = threading.Lock()
        self._log_queue = queue.Queue()

        # Create log file for this session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"session_{timestamp}.log"

        # Setup file handler
        self._setup_file_handler()

    def _setup_file_handler(self):
        """Setup file logging."""
        self._file = open(self.log_file, 'a', encoding='utf-8')

    def _get_thread_prefix(self) -> str:
        """Get current thread prefix."""
        thread_name = threading.current_thread().name
        if thread_name.startswith("Thread-"):
            return f"[{thread_name}]"
        elif thread_name == "MainThread":
            return "[Main]"
        else:
            return f"[{thread_name}]"

    def _format_message(self, level: str, message: str) -> str:
        """Format log message with timestamp and thread."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = self._get_thread_prefix()
        return f"{timestamp} {prefix} [{level}] {message}"

    def _log(self, level: str, message: str, force: bool = False):
        """Internal log method."""
        if not self.verbose and not force:
            return

        formatted = self._format_message(level, message)

        with self._lock:
            # Write to file
            self._file.write(formatted + "\n")
            self._file.flush()

            # Send to GUI
            if self.gui_callback:
                try:
                    self.gui_callback(formatted)
                except Exception:
                    pass

            # Also print to console
            print(formatted)

    def info(self, message: str):
        """Log info message."""
        self._log("INFO", message)

    def debug(self, message: str):
        """Log debug message."""
        self._log("DEBUG", message)

    def warning(self, message: str):
        """Log warning message."""
        self._log("WARN", message, force=True)

    def error(self, message: str):
        """Log error message."""
        self._log("ERROR", message, force=True)

    def success(self, message: str):
        """Log success message."""
        self._log("OK", message, force=True)

    def set_verbose(self, verbose: bool):
        """Toggle verbose logging."""
        self.verbose = verbose

    def set_gui_callback(self, callback: Callable[[str], None]):
        """Set GUI callback for log display."""
        self.gui_callback = callback

    def close(self):
        """Close log file."""
        if hasattr(self, '_file') and self._file:
            self._file.close()


# Global logger instance
_logger_instance = None


def get_logger() -> ThreadLogger:
    """Get global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ThreadLogger()
    return _logger_instance


def init_logger(log_dir: str = None,
                gui_callback: Callable[[str], None] = None,
                verbose: bool = True) -> ThreadLogger:
    """Initialize global logger with custom settings."""
    global _logger_instance
    _logger_instance = ThreadLogger(log_dir, gui_callback, verbose)
    return _logger_instance
