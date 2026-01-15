"""
Grok Automation - Interact with Grok Imagine website
"""
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .browser_manager import BrowserManager
from .config import get_config
from .logger import get_logger


class GrokAutomation:
    """Automate Grok Imagine for image and video generation."""
    
    # URLs
    GROK_URL = "https://grok.com"
    IMAGINE_URL = "https://grok.com/imagine"
    
    # Selectors (language-independent)
    PROMPT_INPUT = "div.tiptap.ProseMirror[contenteditable='true']"
    SUBMIT_BTN = "button[type='submit']"
    GENERATED_IMAGE = "img[src*='imagine-public']"
    GENERATED_VIDEO = "video[src*='imagine-public']"
    
    def __init__(self, browser_manager: BrowserManager):
        """
        Initialize Grok automation.
        
        Args:
            browser_manager: Browser manager instance
        """
        self.browser = browser_manager
        self.config = get_config()
        self.logger = get_logger()
        self.driver = browser_manager.get_driver()
    
    def navigate_to_imagine(self) -> bool:
        """Navigate to Grok Imagine page."""
        return self.browser.navigate(self.IMAGINE_URL)
    
    def enter_prompt(self, prompt: str) -> bool:
        """
        Enter prompt into the TipTap editor.
        
        Args:
            prompt: The prompt text to enter
            
        Returns:
            True if successful
        """
        if not self.driver:
            self.logger.error("Trình duyệt chưa khởi động")
            return False
        
        try:
            timeout = self.config.get("timeout_seconds", 60)
            
            # Wait for TipTap editor
            editor = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.PROMPT_INPUT))
            )
            
            # Clear existing content and enter new prompt via JavaScript
            # TipTap uses contenteditable, so we need JS to set content
            self.driver.execute_script("""
                const editor = arguments[0];
                editor.innerHTML = '<p>' + arguments[1] + '</p>';
                
                // Trigger input event to notify TipTap
                const event = new InputEvent('input', {
                    bubbles: true,
                    cancelable: true,
                });
                editor.dispatchEvent(event);
            """, editor, prompt)
            
            self.logger.info("Đã nhập prompt thành công")
            return True
            
        except TimeoutException:
            self.logger.error("Hết thời gian chờ ô nhập liệu")
            return False
        except Exception as e:
            self.logger.error(f"Không thể nhập prompt: {e}")
            return False
    
    def submit_prompt(self) -> bool:
        """Submit the prompt by clicking send button."""
        try:
            timeout = self.config.get("timeout_seconds", 60)
            
            # Wait for submit button to be clickable
            submit_btn = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, self.SUBMIT_BTN))
            )
            
            submit_btn.click()
            
            self.logger.info("Đã gửi prompt")
            return True
            
        except TimeoutException:
            self.logger.error("Hết thời gian chờ nút gửi")
            return False
        except Exception as e:
            self.logger.error(f"Không thể gửi prompt: {e}")
            return False
    
    def count_current_images(self) -> int:
        """Count current valid images on page (including Base64 JPEGs which are completed images)."""
        try:
            # Find all images that might be generated results
            images = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem'] img")
            count = 0
            for img in images:
                src = img.get_attribute("src") or ""
                # Valid images are either standard URLs containing 'imagine-public' (excluding thumbnails)
                # OR Base64 JPEGs (which user confirmed are "done" images)
                # We specifically exclude PNGs as those are placeholders
                is_valid_url = "imagine-public" in src and "_thumbnail" not in src
                is_valid_base64 = src.startswith("data:image/jpeg")
                
                if is_valid_url or is_valid_base64:
                    count += 1
            return count
        except Exception:
            return 0
    
    def is_generating(self) -> bool:
        """Check if generation is in progress by checking submit button disabled state."""
        try:
            submit_btn = self.driver.find_element(By.CSS_SELECTOR, self.SUBMIT_BTN)
            # Check if button has disabled attribute
            is_disabled = submit_btn.get_attribute("disabled") is not None
            return is_disabled
        except Exception:
            return False
    
    def has_invisible_elements(self) -> bool:
        """Check if there are elements with class 'invisible' (generating placeholders)."""
        try:
            # Check for any element with class 'invisible' inside the masonry container
            elements = self.driver.find_elements(By.CSS_SELECTOR, ".invisible")
            return len(elements) > 0
        except Exception:
            return False

    def wait_for_generation_complete(self, initial_count: int = 0, timeout: int = None) -> bool:
        """
        Smart polling: wait for generation to complete using multiple signals:
        1. Submit button state (is_generating)
        2. Presence of .invisible placeholders
        3. JPEG image count increase
        
        Args:
            initial_count: Number of images before submitting prompt
            timeout: Maximum wait time in seconds
            
        Returns:
            True if new images are generated
        """
        if timeout is None:
            timeout = self.config.get("timeout_seconds", 60)
        
        self.logger.info(f"Đang chờ tạo ảnh (ảnh hiện tại: {initial_count})...")
        
        start_time = time.time()
        was_generating = False
        invisible_seen = False
        
        # Helper to generate filename
        def get_timestamp_filename(idx):
            timestamp = datetime.now().strftime("%d-%m_%H-%M-%S")
            return f"{timestamp}_{idx:03d}.jpg"

        # Track processed images to prevent duplicates
        processed_srcs = set()
        output_dir = Path(self.config.get("images_dir", "./images"))
        output_dir.mkdir(parents=True, exist_ok=True)
        
        while time.time() - start_time < timeout:
            try:
                is_gen = self.is_generating()
                has_invisible = self.has_invisible_elements()
                has_placeholders = self.has_generating_placeholders()
                
                # Incremental Download Logic
                valid_images = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem'] img")
                current_count = 0
                
                for img in valid_images:
                    src = img.get_attribute("src") or ""
                    
                    # Logic identifying COMPLETED images (same as count_current_images)
                    is_valid_url = "imagine-public" in src and "_thumbnail" not in src
                    is_valid_base64 = src.startswith("data:image/jpeg")
                    
                    if is_valid_url or is_valid_base64:
                        current_count += 1
                        
                        # Use a hash or just the src content (if short enough) as key. 
                        # Base64 can be long, but safe enough for checking unique strings in memory for one session.
                        # For URLs, it's short.
                        if src not in processed_srcs:
                            self.logger.info(f"Phát hiện ảnh mới, đang tải xuống... ({current_count})")
                            try:
                                if is_valid_base64:
                                    # Handle Base64
                                    self._save_base64_image(src, output_dir, get_timestamp_filename(len(processed_srcs) + 1))
                                else:
                                    # Handle URL
                                    self._download_single_image(src, output_dir, get_timestamp_filename(len(processed_srcs) + 1))
                                
                                processed_srcs.add(src)
                                self.logger.success(f"Đã tải ảnh {len(processed_srcs)}")
                            except Exception as dl_err:
                                self.logger.error(f"Lỗi tải ảnh: {dl_err}")

                # Debug status every 5 seconds
                if int(time.time() - start_time) % 5 == 0:
                    self.logger.debug(f"Status: Gen={is_gen}, Invis={has_invisible}, Placeholders={has_placeholders}, Count={current_count}/{initial_count} (Downloaded: {len(processed_srcs)})")

                # Track states: considered generating if button disabled OR invisible items OR placeholder items
                if is_gen or has_invisible or has_placeholders:
                    if not was_generating:
                        self.logger.info("Phát hiện đang tạo ảnh...")
                    was_generating = True
                
                if has_invisible:
                    invisible_seen = True

                # Completion logic:
                if was_generating and not is_gen and not has_invisible and not has_placeholders:
                    if current_count > initial_count:
                        # Double check stabilization
                        time.sleep(2)
                        final_count = self.count_current_images()
                        # Final check to ensure no regression
                        if final_count > initial_count and not self.has_invisible_elements() and not self.has_generating_placeholders():
                            self.logger.success(f"Hoàn thành! Tổng số ảnh mới đã tải: {len(processed_srcs)}")
                            return True
                    else:
                        # Waiting for images to load/appear
                        pass
                
            except Exception as e:
                self.logger.debug(f"Lỗi khi kiểm tra: {e}")
            
            time.sleep(1)
        
        self.logger.error("Hết thời gian chờ tạo ảnh")
        return False

    def has_generating_placeholders(self) -> bool:
        """Check if there are generating placeholder images (Base64 PNGs) in the generation list."""
        try:
            # Check for images with data:image/png src inside list items
            # These are typically the blurred/loading placeholders
            elements = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listitem'] img[src^='data:image/png']")
            return len(elements) > 0
        except Exception:
            return False
    
    def wait_for_images(self, timeout: int = None, min_count: int = 1) -> bool:
        """
        Wait for images to be generated (legacy method, uses smart polling internally).
        
        Args:
            timeout: Maximum wait time in seconds
            min_count: Minimum number of NEW images to wait for
            
        Returns:
            True if images are ready
        """
        initial_count = self.count_current_images()
        return self.wait_for_generation_complete(initial_count, timeout)
    
    def get_image_urls(self, count: int = 4) -> List[str]:
        """
        Get URLs of generated images.
        
        Args:
            count: Maximum number of images to get
            
        Returns:
            List of image URLs
        """
        try:
            images = self.driver.find_elements(By.CSS_SELECTOR, self.GENERATED_IMAGE)
            
            urls = []
            for img in images:
                src = img.get_attribute("src")
                if src and "imagine-public" in src and "_thumbnail" not in src:
                    if src not in urls:  # Avoid duplicates
                        urls.append(src)
                        if len(urls) >= count:
                            break
            
            self.logger.info(f"Tìm thấy {len(urls)} ảnh")
            return urls
            
        except Exception as e:
            self.logger.error(f"Không thể lấy URL ảnh: {e}")
            return []
    
    def download_images(self, urls: List[str], output_dir: str) -> List[str]:
        """
        Download images from URLs.
        
        Args:
            urls: List of image URLs
            output_dir: Directory to save images
            
        Returns:
            List of saved file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = []
        timestamp = datetime.now().strftime("%d-%m_%H-%M-%S")
        
        for idx, url in enumerate(urls, 1):
            try:
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    filename = f"{timestamp}_{idx:03d}.jpg"
                    filepath = output_path / filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    saved_files.append(str(filepath))
                    self.logger.info(f"Đã tải: {filename}")
                else:
                    self.logger.error(f"Không thể tải ảnh {idx}: HTTP {response.status_code}")
                    
            except Exception as e:
                self.logger.error(f"Không thể tải ảnh {idx}: {e}")
        
        return saved_files
    
    def wait_for_video(self, timeout: int = None) -> bool:
        """
        Wait for video to be generated.
        
        Args:
            timeout: Maximum wait time in seconds
            
        Returns:
            True if video is ready
        """
        if timeout is None:
            timeout = self.config.get("timeout_seconds", 180)  # Videos take longer
        
        self.logger.info(f"Đang chờ video (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                videos = self.driver.find_elements(By.CSS_SELECTOR, self.GENERATED_VIDEO)
                
                for video in videos:
                    src = video.get_attribute("src") or ""
                    if "imagine-public" in src and ".mp4" in src:
                        time.sleep(2)
                        self.logger.success("Video đã sẵn sàng")
                        return True
                        
            except Exception:
                pass
            
            time.sleep(2)
        
        self.logger.error("Hết thời gian chờ video")
        return False
    
    def get_video_url(self) -> Optional[str]:
        """Get the URL of the generated video."""
        try:
            videos = self.driver.find_elements(By.CSS_SELECTOR, self.GENERATED_VIDEO)
            
            for video in videos:
                src = video.get_attribute("src")
                if src and "imagine-public" in src and ".mp4" in src:
                    return src
            
            self.logger.error("Không tìm thấy URL video")
            return None
            
        except Exception as e:
            self.logger.error(f"Không thể lấy URL video: {e}")
            return None
    
    def download_video(self, url: str, output_path: str) -> bool:
        """
        Download video from URL.
        
        Args:
            url: Video URL
            output_path: Path to save video
            
        Returns:
            True if successful
        """
        try:
            self.logger.info("Đang tải video...")
            
            response = requests.get(url, timeout=180, stream=True)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.logger.success(f"Đã lưu video: {output_path}")
                return True
            else:
                self.logger.error(f"Không thể tải video: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Không thể tải video: {e}")
            return False
    
    def _save_base64_image(self, base64_data: str, output_dir: Path, filename: str) -> bool:
        """Save Base64 image data to file."""
        import base64
        try:
            # Remove header if present (e.g., "data:image/jpeg;base64,")
            if "," in base64_data:
                base64_data = base64_data.split(",")[1]
            
            image_data = base64.b64decode(base64_data)
            filepath = output_dir / filename
            
            with open(filepath, "wb") as f:
                f.write(image_data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to save Base64 image: {e}")
            return False

    def _download_single_image(self, url: str, output_dir: Path, filename: str) -> bool:
        """Download a single image from URL."""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                filepath = output_dir / filename
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to download image {url}: {e}")
            return False

    def refresh_driver(self):
        """Refresh driver reference after browser restart."""
        self.driver = self.browser.get_driver()
