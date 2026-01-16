"""
Config Manager - Auto-save configuration
"""
import json
import os
from pathlib import Path
from typing import Any


class Config:
    """Configuration manager with auto-save functionality."""
    
    DEFAULT_CONFIG = {
        "thread_count": 1,
        "batch_size": 10,
        "delay_ms": 1000,
        "chrome_position": "left",
        "images_dir": "./images/",
        "videos_dir": "./videos/",
        "profiles_dir": "./profiles/",
        "openrouter_api_key": "",
        "openrouter_model": "",
        "timeout_seconds": 60,
        "verbose_logging": True,
        "logged_in": False
    }
    
    def __init__(self, config_path: str = None):
        """Initialize config manager."""
        if config_path is None:
            # Get path relative to exe/script
            base_dir = Path(__file__).parent.parent
            self.config_path = base_dir / "config.json"
        else:
            self.config_path = Path(config_path)
        
        self._config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load config from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(loaded)
                    return config
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_CONFIG.copy()
        else:
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: dict = None):
        """Save config to file."""
        if config is None:
            config = self._config
        
        # Ensure parent directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set config value and auto-save."""
        self._config[key] = value
        self._save_config()
    
    def get_all(self) -> dict:
        """Get all config values."""
        return self._config.copy()
    
    def update(self, values: dict):
        """Update multiple values and auto-save."""
        self._config.update(values)
        self._save_config()
    
    def reset(self):
        """Reset to default config."""
        self._config = self.DEFAULT_CONFIG.copy()
        self._save_config()
    
    def get_path(self, key: str) -> Path:
        """Get path config value resolved relative to app root."""
        path_str = self.get(key, "")
        if not path_str:
            return None
        
        path = Path(path_str)
        if not path.is_absolute():
            base_dir = Path(__file__).parent.parent
            path = base_dir / path
        
        return path


# Global config instance
_config_instance = None


def get_config() -> Config:
    """Get global config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
