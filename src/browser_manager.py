"""
Browser Manager - Selenium WebDriver with Chrome profile management
"""
import os
from pathlib import Path
from typing import Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from .config import get_config
from .logger import get_logger
from .process_cleaner import get_cleaner


class BrowserManager:
    """Manage Chrome browser instances with profiles."""
    
    def __init__(self, thread_id: int = 1):
        """
        Initialize browser manager for a specific thread.
        
        Args:
            thread_id: Thread identifier (1-20)
        """
        self.thread_id = thread_id
        self.config = get_config()
        self.logger = get_logger()
        self.driver: Optional[webdriver.Chrome] = None
    
    def _get_profile_path(self) -> Path:
        """Get Chrome profile path for this thread."""
        profiles_dir = self.config.get_path("profiles_dir")
        if profiles_dir is None:
            profiles_dir = Path("./profiles")
        
        profile_path = profiles_dir / f"thread_{self.thread_id}"
        profile_path.mkdir(parents=True, exist_ok=True)
        
        return profile_path
    
    def _get_window_position(self) -> Tuple[int, int]:
        """Get window position based on config (left/right monitor)."""
        position = self.config.get("chrome_position", "left")
        
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            
            if len(monitors) == 1:
                # Single monitor - use small window
                return (0, 0)
            
            if position == "right" and len(monitors) > 1:
                # Right monitor
                right_monitor = monitors[1]
                return (right_monitor.x, right_monitor.y)
            else:
                # Left monitor (default)
                return (0, 0)
                
        except ImportError:
            self.logger.warning("screeninfo not installed, using default position")
            return (0, 0)
        except Exception as e:
            self.logger.warning(f"Failed to get monitor info: {e}")
            return (0, 0)
    
    def _get_chrome_options(self) -> Options:
        """Configure Chrome options."""
        options = Options()
        
        # Use persistent profile
        profile_path = self._get_profile_path()
        options.add_argument(f"--user-data-dir={profile_path}")
        
        # Disable automation flags
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Disable notifications
        options.add_argument("--disable-notifications")
        
        # Disable infobars
        options.add_argument("--disable-infobars")
        
        # Start maximized or set size
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            
            if len(monitors) == 1:
                # Single monitor - small window with zoom
                options.add_argument("--window-size=400,300")
                options.add_argument("--force-device-scale-factor=0.25")
            else:
                # Multiple monitors - normal size
                options.add_argument("--start-maximized")
                
        except ImportError:
            options.add_argument("--window-size=800,600")
        
        return options
    
    def start(self) -> bool:
        """
        Start Chrome browser.
        
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Starting Chrome for thread {self.thread_id}...")
            
            # Get Chrome options
            options = self._get_chrome_options()
            
            # Install and get chromedriver
            service = Service(ChromeDriverManager().install())
            
            # Create driver
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Save PID for cleanup
            pid = self.driver.service.process.pid
            get_cleaner().save_pid(pid)
            
            # Set window position
            x, y = self._get_window_position()
            self.driver.set_window_position(x, y)
            
            self.logger.success(f"Chrome started (PID: {pid})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start Chrome: {e}")
            return False
    
    def navigate(self, url: str) -> bool:
        """Navigate to URL."""
        if not self.driver:
            self.logger.error("Browser not started")
            return False
        
        try:
            self.logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            return True
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            return False
    
    def get_driver(self) -> Optional[webdriver.Chrome]:
        """Get the WebDriver instance."""
        return self.driver
    
    def close(self):
        """Close browser."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info(f"Chrome closed for thread {self.thread_id}")
            except Exception as e:
                self.logger.warning(f"Error closing Chrome: {e}")
            finally:
                self.driver = None
    
    def is_running(self) -> bool:
        """Check if browser is running."""
        if not self.driver:
            return False
        
        try:
            # Try to get current URL to check if browser is alive
            _ = self.driver.current_url
            return True
        except Exception:
            return False
