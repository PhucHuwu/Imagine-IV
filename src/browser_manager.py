"""
Browser Manager - Undetected ChromeDriver with Chrome profile management
"""
import os
import threading
from pathlib import Path
from typing import Optional, Tuple

import undetected_chromedriver as uc

from .config import get_config
from .logger import get_logger
from .process_cleaner import get_cleaner


# Lock to prevent race condition when initializing Chrome driver
_driver_lock = threading.Lock()


class BrowserManager:
    """Manage Chrome browser instances with profiles using undetected-chromedriver."""
    
    def __init__(self, thread_id: int = 1):
        """
        Initialize browser manager for a specific thread.
        
        Args:
            thread_id: Thread identifier (1-20)
        """
        self.thread_id = thread_id
        self.config = get_config()
        self.logger = get_logger()
        self.driver: Optional[uc.Chrome] = None
    
    def _get_profile_path(self) -> Path:
        """Get Chrome profile path for this thread."""
        profiles_dir = self.config.get_path("profiles_dir")
        if profiles_dir is None:
            profiles_dir = Path("./profiles")
        
        profile_path = profiles_dir / f"Profile_{self.thread_id}"
        profile_path.mkdir(parents=True, exist_ok=True)
        
        return profile_path
    
    def _get_chrome_options(self) -> uc.ChromeOptions:
        """Configure Chrome options for undetected-chromedriver."""
        options = uc.ChromeOptions()
        
        # Disable password manager
        options.add_argument("--password-store=basic")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--disable-notifications")
        
        options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
            },
        )
        
        return options
    
    def _setup_window(self):
        """Setup window size and position after driver started."""
        if not self.driver:
            return
        
        try:
            # Get screen size via JavaScript
            screen_width = self.driver.execute_script("return window.screen.availWidth;")
            screen_height = self.driver.execute_script("return window.screen.availHeight;")
            
            # Window size = 1/6 of screen (3 columns x 2 rows)
            window_width = screen_width // 3
            window_height = screen_height // 2
            
            # Position: stagger each thread by offset
            offset = (self.thread_id - 1) * 30
            position_x = offset % (screen_width // 2)
            position_y = offset % (screen_height)
            
            self.driver.set_window_size(window_width, window_height)
            self.driver.set_window_position(position_x, position_y)
            
        except Exception as e:
            self.logger.warning(f"Không thể set kích thước cửa sổ: {e}")
    
    def start(self) -> bool:
        """
        Start Chrome browser using undetected-chromedriver.
        
        Returns:
            True if successful
        """
        try:
            self.logger.info(f"Đang khởi động Chrome cho luồng {self.thread_id}...")
            
            # Get Chrome options
            options = self._get_chrome_options()
            
            # Get profile path and set via options
            profile_path = self._get_profile_path()
            options.user_data_dir = str(profile_path)
            
            # Use lock to prevent race condition when initializing driver
            with _driver_lock:
                try:
                    self.driver = uc.Chrome(options=options)
                except Exception as e:
                    self.logger.error(f"Lỗi khởi tạo Chrome: {e}")
                    return False
            
            # Save PID for cleanup
            if hasattr(self.driver, 'browser_pid'):
                pid = self.driver.browser_pid
                get_cleaner().save_pid(pid)
                self.logger.success(f"Chrome đã khởi động (PID: {pid})")
            else:
                self.logger.success("Chrome đã khởi động")
            
            # Setup window size and position
            self._setup_window()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Không thể khởi động Chrome: {e}")
            return False
    
    def navigate(self, url: str) -> bool:
        """Navigate to URL."""
        if not self.driver:
            self.logger.error("Trình duyệt chưa khởi động")
            return False
        
        try:
            self.logger.info(f"Đang chuyển đến: {url}")
            self.driver.get(url)
            return True
        except Exception as e:
            self.logger.error(f"Chuyển trang thất bại: {e}")
            return False
    
    def get_driver(self) -> Optional[uc.Chrome]:
        """Get the WebDriver instance."""
        return self.driver
    
    def close(self):
        """Close browser."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info(f"Đã đóng Chrome cho luồng {self.thread_id}")
            except Exception as e:
                self.logger.warning(f"Lỗi khi đóng Chrome: {e}")
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
    
    def set_zoom(self, zoom_percent: int = 100):
        """Set page zoom level using Chrome DevTools Protocol.
        
        Args:
            zoom_percent: Target zoom level (e.g., 25 for 25%)
        """
        if not self.driver:
            return
            
        try:
            # Convert percent to scale factor (25% = 0.25)
            scale = zoom_percent / 100.0
            
            # Use CDP to set device metrics with scale
            self.driver.execute_cdp_cmd(
                "Emulation.setPageScaleFactor",
                {"pageScaleFactor": scale}
            )
            self.logger.info(f"Đã zoom xuống {zoom_percent}%")
        except Exception as e:
            self.logger.warning(f"Không thể set zoom: {e}")
