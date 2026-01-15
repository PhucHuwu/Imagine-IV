"""
Browser Manager - Undetected ChromeDriver with Chrome profile management
"""
import os
from pathlib import Path
from typing import Optional, Tuple

import undetected_chromedriver as uc

from .config import get_config
from .logger import get_logger
from .process_cleaner import get_cleaner


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
        
        profile_path = profiles_dir / f"thread_{self.thread_id}"
        profile_path.mkdir(parents=True, exist_ok=True)
        
        return profile_path
    
    def _get_window_size(self) -> Tuple[int, int]:
        """Get window size (1/6 of screen)."""
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            primary = monitors[0]
            
            # 1/6 of screen = roughly 3 columns x 2 rows
            width = primary.width // 3
            height = primary.height // 2
            
            return (width, height)
            
        except Exception:
            # Fallback to reasonable size
            return (640, 360)
    
    def _get_window_position(self) -> Tuple[int, int]:
        """Get window position based on thread_id (staggered)."""
        try:
            import screeninfo
            monitors = screeninfo.get_monitors()
            primary = monitors[0]
            
            # Calculate offset based on thread_id (stagger windows)
            offset = (self.thread_id - 1) * 30  # 30px offset per thread
            
            # Stay in top-left area
            x = offset % (primary.width // 2)
            y = offset % (primary.height // 2)
            
            return (x, y)
            
        except ImportError:
            self.logger.warning("screeninfo chưa cài, sử dụng vị trí mặc định")
            return (0, 0)
        except Exception as e:
            self.logger.warning(f"Không lấy được thông tin màn hình: {e}")
            return (0, 0)
    
    def _get_chrome_options(self) -> uc.ChromeOptions:
        """Configure Chrome options for undetected-chromedriver."""
        options = uc.ChromeOptions()
        
        # Disable notifications
        options.add_argument("--disable-notifications")
        
        # Disable infobars
        options.add_argument("--disable-infobars")
        
        # Get window size (1/6 of screen)
        width, height = self._get_window_size()
        options.add_argument(f"--window-size={width},{height}")
        
        return options
    
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
            
            # Get profile path
            profile_path = self._get_profile_path()
            
            # Create undetected Chrome driver
            self.driver = uc.Chrome(
                options=options,
                user_data_dir=str(profile_path),
                use_subprocess=True
            )
            
            # Save PID for cleanup
            if hasattr(self.driver, 'browser_pid'):
                pid = self.driver.browser_pid
                get_cleaner().save_pid(pid)
                self.logger.success(f"Chrome đã khởi động (PID: {pid})")
            else:
                self.logger.success("Chrome đã khởi động")
            
            # Set window position
            x, y = self._get_window_position()
            self.driver.set_window_position(x, y)
            
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
